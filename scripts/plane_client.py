#!/usr/bin/env python3
"""
plane_client.py — Minimal Python client for the Plane Cloud REST API.

Uses only the Python standard library (urllib). No pip install required.

Environment variables:
    PLANE_API_KEY  (required)  Personal access token from Plane Profile Settings.
    PLANE_BASE_URL (optional)  API base URL. Defaults to https://api.plane.so/api/v1

Import it:
    from plane_client import PlaneClient
    c = PlaneClient()
    projects = c.list_projects("my-team")

Or use the CLI — run `python plane_client.py --help` for all commands.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

DEFAULT_BASE_URL = "https://api.plane.so/api/v1"


class PlaneAPIError(RuntimeError):
    """Raised when the Plane API returns a non-2xx response."""

    def __init__(self, status: int, reason: str, method: str, path: str, body: str):
        self.status = status
        self.reason = reason
        self.method = method
        self.path = path
        self.body = body
        super().__init__(
            f"HTTP {status} {reason} on {method} {path}\nResponse: {body}"
        )


class PlaneClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.environ.get("PLANE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "PLANE_API_KEY is not set. Export it in your shell:\n"
                "    export PLANE_API_KEY='plane_api_xxxxxxxx'\n"
                "Generate a token in Plane under Profile Settings → Personal Access Tokens."
            )
        self.base_url = (
            base_url or os.environ.get("PLANE_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")

    # ---------------- HTTP core ----------------

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        if params:
            # Drop None values
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)

        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("X-API-Key", self.api_key)
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "plane-client/1.0")

        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read().decode("utf-8")
                if not raw:
                    return None
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise PlaneAPIError(e.code, e.reason, method, path, err_body) from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error reaching {url}: {e.reason}") from None

    # ---------------- Discovery / listing ----------------

    def list_workspaces(self) -> Any:
        return self._request("GET", "/workspaces/")

    def list_projects(self, workspace_slug: str) -> Any:
        return self._request("GET", f"/workspaces/{workspace_slug}/projects/")

    def get_project(self, workspace_slug: str, project_id: str) -> Any:
        return self._request(
            "GET", f"/workspaces/{workspace_slug}/projects/{project_id}/"
        )

    def list_states(self, workspace_slug: str, project_id: str) -> Any:
        return self._request(
            "GET", f"/workspaces/{workspace_slug}/projects/{project_id}/states/"
        )

    def list_labels(self, workspace_slug: str, project_id: str) -> Any:
        return self._request(
            "GET", f"/workspaces/{workspace_slug}/projects/{project_id}/labels/"
        )

    def list_members(self, workspace_slug: str, project_id: str) -> Any:
        return self._request(
            "GET", f"/workspaces/{workspace_slug}/projects/{project_id}/members/"
        )

    def list_modules(self, workspace_slug: str, project_id: str) -> Any:
        return self._request(
            "GET", f"/workspaces/{workspace_slug}/projects/{project_id}/modules/"
        )

    def list_cycles(self, workspace_slug: str, project_id: str) -> Any:
        return self._request(
            "GET", f"/workspaces/{workspace_slug}/projects/{project_id}/cycles/"
        )

    def list_work_items(
        self,
        workspace_slug: str,
        project_id: str,
        params: Optional[dict] = None,
    ) -> Any:
        return self._request(
            "GET",
            f"/workspaces/{workspace_slug}/projects/{project_id}/work-items/",
            params=params,
        )

    def get_work_item_by_identifier(
        self, workspace_slug: str, identifier: str
    ) -> Any:
        """Fetch a work item by human-readable identifier like 'ENG-42'."""
        return self._request(
            "GET", f"/workspaces/{workspace_slug}/work-items/{identifier}/"
        )

    # ---------------- Work item creation ----------------

    def create_work_item(
        self,
        workspace_slug: str,
        project_id: str,
        *,
        name: str,
        description_html: Optional[str] = None,
        priority: Optional[str] = None,
        state: Optional[str] = None,
        assignees: Optional[list] = None,
        labels: Optional[list] = None,
        parent: Optional[str] = None,
        estimate_point: Optional[int] = None,
        type: Optional[str] = None,
        module: Optional[str] = None,
        start_date: Optional[str] = None,
        target_date: Optional[str] = None,
    ) -> Any:
        if not name or not name.strip():
            raise ValueError("name is required and cannot be empty")

        if priority is not None and priority not in {
            "none",
            "urgent",
            "high",
            "medium",
            "low",
        }:
            raise ValueError(
                f"priority must be one of none|urgent|high|medium|low, got {priority!r}"
            )

        body = {
            "name": name,
            "description_html": description_html,
            "priority": priority,
            "state": state,
            "assignees": assignees,
            "labels": labels,
            "parent": parent,
            "estimate_point": estimate_point,
            "type": type,
            "module": module,
            "start_date": start_date,
            "target_date": target_date,
        }
        # Drop unset fields so we don't send nulls the API may reject.
        body = {k: v for k, v in body.items() if v is not None}

        return self._request(
            "POST",
            f"/workspaces/{workspace_slug}/projects/{project_id}/work-items/",
            body=body,
        )

    def attach_to_cycle(
        self,
        workspace_slug: str,
        project_id: str,
        cycle_id: str,
        work_item_id: str,
    ) -> Any:
        """Link an existing work item to a cycle."""
        return self._request(
            "POST",
            f"/workspaces/{workspace_slug}/projects/{project_id}/cycles/{cycle_id}/cycle-issues/",
            body={"issues": [work_item_id]},
        )


# ---------------- CLI ----------------


def _print_json(obj: Any) -> None:
    json.dump(obj, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def _split_csv(value: Optional[str]) -> Optional[list]:
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


def _cmd_list_workspaces(client: PlaneClient, args: argparse.Namespace) -> None:
    data = client.list_workspaces()
    items = data.get("results") if isinstance(data, dict) else data
    if not items:
        print("(no workspaces)", file=sys.stderr)
        return
    for w in items:
        print(
            f"{w.get('id', '')}\t{w.get('slug', '')}\t{w.get('name', '')}"
        )


def _cmd_list_projects(client: PlaneClient, args: argparse.Namespace) -> None:
    data = client.list_projects(args.workspace)
    # Plane paginates with {"results": [...]} on list endpoints.
    items = data.get("results") if isinstance(data, dict) else data
    if not items:
        print("(no projects)", file=sys.stderr)
        return
    # Tab-separated for easy parsing: id<TAB>identifier<TAB>name
    for p in items:
        print(
            f"{p.get('id', '')}\t{p.get('identifier', '')}\t{p.get('name', '')}"
        )


def _cmd_list_metadata(client: PlaneClient, args: argparse.Namespace) -> None:
    fn = {
        "states": client.list_states,
        "labels": client.list_labels,
        "members": client.list_members,
        "modules": client.list_modules,
        "cycles": client.list_cycles,
    }[args.kind]
    _print_json(fn(args.workspace, args.project_id))


def _cmd_list_work_items(client: PlaneClient, args: argparse.Namespace) -> None:
    _print_json(client.list_work_items(args.workspace, args.project_id))


def _cmd_get_work_item(client: PlaneClient, args: argparse.Namespace) -> None:
    _print_json(client.get_work_item_by_identifier(args.workspace, args.identifier))


def _cmd_create_task(client: PlaneClient, args: argparse.Namespace) -> None:
    result = client.create_work_item(
        args.workspace,
        args.project_id,
        name=args.name,
        description_html=args.description_html,
        priority=args.priority,
        state=args.state,
        assignees=_split_csv(args.assignees),
        labels=_split_csv(args.labels),
        parent=args.parent,
        estimate_point=args.estimate_point,
        type=args.type,
        module=args.module,
        start_date=args.start_date,
        target_date=args.target_date,
    )
    _print_json(result)


def _cmd_attach_cycle(client: PlaneClient, args: argparse.Namespace) -> None:
    _print_json(
        client.attach_to_cycle(
            args.workspace, args.project_id, args.cycle_id, args.work_item_id
        )
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Plane Cloud API client — list projects/metadata and create work items."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list-workspaces", help="List all workspaces")

    lp = sub.add_parser("list-projects", help="List projects in a workspace")
    lp.add_argument("workspace", help="workspace_slug, e.g. 'my-team'")

    lm = sub.add_parser(
        "list-metadata",
        help="List states/labels/members/modules/cycles for a project",
    )
    lm.add_argument("workspace")
    lm.add_argument("project_id")
    lm.add_argument(
        "--kind",
        required=True,
        choices=["states", "labels", "members", "modules", "cycles"],
    )

    lwi = sub.add_parser(
        "list-work-items", help="List work items in a project"
    )
    lwi.add_argument("workspace")
    lwi.add_argument("project_id")

    gwi = sub.add_parser(
        "get-work-item",
        help="Get a work item by human identifier like 'ENG-42'",
    )
    gwi.add_argument("workspace")
    gwi.add_argument("identifier", help="e.g. ENG-42")

    ct = sub.add_parser("create-task", help="Create a work item (task)")
    ct.add_argument("workspace")
    ct.add_argument("project_id")
    ct.add_argument("--name", required=True, help="Task title")
    ct.add_argument(
        "--description-html",
        dest="description_html",
        help="HTML description, e.g. '<p>Details here.</p>'",
    )
    ct.add_argument(
        "--priority",
        choices=["none", "urgent", "high", "medium", "low"],
    )
    ct.add_argument("--state", help="State UUID (resolve via list-metadata --kind states)")
    ct.add_argument(
        "--assignees",
        help="Comma-separated user UUIDs (resolve via list-metadata --kind members)",
    )
    ct.add_argument(
        "--labels",
        help="Comma-separated label UUIDs (resolve via list-metadata --kind labels)",
    )
    ct.add_argument("--parent", help="Parent work item UUID")
    ct.add_argument(
        "--estimate-point",
        dest="estimate_point",
        type=int,
        help="Estimate point (integer, typically 0-7)",
    )
    ct.add_argument("--type", help="Work item type UUID")
    ct.add_argument(
        "--module",
        help="Module UUID (resolve via list-metadata --kind modules)",
    )
    ct.add_argument("--start-date", dest="start_date", help="YYYY-MM-DD")
    ct.add_argument("--target-date", dest="target_date", help="YYYY-MM-DD")

    ac = sub.add_parser(
        "attach-cycle", help="Attach an existing work item to a cycle"
    )
    ac.add_argument("workspace")
    ac.add_argument("project_id")
    ac.add_argument("cycle_id")
    ac.add_argument("work_item_id")

    return p


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        client = PlaneClient()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    handlers = {
        "list-workspaces": _cmd_list_workspaces,
        "list-projects": _cmd_list_projects,
        "list-metadata": _cmd_list_metadata,
        "list-work-items": _cmd_list_work_items,
        "get-work-item": _cmd_get_work_item,
        "create-task": _cmd_create_task,
        "attach-cycle": _cmd_attach_cycle,
    }
    handler = handlers[args.cmd]

    try:
        handler(client, args)
    except PlaneAPIError as e:
        print(str(e), file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
