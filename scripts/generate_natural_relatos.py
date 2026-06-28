"""
Gera seed_relatos_fala_gavea_1k.csv com textos variados via templates.
Nao requer LLM nem API key.

Uso:
    uv run python scripts/generate_natural_relatos.py
"""
import csv
import random
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

# scripts/ não é um pacote; garante que o módulo irmão seja importável quando
# o script é executado diretamente (`python scripts/generate_natural_relatos.py`).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gavea_clusters import sample_coordinate  # noqa: E402

OUTPUT_PATH = Path("data/seed_relatos_fala_gavea_1k.csv")
TOTAL_PER_TOPIC = 125

RUAS = [
    "na Rua Marquês de São Vicente",
    "na Estrada da Gávea",
    "na Rua Padre Leonel Franca",
    "na Rua Vice-Governador Rubens Berardo",
    "na Rua Jardim Botânico",
    "na Rua Pacheco Leão",
    "na Rua Casuarina",
    "na Praça Santos Dumont",
    "na Rua Lopes Quintas",
    "na Rua Fonte da Saudade",
    "na Rua Álvaro Chaves",
    "na Pista Cláudio Coutinho",
    "no Parque da Cidade",
    "perto da PUC-Rio",
    "perto do Shopping da Gávea",
    "na beira da Lagoa",
    "aqui no bairro",
    "na minha rua",
    "logo ali na esquina",
]

URGENCY_WEIGHTS: dict[str, list] = {
    "Conflito social":        [("alta", 0.6), ("media", 0.3), ("baixa", 0.1)],
    "Seguranca e circulacao": [("alta", 0.5), ("media", 0.35), ("baixa", 0.15)],
    "Iluminacao publica":     [("alta", 0.4), ("media", 0.4), ("baixa", 0.2)],
    "Transito e mobilidade":  [("alta", 0.2), ("media", 0.5), ("baixa", 0.3)],
    "Lixo e conservacao":     [("alta", 0.2), ("media", 0.45), ("baixa", 0.35)],
    "Vandalismo":             [("alta", 0.3), ("media", 0.45), ("baixa", 0.25)],
    "Espaco publico":         [("alta", 0.15), ("media", 0.45), ("baixa", 0.4)],
    "Outro":                  [("alta", 0.2), ("media", 0.4), ("baixa", 0.4)],
}

USERS = [f"citizen{i:03d}" for i in range(1, 61)]
DATE_START = datetime(2025, 1, 1)
DATE_END   = datetime(2026, 6, 1)

# ── Templates por tópico ──────────────────────────────────────────────────────
# Cada entry é uma lista de frases; o gerador combina aleatoriamente 1-3 delas.

