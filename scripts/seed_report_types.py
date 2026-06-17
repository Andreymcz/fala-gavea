"""Seed script: creates 8 initial ReportType records via the HTTP API.

Usage:
    FALA_GAVEA_ADMIN_EMAIL=admin@gavea.br FALA_GAVEA_ADMIN_PASSWORD=<pass> \
        uv run python scripts/seed_report_types.py
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

REPORT_TYPES = [
    ("Iluminacao publica", "Postes apagados, falha na rede eletrica de logradouros"),
    ("Transito e mobilidade", "Sinalizacao, semaforos, transporte publico"),
    ("Vandalismo", "Depredacao de patrimonio publico ou privado"),
    ("Espaco publico", "Calcadas, pracas, parques, equipamentos urbanos"),
    ("Lixo e conservacao", "Acumulo de lixo, entulho, limpeza urbana"),
    ("Seguranca e circulacao", "Pontos de risco, iluminacao de vias, seguranca viaria"),
    ("Conflito social", "Situacoes de conflito ou perturbacao da ordem publica"),
    ("Outro", "Demandas que nao se enquadram nas categorias anteriores"),
]


def main() -> None:
    api_url = os.environ.get("FALA_GAVEA_API_URL", "http://localhost:8000").rstrip("/")
    admin_email = os.environ.get("FALA_GAVEA_ADMIN_EMAIL", "")
    admin_password = os.environ.get("FALA_GAVEA_ADMIN_PASSWORD", "")

    if not admin_email or not admin_password:
        print("Error: FALA_GAVEA_ADMIN_EMAIL and FALA_GAVEA_ADMIN_PASSWORD must be set.", file=sys.stderr)
        sys.exit(1)

    # Login
    login_data = urllib.parse.urlencode({"username": admin_email, "password": admin_password}).encode()
    req = urllib.request.Request(f"{api_url}/auth/token", data=login_data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req) as resp:
            token_data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"Error: login failed ({e.code}): {body}", file=sys.stderr)
        sys.exit(1)

    token = token_data["access_token"]
    auth_header = f"Bearer {token}"

    created = 0
    skipped = 0
    for name, description in REPORT_TYPES:
        payload = json.dumps({"name": name, "description": description}).encode()
        req = urllib.request.Request(f"{api_url}/report_types/", data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", auth_header)
        try:
            with urllib.request.urlopen(req) as resp:
                resp.read()
                created += 1
                print(f"  Created: {name}")
        except urllib.error.HTTPError as e:
            if e.code == 422:
                skipped += 1
                print(f"  Skipped (already exists or validation error): {name}")
            else:
                body = e.read().decode()
                print(f"  Error creating '{name}' ({e.code}): {body}", file=sys.stderr)

    print(f"\nDone. Created: {created}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
