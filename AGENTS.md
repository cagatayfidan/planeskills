---
name: plane-task-creator
description: Creates tasks (work items) in Plane Cloud via REST API. Resolves states, assignees, labels, modules, and cycles to UUIDs automatically. Stores workspace slug in session memory after first request so subsequent calls don't re-ask.
---

# Plane Task Creator

Creates work items in Plane Cloud through the REST API with full support for title, description, priority, state, assignees, labels, modules, cycles, parent items, estimates, and due dates.

## Session Workflow

When the user first makes a request:

1. **Ask for workspace slug** — Extract from Plane URL (e.g., `app.plane.so/YOUR-WORKSPACE/...`)
2. **Store in memory** — Reuse for all subsequent requests in the session

## Steps for Any Request

1. Verify `PLANE_API_KEY` is set in environment
2. List projects to find the target project (match by name/identifier)
3. List metadata (states, members, labels, etc.) for fields the user mentioned
4. Resolve human names to UUIDs (case-insensitive substring match)
5. Build the request with resolved UUIDs
6. Confirm with user before creating
7. Create task and return the link

## Key Commands

```bash
python scripts/plane_client.py list-projects <workspace>
python scripts/plane_client.py list-metadata <workspace> <project> --kind members
python scripts/plane_client.py create-task <workspace> <project> --name "..." --assignees <uuid>
```

## Notes

- Priority is a string enum (`none`, `urgent`, `high`, `medium`, `low`) — not a UUID
- Description must be HTML (`<p>...</p>`)
- Assignees and labels are arrays even for single values
- Rate limit: 60 requests/minute per API key