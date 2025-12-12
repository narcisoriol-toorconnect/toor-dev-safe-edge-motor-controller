
from client import HephoraClient
from writer import RstWriter
from bootstrap import ensure_sphinx_skeleton
from pathlib import Path
from typing import Dict, Any, List
import shutil


def main() -> None:
    # Standard docs path
    out_dir = Path("tools/hephora_docgen/docs/source")
    ensure_sphinx_skeleton(out_dir)

    client = HephoraClient("http://http_server:8080")
    writer = RstWriter(Path("tools/hephora_docgen/templates"))

    # -------------------- Project Overview --------------------
    v_models = client.list_nodes("v_model")
    assert v_models, "No v_model nodes found"
    v_model = client.get_node("v_model", v_models[0]["id"])
    # Normalize v_model fields as server returns {label, id, fields:{description, client, version}}
    v_fields: Dict[str, Any] = v_model.get("fields", {})
    v_label = v_model.get("label") or v_model.get("_label", "Project Overview")
    writer.write(
        "project/index.rst.j2",
        {
            "title": v_label,
            "description": v_fields.get("description"),
            "client": v_fields.get("client"),
            "version": v_fields.get("version"),
        },
        out_dir / "project" / "index.rst",
    )

    # -------------------- Requirements --------------------
    groups: List[Dict[str, Any]] = client.list_nodes("sw_requirements_group")
    group_pages: List[Dict[str, Any]] = []

    # Preload all requirements (avoid many network calls if needed)
    all_requirements: List[Dict[str, Any]] = []
    try:
        all_requirements = [client.get_node("sw_requirement", r["id"]) for r in client.list_nodes("sw_requirement")]
    except Exception:
        pass

    for g in groups:
        g_node = client.get_node("sw_requirements_group", g["id"])
        g_fields: Dict[str, Any] = g_node.get("fields", {})
        group_label = g_node.get("label") or g_node.get("_label", "Group")
        group_slug = group_label.replace(" ", "-")

        # Filter requirements by parent id (new shape uses top-level 'parent')
        reqs_filtered: List[Dict[str, Any]] = []
        for r in all_requirements:
            parent = r.get("parent") or r.get("_parent_id")
            if parent == g_node.get("id") or parent == g_node.get("_id"):
                r_fields = r.get("fields", {})
                r_label = r.get("label") or r.get("_label")
                req_slug = (r_label or "").replace(" ", "-")
                reqs_filtered.append({
                    "label": r_label,
                    "brief": r_fields.get("brief"),
                    "slug": req_slug,
                })

                # Write requirement detail page
                writer.write(
                    "requirements/item.rst.j2",
                    {
                        "label": r_label,
                        "brief": r_fields.get("brief"),
                        "details": r_fields.get("details"),
                        "rationale": r_fields.get("rationale"),
                        "acceptance_criteria": r_fields.get("acceptance_criteria"),
                    },
                    out_dir / "requirements" / "items" / f"{req_slug}.rst",
                )

        writer.write(
            "requirements/group.rst.j2",
            {
                "group_label": group_label,
                "description": g_fields.get("description"),
                "requirements": reqs_filtered,
            },
            out_dir / "requirements" / "groups" / f"{group_slug}.rst",
        )

        group_pages.append({
            "label": group_label,
            "doc_path": f"groups/{group_slug}",
            "description": g_fields.get("description"),
        })

    writer.write(
        "requirements/index.rst.j2",
        {"groups": group_pages},
        out_dir / "requirements" / "index.rst",
    )
    
    # -------------------- Architecture --------------------
    architectures: List[Dict[str, Any]] = client.list_nodes("sw_architecture")
    if architectures:
        arch = client.get_node("sw_architecture", architectures[0]["id"])  # single architecture for now
        a_fields: Dict[str, Any] = arch.get("fields", {})
        arch_label = arch.get("label") or arch.get("_label", "Software Architecture")

        # Collect attachments from architecture fields (copy assets into _static/attachments)
        attachments_meta: List[Dict[str, Any]] = []
        try:
            att_ids = a_fields.get("attachments") or []
            static_dir = out_dir / "_static" / "attachments"
            static_dir.mkdir(parents=True, exist_ok=True)
            for aid in att_ids:
                try:
                    anode = client.get_node("attachment", aid)
                    afields = anode.get("fields", {}) or {}
                    src_path = (afields.get("filepath") or anode.get("filepath") or "").strip()
                    if not src_path:
                        continue
                    # Resolve and copy file if it exists
                    src = Path(src_path)
                    if not src.is_absolute():
                        src = Path.cwd() / src
                    if src.exists() and src.is_file():
                        dest = static_dir / src.name
                        try:
                            shutil.copyfile(src, dest)
                        except Exception:
                            # Best effort; if copy fails, still reference original path
                            dest = src
                        # Build path relative to architecture/index.rst (one level deeper than docs root)
                        if dest.exists():
                            rel_from_arch = Path("..") / "_static" / "attachments" / dest.name
                            doc_rel = rel_from_arch.as_posix()
                        else:
                            doc_rel = src_path
                    else:
                        # If file not found, prefix with .. so user sees attempted path relative to architecture page
                        doc_rel = (Path("..") / src_path).as_posix() if not src_path.startswith("..") else src_path
                    lower = src.suffix.lower()
                    is_image = lower in [".png", ".jpg", ".jpeg", ".svg", ".gif", ".bmp", ".webp"]
                    attachments_meta.append({
                        "filename": src.name,
                        "doc_path": doc_rel,
                        "description": afields.get("description") or anode.get("description"),
                        "is_image": is_image,
                    })
                except Exception:
                    continue
        except Exception:
            attachments_meta = []

        # Collect components belonging to this architecture (by parent)
        comps_raw: List[Dict[str, Any]] = []
        try:
            comps_raw = [client.get_node("sw_component", c["id"]) for c in client.list_nodes("sw_component")]
        except Exception:
            comps_raw = []

        # Preload interfaces and data structures for relationship resolution
        interfaces_raw: List[Dict[str, Any]] = []
        data_structures_raw: List[Dict[str, Any]] = []
        try:
            interfaces_raw = [client.get_node("sw_interface", i["id"]) for i in client.list_nodes("sw_interface")]
        except Exception:
            interfaces_raw = []
        try:
            data_structures_raw = [client.get_node("sw_data_structure", d["id"]) for d in client.list_nodes("sw_data_structure")]
        except Exception:
            data_structures_raw = []
        ds_map = {d.get("id"): d for d in data_structures_raw}

        components = []
        for c in comps_raw:
            parent = c.get("parent") or c.get("_parent_id")
            if parent == arch.get("id") or parent == arch.get("_id"):
                c_fields = c.get("fields", {})
                c_label = c.get("label") or c.get("_label", "Component")
                slug = c_label.replace(" ", "-")
                # Collect requirement labels linked to this component
                req_ids = c_fields.get("sw_requirements") or []
                req_links_arch: List[Dict[str, str]] = []
                req_links_comp: List[Dict[str, str]] = []
                for rid in req_ids:
                    try:
                        r = client.get_node("sw_requirement", rid)
                        r_label = r.get("label") or r.get("_label", "")
                        r_slug = (r_label or "").replace(" ", "-")
                        req_links_arch.append({
                            "label": r_label,
                            # architecture/index.rst lives under architecture/, so use relative path to requirements/items
                            "doc_path": f"../requirements/items/{r_slug}",
                        })
                        req_links_comp.append({
                            "label": r_label,
                            # component pages live under architecture/components/
                            "doc_path": f"../../requirements/items/{r_slug}",
                        })
                    except Exception:
                        pass

                # Interfaces related to this component (provided_by / required_by reference this component)
                provided_ifaces = []
                required_ifaces = []
                related_ds_set = set()
                for iface in interfaces_raw:
                    f_fields = iface.get("fields", {}) or {}
                    provided_by = f_fields.get("provided_by") or []
                    required_by = f_fields.get("required_by") or []
                    if c.get("id") in provided_by or c.get("id") in required_by:
                        iface_label = iface.get("label") or iface.get("_label", "Interface")
                        # Details
                        direction = f_fields.get("data_direction")
                        comm = f_fields.get("communication") or {}
                        mode = (comm or {}).get("mode")
                        ctype = (comm or {}).get("type")
                        # Data structures linked to interface
                        ds_ids = f_fields.get("sw_data_structures") or []
                        ds_labels = []
                        for did in ds_ids:
                            dnode = ds_map.get(did)
                            if dnode:
                                dlabel = dnode.get("label") or dnode.get("_label", "Data Structure")
                                ds_labels.append(dlabel)
                                related_ds_set.add(dlabel)
                        iface_entry = {
                            "label": iface_label,
                            "direction": direction,
                            "mode": mode,
                            "comm_type": ctype,
                            "data_structures": ds_labels,
                        }
                        if c.get("id") in provided_by:
                            provided_ifaces.append(iface_entry)
                        if c.get("id") in required_by:
                            required_ifaces.append(iface_entry)

                related_data_structures = [
                    {"label": lbl}
                    for lbl in sorted(related_ds_set)
                ]

                components.append({
                    "label": c_label,
                    "slug": slug,
                    "description": c_fields.get("description"),
                    "requirements": req_links_arch,
                    "requirements_for_component": req_links_comp,
                    "provided_interfaces": provided_ifaces,
                    "required_interfaces": required_ifaces,
                    "data_structures": related_data_structures,
                    "doc_path": f"components/{slug}",
                })

        # Build interface and data structure page metadata (global lists)
        interfaces_pages = []
        for iface in interfaces_raw:
            f_fields = iface.get("fields", {}) or {}
            iface_label = iface.get("label") or iface.get("_label", "Interface")
            iface_slug = (iface_label or "").replace(" ", "-")
            interfaces_pages.append({
                "label": iface_label,
                "slug": iface_slug,
                "doc_path": f"interfaces/{iface_slug}",
            })

        data_structures_pages = []
        for ds in data_structures_raw:
            ds_fields = ds.get("fields", {}) or {}
            ds_label = ds.get("label") or ds.get("_label", "Data Structure")
            ds_slug = (ds_label or "").replace(" ", "-")
            data_structures_pages.append({
                "label": ds_label,
                "slug": ds_slug,
                "doc_path": f"data_structures/{ds_slug}",
            })

        # Write architecture index with description and components list plus global interface & data structure toctrees
        writer.write(
            "architecture/index.rst.j2",
            {
                "title": arch_label,
                "description": a_fields.get("description"),
                "components": components,
                "interfaces_all": interfaces_pages,
                "data_structures_all": data_structures_pages,
                "attachments": attachments_meta,
            },
            out_dir / "architecture" / "index.rst",
        )

        # Write per-component detail pages
        for comp in components:
            # Convert interfaces lists to include doc_path and linkable data structures
            def map_iface(i: Dict[str, Any]) -> Dict[str, Any]:
                ds = i.get("data_structures") or []
                ds_objs = [
                    {
                        "label": lbl,
                        "doc_path": f"../data_structures/{(lbl or '').replace(' ', '-')}"
                    }
                    for lbl in ds
                ]
                return {
                    **i,
                    "doc_path": f"../interfaces/{(i.get('label') or '').replace(' ', '-')}",
                    "data_structures": ds_objs,
                }

            writer.write(
                "architecture/component.rst.j2",
                {
                    "title": comp["label"],
                    "description": comp.get("description"),
                    "requirements": comp.get("requirements_for_component", []),
                    "provided_interfaces": [map_iface(i) for i in comp.get("provided_interfaces", [])],
                    "required_interfaces": [map_iface(i) for i in comp.get("required_interfaces", [])],
                    "data_structures": [
                        {
                            **d,
                            "doc_path": f"../data_structures/{(d['label'] or '').replace(' ', '-')}"
                        }
                        for d in comp.get("data_structures", [])
                    ],
                },
                out_dir / "architecture" / "components" / f"{comp['slug']}.rst",
            )

        # Write interface detail pages
        for iface in interfaces_raw:
            f_fields = iface.get("fields", {}) or {}
            iface_label = iface.get("label") or iface.get("_label", "Interface")
            iface_slug = (iface_label or "").replace(" ", "-")
            provided_by_ids = f_fields.get("provided_by") or []
            required_by_ids = f_fields.get("required_by") or []
            req_ids = f_fields.get("sw_requirements") or []
            ds_ids = f_fields.get("sw_data_structures") or []

            def comp_entry(cid: str) -> Dict[str, str]:
                try:
                    comp_node = client.get_node("sw_component", cid)
                    label = comp_node.get("label") or comp_node.get("_label", "Component")
                    slug = (label or "").replace(" ", "-")
                    return {"label": label, "doc_path": f"../components/{slug}"}
                except Exception:
                    return {"label": cid, "doc_path": ""}

            provided_by = [comp_entry(cid) for cid in provided_by_ids]
            required_by = [comp_entry(cid) for cid in required_by_ids]

            requirements_entries = []
            for rid in req_ids:
                try:
                    rnode = client.get_node("sw_requirement", rid)
                    rlabel = rnode.get("label") or rnode.get("_label", "")
                    rslug = (rlabel or "").replace(" ", "-")
                    requirements_entries.append({
                        "label": rlabel,
                        "doc_path": f"../../requirements/items/{rslug}",
                    })
                except Exception:
                    pass

            ds_entries = []
            for did in ds_ids:
                dnode = ds_map.get(did)
                if dnode:
                    dlabel = dnode.get("label") or dnode.get("_label", "Data Structure")
                    dslug = (dlabel or "").replace(" ", "-")
                    ds_entries.append({"label": dlabel, "doc_path": f"../data_structures/{dslug}"})

            writer.write(
                "architecture/interface.rst.j2",
                {
                    "title": iface_label,
                    "description": f_fields.get("description"),
                    "direction": f_fields.get("data_direction"),
                    "mode": (f_fields.get("communication") or {}).get("mode"),
                    "comm_type": (f_fields.get("communication") or {}).get("type"),
                    "provided_by": provided_by,
                    "required_by": required_by,
                    "data_structures": ds_entries,
                    "requirements": requirements_entries,
                },
                out_dir / "architecture" / "interfaces" / f"{iface_slug}.rst",
            )

        # Write data structure detail pages
        for ds in data_structures_raw:
            ds_fields = ds.get("fields", {}) or {}
            ds_label = ds.get("label") or ds.get("_label", "Data Structure")
            ds_slug = (ds_label or "").replace(" ", "-")
            field_entries = []
            for f in (ds_fields.get("fields") or []):
                field_entries.append({
                    "name": f.get("name"),
                    "data_type": f.get("data_type"),
                })
            writer.write(
                "architecture/data_structure.rst.j2",
                {
                    "title": ds_label,
                    "description": ds_fields.get("description"),
                    "fields": field_entries,
                },
                out_dir / "architecture" / "data_structures" / f"{ds_slug}.rst",
            )

    # -------------------- Design (Detailed) --------------------
    designs: List[Dict[str, Any]] = client.list_nodes("sw_design")
    if designs:
        design = client.get_node("sw_design", designs[0]["id"])  # single design for now
        d_fields: Dict[str, Any] = design.get("fields", {})
        design_label = design.get("label") or design.get("_label", "Software Design")

        # Gather units under design (children sw_unit)
        units_raw: List[Dict[str, Any]] = []
        try:
            units_raw = [client.get_node("sw_unit", u["id"]) for u in client.list_nodes("sw_unit")]
        except Exception:
            units_raw = []

        # Build a global map of units for cross-page linking
        units_map: Dict[str, Dict[str, str]] = {}
        for u in units_raw:
            try:
                ulab = u.get("label") or u.get("_label") or (u.get("fields") or {}).get("name") or "Unit"
                uslug = (ulab or "").replace(" ", "-")
                units_map[u.get("id")] = {"label": ulab, "slug": uslug, "doc_path": f"design/items/{uslug}"}
            except Exception:
                continue

        # Attachments for design (children attachments)
        design_attachments: List[Dict[str, Any]] = []
        try:
            att_nodes = []
            # We attempt to load attachments referenced directly in design's children definition.
            # The backend may expose them via list_nodes("attachment") and filter by parent.
            for att in client.list_nodes("attachment"):
                parent = att.get("parent") or att.get("_parent_id")
                if parent == design.get("id"):
                    att_nodes.append(client.get_node("attachment", att["id"]))
            static_dir = out_dir / "_static" / "design_attachments"
            static_dir.mkdir(parents=True, exist_ok=True)
            for anode in att_nodes:
                afields = anode.get("fields", {}) or {}
                src_path = (afields.get("filepath") or anode.get("filepath") or "").strip()
                if not src_path:
                    continue
                src = Path(src_path)
                if not src.is_absolute():
                    src = Path.cwd() / src
                if src.exists() and src.is_file():
                    dest = static_dir / src.name
                    try:
                        shutil.copyfile(src, dest)
                        rel_path = Path("..") / "_static" / "design_attachments" / dest.name
                    except Exception:
                        rel_path = Path("..") / src_path
                else:
                    rel_path = Path("..") / src_path
                is_image = src.suffix.lower() in [".png", ".jpg", ".jpeg", ".svg", ".gif", ".bmp", ".webp"]
                design_attachments.append({
                    "filename": src.name,
                    "doc_path": rel_path.as_posix(),
                    "description": afields.get("description") or anode.get("description"),
                    "is_image": is_image,
                })
        except Exception:
            design_attachments = []

        # Preload unit-related subnodes for detail pages
        unit_data_types_raw: List[Dict[str, Any]] = []
        unit_methods_raw: List[Dict[str, Any]] = []
        unit_attributes_raw: List[Dict[str, Any]] = []
        unit_relationships_raw: List[Dict[str, Any]] = []
        try:
            unit_data_types_raw = [client.get_node("sw_unit_data_type", n["id"]) for n in client.list_nodes("sw_unit_data_type")]
        except Exception:
            pass
        try:
            unit_methods_raw = [client.get_node("sw_unit_method", n["id"]) for n in client.list_nodes("sw_unit_method")]
        except Exception:
            pass
        try:
            unit_attributes_raw = [client.get_node("sw_unit_attribute", n["id"]) for n in client.list_nodes("sw_unit_attribute")]
        except Exception:
            pass
        try:
            unit_relationships_raw = [client.get_node("sw_unit_relationship", n["id"]) for n in client.list_nodes("sw_unit_relationship")]
        except Exception:
            pass

        # Build a global map of unit data types for cross-unit linking (dt_id -> anchors)
        dt_map_global: Dict[str, Dict[str, str]] = {}
        for dt in unit_data_types_raw:
            try:
                parent_u = dt.get("parent") or dt.get("_parent_id")
                u_meta = units_map.get(parent_u) or {}
                dtf = dt.get("fields", {}) or {}
                dt_label = dt.get("label") or dt.get("_label") or dtf.get("name") or "DataType"
                dt_slug = (dt_label or "").replace(" ", "-")
                unit_slug = u_meta.get("slug") or ""
                anchor = f"dt-{unit_slug}-{dt_slug}" if unit_slug else f"dt-{dt_slug}"
                dt_map_global[dt.get("id")] = {
                    "label": dt_label,
                    "slug": dt_slug,
                    "unit_slug": unit_slug,
                    "unit_label": u_meta.get("label") or "",
                    "anchor": anchor,
                    "doc_path": f"design/items/{unit_slug}"
                }
            except Exception:
                continue

        # Index of design units
        units_summary = []
        for u in units_raw:
            parent = u.get("parent") or u.get("_parent_id")
            if parent == design.get("id"):
                u_fields = u.get("fields", {}) or {}
                u_label = u.get("label") or u.get("_label", "Unit")
                u_slug = (u_label or "").replace(" ", "-")
                units_summary.append({
                    "label": u_label,
                    "slug": u_slug,
                    "description": u_fields.get("description"),
                    "doc_path": f"items/{u_slug}",
                })

        # Write design index
        def fix_description_rst(text: str | None) -> str | None:
            if not text:
                return text
            try:
                # Ensure a blank line before nested bullet lists after a colon-terminated line
                return text.replace(":\n  -", ":\n\n  -")
            except Exception:
                return text

        writer.write(
            "design/index.rst.j2",
            {
                "title": design_label,
                "description": fix_description_rst(d_fields.get("description")),
                "units": units_summary,
                "attachments": design_attachments,
            },
            out_dir / "design" / "index.rst",
        )

        # Build per-unit detail pages
        for u in units_raw:
            parent = u.get("parent") or u.get("_parent_id")
            if parent != design.get("id"):
                continue
            u_fields = u.get("fields", {}) or {}
            u_label = u.get("label") or u.get("_label", "Unit")
            u_slug = (u_label or "").replace(" ", "-")

            # Attributes
            attributes = []
            for a in unit_attributes_raw:
                if (a.get("parent") or a.get("_parent_id")) == u.get("id"):
                    af = a.get("fields", {}) or {}
                    # Resolve data type label and link display
                    dt_id = af.get("data_type")
                    dt_meta = dt_map_global.get(dt_id)
                    dt_label = client.get_node("sw_unit_data_type", dt_id).get("label") if dt_id else None
                    dt_display = f":ref:`{dt_meta['label']} <{dt_meta['anchor']}>`" if dt_meta else (dt_label or "-")
                    attributes.append({
                        "label": a.get("label") or a.get("_label") or af.get("name"),
                        "description": af.get("description"),
                        "data_type": dt_label,
                        "data_type_display": dt_display,
                        "scope": af.get("scope"),
                    })

            # Methods
            methods = []
            for m in unit_methods_raw:
                if (m.get("parent") or m.get("_parent_id")) == u.get("id"):
                    mf = m.get("fields", {}) or {}
                    m_label = m.get("label") or m.get("_label") or mf.get("name")
                    params = []
                    for p in (mf.get("parameters") or []):
                        p_dt_id = p.get("data_type")
                        p_dt_meta = dt_map_global.get(p_dt_id)
                        p_dt_label = client.get_node("sw_unit_data_type", p_dt_id).get("label") if p_dt_id else None
                        # If a unit_ref exists, try to link to that unit page
                        p_unit_ref_id = p.get("unit_ref")
                        p_unit_meta = units_map.get(p_unit_ref_id) if p_unit_ref_id else None
                        p_unit_display = f":ref:`{p_unit_meta['label']} <unit-{p_unit_meta['slug']}>`" if p_unit_meta else None
                        p_dt_display = f":ref:`{p_dt_meta['label']} <{p_dt_meta['anchor']}>`" if p_dt_meta else (p_dt_label or p_unit_display or "")
                        params.append({
                            "name": p.get("name"),
                            "description": p.get("description"),
                            "data_type": p_dt_label,
                            "data_type_display": p_dt_display,
                            "unit_ref": client.get_node("sw_unit", p.get("unit_ref")).get("label") if p.get("unit_ref") else None,
                        })
                    ret = mf.get("return") or {}
                    ret_dt_id = ret.get("data_type") if ret else None
                    ret_dt_meta = dt_map_global.get(ret_dt_id) if ret_dt_id else None
                    ret_dt_label = client.get_node("sw_unit_data_type", ret_dt_id).get("label") if ret_dt_id else None
                    ret_unit_ref_id = ret.get("unit_ref") if ret else None
                    ret_unit_meta = units_map.get(ret_unit_ref_id) if ret_unit_ref_id else None
                    ret_unit_display = f":ref:`{ret_unit_meta['label']} <unit-{ret_unit_meta['slug']}>`" if ret_unit_meta else None
                    ret_dt_display = f":ref:`{ret_dt_meta['label']} <{ret_dt_meta['anchor']}>`" if ret_dt_meta else (ret_dt_label or ret_unit_display or "")
                    methods.append({
                        "label": m_label,
                        "description": mf.get("description"),
                        "scope": mf.get("scope"),
                        "parameters": params,
                        "return": {
                            "description": ret.get("description"),
                            "data_type": ret_dt_label,
                            "data_type_display": ret_dt_display,
                            "unit_ref": client.get_node("sw_unit", ret.get("unit_ref")).get("label") if ret.get("unit_ref") else None,
                        } if ret else None,
                    })

            # Data types defined under this unit
            data_types = []
            for dt in unit_data_types_raw:
                if (dt.get("parent") or dt.get("_parent_id")) == u.get("id"):
                    dtf = dt.get("fields", {}) or {}
                    dt_label = dt.get("label") or dt.get("_label") or dtf.get("name")
                    dt_slug = (dt_label or "").replace(" ", "-")
                    fields_list = []
                    for f in (dtf.get("fields") or []):
                        f_dt_id = f.get("data_type")
                        f_dt_meta = dt_map_global.get(f_dt_id)
                        f_dt_label = client.get_node("sw_unit_data_type", f_dt_id).get("label") if f_dt_id else None
                        f_dt_display = f":ref:`{f_dt_meta['label']} <{f_dt_meta['anchor']}>`" if f_dt_meta else (f_dt_label or (client.get_node("sw_unit", f.get("unit_ref")).get("label") if f.get("unit_ref") else None) or "-")
                        fields_list.append({
                            "name": f.get("name"),
                            "data_type": f_dt_label,
                            "data_type_display": f_dt_display,
                            "unit_ref": client.get_node("sw_unit", f.get("unit_ref")).get("label") if f.get("unit_ref") else None,
                        })
                    enum_values = []
                    for ev in (dtf.get("enum_values") or []):
                        enum_values.append({
                            "name": ev.get("name"),
                            "value": ev.get("value"),
                            "description": ev.get("description"),
                        })
                    data_types.append({
                        "label": dt_label,
                        "slug": dt_slug,
                        "kind": dtf.get("kind"),
                        "alias_of": dtf.get("alias_of"),
                        "description": dtf.get("description"),
                        "fields": fields_list,
                        "enum_values": enum_values,
                        "function_pointer_parameters": dtf.get("function_pointer_parameters"),
                        "function_pointer_return": dtf.get("function_pointer_return"),
                    })

            # Interfaces provided (references) - convert to labels
            provided_interface_ids = u_fields.get("interfaces_provided") or []
            provided_interfaces = []
            for iid in provided_interface_ids:
                try:
                    iface = client.get_node("sw_interface", iid)
                    ilabel = iface.get("label") or iface.get("_label", "Interface")
                    provided_interfaces.append({
                        "label": ilabel,
                        # from design/items/ -> up two levels to root then into architecture/interfaces/
                        "doc_path": f"../../architecture/interfaces/{(ilabel or '').replace(' ', '-')}",
                    })
                except Exception:
                    pass

            # Components referenced
            component_ids = u_fields.get("sw_component_refs") or []
            components_refs = []
            for cid in component_ids:
                try:
                    comp_node = client.get_node("sw_component", cid)
                    clabel = comp_node.get("label") or comp_node.get("_label", "Component")
                    components_refs.append({
                        "label": clabel,
                        # from design/items/ -> up two levels to root then into architecture/components/
                        "doc_path": f"../../architecture/components/{(clabel or '').replace(' ', '-')}",
                    })
                except Exception:
                    pass

            # Unit attachments
            unit_attachments = []
            try:
                att_nodes = []
                # Prefer listing children of the unit (more reliable than scanning all attachments)
                try:
                    children = client.list_children("sw_unit", u.get("id")) or []
                except Exception:
                    children = []
                # Collect attachment child nodes
                for child in children:
                    # Some backends include 'profile' on child entries; if available, filter by it
                    profile = child.get("profile") or child.get("_profile") or ""
                    cid = child.get("id") or child.get("_id")
                    if not cid:
                        continue
                    if profile == "attachment":
                        try:
                            att_nodes.append(client.get_node("attachment", cid))
                        except Exception:
                            continue
                # Fallback: scan all attachments and match by parent id if no children were found
                if not att_nodes:
                    try:
                        for att in client.list_nodes("attachment"):
                            parent_att = att.get("parent") or att.get("_parent_id")
                            if parent_att == u.get("id"):
                                att_nodes.append(client.get_node("attachment", att["id"]))
                    except Exception:
                        pass

                static_dir = out_dir / "_static" / "unit_attachments"
                static_dir.mkdir(parents=True, exist_ok=True)
                for anode in att_nodes:
                    afields = anode.get("fields", {}) or {}
                    # Some backends may store filepath at the top level
                    src_path = (afields.get("filepath") or anode.get("filepath") or "").strip()
                    if not src_path:
                        continue
                    src = Path(src_path)
                    if not src.is_absolute():
                        src = Path.cwd() / src
                    if src.exists() and src.is_file():
                        dest = static_dir / src.name
                        try:
                            shutil.copyfile(src, dest)
                            # Unit item pages live under design/items/, which is two levels below the docs root
                            # Static assets are referenced from the docs root under _static/
                            rel_path = Path("..") / ".." / "_static" / "unit_attachments" / dest.name
                        except Exception:
                            rel_path = Path("..") / ".." / src_path
                    else:
                        rel_path = Path("..") / ".." / src_path
                    is_image = src.suffix.lower() in [".png", ".jpg", ".jpeg", ".svg", ".gif", ".bmp", ".webp"]
                    unit_attachments.append({
                        "filename": src.name,
                        "doc_path": rel_path.as_posix(),
                        "description": afields.get("description") or anode.get("description"),
                        "is_image": is_image,
                    })
            except Exception:
                unit_attachments = []

            writer.write(
                "design/unit.rst.j2",
                {
                    "title": u_label,
                    "description": u_fields.get("description"),
                    "unit_slug": u_slug,
                    "attributes": attributes,
                    "methods": methods,
                    "data_types": data_types,
                    "provided_interfaces": provided_interfaces,
                    "components_refs": components_refs,
                    "attachments": unit_attachments,
                },
                out_dir / "design" / "items" / f"{u_slug}.rst",
            )
    
    # -------------------- Unit Tests --------------------
    try:
        strategies_raw: List[Dict[str, Any]] = client.list_nodes("sw_unit_test_strategy")
    except Exception:
        strategies_raw = []

    # Build a minimal units map for linking (independent of design section)
    units_raw_for_tests: List[Dict[str, Any]] = []
    try:
        units_raw_for_tests = [client.get_node("sw_unit", u["id"]) for u in client.list_nodes("sw_unit")]
    except Exception:
        pass
    units_map_tests: Dict[str, Dict[str, str]] = {}
    for u in units_raw_for_tests:
        try:
            ulab = u.get("label") or u.get("_label") or (u.get("fields") or {}).get("name") or "Unit"
            uslug = (ulab or "").replace(" ", "-")
            units_map_tests[u.get("id")] = {"label": ulab, "slug": uslug, "doc_path": f"design/items/{uslug}"}
        except Exception:
            continue

    strategies_pages: List[Dict[str, Any]] = []

    for s in strategies_raw:
        try:
            strategy = client.get_node("sw_unit_test_strategy", s["id"])
        except Exception:
            continue
        s_fields = strategy.get("fields", {}) or {}
        s_label = strategy.get("label") or strategy.get("_label") or "Unit Test Strategy"
        s_slug = (s_label or "").replace(" ", "-")

        # Gather plans under the strategy
        plans_nodes: List[Dict[str, Any]] = []
        try:
            children = client.list_children("sw_unit_test_strategy", strategy.get("id")) or []
        except Exception:
            children = []
        for ch in children:
            profile = ch.get("profile") or ch.get("_profile") or ""
            cid = ch.get("id") or ch.get("_id")
            if profile == "sw_unit_test_plan" and cid:
                try:
                    plans_nodes.append(client.get_node("sw_unit_test_plan", cid))
                except Exception:
                    continue
        if not plans_nodes:
            try:
                for p in client.list_nodes("sw_unit_test_plan"):
                    parent = p.get("parent") or p.get("_parent_id")
                    if parent == strategy.get("id"):
                        plans_nodes.append(client.get_node("sw_unit_test_plan", p["id"]))
            except Exception:
                pass

        plans_render: List[Dict[str, Any]] = []
        for p in plans_nodes:
            pf = p.get("fields", {}) or {}
            p_label = p.get("label") or p.get("_label") or "Test Plan"
            p_slug = (p_label or "").replace(" ", "-")
            p_unit_id = pf.get("sw_unit")
            p_unit_meta = units_map_tests.get(p_unit_id)

            # Collect test cases and evidences
            test_cases: List[Dict[str, Any]] = []
            evidences_nodes: List[Dict[str, Any]] = []
            try:
                p_children = client.list_children("sw_unit_test_plan", p.get("id")) or []
            except Exception:
                p_children = []
            for ch in p_children:
                profile = ch.get("profile") or ch.get("_profile") or ""
                cid = ch.get("id") or ch.get("_id")
                if profile == "sw_unit_test_case" and cid:
                    try:
                        test_cases.append(client.get_node("sw_unit_test_case", cid))
                    except Exception:
                        continue
                if profile == "attachment" and cid:
                    try:
                        evidences_nodes.append(client.get_node("attachment", cid))
                    except Exception:
                        continue
            if not test_cases:
                try:
                    for tc in client.list_nodes("sw_unit_test_case"):
                        parent = tc.get("parent") or tc.get("_parent_id")
                        if parent == p.get("id"):
                            test_cases.append(client.get_node("sw_unit_test_case", tc["id"]))
                except Exception:
                    pass

            # Copy evidences
            evidences_meta: List[Dict[str, Any]] = []
            static_dir = out_dir / "_static" / "unit_test_evidences"
            static_dir.mkdir(parents=True, exist_ok=True)
            for anode in evidences_nodes:
                af = anode.get("fields", {}) or {}
                src_path = (af.get("filepath") or anode.get("filepath") or "").strip()
                if not src_path:
                    continue
                src = Path(src_path)
                if not src.is_absolute():
                    src = Path.cwd() / src
                if src.exists() and src.is_file():
                    dest = static_dir / src.name
                    try:
                        shutil.copyfile(src, dest)
                        rel_path = Path("..") / ".." / "_static" / "unit_test_evidences" / dest.name
                    except Exception:
                        rel_path = Path("..") / ".." / src_path
                else:
                    rel_path = Path("..") / ".." / src_path
                is_image = src.suffix.lower() in [".png", ".jpg", ".jpeg", ".svg", ".gif", ".bmp", ".webp"]
                evidences_meta.append({
                    "filename": src.name,
                    "doc_path": rel_path.as_posix(),
                    "description": af.get("description") or anode.get("description"),
                    "is_image": is_image,
                })

            # Prepare test cases for plan page and generate per-test-case pages
            tc_render: List[Dict[str, Any]] = []
            for tc in test_cases:
                tcf = tc.get("fields", {}) or {}
                tc_label = tc.get("label") or tc.get("_label") or "Test Case"
                tc_slug = (tc_label or "").replace(" ", "-")
                tc_ctx = {
                    "title": tc_label,
                    "description": tcf.get("description"),
                    "preconditions": tcf.get("preconditions"),
                    "steps": tcf.get("steps"),
                    "expected_result": tcf.get("expected_result"),
                    "status": tcf.get("status"),
                }
                # Write individual test case page
                writer.write(
                    "unit_tests/test_case.rst.j2",
                    tc_ctx,
                    out_dir / "unit_tests" / "cases" / f"{tc_slug}.rst",
                )
                # Use path relative to the plan page (plans/ -> ../cases/)
                tc_render.append({
                    "label": tc_label,
                    "doc_path": f"../cases/{tc_slug}",
                    "description": tcf.get("description"),
                    "preconditions": tcf.get("preconditions"),
                    "steps": tcf.get("steps"),
                    "expected_result": tcf.get("expected_result"),
                    "status": tcf.get("status"),
                })

            writer.write(
                "unit_tests/plan.rst.j2",
                {
                    "title": p_label,
                    "description": pf.get("description"),
                    "unit": ({"label": p_unit_meta.get("label"), "doc_path": f"../../{p_unit_meta.get('doc_path')}"} if p_unit_meta else None),
                    "test_cases": tc_render,
                    "evidences": evidences_meta,
                },
                out_dir / "unit_tests" / "plans" / f"{p_slug}.rst",
            )

            plans_render.append({
                "label": p_label,
                "slug": p_slug,
                "description": pf.get("description"),
                "doc_path": f"../plans/{p_slug}",
                "test_cases_count": len(tc_render),
                "evidences_count": len(evidences_meta),
                "unit": ({"label": p_unit_meta.get("label"), "doc_path": f"../../{p_unit_meta.get('doc_path')}"} if p_unit_meta else None),
            })

        writer.write(
            "unit_tests/strategy.rst.j2",
            {
                "title": s_label,
                "description": s_fields.get("description"),
                "tools": s_fields.get("tools"),
                "environment": s_fields.get("environment"),
                "plans": plans_render,
            },
            out_dir / "unit_tests" / "strategies" / f"{s_slug}.rst",
        )

        strategies_pages.append({"label": s_label, "slug": s_slug, "doc_path": f"strategies/{s_slug}"})

    # Unit tests index
    writer.write(
        "unit_tests/index.rst.j2",
        {
            "strategies": strategies_pages,
        },
        out_dir / "unit_tests" / "index.rst",
    )

    # Ensure root index references unit_tests/index
    try:
        root_index = out_dir / "index.rst"
        text = root_index.read_text(encoding="utf-8")
        if "unit_tests/index" not in text:
            lines = text.splitlines()
            # Append after design/index if present
            inserted = False
            for i, line in enumerate(lines):
                if line.strip() == "design/index":
                    lines.insert(i + 1, "   unit_tests/index")
                    inserted = True
                    break
            if not inserted:
                lines.append("   unit_tests/index")
            root_index.write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        pass

if __name__ == "__main__":
    main()