TEMPLATES: dict[str, list[str]] = {
    "Lixo e conservacao": [
        "O lixo {rua} tá acumulado há dias e ninguém faz nada.",
        "Tem um monte de entulho abandonado {rua}, absurdo.",
        "Tô passando {rua} e o cheiro de lixo tá insuportável.",
        "Já faz uma semana que o lixo não é coletado {rua}.",
        "A prefeitura precisa agir! O lixo {rua} tá atraindo rato.",
        "Sacos de lixo espalhados na calçada {rua} desde ontem.",
        "Alguém jogou entulho de obra {rua} e deixou largado.",
        "A coleta de lixo {rua} sumiu. O que aconteceu?",
        "Minha rua virou lixão. Tem lixo {rua} por todo lado.",
        "Cara, o lixo {rua} tá ridículo. Já liguei pra prefeitura e nada.",
        "Tem uma montanha de lixo {rua} que ninguém tira.",
        "Esgoto entupido e lixo acumulado {rua}, situação precária.",
        "Há dias com sacos de lixo rasgados {rua}, cheios de inseto.",
        "O lixo orgânico {rua} tá fedendo demais com esse calor.",
        "Entulho de construção abandonado {rua} há mais de um mês.",
        "Jogaram móveis velhos {rua} e ninguém recolhe.",
        "Lixo espalhado por toda a calçada {rua}, impossível passar.",
        "A limpeza urbana {rua} foi esquecida completamente.",
        "Ratos aparecendo por causa do lixo acumulado {rua}.",
        "Terceiro dia seguido sem coleta {rua}. Até quando?",
    ],
    "Iluminacao publica": [
        "Os postes {rua} estão todos apagados faz dias.",
        "Voltei do trabalho tarde e a rua {rua} tava no breu total.",
        "Poste queimado {rua} há mais de uma semana, ninguém conserta.",
        "Sem iluminação {rua}, fica perigoso à noite.",
        "Toda a quadra {rua} no escuro. Cadê a Enel?",
        "Minha filha tem medo de passar {rua} de noite por causa do escuro.",
        "Poste piscando {rua} já faz 10 dias, parece discoteca.",
        "Rua totalmente escura {rua}, fácil de assaltar assim.",
        "Fiz o chamado pra Enel semana passada sobre o poste {rua} e nada.",
        "Vários postes apagados {rua}. Isso é descaso.",
        "Sem luz {rua} à noite, carro entrou em buraco ontem.",
        "A iluminação {rua} simplesmente parou de funcionar.",
        "Poste caindo {rua}, além de escuro é perigoso.",
        "Ia sair pra correr mas {rua} tá escuro demais.",
        "Três postes apagados em sequência {rua}. Que descuido.",
        "Passando {rua} à noite dá medo, zero iluminação.",
        "Lâmpada queimada {rua} há quinze dias sem previsão de troca.",
        "A rua {rua} ficou escura e aumentou os furtos.",
        "Acionei a prefeitura sobre o poste {rua} e ficou no papel.",
        "Nem a lua ilumina tanto quanto deveria os postes {rua}.",
    ],
    "Transito e mobilidade": [
        "O trânsito {rua} tá um caos nessa hora do dia.",
        "Semáforo quebrado {rua} há dias, acidentes à vista.",
        "Buraco enorme {rua} que já danificou dois carros.",
        "Não tem sinalização nenhuma {rua}, é temerário atravessar.",
        "Ciclista quase atropelado {rua} por falta de ciclofaixa.",
        "Ônibus parando no meio da rua {rua} e travando tudo.",
        "Desvio de obra {rua} sem sinalização adequada, confuso demais.",
        "Carro estacionado em cima da calçada {rua}, pedestres na rua.",
        "Valão aberto {rua} que já engoliu o pneu do meu carro.",
        "Faixa de pedestres {rua} completamente apagada.",
        "Engarrafamento {rua} todo dia no horário de pico.",
        "Motocicleta subindo calçada {rua} assustando pedestres.",
        "Asfalto esburacado {rua}, minha suspensão já sofreu.",
        "Placa de rua caída {rua} há semanas.",
        "Semáforo {rua} em modo piscante desde segunda.",
        "Lombada {rua} destruída, carros passando em alta velocidade.",
        "Trânsito parado {rua} por obra sem aviso prévio.",
        "Calçada destruída {rua}, idosos e cadeirantes sem passagem.",
        "O ônibus linha 583 não para mais {rua}, abandonaram o ponto.",
        "Buraco {rua} que a prefeitura tampou com areia e abriu de novo.",
    ],
    "Seguranca e circulacao": [
        "Fui assaltado {rua} ontem à noite, tá perigoso.",
        "Tem pessoas suspeitas circulando {rua} toda noite.",
        "Assalto a pedestres {rua} virou rotina.",
        "Meu vizinho foi roubado {rua} em plena tarde.",
        "Câmera de segurança {rua} quebrada há meses.",
        "Carro arrombado {rua} de madrugada, terceiro esse mês.",
        "Grupo bagunçando {rua} até tarde, moradores com medo.",
        "Furto de bike {rua}, precisamos de mais policiamento.",
        "Tentativa de assalto {rua} esta manhã, me assustou muito.",
        "Traficantes na esquina {rua} intimidando quem passa.",
        "Preciso sair cedo e {rua} tá perigoso antes de amanhecer.",
        "Quiosque clandestino {rua} gerando confusão e briga.",
        "Minha bolsa foi arrancada {rua} numa moto.",
        "Furto de retrovisor {rua}, segundo da semana.",
        "Criança com medo de ir pra escola passando {rua}.",
        "Viatura não passa {rua} há dias, abandono policial.",
        "Atividade suspeita {rua} toda madrugada.",
        "Barulho de tiro {rua} ontem à noite, assustador.",
        "Porta de garagem arrombada {rua}, terceiro caso.",
        "Cheguei em casa e havia marcas de tentativa de arrombamento {rua}.",
    ],
    "Conflito social": [
        "Briga feia entre vizinhos {rua} que já durou horas.",
        "Confusão generalizada {rua} com xingamentos e empurrão.",
        "Moradores brigando por causa de barulho {rua} todo fim de semana.",
        "Desentendimento entre grupos {rua} que quase virou pancadaria.",
        "Discussão de trânsito {rua} que desceu pro pessoal.",
        "Vizinho colocando som alto {rua} até meia-noite toda noite.",
        "Conflito entre moradores e ambulantes {rua}.",
        "Briga entre crianças {rua} que virou bagunça de adulto.",
        "Família brigando na rua {rua}, situação constrangedora.",
        "Denúncia de agressão verbal constante {rua}.",
        "Grupo de jovens causando confusão {rua} toda noite.",
        "Discussão por vaga de estacionamento {rua} virou caso de polícia.",
        "Barulho de briga {rua} perturbando todo o quarteirão.",
        "Conflito entre comerciantes e moradores {rua} sem solução.",
        "Agressão entre pedestres {rua} filmada por testemunhas.",
        "Morador perturbando a vizinhança {rua} com ameaças.",
        "Disputa de área {rua} entre grupos rivais.",
        "Briga de bar {rua} que saiu pro meio da rua.",
        "Confusão no ponto de ônibus {rua} com gritos e empurra-empurra.",
        "Conflito relacionado a entrega de aplicativo {rua} ficou feio.",
    ],
    "Vandalismo": [
        "Picharam toda a parede {rua} de madrugada.",
        "Vandalizaram o banco da praça {rua}, destruído.",
        "Quebraram as lâmpadas do poste {rua} de propósito.",
        "Grafite obsceno na parede da escola {rua}.",
        "Placa de trânsito arrancada {rua} por vândalos.",
        "Pichação em cima de pichação {rua}, ninguém limpa.",
        "Ônibus riscado e vandalizado {rua}.",
        "Quebraram o espelho do retrovisor do meu carro {rua}.",
        "Lixeiras públicas {rua} destruídas, joguei fora.",
        "Bancos da praça {rua} todos depredados.",
        "Vidro de poste de semáforo quebrado {rua}.",
        "Picharam o muro do condomínio {rua} de novo.",
        "Vandalizaram o playground {rua}, crianças sem onde brincar.",
        "Câmera de segurança {rua} arrancada propositalmente.",
        "Portão da praça {rua} forçado e quebrado.",
        "Escrita de gangue pichada {rua}, intimidatório.",
        "Muros recém-pintados {rua} já pichados novamente.",
        "Equipamento de academia ao ar livre {rua} destruído.",
        "Bebedouro público {rua} vandalizado, sem funcionar.",
        "Quebraram o monumento {rua} que estava restaurado.",
    ],
    "Espaco publico": [
        "A praça {rua} tá abandonada, ninguém cuida.",
        "Calçada toda quebrada {rua}, impossível pra cadeirante.",
        "Árvore caída {rua} desde a última chuva, ninguém tirou.",
        "Buraco na calçada {rua} engoliu o salto do sapato da minha mãe.",
        "Praça {rua} tomada por grama alta e mato.",
        "Não tem bancos na praça {rua} pra sentar.",
        "Brinquedo do parquinho {rua} quebrado há meses.",
        "Calçada {rua} com entulho e ninguém desobstrui.",
        "Drenagem entupida {rua}, qualquer chuva alaga tudo.",
        "Espaço público {rua} virou estacionamento irregular.",
        "A praça {rua} deveria ser pra todos mas tá inacessível.",
        "Mato alto na calçada {rua} escondendo buracos.",
        "Falta rampa de acessibilidade {rua}.",
        "Totem de informação {rua} quebrado e apagado.",
        "Bebedouro público {rua} sem funcionar faz meses.",
        "Área verde {rua} sendo invadida por carros.",
        "Equipamentos de ginástica {rua} enferrujados e sem manutenção.",
        "Calçada {rua} com desnível perigoso pra quem corre.",
        "Lixeira pública {rua} transbordando sem coleta.",
        "Ponto de ônibus {rua} sem cobertura, chuva molha todo mundo.",
    ],
    "Outro": [
        "Situação estranha {rua} que não sei bem como classificar.",
        "Problema que precisa de atenção {rua} mas não sei pra quem ligar.",
        "Obra irregular acontecendo {rua} sem autorização aparente.",
        "Animal abandonado {rua} há dias, alguém pode ajudar?",
        "Cano d'água estourando {rua} e ninguém da Cedae aparece.",
        "Barulho de obra {rua} às seis da manhã todo dia.",
        "Animal silvestre ferido {rua}, precisa de resgate.",
        "Veículo abandonado {rua} há semanas, virou lixo.",
        "Evento privado bloqueando a calçada {rua} sem aviso.",
        "Fiação elétrica exposta {rua}, perigo de choque.",
        "Terreno abandonado {rua} com mato e lixo acumulado.",
        "Goteira de prédio {rua} molhando pedestres embaixo.",
        "Carro com alarme disparado {rua} há horas.",
        "Buraco na rede de esgoto {rua} com cheiro forte.",
        "Tapume de obra {rua} tomando calçada inteira.",
        "Entupimento de bueiro {rua} que alaga tudo.",
        "Pombos infestando o telhado {rua}, situação insalubre.",
        "Fio de alta tensão caído {rua}, urgente.",
        "Vazamento de gás {rua}, chamei o Riogas mas demora.",
        "Lona improvisada {rua} bloqueando sinalização.",
    ],
}


