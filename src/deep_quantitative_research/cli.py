"""Entry point for the `deep-quant` CLI.

Phase 2 ships `query-datasources` (healthcheck + search). Later phases will
add `formulate-hypothesis`, `find-datasets`, `design-signal`, `run-signal`,
`render-signal-card`, `render-dashboard`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from . import __version__
from .registry import (
    RegistryError,
    build_dataset_contract,
    build_join_assessment,
    get_client,
    score_dataset_fit,
    search_datasets,
    search_sources,
)


def _client_or_die(config: str | None):
    try:
        return get_client(config_path=config) if config else get_client()
    except RegistryError as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(2)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-V", "--version", prog_name="deep-quant")
def main() -> None:
    """deep-quant: registry-aware quantitative research engine."""


@main.command("query-datasources")
@click.option("--healthcheck", is_flag=True, help="Verify the registry is reachable and print stats.")
@click.option("--query", "query_text", default=None, help="Free-text search across the registry.")
@click.option("--domain", default=None, help="Filter results to one domain (e.g. finance-markets).")
@click.option(
    "--kind",
    "entry_kind",
    default=None,
    help="Filter by entry_kind (corpus, registry, time-series, panel, ...).",
)
@click.option("--cadence", default=None, help="Filter datasets by cadence (monthly, quarterly, ...).")
@click.option("--join-key", default=None, help="Filter to datasets exposing this canonical join key.")
@click.option("--limit", default=10, show_default=True, help="Maximum hits to return.")
@click.option("--config", default=None, help="Path to config/datasources.yaml.")
@click.option(
    "--output",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    show_default=True,
)
def query_datasources(
    healthcheck: bool,
    query_text: str | None,
    domain: str | None,
    entry_kind: str | None,
    cadence: str | None,
    join_key: str | None,
    limit: int,
    config: str | None,
    output_format: str,
) -> None:
    """Search the sibling datasources registry, or run a healthcheck."""
    client = _client_or_die(config)

    if healthcheck:
        info = client.healthcheck()
        if output_format == "json":
            click.echo(json.dumps(info, indent=2))
            return
        click.echo(f"repo:               {info['repo_path']}")
        click.echo(f"generated:          {info['generated_path']}")
        click.echo(f"registry commit:    {info['registry_commit'] or '(not a git repo)'}")
        click.echo(f"checked at:         {info['checked_at']}")
        counts = info["counts"]
        click.echo(
            f"counts:             sources={counts['sources']} datasets={counts['datasets']} "
            f"fields={counts['fields']} join_keys={counts['join_keys']}"
        )
        if info["requires_commit_hash"] and not info["registry_commit"]:
            click.echo(
                "warning: config requires a commit hash but the datasources repo "
                "is not a git checkout. Research runs will refuse to start.",
                err=True,
            )
        return

    if query_text is None and not (domain or entry_kind or cadence or join_key):
        click.echo("provide --healthcheck or a search filter (--query / --domain / ...)", err=True)
        sys.exit(2)

    hits = search_datasets(
        query_text or "",
        domain=domain,
        cadence=cadence,
        join_key=join_key,
        entry_kind=entry_kind,
        client=client,
        limit=limit,
    )
    if not hits and (query_text or domain):
        source_hits = search_sources(
            query_text or "",
            domain=domain,
            entry_kind=entry_kind,
            join_key=join_key,
            client=client,
            limit=limit,
        )
        hits = source_hits

    if output_format == "json":
        click.echo(json.dumps([h.__dict__ for h in hits], indent=2))
        return

    if not hits:
        click.echo("no matches")
        return
    width = max(len(h.id) for h in hits)
    for hit in hits:
        click.echo(
            f"{hit.kind:7}  {hit.id:<{width}}  {hit.domain:<18}  {hit.entry_kind:<12}  {hit.name}"
        )


@main.command("build-dataset-contract")
@click.argument("dataset_id")
@click.option("--role", default="predictor", type=click.Choice(["target", "predictor", "context", "benchmark"]))
@click.option("--target-cadence", default=None)
@click.option("--config", default=None, help="Path to config/datasources.yaml.")
def build_contract_cmd(
    dataset_id: str, role: str, target_cadence: str | None, config: str | None
) -> None:
    """Print a dataset_contract YAML for the given dataset_id."""
    client = _client_or_die(config)
    try:
        contract = build_dataset_contract(
            dataset_id, role=role, target_cadence=target_cadence, client=client
        )
    except RegistryError as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(2)
    import yaml

    click.echo(yaml.safe_dump(contract, sort_keys=False))


@main.command("score-dataset")
@click.argument("dataset_id")
@click.option("--hypothesis", "hypothesis_path", required=True, type=click.Path(exists=True))
@click.option("--config", default=None, help="Path to config/datasources.yaml.")
def score_cmd(dataset_id: str, hypothesis_path: str, config: str | None) -> None:
    """Score a dataset against a Hypothesis YAML."""
    import yaml

    client = _client_or_die(config)
    hypothesis = yaml.safe_load(Path(hypothesis_path).read_text()) or {}
    try:
        score = score_dataset_fit(hypothesis, dataset_id, client=client)
    except RegistryError as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(2)
    click.echo(yaml.safe_dump(score, sort_keys=False))


@main.command("assess-join")
@click.argument("source_dataset")
@click.argument("target_dataset")
@click.option("--config", default=None, help="Path to config/datasources.yaml.")
def assess_join_cmd(source_dataset: str, target_dataset: str, config: str | None) -> None:
    """Print the join_assessment between two datasets."""
    import yaml

    client = _client_or_die(config)
    try:
        assessment = build_join_assessment(source_dataset, target_dataset, client=client)
    except RegistryError as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(2)
    click.echo(yaml.safe_dump(assessment.to_dict(), sort_keys=False))


if __name__ == "__main__":
    main()
