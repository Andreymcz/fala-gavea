"""Seed script: creates forwarding records via the REST API.

Authenticates as the dev agent, queries all pendente reports, draws a
50% random sample, groups by report_type_id, and POSTs one Forwarding
per sub-batch.  Each forwarding atomically transitions its linked
reports to status=encaminhado.

Pre-requisites:
    uv run python scripts/seed_users.py
    uv run python scripts/seed_report_types.py
    uv run python scripts/seed_relatos.py
    API server must be running.

Usage:
    uv run python scripts/seed_forwardings.py [--url http://localhost:8000]
                                               [--user agente@gavea.br]
                                               [--password agente12345]
                                               [--batch-size 20]
                                               [--seed 42]
                                               [--include-em-analise]
                                               [--force]
"""
from __future__ import annotations

import argparse
import math
import random
import sys
from collections import defaultdict

import httpx

# Maps report_type name (normalised lower-case) to (institution, proposed_solution)
_INSTITUTION_MAP: dict[str, tuple[str, str]] = {
    "iluminacao publica": (
        "RioLuz",
        "Substituicao das lampadas e manutencao da rede de iluminacao publica",
    ),
    "transito e mobilidade": (
        "CET-Rio",
        "Revisao da sinalizacao viaria e cronograma de manutencao das vias",
    ),
    "vandalismo": (
        "Guarda Municipal",
        "Aumento do patrulhamento preventivo e registro de boletim de ocorrencia",
    ),
    "espaco publico": (
        "SEOP",
        "Vistoria tecnica e reparo dos equipamentos urbanos e calcadas afetadas",
    ),
    "lixo e conservacao": (
        "COMLURB",
        "Programacao de coleta especial e limpeza do logradouro afetado",
    ),
    "seguranca e circulacao": (
        "Secretaria de Ordem Publica",
        "Avaliacao de risco e instalacao de sinalizacao de seguranca viaria",
    ),
    "conflito social": (
        "Secretaria de Ordem Publica",
        "Mediacao comunitaria e reforco do patrulhamento preventivo na area",
    ),
    "outro": (
        "Subprefeitura da Gavea",
        "Analise tecnica e encaminhamento ao orgao competente",
    ),
}
_DEFAULT_INSTITUTION = (
    "Subprefeitura da Gavea",
    "Analise tecnica e encaminhamento ao orgao competente",
)


def _login(client: httpx.Client, email: str, password: str) -> str:
    resp = client.post(
        "/auth/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if resp.status_code != 200:
        print(f"Error: login failed ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()["access_token"]


def _fetch_report_types(client: httpx.Client) -> dict[str, str]:
    resp = client.get("/report_types")
    if resp.status_code != 200:
        print(f"Error: could not fetch report_types ({resp.status_code})", file=sys.stderr)
        sys.exit(1)
    return {rt["id"]: rt["name"] for rt in resp.json()}


def _has_existing_forwardings(client: httpx.Client, token: str) -> bool:
    resp = client.get("/forwardings/", headers={"Authorization": f"Bearer {token}"})
    if resp.status_code != 200:
        print(
            f"Warning: could not check existing forwardings ({resp.status_code}); proceeding.",
            file=sys.stderr,
        )
        return False
    return len(resp.json()) > 0


def _fetch_all_reports(
    client: httpx.Client,
    token: str,
    *,
    include_em_analise: bool,
) -> list[dict]:
    statuses = ["pendente", "em_analise"] if include_em_analise else ["pendente"]
    headers = {"Authorization": f"Bearer {token}"}
    reports: list[dict] = []
    offset = 0
    limit = 200

    while True:
        resp = client.post(
            "/reports/query",
            json={"statuses": statuses, "limit": limit, "offset": offset},
            headers=headers,
        )
        if resp.status_code != 200:
            print(
                f"Error: failed to query reports ({resp.status_code}): {resp.text}",
                file=sys.stderr,
            )
            sys.exit(1)
        data = resp.json()
        items = data.get("items", [])
        reports.extend(items)
        if len(reports) >= data.get("total", 0) or not items:
            break
        offset += limit

    return reports


def _resolve_institution(type_name: str) -> tuple[str, str]:
    key = type_name.lower().strip()
    return _INSTITUTION_MAP.get(key, _DEFAULT_INSTITUTION)


def _chunks(lst: list, size: int):
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed forwardings: groups ~50%% of pendente relatos into forwarding records."
    )
    parser.add_argument("--url", default="http://localhost:8000", help="Base API URL")
    parser.add_argument("--user", default="agente@gavea.br", help="Agent login email")
    parser.add_argument("--password", default="agente12345", help="Agent password")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Max reports per forwarding (default: 20)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--include-em-analise",
        action="store_true",
        help="Also include em_analise reports as forwarding candidates",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Create forwardings even if some already exist",
    )
    args = parser.parse_args()

    base = args.url.rstrip("/")

    with httpx.Client(base_url=base, timeout=30) as client:
        token = _login(client, args.user, args.password)
        print(f"Logged in as {args.user}")

        if not args.force and _has_existing_forwardings(client, token):
            print(
                "Forwardings already exist. Run with --force to create more. Exiting."
            )
            return

        report_types = _fetch_report_types(client)
        print(f"Loaded {len(report_types)} report type(s)")

        all_reports = _fetch_all_reports(
            client, token, include_em_analise=args.include_em_analise
        )
        total = len(all_reports)
        print(f"Found {total} candidate report(s)")

        if total == 0:
            print("No candidate reports found. Run seed_relatos.py first.")
            return

        random.seed(args.seed)
        random.shuffle(all_reports)
        sample_size = math.ceil(total * 0.5)
        sample = all_reports[:sample_size]
        print(f"Selected {len(sample)} reports (~50%% sample)")

        # Group by report_type_id
        by_type: dict[str, list[str]] = defaultdict(list)
        for report in sample:
            by_type[report["report_type_id"]].append(report["id"])

        created = 0
        errors = 0
        headers = {"Authorization": f"Bearer {token}"}

        for type_id, report_ids in by_type.items():
            type_name = report_types.get(type_id, "")
            institution, proposed_solution = _resolve_institution(type_name)

            for batch in _chunks(report_ids, args.batch_size):
                payload = {
                    "institution": institution,
                    "proposed_solution": proposed_solution,
                    "report_ids": batch,
                }
                resp = client.post("/forwardings", json=payload, headers=headers)
                if resp.status_code in (200, 201):
                    created += 1
                else:
                    errors += 1
                    print(
                        f"  Error ({resp.status_code}) for {institution}: {resp.text}",
                        file=sys.stderr,
                    )

        print(f"\nDone. Forwardings created: {created}, Errors: {errors}")


if __name__ == "__main__":
    main()
