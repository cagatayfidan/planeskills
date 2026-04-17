# plane-task-creator

A Claude skill that creates tasks (work items) in [Plane](https://plane.so) Cloud through the public REST API — with full support for priorities, states, assignees, labels, modules, cycles, parent items, estimates, and due dates.

When installed, Claude can turn natural requests like *"create a Safari login bug in the Engineering project, assign it to Ayşe, high priority"* or *"Plane'de ENG-42'nin alt task'ı olarak yeni bir issue aç"* into real Plane work items. Claude handles the tedious part — looking up projects, resolving people/labels/states to UUIDs — so you just describe the task.

## Requirements

- A Plane Cloud account (app.plane.so) or a self-hosted Plane instance
- **A Plane API key** (see setup below)
- Python 3 (standard library only — no `pip install` needed)

## API key setup

This skill requires a personal access token from Plane. Without one, the skill cannot reach the API.

1. Log in to Plane and open **Profile Settings → Personal Access Tokens**
2. Click **Add personal access token**
3. Give it a title (e.g. "Claude skill") and an optional expiry
4. Copy the token — it starts with `plane_api_...`
5. Export it as an environment variable in your shell:

   ```bash
   export PLANE_API_KEY='plane_api_xxxxxxxxxxxxxxxx'
   ```

   To persist it across sessions, add the line to `~/.zshrc`, `~/.bashrc`, or your shell's equivalent config file.

**Never paste the token into chat.** The skill reads it only from the environment — it's never logged or written to disk.

### Self-hosted instances

If you run Plane on your own infrastructure, also set:

```bash
export PLANE_BASE_URL='https://plane.yourcompany.com/api/v1'
```

Otherwise the skill defaults to `https://api.plane.so/api/v1`.

## Installation

### Claude.ai / Claude Desktop

1. Download [`plane-task-creator.skill`](./plane-task-creator.skill) from the [releases page](../../releases) (or package it yourself — see below)
2. In Claude, go to **Customize → Skills → Upload skill**
3. Select the `.skill` file and enable it

### Claude Code

Clone this repo into your skills directory:

```bash
git clone https://github.com/<your-username>/plane-task-creator.git ~/.claude/skills/plane-task-creator
```

Claude Code picks it up automatically in the current session.

## Usage

Once enabled and the API key is set, just ask Claude in natural language:

- *"Create a task in Plane: fix the login bug in Engineering, assign to Ayşe, high priority"*
- *"Log these five items from the meeting notes as Plane tasks in the Product project"*
- *"Open a sub-task under ENG-42 for the database migration step"*
- *"What projects do I have in Plane?"*

Claude will walk through resolution and confirm before creating each task.

### Using the CLI directly

The bundled Python client also works as a standalone tool:

```bash
# List projects in a workspace
python scripts/plane_client.py list-projects my-team

# List metadata (states, labels, members, modules, cycles)
python scripts/plane_client.py list-metadata my-team <project_id> --kind members

# Create a task
python scripts/plane_client.py create-task my-team <project_id> \
    --name "Fix Safari login bug" \
    --priority high \
    --assignees <user_uuid>

# Attach a work item to a cycle (done after creation)
python scripts/plane_client.py attach-cycle my-team <project_id> <cycle_id> <work_item_id>
```

Run `python scripts/plane_client.py --help` for the full command list.

You can also import it in Python:

```python
from plane_client import PlaneClient

c = PlaneClient()  # reads PLANE_API_KEY from env
task = c.create_work_item(
    "my-team",
    "<project_id>",
    name="Fix Safari login bug",
    priority="high",
    assignees=["<user_uuid>"],
)
print(task["id"], task["sequence_id"])
```

## Repository structure

```
plane-task-creator/
├── SKILL.md                    # Skill entry point — instructions Claude follows
├── scripts/
│   └── plane_client.py         # Python API client (stdlib only)
└── references/
    └── api_reference.md        # Full Plane API reference for the endpoints used
```

## Features

- ✅ Create work items with all advanced fields (assignees, labels, modules, parent, estimate, dates)
- ✅ Attach work items to cycles
- ✅ Resolve human names to UUIDs automatically (states, labels, members, modules, cycles)
- ✅ Look up work items by human identifier (e.g. `ENG-42`) for parent resolution
- ✅ List projects and project metadata
- ✅ Works with Plane Cloud and self-hosted instances
- ✅ No external dependencies — uses only Python's standard library

## Packaging the .skill file

To build the `.skill` archive yourself (e.g. for releases), use Anthropic's `skill-creator` packager, or zip the skill folder manually:

```bash
cd plane-task-creator
zip -r ../plane-task-creator.skill SKILL.md scripts/ references/
```

## Rate limits

Plane's API is limited to **60 requests per minute per API key**. For bulk operations, space your requests and watch the `X-RateLimit-Remaining` response header.

## Contributing

Issues and PRs are welcome. If you run into an API field that isn't supported yet, or a Plane API change breaks something, please open an issue with the request/response you're seeing.

## License

[Add your license of choice here.]