# ── Gerador ───────────────────────────────────────────────────────────────────
def make_relato(topic: str) -> str:
    templates = TEMPLATES[topic]
    rua = random.choice(RUAS)

    # Combina 1, 2 ou 3 frases (com pesos — maioria 1-2 frases)
    n_frases = random.choices([1, 2, 3], weights=[0.5, 0.35, 0.15])[0]
    escolhidas = random.sample(templates, min(n_frases, len(templates)))

    partes = [t.format(rua=rua) for t in escolhidas]
    return " ".join(partes)


def random_date() -> str:
    delta = (DATE_END - DATE_START).days
    return (DATE_START + timedelta(days=random.randint(0, delta))).strftime("%Y-%m-%d")


def weighted_urgency(topic: str) -> str:
    options, weights = zip(*URGENCY_WEIGHTS[topic])
    return random.choices(options, weights=weights)[0]


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    rows: list[list] = []

    # Saída opcional via argv[1] (default = OUTPUT_PATH), útil para validar a
    # geração sem sobrescrever o CSV commitado.
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT_PATH

    # RNG determinístico para que regenerações sejam estáveis e diff-reviewáveis.
    rng = random.Random(20260628)
    random.seed(20260628)

    for topic in TEMPLATES:
        for _ in range(TOTAL_PER_TOPIC):
            # Coordenadas clusterizadas em POIs reais da Gávea (ver
            # scripts/gavea_clusters.py) — não mais espalhadas num retângulo
            # que vazava para o Jardim Botânico/Lagoa.
            lat, lon = sample_coordinate(rng)
            rows.append([
                random.choice(USERS),
                make_relato(topic),
                lat,
                lon,
                random_date(),
                topic,
                weighted_urgency(topic),
            ])

    random.shuffle(rows)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "texto_relato", "latitude", "longitude", "data", "topico", "urgency"])
        writer.writerows(rows)

    total = len(rows)
    print(f"Gerado: {out_path} ({total} relatos)")
    counts = Counter(r[5] for r in rows)
    for t, c in sorted(counts.items()):
        print(f"  {t:<28} {c}")


if __name__ == "__main__":
    main()
