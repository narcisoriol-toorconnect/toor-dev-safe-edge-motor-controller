from __future__ import annotations
from pathlib import Path

CONF_PY = """\
import sphinx_rtd_theme
project = "Hephora Generated Docs"
extensions = [
   "sphinx.ext.autosectionlabel",
   "sphinx_rtd_theme",
]
templates_path = ["_templates"]
exclude_patterns = []
html_theme = "sphinx_rtd_theme"
autosectionlabel_prefix_document = True
"""

INDEX_RST = """\
Hephora Documentation
=====================

.. toctree::
   :maxdepth: 2

   project/index
   requirements/index
   architecture/index
   design/index
   unit_tests/index
"""

SECTION_TPL = """\
{{ title }}
{{ '=' * len(title) }}

.. note::
   This section is created by bootstrap. Generators will populate it.
"""

def ensure_sphinx_skeleton(source_dir: Path):
   """Create a Sphinx source tree with common sections for the project.

   Structure:
     - project/
     - requirements/
     - architecture/
     - design/
     - unit_tests/
   """

   (source_dir / "_templates").mkdir(parents=True, exist_ok=True)

   # Always ensure core files exist (overwrite to keep config up to date)
   (source_dir / "conf.py").write_text(CONF_PY, encoding="utf-8")
   (source_dir / "index.rst").write_text(INDEX_RST, encoding="utf-8")

   # Define sections and friendly titles
   sections = [
      ("project", "Project Overview"),
      ("requirements", "Software Requirements"),
      ("architecture", "Software Architecture"),
      ("design", "Software Design"),
      ("unit_tests", "Unit Tests"),
   ]

   # Create directories and placeholder index.rst for each section
   for folder, title in sections:
      section_dir = source_dir / folder
      section_dir.mkdir(parents=True, exist_ok=True)
      section_index = section_dir / "index.rst"
      if not section_index.exists():
         # Only create placeholder if user hasn't authored content yet
         section_index.write_text(
            SECTION_TPL.replace("{{ title }}", title).replace("{{ '=' * len(title) }}", "=" * len(title)),
            encoding="utf-8",
         )