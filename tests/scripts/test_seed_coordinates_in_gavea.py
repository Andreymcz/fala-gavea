"""Regressão: toda coordenada seedada deve cair dentro da Gávea.

Captura qualquer reintrodução de coordenadas espalhadas para o Jardim
Botânico/Lagoa (ex.: alguém regenerar com o retângulo uniforme antigo).
Cobre os 3 CSVs em massa, as âncoras de jornada e os relatos hardcoded de
citizen01. `scripts/` não é um pacote, então os módulos são carregados via
importlib (registrados em sys.modules para o @dataclass resolver).
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, _REPO_ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_clusters = _load_script("gavea_clusters")
in_gavea = _clusters.in_gavea

_CSV_FILES = [
    _REPO_ROOT / "data" / "seed_relatos_fala_gavea_200.csv",
    _REPO_ROOT / "data" / "seed_relatos_fala_gavea_1k.csv",
    _REPO_ROOT / "data" / "seed_relatos_fala_gavea_5k.csv",
    _REPO_ROOT / "data" / "seed_journey_anchors.csv",
]


@pytest.mark.parametrize("csv_path", _CSV_FILES, ids=lambda p: p.name)
def test_csv_coordinates_inside_gavea(csv_path: Path) -> None:
    with csv_path.open(encoding="utf-8", newline="") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):  # linha 1 = header
            lat, lon = float(row["latitude"]), float(row["longitude"])
            assert in_gavea(lat, lon), f"{csv_path.name}:{i} -> ({lat}, {lon}) fora da Gávea"


def test_citizen01_hardcoded_coordinates_inside_gavea() -> None:
    citizen01 = _load_script("seed_citizen01")
    for i, relato in enumerate(citizen01._RELATOS):
        assert in_gavea(relato["lat"], relato["lon"]), f"_RELATOS[{i}] fora da Gávea"
