---
name: plane-task-creator
description: Create tasks (Plane calls them "work items" or "issues") in Plane Cloud via the Plane REST API, with full support for title, description, priority, state, assignees, labels, modules, cycles, parent items, estimate points, and start/target dates. Also lists projects and project metadata (states, labels, members, modules, cycles) so names can be resolved into the UUIDs that Plane's API requires. Use this skill whenever the user mentions Plane (app.plane.so or plane.so) in the context of creating, adding, filing, logging, or opening a task / issue / work item / ticket — including phrases like "Plane'de görev aç", "Plane'e task ekle", "add this to Plane", "create an issue in my Plane project", or when the user wants to convert meeting notes, bug reports, or todo lists into Plane work items. Also use when the user asks to see Plane projects or workspace structure as a setup for creating tasks. Prefer this skill over generic web/API instructions whenever Plane is the target system.
---

# Plane Task Creator

Create work items in Plane Cloud (app.plane.so) through the public REST API.

## What you're actually doing

Plane's API takes **UUIDs** for almost everything — `state`, `assignees`, `labels`, `module`, `parent`. Users almost never know those UUIDs; they say things like "assign it to Ayşe, mark it high priority, put it In Progress." So the real job of this skill is in two steps:

1. **Resolve human-friendly names → UUIDs** by listing the relevant metadata on the project.
2. **POST the task** with the resolved IDs.

A bundled Python client (`scripts/plane_client.py`, stdlib-only — no `pip install` needed) handles the HTTP plumbing so neither you nor the user has to rewrite curl invocations every time.

## Credentials

The script reads two environment variables:

- `PLANE_API_KEY` (required) — a personal access token starting with `plane_api_...`. The user creates this in Plane under **Profile Settings → Personal Access Tokens → Add personal access token**.
- `PLANE_BASE_URL` (optional) — defaults to `https://api.plane.so/api/v1`. Only change for self-hosted.

If `PLANE_API_KEY` is not set, ask the user to export it in their shell before running anything:

```bash
export PLANE_API_KEY='plane_api_xxxxxxxxxxxxxxxx'
```

Never ask the user to paste the token into the chat, never echo it back, and never write it to a file. The script only reads it from the environment.

## The workflow

### Step 1 — Identify workspace and project

A Plane URL looks like `https://app.plane.so/my-team/projects/4af68566-.../issues/`. The segment right after the domain (`my-team`) is the **workspace_slug**. The UUID after `projects/` is the **project_id**.

If the user gives you a URL, parse it. If the user names a project by its display name or identifier (like "Engineering" or "ENG"), list projects and match:

```bash
python scripts/plane_client.py list-projects <workspace_slug>
```

Output is one project per line: `<project_id>\t<identifier>\t<name>`. Pick the match (case-insensitive, tolerant of typos) and confirm with the user if there's any ambiguity.

### Step 2 — Resolve the fields the user mentioned (and only those)

Don't eagerly fetch every collection. Only list metadata you actually need for the fields the user specified. This keeps the API calls minimal and the interaction fast.

| User mentioned...                       | Fetch           | Command                                                      |
|-----------------------------------------|-----------------|--------------------------------------------------------------|
| State like "In Progress", "Todo"        | states          | `list-metadata <ws> <proj> --kind states`                    |
| Assignee by name or email               | members         | `list-metadata <ws> <proj> --kind members`                   |
| Label(s) by name                        | labels          | `list-metadata <ws> <proj> --kind labels`                    |
| Module name                             | modules         | `list-metadata <ws> <proj> --kind modules`                   |
| Cycle name                              | cycles          | `list-metadata <ws> <proj> --kind cycles`                    |
| Parent issue by identifier (e.g. ENG-42)| work item lookup| `get-work-item <ws> <ENG-42>`                                |

**Priority is NOT a UUID** — it's a string enum: `none`, `urgent`, `high`, `medium`, `low`. Pass it directly. Map common phrasing sensibly: "critical" → `urgent`, "no rush" → `low`, unspecified → omit the field (Plane defaults to `none`).

**Matching strategy**: case-insensitive substring match on the obvious name field (`name` for states/labels/modules/cycles, `display_name` or `email` for members). If two records match equally well (e.g. two "Ali"s), don't guess — show the candidates to the user and ask.

### Step 3 — Create the task

