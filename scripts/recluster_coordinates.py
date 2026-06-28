"""Re-clusteriza as coordenadas de um CSV de relatos para POIs reais da Gávea.

Reescreve **apenas** as colunas `latitude`/`longitude` de cada linha, preservando
texto, data, tópico e urgência. O RNG é semeado pelo índice da linha, então o
resultado é determinístico e o diff dos CSVs commitados é estável e revisável.

Uso:
    uv run python scripts/recluster_coordinates.py            # os 3 CSVs em massa
    uv run python scripts/recluster_coordinates.py --csv data/foo.csv [--csv ...]
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gavea_clusters import sample_coordinate  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_CSVS = [
    _REPO_ROOT / "data" / "seed_relatos_fala_gavea_200.csv",
    _REPO_ROOT / "data" / "seed_relatos_fala_gavea_1k.csv",
    _REPO_ROOT / "data" / "seed_relatos_fala_gavea_5k.csv",
]


def recluster_csv(path: Path) -> int:
    """Reescreve lat/lon de cada linha de `path` in-place. Retorna nº de linhas."""
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if fieldnames is None or "latitude" not in fieldnames or "longitude" not in fieldnames:
            raise ValueError(f"{path.name}: faltam colunas latitude/longitude")
        rows = list(reader)

    for index, row in enumerate(rows):
        rng = random.Random(index)
        lat, lon = sample_coordinate(rng)
        row["latitude"] = f"{lat:.6f}"
        row["longitude"] = f"{lon:.6f}"

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-clusteriza coordenadas de CSVs de relatos.")
    parser.add_argument(
        "--csv",
        action="append",
        type=Path,
        help="CSV a re-clusterizar (repetível). Default: os 3 CSVs de seed.",
    )
    args = parser.parse_args()

    targets = args.csv if args.csv else _DEFAULT_CSVS
    for path in targets:
        if not path.exists():
            print(f"Aviso: pulando inexistente {path}", file=sys.stderr)
            continue
        n = recluster_csv(path)
        print(f"Re-clusterizado: {path.name} ({n} linhas)")


if __name__ == "__main__":
    main()
