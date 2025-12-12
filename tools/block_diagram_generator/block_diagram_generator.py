from client import HephoraClient
from writer import RstWriter
from pathlib import Path
from typing import Dict, Any, List


def main() -> None:
    # Standard docs path
    out_dir = Path("tools/block_diagram_generator/out")

    client = HephoraClient("http://http_server:8080")
    writer = RstWriter(Path("tools/block_diagram_generator/templates"))

    # Fetch software components from Hephora
    components = client.list_nodes("sw_component")
    component_dicts: List[Dict[str, Any]] = []
    for component in components:
        component_id = component["id"]
        component_details = client.get_node("sw_component", component_id)
        component_dicts.append({
            "label": component_details.get("label"),
            "id": component_id,
        })

    #Fetch interfaces from Hephora
    interfaces = client.list_nodes("sw_interface")
    interface_dicts: List[Dict[str, Any]] = []
    for interface in interfaces:
        interface_id = interface["id"]
        interface_details = client.get_node("sw_interface", interface_id)
        i_fields = interface_details.get("fields", {})
        interface_dicts.append({
            "label": interface_details.get("label"),
            "id": interface_id,
            "provided_by": i_fields.get("provided_by"),
            "required_by": i_fields.get("required_by"),
        })

    writer.write(
        "block_diagram.puml.j2",
        {
            "components": component_dicts,
            "interfaces": interface_dicts,
        },
        out_dir / "block_diagram.puml",
    )

    writer.write(
        "block_diagram.mmd.j2",
        {
            "components": component_dicts,
            "interfaces": interface_dicts,
        },
        out_dir / "block_diagram.mmd",
    )

if __name__ == "__main__":
    main()