```bash
python scripts/plane_client.py create-task <workspace_slug> <project_id> \
    --name "Fix login bug on Safari 17" \
    --description-html "<p>Users on Safari 17 see a blank page after SSO redirect.</p>" \
    --priority high \
    --state <state_uuid> \
    --assignees <uuid1>,<uuid2> \
    --labels <label_uuid1>,<label_uuid2> \
    --module <module_uuid> \
    --parent <parent_work_item_uuid> \
    --estimate-point 3 \
    --start-date 2026-04-20 \
    --target-date 2026-05-01
```

The script prints the created work item as JSON. Extract `sequence_id` (human-readable identifier number) and `id` (UUID) from the response, and report back to the user with a clickable link:

```
https://app.plane.so/<workspace_slug>/projects/<project_id>/issues/<work_item_id>/
```

### Step 4 — Attach cycle (if requested)

Cycles are linked through a separate endpoint. If the user wants the new task in a cycle, do it right after creation:

```bash
python scripts/plane_client.py attach-cycle <workspace_slug> <project_id> <cycle_id> <work_item_id>
```

## Description formatting

Plane stores descriptions as HTML in the `description_html` field. Wrap plain text in `<p>...</p>`. Use `<strong>`, `<em>`, `<ul>/<li>`, `<code>`, `<pre>`, `<a href="...">` as needed. Don't pass raw Markdown — it will display literally. If the user gives you Markdown, convert it to HTML before passing it in.

If the user didn't provide a description, omit the field rather than sending empty HTML.

## Confirm before creating

Creating a task sends notifications to assignees, so before firing the POST, show the user a short summary:

> About to create in **MyTeam / Engineering**:
> - Title: Fix login bug on Safari 17
> - Priority: high
> - Assignee: Ayşe Yılmaz
> - State: In Progress
> - Due: 2026-05-01
>
> Proceed?

Skip the confirmation only if the user has explicitly asked for batch/unattended creation (e.g. "create these 20 tasks from my list, don't ask me for each one").

## Pitfalls to avoid

- **Workspace slug ≠ display name.** The slug comes from the URL and is usually lowercase, hyphenated. "My Team" in the UI is often `my-team` in the URL.
- **`assignees` and `labels` are arrays**, even for a single value. The script handles this by splitting comma-separated input — if you're calling the API directly, remember to send `["uuid"]` not `"uuid"`.
- **Rate limit is 60 requests/minute per API key.** For bulk creation, sequence the requests and watch `X-RateLimit-Remaining` headers.
- **Don't invent UUIDs.** If a name doesn't resolve confidently, ask the user instead of guessing. A wrong UUID silently assigns the task to the wrong person or state — much worse than a clarifying question.
- **404 on a project endpoint** usually means the project was archived or the URL is stale. Ask the user to confirm the current URL.
- **Self-hosted users**: change `PLANE_BASE_URL` to their domain (e.g. `https://plane.mycompany.com/api/v1`). Everything else works the same.

## Bulk creation from a list

If the user dumps a list ("create these five tasks in Engineering: ...") or points to a file (CSV, markdown checklist), you can either:

- Invoke `create-task` once per item (simple, good for <10 tasks), or
- `import plane_client` inside a short Python script and loop (faster, reuses a single process, gives you clean error handling for partial failures).

Either way: resolve metadata (states/labels/members) **once** at the start, build a name→UUID lookup dict, then reuse it for every task. Don't re-fetch the same metadata for every row.

## Script reference

`scripts/plane_client.py` commands (run with `python scripts/plane_client.py <cmd>`):

- `list-projects <ws>` — list projects in a workspace
- `list-metadata <ws> <proj> --kind {states|labels|members|modules|cycles}` — list the chosen collection as JSON
- `get-work-item <ws> <identifier>` — fetch a work item by its human identifier like `ENG-42` (useful for finding parent UUIDs)
- `list-work-items <ws> <proj>` — list work items in a project
- `create-task <ws> <proj> --name <t> [flags]` — create a work item (see above for all flags)
- `attach-cycle <ws> <proj> <cycle_id> <work_item_id>` — link a work item to a cycle

You can also `from plane_client import PlaneClient` and use the class directly for bulk/custom flows.

See `references/api_reference.md` for the full field definitions, response schemas, and priority/state semantics.
