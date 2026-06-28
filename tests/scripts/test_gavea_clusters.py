"""Tests for scripts/gavea_clusters.py — clusterização geográfica do seed.

`scripts/` não é um pacote, então o módulo é carregado via importlib.
"""

from __future__ import annotations

import importlib.util
import random
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "gavea_clusters.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("gavea_clusters", _SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec so @dataclass can resolve the module via sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def mod() -> ModuleType:
    return _load_module()


def test_all_clusters_inside_gavea(mod: ModuleType) -> None:
    for cluster in mod.CLUSTERS:
        assert mod.in_gavea(cluster.lat, cluster.lon), cluster.name


def test_sampled_coordinates_never_leak_outside_gavea(mod: ModuleType) -> None:
    rng = random.Random(0)
    for _ in range(10_000):
        lat, lon = mod.sample_coordinate(rng)
        assert mod.in_gavea(lat, lon), (lat, lon)


def test_weighted_distribution_favors_hotspots(mod: ModuleType) -> None:
    rng = random.Random(0)
    counts: Counter[str] = Counter()
    for _ in range(10_000):
        lat, lon = mod.sample_coordinate(rng)
        counts[mod.nearest_cluster(lat, lon).name] += 1

    top_two = {name for name, _ in counts.most_common(2)}
    assert "Rocinha (borda Estrada da Gavea)" in top_two
    assert "PUC-Rio" in top_two


def test_in_gavea_rejects_jardim_botanico_and_lagoa(mod: ModuleType) -> None:
    # Pontos a NE (Lagoa / Jardim Botânico) — lat/lon menos negativos.
    assert not mod.in_gavea(-22.955839, -43.205901)  # Lagoa
    assert not mod.in_gavea(-22.966632, -43.220000)  # borda Jardim Botânico
