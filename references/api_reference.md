# Plane API Reference

Quick reference for the endpoints this skill uses. The base URL is
`https://api.plane.so/api/v1` for Plane Cloud.

Authentication: every request must include
`X-API-Key: <personal access token>`.

---

## Create a work item (the main one)

```
POST /workspaces/{workspace_slug}/projects/{project_id}/work-items/
```

### Request body fields

| Field              | Type      | Required | Notes                                                                 |
|--------------------|-----------|----------|-----------------------------------------------------------------------|
| `name`             | string    | yes      | Title of the work item.                                               |
| `description_html` | string    | no       | HTML-formatted body. Use `<p>`, `<strong>`, `<ul>/<li>`, `<a>`, etc.  |
| `state`            | UUID      | no       | Project state UUID. Defaults to the project's default state.          |
| `priority`         | enum      | no       | One of `none`, `urgent`, `high`, `medium`, `low`. Default `none`.     |
| `assignees`        | UUID[]    | no       | Array of user UUIDs. Must be members of the project.                  |
| `labels`           | UUID[]    | no       | Array of label UUIDs defined on the project.                          |
| `parent`           | UUID      | no       | UUID of a parent work item in the same project.                       |
| `estimate_point`   | integer   | no       | Estimate point value, typically 0–7.                                  |
| `type`             | UUID      | no       | UUID of the work item type (if the project has custom types).         |
| `module`           | UUID      | no       | UUID of a module this work item belongs to.                           |
| `start_date`       | string    | no       | `YYYY-MM-DD`.                                                         |
| `target_date`      | string    | no       | `YYYY-MM-DD`.                                                         |

### Response (201 Created)

```json
{
  "id": "e1c25c66-5bb8-465e-a818-92a483423443",
  "name": "First Work Item",
  "description_html": "<p>Details...</p>",
  "priority": "high",
  "sequence_id": 421,
  "created_at": "2026-04-17T10:00:00Z",
  "updated_at": "2026-04-17T10:00:00Z",
  "project": "4af68566-94a4-4eb3-94aa-50dc9427067b",
  "workspace": "cd4ab5a2-1a5f-4516-a6c6-8da1a9fa5be4",
  "state": "f3f045db-7e74-49f2-b3b2-0b7dee4635ae",
  "parent": null,
  "assignees": ["797b5aea-3f40-4199-be84-5f94e0d04501"],
  "labels": [],
  "start_date": null,
  "target_date": null,
  "estimate_point": null,
  "is_draft": false,
  "archived_at": null,
  "completed_at": null,
  "created_by": "16c61a3a-512a-48ac-b0be-b6b46fe6f430",
  "updated_by": "16c61a3a-512a-48ac-b0be-b6b46fe6f430"
}
```

The user-facing identifier is built from the project's `identifier` plus the
response's `sequence_id` — e.g. a project with identifier `ENG` + sequence
421 → `ENG-421`.

The issue URL is:
```
https://app.plane.so/{workspace_slug}/projects/{project_id}/issues/{id}/
```

---

## List projects

```
GET /workspaces/{workspace_slug}/projects/
```

Returns a paginated response:
```json
{"results": [{"id": "...", "identifier": "ENG", "name": "Engineering", ...}], "next_cursor": "...", ...}
```

Key fields per project: `id`, `identifier` (short code like `ENG`), `name`,
`description`, `workspace`, `project_lead`, `default_assignee`,
`module_view`, `cycle_view`, `is_issue_type_enabled`.

---

## List project metadata (for resolving names → UUIDs)

All of these live under `/workspaces/{ws}/projects/{proj}/…/` and return
`{"results": [...]}`.

| Endpoint suffix | Use                                            | Key fields on each item                   |
|-----------------|------------------------------------------------|-------------------------------------------|
| `/states/`      | Resolve state names ("In Progress")            | `id`, `name`, `color`, `group`            |
| `/labels/`      | Resolve label names                            | `id`, `name`, `color`                     |
| `/members/`     | Resolve assignee names / emails                | `member` (user UUID), `role`, `workspace` — expand to get `display_name`, `email` |
| `/modules/`     | Resolve module names                           | `id`, `name`, `description`, `lead`       |
| `/cycles/`      | Resolve cycle names                            | `id`, `name`, `start_date`, `end_date`    |

Note: the `/members/` endpoint may return items where the user UUID is in a
nested field like `member`. When passing to `assignees`, use the user UUID,
not the membership record UUID.

---

## Look up a work item by identifier (for parent resolution)

```
GET /workspaces/{workspace_slug}/work-items/{identifier}/
```

Where `identifier` is like `ENG-42`. Returns the full work item JSON, from
which you can read `id` to use as a parent UUID.

---

## Attach a work item to a cycle

```
POST /workspaces/{ws}/projects/{proj}/cycles/{cycle_id}/cycle-issues/
```

Body:
```json
{"issues": ["<work_item_uuid>"]}
```

Cycles are not settable through the `create-work-item` endpoint — use this
after creation.

---

## Rate limits

- 60 requests per minute per API key.
- Response headers to watch:
  - `X-RateLimit-Remaining` — calls left in the current window.
  - `X-RateLimit-Reset` — UTC epoch seconds when the window resets.

If you hit 429, back off until `X-RateLimit-Reset`.

---

## Common errors

| Status | Likely cause                                                               |
|--------|----------------------------------------------------------------------------|
| 400    | Invalid field value (often a bad priority string or malformed UUID).       |
| 401    | Missing or invalid `X-API-Key`.                                            |
| 403    | API key doesn't have access to this workspace/project.                     |
| 404    | Wrong `workspace_slug`, archived/deleted project, or nonexistent resource. |
| 429    | Rate limit exceeded — back off.                                            |

The error response body typically looks like
`{"error": "...", "detail": "..."}` — surface the `detail` field to the
user rather than the raw JSON.
