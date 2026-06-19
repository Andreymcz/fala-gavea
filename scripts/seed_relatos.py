"""Seed script: populates the database with reports via the REST API.

Reads CSV files from --csv-dir (columns: id_cidadao, texto_relato, latitude, longitude,
data, topico) and replicates the corpus with random jitter until --count is reached.
Falls back to built-in templates if no CSV files are found.

Pre-requisites:
    uv run python scripts/seed_report_types.py
    uv run python scripts/seed_users.py
    API server must be running.

Usage:
    uv run python scripts/seed_relatos.py [--url http://localhost:8000] [--csv-dir seeds/relatos/] [--count N] [--force]

Options:
    --url URL       Base URL of the API (default: http://localhost:8000)
    --csv-dir DIR   Directory with CSV seed files (default: seeds/relatos/)
    --count N       Target number of reports to insert (default: 10000)
    --force         Re-seed even if reports already exist
    --user EMAIL    Login email to use for seeding (default: citizen01@gavea.br)
    --password PWD  Login password (default: citizen01pass)
    --batch N       Number of reports per batch progress update (default: 100)
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

LAT_MIN, LAT_MAX = -22.975, -22.953
LON_MIN, LON_MAX = -43.235, -43.205

URGENCY_WEIGHTS = [("alta", 0.15), ("media", 0.60), ("baixa", 0.25)]

# Templates organized by research connection axis (for Herbert's social science questions).
TEXTS = [
    # --- Eixo 1: Saneamento → Saúde / Assistência básica ---
    "Acumulo de lixo ha mais de uma semana no beco da Rua Coracao de Maria. "
    "Ja apareceram ratos e temo surto de leptospirose na vizinhanca.",
    "Bueiro entupido na Rua Lopes Quintas acumula agua parada ha dias. "
    "Mosquitos proliferando, moradores com medo de dengue.",
    "Esgoto a ceu aberto na lateral da Rua Corneio. Odor insuportavel e criancas "
    "brincando perto; risco real de contaminacao e doenca.",
    "Lixo e entulho descartados irregularmente no acesso ao Parque da Cidade ha semanas. "
    "Cheiro forte, moscas e sinais de ratos. Peco providencias urgentes.",
    "Caixas de agua da rua com tampas danificadas na Rua Pacheco Leao. "
    "Agua exposta a contaminacao, risco a saude de quem consome direto da rede.",
    "Ponto de descarte irregular de residuos na esquina da Rua Sao Clemente com "
    "Macedo Sobrinho acumula lixo organico. Proliferacao de insetos e mau cheiro constante.",
    # --- Eixo 2: Iluminação → Segurança / Circulação ---
    "Poste apagado no trecho da Rua Marques de Sao Vicente entre os numeros 80 e 140. "
    "Tres assaltos reportados nesse mesmo trecho nas ultimas duas semanas.",
    "Toda a calcada da Rua General Garzon fica as escuras apos as 22h. "
    "Moradores relatam medo de sair para buscar filhos na escola noturna.",
    "Iluminacao do tunel da Lagoa-Barra com quatro lampadas queimadas. "
    "Motoristas reduzem velocidade abruptamente, gerando risco de colisao.",
    "Escadaria publica da subida para a Gavea pequena sem iluminacao. "
    "Unico acesso de idosos e criancas que moram no alto; ja houve queda com fratura.",
    "Praca Santos Dumont com iluminacao falha em dois dos tres pontos de luz. "
    "Area frequentada por usuarios de drogas a noite por conta da escuridao.",
    "Poste inclinado e com fios expostos na Rua Visconde de Caravelas. "
    "Risco de choque e de queda sobre veiculos; equipe da Light nao compareceu.",
    # --- Eixo 3: Espaço público degradado → Conflito social / Uso de drogas ---
    "Banheiro publico da Praca da Gavea sem manutencao ha meses: portas quebradas, "
    "sem agua. Virou ponto de uso de drogas segundo moradores do entorno.",
    "Parque infantil no Parque Brigadeiro Faria Lima com brinquedos vandalizados e "
    "matagal crescendo. Criancas sem espaco seguro; adultos usando o local a noite.",
    "Academia ao ar livre da Rua Jardim Botanico com equipamentos quebrados ha 4 meses. "
    "Idosos sem opcao de exercicio; local virou ponto de conflito entre grupos.",
    "Quadra esportiva da Gavea com grade danificada e iluminacao inexistente. "
    "Jovens sem opcao de lazer seguro; episodios de briga frequentes no local.",
    "Pracinha da Rua Lopes Quintas com banco destruido e lixo acumulado. "
    "Maes relatam que nao levam mais filhos por medo de encontrar seringa no chao.",
    # --- Eixo 4: Transito / Mobilidade → Segurança viária ---
    "Semaforo apagado no cruzamento da Rua Jardim Botanico com Lopes Quintas ha 5 dias. "
    "Quase-colisao registrada ontem; ciclistas e pedestres em risco constante.",
    "Buraco de 30cm de profundidade no asfalto da Rua Pacheco Leao em frente ao numero 200. "
    "Motociclista caiu e fraturou o pulso na semana passada.",
    "Onibus da linha 584 superlotado e ultrapassando pontos sem parar no horario de pico. "
    "Idosos e pessoas com mobilidade reduzida ficam para tras; denuncio para providencias.",
    "Faixa de pedestres apagada no cruzamento da Rua Marques de Sao Vicente com "
    "Joquei Clube. Motoristas nao dao preferencia; situacao perigosa para quem cruza.",
    "Ciclovia da Rua Jardim Botanico bloqueada por obra sem sinalizacao adequada. "
    "Ciclistas obrigados a usar a pista de rolamento entre onibus; risco de atropelamento.",
    # --- Eixo 5: Vandalismo → Espaço público / Patrimônio cultural ---
    "Muro historico do Instituto Moreira Salles pichado com tinta spray. "
    "Patrimonio cultural do bairro depredado; peco restauracao e vigilancia.",
    "Placa de nome de rua na esquina da Rua Sao Clemente com Lopes Quintas destruida. "
    "Terceira vez em seis meses; servicos de entrega e emergencia se perdem.",
    "Painel de azulejos decorativos da Praca da Gavea danificado por vandalismo. "
    "Obra de arte urbana historica; perda irreparavel se nao houver protecao.",
    "Lixeira publica nova instalada ha dois meses na Rua Macedo Sobrinho ja esta quebrada. "
    "Vandalismo reincidente no mesmo ponto; lixo volta a ser descartado no chao.",
    # --- Eixo 6: Conflito social → Saúde mental / Assistência social ---
    "Grupo em situacao de rua instalado sob o viaduto da Rua General Garzon. "
    "Conflitos frequentes com moradores; pedimos assistencia social, nao apenas remocao.",
    "Briga generalizada na Praca da Gavea na madrugada do fim de semana. "
    "Tiros foram ouvidos; moradores com ansiedade e criancas traumatizadas relatam insonia.",
    "Mulher em crise de saude mental perambulando pela Rua Sao Clemente sem assistencia. "
    "Ja foi agredida por passantes; peco atendimento do CAPS, nao policia.",
    "Barulho excessivo de estabelecimento noturno na Rua Coracao de Maria todas as noites. "
    "Moradores sem dormir ha semanas; relatos de aumento de pressao e ansiedade.",
    # --- Eixo 7: Infraestrutura → Acessibilidade / Vulnerabilidade social ---
    "Calcada completamente destruida na Rua Jardim Botanico 1008. "
    "Cadeirante do numero 1010 nao consegue sair de casa sem ajuda; situacao urgente.",
    "Arvore de grande porte caiu sobre a calcada da Rua General Garzon bloqueando "
    "totalmente o acesso. Escola municipal a 50m ficou inacessivel por dois dias.",
    "Caixa de energia publica aberta na Rua Lopes Quintas ha uma semana. "
    "Criancas brincam perto; risco grave de choque eletrico; Comlurb nao atendeu.",
    "Rua Corneio alagada apos chuva moderada; agua invade terecos de tres moradias de "
    "baixa renda. Familias vulneraveis sem resposta da Defesa Civil.",
    # --- Eixo 8: Saneamento + Iluminação (intersecção múltipla) ---
    "Beco da Rua Macedo Sobrinho: lixo acumulado, esgoto a ceu aberto e sem iluminacao. "
    "Combinacao perfeita para crime e doenca; moradores se sentem abandonados.",
    "Calcada da Rua Sao Clemente 310 com entulho de obra irregular, poste apagado e "
    "bueiro obstruido. Tres problemas no mesmo ponto; nenhum atendido em dois meses.",
]

_DEFAULT_COORDS = [
    (-22.9651, -43.2180),
    (-22.9620, -43.2150),
    (-22.9680, -43.2200),
    (-22.9700, -43.2120),
    (-22.9640, -43.2250),
]


def weighted_choice(weights: list[tuple[str, float]]) -> str:
    values, probs = zip(*weights)
    r = random.random()
    cumulative = 0.0
    for value, prob in zip(values, probs):
        cumulative += prob
        if r <= cumulative:
            return value
    return values[-1]


def parse_date(date_str: str) -> datetime:
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str!r}")


def jitter_date(base_dt: datetime) -> datetime:
    delta = timedelta(days=random.randint(-15, 15), hours=random.randint(0, 23))
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    year_ago = now - timedelta(days=365)
    result = base_dt + delta
    return max(year_ago, min(now, result))


def load_csv_corpus(
    csv_dir: str,
    type_map: dict[str, str],
    default_type_id: str,
) -> list[dict]:
    rows: list[dict] = []
    csv_dir_path = Path(csv_dir)
    if not csv_dir_path.exists():
        return rows
    for csv_file in sorted(csv_dir_path.glob("*.csv")):
        with csv_file.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for line in reader:
                topico_key = line["topico"].strip().lower()
                type_id = type_map.get(topico_key, default_type_id)
                rows.append(
                    {
                        "text": line["texto_relato"].strip(),
                        "lat": float(line["latitude"]),
                        "lon": float(line["longitude"]),
                        "created_at": parse_date(line["data"]),
                        "report_type_id": type_id,
                    }
                )
    return rows


def build_synthetic_corpus(type_map: dict[str, str]) -> list[dict]:
    type_ids = list(type_map.values())
    corpus = []
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    year_ago = now - timedelta(days=365)
    for i, text in enumerate(TEXTS):
        lat, lon = _DEFAULT_COORDS[i % len(_DEFAULT_COORDS)]
        offset_seconds = int((i / len(TEXTS)) * 365 * 24 * 3600)
        created_at = year_ago + timedelta(seconds=offset_seconds)
        corpus.append(
            {
                "text": text,
                "lat": lat,
                "lon": lon,
                "created_at": created_at,
                "report_type_id": type_ids[i % len(type_ids)],
            }
        )
    return corpus


def login(client: httpx.Client, email: str, password: str) -> str:
    resp = client.post("/auth/token", data={"username": email, "password": password})
    if resp.status_code != 200:
        print(f"Login failed ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()["access_token"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed reports via the Fala Gávea API.")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--csv-dir", default="seeds/relatos/", help="Directory with CSV seed files")
    parser.add_argument("--count", type=int, default=10000, help="Target number of reports")
    parser.add_argument("--force", action="store_true", help="Re-seed without checking existing count")
    parser.add_argument("--user", default="citizen01@gavea.br", help="Login email")
    parser.add_argument("--password", default="citizen01pass", help="Login password")
    parser.add_argument("--batch", type=int, default=100, help="Progress update interval")
    args = parser.parse_args()

    base = args.url.rstrip("/")

    with httpx.Client(base_url=base, timeout=30) as client:
        token = login(client, args.user, args.password)
        headers = {"Authorization": f"Bearer {token}"}

        # Fetch available report types
        rt_resp = client.get("/report_types/")
        if rt_resp.status_code != 200:
            print(f"Failed to fetch report types: {rt_resp.text}", file=sys.stderr)
            sys.exit(1)
        report_types = rt_resp.json()
        if not report_types:
            print("Error: no report types found. Run seed_report_types.py first.", file=sys.stderr)
            sys.exit(1)
        type_map = {rt["name"].strip().lower(): rt["id"] for rt in report_types}
        default_type_id = report_types[0]["id"]

        corpus = load_csv_corpus(args.csv_dir, type_map, default_type_id)
        if corpus:
            print(f"Loaded {len(corpus)} rows from {args.csv_dir}.")
        else:
            print(f"No CSV files found in {args.csv_dir}. Using built-in templates.")
            corpus = build_synthetic_corpus(type_map)

        created = 0
        errors = 0
        for i in range(args.count):
            base_entry = corpus[i % len(corpus)]
            payload = {
                "text": base_entry["text"],
                "lat": round(base_entry["lat"] + random.uniform(-0.003, 0.003), 6),
                "lon": round(base_entry["lon"] + random.uniform(-0.003, 0.003), 6),
                "urgency": weighted_choice(URGENCY_WEIGHTS),
                "report_type_id": base_entry["report_type_id"],
                "photo_url": None,
            }
            resp = client.post("/reports/", json=payload, headers=headers)
            if resp.status_code in (200, 201):
                created += 1
            else:
                errors += 1
                if errors <= 5:
                    print(f"  Error {resp.status_code}: {resp.text}", file=sys.stderr)

            if (i + 1) % args.batch == 0:
                print(f"  Progress: {i + 1}/{args.count} ({errors} errors)")

    print(f"\nDone. Created: {created}, Errors: {errors}")


if __name__ == "__main__":
    main()
