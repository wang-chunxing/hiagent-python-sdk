"""HiAgent SDK CLI - Main entry point with Click."""

import sys
from pathlib import Path
from typing import Optional

import click

def _ensure_local_hiagent_api_on_path() -> None:
    candidates = []
    try:
        candidates.append(Path(__file__).resolve().parents[3] / "libs" / "api")
    except Exception:
        pass
    candidates.append(Path.cwd() / "libs" / "api")

    for p in candidates:
        if (p / "hiagent_api").is_dir():
            sys.path.insert(0, str(p))
            return


_ensure_local_hiagent_api_on_path()

from cli_anything.hiagent_sdk.core.project import Project
from cli_anything.hiagent_sdk.core.services import ServiceManager
from cli_anything.hiagent_sdk.core.export import Exporter


class CLIContext:
    """CLI context object passed between commands."""

    def __init__(self, json_mode: bool = False, project_root: Optional[Path] = None):
        """Initialize CLI context."""
        self.json_mode = json_mode
        self.project_root = project_root or Path.cwd()
        self.project = Project(self.project_root)
        self.exporter = Exporter(json_mode=json_mode)
        self._service_manager: Optional[ServiceManager] = None

    @property
    def service_manager(self) -> ServiceManager:
        """Get service manager with effective configuration."""
        if self._service_manager is None:
            config = self.project.get_effective_config()
            self._service_manager = ServiceManager(config)
        return self._service_manager


@click.group(invoke_without_command=True)
@click.option("--json", is_flag=True, help="Output in JSON format")
@click.option(
    "--project",
    "-p",
    type=click.Path(exists=True, path_type=Path, file_okay=False),
    help="Project root directory",
)
@click.option("--version", is_flag=True, help="Show version")
@click.pass_context
def cli(ctx: click.Context, json: bool, project: Optional[Path], version: bool):
    """HiAgent SDK CLI - Observe service commands."""
    if version:
        click.echo("hiagent-sdk-cli 0.1.0")
        sys.exit(0)

    # Initialize context
    ctx.ensure_object(dict)
    ctx.obj = CLIContext(json_mode=json, project_root=project)


@cli.group()
@click.pass_context
def observe(ctx: click.Context):
    """Observe service commands (API Token, Trace Spans)."""
    pass


@observe.group()
@click.pass_context
def token(ctx: click.Context):
    """API Token management commands."""
    pass


@token.command("create")
@click.option("--workspace-id", required=True, help="Workspace ID")
@click.option("--custom-app-id", required=True, help="Custom App ID")
@click.pass_obj
def observe_token_create(
    ctx: CLIContext,
    workspace_id: str,
    custom_app_id: str,
):
    """Create an API Token for observe service."""
    try:
        from cli_anything.hiagent_sdk.utils.hiagent_backend import ensure_volc_credentials
        from hiagent_api.observe_types import CreateApiTokenRequest

        ensure_volc_credentials()
        req = CreateApiTokenRequest(
            WorkspaceID=workspace_id,
            CustomAppID=custom_app_id,
        )

        resp = ctx.service_manager.get_observe_service().CreateApiToken(req)

        ctx.exporter.print_result(
            resp.model_dump(),
            True,
            f"API Token created (expires in {resp.ExpiresIn}s)",
        )

    except Exception as e:
        ctx.exporter.print_result(None, False, f"Error: {str(e)}")
        sys.exit(1)


@observe.group()
@click.pass_context
def trace(ctx: click.Context):
    """Trace span management commands."""
    pass


@trace.command("list")
@click.option("--workspace-id", required=True, help="Workspace ID")
@click.option("--page-size", type=int, default=10, help="Page size")
@click.option("--last-id", default="", help="Last ID for pagination")
@click.option(
    "--sort-by",
    type=click.Choice(["StartTime", "Latency", "LatencyFirstResp", "TotalTokens"]),
    default="StartTime",
    help="Sort by field",
)
@click.option(
    "--sort-order",
    type=click.Choice(["Asc", "Desc"]),
    default="Desc",
    help="Sort order",
)
@click.pass_obj
def observe_trace_list(
    ctx: CLIContext,
    workspace_id: str,
    page_size: int,
    last_id: str,
    sort_by: str,
    sort_order: str,
):
    """List trace spans."""
    try:
        from cli_anything.hiagent_sdk.utils.hiagent_backend import ensure_volc_credentials
        from hiagent_api.observe_types import (
            ListTraceSpansRequest,
            ListTraceSpansRequestSort,
            ListTraceSpansRequestSortBy,
            SortOrderType,
        )

        ensure_volc_credentials()
        req = ListTraceSpansRequest(
            WorkspaceID=workspace_id,
            PageSize=page_size,
            LastID=last_id,
            Sort=[
                ListTraceSpansRequestSort(
                    SortBy=ListTraceSpansRequestSortBy(sort_by),
                    SortOrder=SortOrderType(sort_order),
                )
            ],
        )

        resp = ctx.service_manager.get_observe_service().ListTraceSpans(req)

        items = [item.model_dump() for item in resp.Items]
        result = {
            "total": resp.Total,
            "has_more": resp.HasMore,
            "items": items,
        }

        ctx.exporter.print_result(
            result,
            True,
            f"Found {len(items)} trace spans (total: {resp.Total})",
        )

    except Exception as e:
        ctx.exporter.print_result(None, False, f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
