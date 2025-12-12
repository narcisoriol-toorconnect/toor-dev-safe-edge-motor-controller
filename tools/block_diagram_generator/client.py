from __future__ import annotations
import requests
from typing import Any, Dict, List, Optional

class HephoraClient:
    def __init__(self, base_url: str, token: Optional[str] = None, timeout: int = 20):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = timeout
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def list_nodes(self, profile: str) -> List[Dict[str, Any]]:
        r = self.session.get(f"{self.base_url}/nodes/list", json={"profile": profile}, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        return data.get("nodes", data)

    def get_node(self, profile: str, node_id: str) -> Dict[str, Any]:
        r = self.session.get(f"{self.base_url}/nodes", json={"profile": profile, "id": node_id}, timeout=self.timeout)
        r.raise_for_status()
        return r.json().get("node", r.json())

    def list_children(self, profile: str, node_id: str) -> List[Dict[str, Any]]:
        r = self.session.get(f"{self.base_url}/nodes/children", json={"profile": profile, "id": node_id}, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        return data.get("nodes", data)