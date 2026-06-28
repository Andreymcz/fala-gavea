"""Fonte única de verdade da clusterização geográfica dos relatos seedados.

Os relatos do seed são distribuídos em torno de POIs reais da Gávea (em vez de
espalhados uniformemente num retângulo, que vazava para o Jardim Botânico e a
Lagoa Rodrigo de Freitas a nordeste). Cada relato é atribuído a um cluster por
escolha ponderada e recebe um jitter gaussiano pequeno (~100m) em volta do
centro, sempre dentro da bounding box da Gávea.

`scripts/` não é um pacote; importe via importlib/path quando necessário.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Cluster:
    """Um ponto de interesse (POI) da Gávea usado como centro de cluster."""

    name: str
    lat: float
    lon: float
    weight: int


# Centros de cluster — todos dentro da Gávea, com folga em relação ao Jardim
# Botânico/Lagoa (que ficam a NE = lat e lon menos negativos). Distribuição
# ponderada: Rocinha e PUC concentram mais relatos (hotspots).
CLUSTERS: list[Cluster] = [
    Cluster("Rocinha (borda Estrada da Gavea)", -22.9870, -43.2455, 8),
    Cluster("PUC-Rio", -22.9783, -43.2334, 6),
    Cluster("Baixo Gavea / Praca Santos Dumont", -22.9748, -43.2300, 4),
    Cluster("Parque da Cidade (Gavea)", -22.9800, -43.2420, 3),
    Cluster("Shopping da Gavea", -22.9765, -43.2320, 3),
    Cluster("Planetario / V.-Gov. Rubens Berardo", -22.9762, -43.2262, 2),
    Cluster("Jockey Club (Hipodromo)", -22.9762, -43.2248, 2),
]


@dataclass(frozen=True)
class BBox:
    """Bounding box geográfica (graus decimais)."""

    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float


# Bounding box apertada da Gávea. Qualquer coordenada com lat > lat_max ou
# lon > lon_max está derivando para Lagoa/Jardim Botânico (a NE).
GAVEA_BBOX = BBox(lat_min=-22.990, lat_max=-22.972, lon_min=-43.248, lon_max=-43.224)

# Desvio-padrão do jitter gaussiano aplicado em torno de cada centro (~100m).
JITTER_SIGMA = 0.0009


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def in_gavea(lat: float, lon: float) -> bool:
    """True se a coordenada está dentro da bounding box da Gávea."""
    return (
        GAVEA_BBOX.lat_min <= lat <= GAVEA_BBOX.lat_max
        and GAVEA_BBOX.lon_min <= lon <= GAVEA_BBOX.lon_max
    )


def sample_coordinate(rng: random.Random) -> tuple[float, float]:
    """Amostra uma coordenada (lat, lon) clusterizada na Gávea.

    Escolhe um cluster por peso, aplica jitter gaussiano e faz clamp à
    bounding box, garantindo que o resultado satisfaça `in_gavea`.
    """
    cluster = rng.choices(CLUSTERS, weights=[c.weight for c in CLUSTERS], k=1)[0]
    lat = _clamp(
        rng.gauss(cluster.lat, JITTER_SIGMA), GAVEA_BBOX.lat_min, GAVEA_BBOX.lat_max
    )
    lon = _clamp(
        rng.gauss(cluster.lon, JITTER_SIGMA), GAVEA_BBOX.lon_min, GAVEA_BBOX.lon_max
    )
    return round(lat, 6), round(lon, 6)


def nearest_cluster(lat: float, lon: float) -> Cluster:
    """Retorna o cluster cujo centro está mais próximo (distância euclidiana)."""
    return min(
        CLUSTERS, key=lambda c: (c.lat - lat) ** 2 + (c.lon - lon) ** 2
    )
