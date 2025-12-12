from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

class RstWriter:
    def __init__(self, templates_dir: Path):
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(enabled_extensions=("j2",)),
            # Preserve whitespace/newlines to keep RST list-table and toctree formatting stable
            trim_blocks=False, lstrip_blocks=False,
        )

    def write(self, template_name: str, context: dict, out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tpl = self.env.get_template(template_name)
        out_path.write_text(tpl.render(**context), encoding="utf-8")