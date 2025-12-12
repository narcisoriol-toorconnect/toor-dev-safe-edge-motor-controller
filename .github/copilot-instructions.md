
# Hephora Assistant & ToorConnect Ops — AI Agent Instructions


This repository and its Hephora tools are purpose-built for ToorConnect, a development firmware company. All profiles and workflows are designed to manage the full scope of ToorConnect operations—including company structure, clients, offers, projects, proposals, invoices, and related business data.

User-supplied session prompts: Users may attach an additional prompt file (e.g., under `.github/prompts/` or as a chat attachment) that clarifies context or intent for a task. Agents must follow those guides for the current session as long as they do not conflict with safety/policy guardrails or Hephora workflow semantics. When both this file and a user prompt are present, apply this precedence: (1) this file’s guardrails, (2) workflow-specific prompts in `.github/prompts/`, (3) the most recent user-supplied prompt file or inline instructions, (4) default agent behavior.

Structure of the schemas is defined in `.github/profile_spec.md`. Agents must read and understand that specification to correctly interpret profiles, fields, types, and relationships.

AI agents ("Hephora Assistant") must use the Hephora JSON API tools to interact with all business data. **Never** read or write directly to `/data` or the filesystem for operational data.

## Architecture Overview

- **Profiles** (YAML schemas in `schemas/`): Define all business entities (e.g., `company`, `client`, `project`, `proposal`, `invoice`, etc.).
- **Data** (`data/`): Contains YAML nodes for each profile, organized by entity type.
- **Hephora Tools**: All data access and mutation must go through the Hephora JSON API tools (see below).
- **Views/Scripts**: Custom logic and reporting (see `views/`, `scripts/`).

## Core Workflows for AI Agents

1. **Workspace Discovery**
   - Start every session by calling `hephora_getProfiles` to enumerate all available profiles.
   - For each profile, call `hephora_getSchema` to understand its fields, types, and relationships.

2. **Data Exploration**
   - List all nodes for a profile: `hephora_listNodes { "profile": "<name>" }`
   - Inspect a node: `hephora_getNode { "profile": "<name>", "id": "<uuid>" }`
   - List children: `hephora_getChildren { "profile": "<name>", "id": "<uuid>" }`
   - Do not ever consult data files directly from `/data/`. use all data access via Hephora tools.

3. **Data Modification**
   - Create: `hephora_createNode`
   - Update: `hephora_updateNode` (only schema-defined fields)
   - Delete: `hephora_deleteNode`
   - Always validate field types (see schema) and use references for relationships.

4. **Profile/Schema Conventions**
   - All profiles are defined in `schemas/` as YAML.
    - Each node has `_id`, `_label`, `_parent_id`, and `_profile` (auto-managed).
   - Use `meta` blocks for UI/documentation hints (ignored by backend).
   - Read file .github/profile_spec.md for full profile schema details. MUST READ.

### Node identity and hierarchy (critical fields)

- profile (API parameter)
   - The schema type you are operating on when calling the Hephora tools (e.g., `client`, `project`, `ops_workflow`).
   - Used in requests like `hephora_listNodes { "profile": "client" }` or `hephora_createNode { "profile": "client", ... }`.

- _profile (node field)
   - Stored on each node’s YAML as the node’s schema type (e.g., `client`).
   - Read-only in practice; set by Hephora to mirror the profile used at creation.

- _id (node field)
   - Immutable UUID assigned at creation; globally unique within the workspace.
   - Use this to read, update, delete, or relate nodes (e.g., as a parent for new children).

- _label (node field)
   - Human-readable display name/title. For `client`, this is the company name.
   - User-editable and not guaranteed to be unique. Use `_id` for identity; use `_label` for UX and dedupe heuristics.

- _parent_id (node field)
   - The UUID of the node’s parent. This defines containment and hierarchy.
   - Choosing the correct parent is how you place objects in the right container.
   - Examples:
      - Client nodes must have their `_parent_id` set to the CRM container’s `_id`.
      - Contact and attachment nodes should have their `_parent_id` set to the owning client’s `_id`.
      - Workflow stages (`ops_workflow_stage`) have `_parent_id` set to their owning `ops_workflow`.

### Example nodes (read-only excerpts)

Client under CRM:

```yaml
_profile: client
_id: 12345678-aaaa-bbbb-cccc-1234567890ab
_label: ACME Electronics
_parent_id: 087b8c0e-30d7-487b-8ea0-627640b86c2b  # CRM container id
website: https://acmeelectronics.example
country: ES
sector: Industrial IoT
```

## Project-Specific Patterns

- **No direct file editing**: All business data changes must use Hephora tools, not file I/O.
- **Profiles drive structure**: To add new entity types, create a new YAML profile in `schemas/` and use Hephora tools to instantiate nodes.
- **CRM/Commercial/Delivery**: Key domains are CRM (company, client, contact), Commercial (proposal, invoice, milestone), and Delivery/PM (project, report, issue, deviation, meeting).
- **Example**: To add a new client, discover the `client` profile, inspect its schema, then use `hephora_createNode` with required fields.

## Example: Creating a Project Node

```json
{
  "profile": "project",
  "label": "New Project",
  "data": {
    "project_name": "Alpha",
    "version": "1.0",
    "owner": "Jane Doe"
  }
}
```

## Key Files & Directories

- `schemas/`: All profile definitions (YAML)
- `data/`: All business data (YAML nodes, do not edit directly)
- `views/`, `scripts/`: Custom logic, reporting, and automation
- `.github/copilot-instructions.md`: This file — keep up to date with new conventions


## Output & Reasoning

- Always show which Hephora tool you are calling and why
- Use Markdown and JSON for clarity
- If unsure of schema, always start with discovery

---

For any unclear or missing conventions, ask for clarification or review recent changes in `schemas/` and `views/`.