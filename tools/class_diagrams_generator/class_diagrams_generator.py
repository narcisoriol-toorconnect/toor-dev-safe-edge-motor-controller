from client import HephoraClient
from writer import RstWriter
from pathlib import Path
from typing import Dict, Any, List


def main() -> None:
    # Standard docs path
    out_dir = Path("tools/class_diagrams_generator/out")

    client = HephoraClient("http://http_server:8080")
    writer = RstWriter(Path("tools/class_diagrams_generator/templates"))

    # Fetch all sw_units
    sw_us = client.list_nodes("sw_unit")
    for sw_u in sw_us:
        main_class: Dict[str, Any] = []
        classes: List[Dict[str, Any]] = []
        sw_u_details = client.get_node("sw_unit", sw_u["id"])
        # Fetch attributes that belong to this sw_unit (if any)
        try:
            sw_u_children = client.list_children("sw_unit", sw_u["id"])
        except Exception:
            sw_u_children = []

        raw_attrs  = []
        raw_methods = []
        raw_relationships = []
        for c in sw_u_children:
            if c["profile"] == "sw_unit_attribute":
                raw_attrs.append(client.get_node("sw_unit_attribute", c["id"]))
            elif c["profile"] == "sw_unit_method":
                raw_methods.append(client.get_node("sw_unit_method", c["id"]))
            elif c["profile"] == "sw_unit_relationship":
                raw_relationships.append(client.get_node("sw_unit_relationship", c["id"]))

        # Gather attributes
        attrs: List[Dict[str, Any]] = []
        for a in raw_attrs:
            # Try to resolve data type label if data_type is present
            type_label = None
            data_type_id = a.get("fields").get("data_type")
            if data_type_id:
                try:
                    dt = client.get_node("sw_unit_data_type", data_type_id)
                    type_label = dt.get("label")
                except Exception:
                    type_label = data_type_id

            attrs.append(
                {
                    "name": a.get("label"),
                    "type": type_label,
                    "scope": a.get("fields").get("scope"),
                    "multiplicity": a.get("fields").get("multiplicity"),
                }
            )

        #Gather methods
        meths : List[Dict[str, Any]] = []
        for m in raw_methods:
            return_type_label = None
            try:
                return_type_id = m.get("fields").get("return").get("data_type")
            except Exception:
                return_type_id = None
            if return_type_id:
                try:
                    rt = client.get_node("sw_unit_data_type", return_type_id)
                    return_type_label = rt.get("label")
                except Exception:
                    return_type_label = return_type_id
            else:
                try:
                    return_type_id = m.get("fields").get("return").get("unit_ref")
                except Exception:
                    return_type_id = None
                if return_type_id:
                    try:
                        rt = client.get_node("sw_unit", return_type_id)
                        return_type_label = rt.get("label")
                    except Exception:
                        return_type_label = return_type_id

            if return_type_label == None:
                return_type_label = ""


            # Get parameters type and name (may be multiple)
            params: List[Dict[str, Any]] = []
            try:
                raw_params = m.get("fields", {}).get("parameters", []) or []
            except Exception:
                raw_params = []

            for p in raw_params:
                # resolve parameter type (data_type or unit_ref)
                p_type_label = None
                data_type_id = p.get("data_type")
                if data_type_id:
                    try:
                        dt = client.get_node("sw_unit_data_type", data_type_id)
                        p_type_label = dt.get("label")
                    except Exception:
                        p_type_label = data_type_id
                else:
                    unit_ref_id = p.get("unit_ref")
                    if unit_ref_id:
                        try:
                            ur = client.get_node("sw_unit", unit_ref_id)
                            p_type_label = ur.get("label")
                        except Exception:
                            p_type_label = unit_ref_id

                params.append(
                    {
                        "name": p.get("name"),
                        "type": p_type_label,
                    }
                )

            meths.append(
                {
                    "name": m.get("label"),
                    "scope": m.get("fields").get("scope"),
                    "return_type": return_type_label,
                    "parameters": params,
                }
            )

        main_class = {
                "label": sw_u_details.get("label"),
                "id": sw_u["id"],
                "attributes": attrs,
                "methods": meths,
            }

        dependencies: List[Dict[str, Any]] = []
        associations: List[Dict[str, Any]] = []
        aggregations: List[Dict[str, Any]] = []
        compositions: List[Dict[str, Any]] = []
        realizations: List[Dict[str, Any]] = []
        generalizations: List[Dict[str, Any]] = []
        #Gather relationships
        for r in raw_relationships:
            fields = r.get("fields", {})
            # Get related class (target may be missing)
            target_id = fields.get("target")
            r_class = None
            if target_id:
                try:
                    r_class = client.get_node("sw_unit", target_id)
                except Exception:
                    r_class = {"label": target_id, "id": target_id}

            # Gather attributes and methods from the related class
            rel_attrs: List[Dict[str, Any]] = []
            rel_methods: List[Dict[str, Any]] = []
            if r_class and r_class.get("id"):
                try:
                    rel_children = client.list_children("sw_unit", r_class.get("id"))
                except Exception:
                    rel_children = []

                for rc in rel_children:
                    # Attributes
                    if rc.get("profile") == "sw_unit_attribute":
                        try:
                            a = client.get_node("sw_unit_attribute", rc.get("id"))
                        except Exception:
                            a = None
                        if a:
                            # resolve data type label if present
                            type_label = None
                            data_type_id = a.get("fields", {}).get("data_type")
                            if data_type_id:
                                try:
                                    dt = client.get_node("sw_unit_data_type", data_type_id)
                                    type_label = dt.get("label")
                                except Exception:
                                    type_label = data_type_id

                            rel_attrs.append(
                                {
                                    "name": a.get("label"),
                                    "type": type_label,
                                    "scope": a.get("fields", {}).get("scope"),
                                    "multiplicity": a.get("fields", {}).get("multiplicity"),
                                }
                            )

                    # Methods
                    elif rc.get("profile") == "sw_unit_method":
                        try:
                            m = client.get_node("sw_unit_method", rc.get("id"))
                        except Exception:
                            m = None
                        if m:
                            return_type_label = None
                            try:
                                return_type_id = m.get("fields", {}).get("return", {}).get("data_type")
                            except Exception:
                                return_type_id = None
                            if return_type_id:
                                try:
                                    rt = client.get_node("sw_unit_data_type", return_type_id)
                                    return_type_label = rt.get("label")
                                except Exception:
                                    return_type_label = return_type_id
                            else:
                                try:
                                    return_type_id = m.get("fields", {}).get("return", {}).get("unit_ref")
                                except Exception:
                                    return_type_id = None
                                if return_type_id:
                                    try:
                                        rt = client.get_node("sw_unit", return_type_id)
                                        return_type_label = rt.get("label")
                                    except Exception:
                                        return_type_label = return_type_id

                            if return_type_label is None:
                                return_type_label = ""

                            # Get parameters type and name (may be multiple)
                            params: List[Dict[str, Any]] = []
                            try:
                                raw_params = m.get("fields", {}).get("parameters", []) or []
                            except Exception:
                                raw_params = []

                            for p in raw_params:
                                p_type_label = None
                                data_type_id = p.get("data_type")
                                if data_type_id:
                                    try:
                                        dt = client.get_node("sw_unit_data_type", data_type_id)
                                        p_type_label = dt.get("label")
                                    except Exception:
                                        p_type_label = data_type_id
                                else:
                                    unit_ref_id = p.get("unit_ref")
                                    if unit_ref_id:
                                        try:
                                            ur = client.get_node("sw_unit", unit_ref_id)
                                            p_type_label = ur.get("label")
                                        except Exception:
                                            p_type_label = unit_ref_id

                                params.append(
                                    {
                                        "name": p.get("name"),
                                        "type": p_type_label,
                                    }
                                )

                            rel_methods.append(
                                {
                                    "name": m.get("label"),
                                    "scope": m.get("fields", {}).get("scope"),
                                    "return_type": return_type_label,
                                    "parameters": params,
                                }
                            )

            # Append to classes if we have a related class
            if r_class:
                classes.append(
                    {
                        "label": r_class.get("label"),
                        "id": r_class.get("id"),
                        "attributes": rel_attrs,
                        "methods": rel_methods,
                    }
                )

            # Prepare common multiplicities (may be missing)
            origin_mult = fields.get("source_multiplicity", "")
            target_mult = fields.get("target_multiplicity", "")
            rel_type = fields.get("type", "")

            # Get dependency type and append safely
            entry = {"id": target_id, "origin_multiplicity": origin_mult, "target_multiplicity": target_mult}

            if rel_type == "association":
                associations.append(entry)
            elif rel_type == "dependency":
                dependencies.append(entry)
            elif rel_type == "aggregation":
                aggregations.append(entry)
            elif rel_type == "composition":
                compositions.append(entry)
            elif rel_type == "realization":
                realizations.append(entry)
            elif rel_type == "generalization":
                generalizations.append(entry)

        writer.write(
            "class_diagram.mmd.j2",
            {
                "main_class": main_class,
                "classes" : classes,
                "dependencies": dependencies,
                "associations": associations,
                "aggregations": aggregations,
                "compositions": compositions,
                "realizations": realizations,
                "generalizations": generalizations,
            },
            out_dir / f"{sw_u_details.get('label')}-{sw_u['id']}.mmd",
        )

if __name__ == "__main__":
    main()