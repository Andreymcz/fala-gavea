# Prompt — gerar CSV de Seed de Relatos (fala-gavea)

Cole o bloco abaixo em qualquer LLM para gerar um CSV importável pelo painel admin
(`POST /admin/seed/relatos`, card "Seed de Relatos").

O prompt é **auto-contido**: os relatos reais coletados pelo Herbert e os cenários
de uso dos agentes públicos estão **anexados na íntegra** dentro do bloco, então
nenhum acesso a arquivos do repositório é necessário.

O cabeçalho usa `user_id` (canônico); o endpoint também aceita `id_cidadao` como
alias. Apenas `user_id` é obrigatório — as demais colunas têm fallback automático,
mas o prompt instrui o modelo a preenchê-las para gerar dados mais úteis.

---

```text
# Tarefa: gerar CSV de Seed de Relatos para o fala-gavea

Você é um gerador de dados de seed para o sistema **fala-gavea** (demandas de
cidadãos sobre segurança urbana na Gávea, Rio de Janeiro). Use como matéria-prima
os relatos reais coletados pelo Herbert e os cenários de agentes públicos —
ambos anexados na íntegra ao final deste prompt — e produza um CSV de relatos
fictícios, porém realistas, prontos para importar pelo painel admin
(POST /admin/seed/relatos).

## Como usar as fontes anexadas
- O anexo "Banco de relatos-fonte (Herbert)" traz relatos reais agrupados por tema.
  Gere relatos PARECIDOS com esses — mesmo tema, mesma voz de morador — mas NÃO os
  copie: reescreva cada um como uma demanda concreta sobre um ponto da Gávea.
- VOZ EM PRIMEIRA PESSOA: muitos relatos-fonte estão em terceira pessoa
  ("Moradores relatam...", "Idoso relata...", "Universitária relata..."). PERSONIFIQUE
  o morador e escreva cada `texto_relato` em PRIMEIRA PESSOA, como se o próprio cidadão
  estivesse enviando a demanda ("Moro na...", "Tenho medo de...", "Meu filho perdeu
  aulas porque...", "Sofri um acidente...").
- O anexo "Cenários de agentes públicos" traz casos de uso de gestores e pesquisadores.
  Use-os para ENRIQUECER os relatos: conecte cada relato à consequência concreta que
  aquele agente buscaria enxergar — por exemplo:
  iluminação apagada → medo de assalto/assédio, evasão escolar na EJA;
  lixo/entulho → leptospirose, dengue, ratos;
  alagamento/drenagem → mobilidade e acesso a serviços de saúde;
  conflito armado → ansiedade, insônia, saúde mental, faltas no trabalho/escola;
  calçadas/entulho → exclusão de idosos e cadeirantes.

## Formato de saída (OBRIGATÓRIO)
- Apenas o conteúdo CSV, **sem** texto extra, sem markdown, sem cercas de código.
- Codificação UTF-8. Separador vírgula. Campos com vírgula/quebra de linha
  entre aspas duplas.
- Primeira linha exatamente este cabeçalho:

user_id,texto_relato,latitude,longitude,data,topico,urgency

- Gere **40 linhas** de dados (ajuste se eu pedir outra quantidade).

## Regras por coluna
- **user_id** (única coluna obrigatória): identificador curto e estável do autor,
  ex.: `citizen01`, `c0007`. Reutilize o mesmo user_id em várias linhas para
  simular cidadãos recorrentes (use ~10 a 15 cidadãos distintos no total). Nunca
  deixe vazio.
- **texto_relato**: 1 a 3 frases, em PRIMEIRA PESSOA (voz do morador), mencionando
  explicitamente o problema e, quando fizer sentido, a consequência (ex.: poste
  apagado → medo de assalto; lixo → risco de leptospirose). Cite ruas/pontos da Gávea
  quando couber (ex.: Parque da Cidade, Praça Santos Dumont, Rua Marquês de São
  Vicente, Estrada da Gávea, PUC-Rio).
- **latitude / longitude**: ponto dentro do bounding box da Gávea —
  lat entre **-22.975 e -22.953**, lon entre **-43.235 e -43.205**, 6 casas
  decimais. (Se deixar em branco, o sistema gera um ponto aleatório na Gávea —
  prefira preencher.)
- **data**: ISO `YYYY-MM-DD`, distribuída no intervalo **2025-06-18 a 2026-06-18**.
  (Vazio = momento da importação.)
- **topico**: exatamente um destes valores (texto idêntico):
  `Iluminacao publica`, `Transito e mobilidade`, `Vandalismo`, `Espaco publico`,
  `Lixo e conservacao`, `Seguranca e circulacao`, `Conflito social`, `Outro`.
  Escolha o tópico que melhor casa com o texto. (Tópico inexistente seria
  criado automaticamente, mas use esta lista para manter consistência.)
- **urgency**: um de `alta`, `media`, `baixa`. Heurística: risco imediato à vida/
  segurança (assalto, atropelamento, esgoto a céu aberto, tiroteio) → `alta`; incômodo
  relevante mas sem risco iminente → `media`; estético/menor → `baixa`. (Vazio
  assume `media`.)

## Espaçamento e agrupamento (espaço e tempo)
- ESPALHE lat/lon por todo o bounding box da Gávea — não concentre tudo num único
  ponto; varie bairros, ruas e pontos de referência.
- DISTRIBUA as datas ao longo de todo o intervalo 2025-06-18 a 2026-06-18 — não
  agrupe tudo num único mês. Um mesmo user_id recorrente pode relatar em datas
  diferentes ao longo do período.
- MAS crie também AGRUPAMENTOS realistas ligados aos cenários dos agentes: alguns
  eventos devem se concentrar num mesmo período e numa mesma região, reproduzindo
  "ondas" temáticas que um pesquisador veria — por exemplo: vários relatos de
  alagamento/drenagem concentrados num mesmo período chuvoso e numa mesma área;
  um surto de relatos de conflito armado/tiroteio numa mesma semana e logradouro;
  relatos de iluminação apagada que persistem por meses no mesmo trecho. O objetivo
  é uma base com correlação espaço-temporal plausível, não ruído uniforme.

## Qualidade
- Varie tópicos, urgências, localizações e autores — evite repetição mecânica.
- Mantenha coerência entre texto, tópico e urgência.
- Distribua os relatos pelos 7 tópicos de forma proporcional ao banco-fonte anexado.
- Não invente colunas além das sete do cabeçalho.

## Banco de relatos-fonte (Herbert) — texto integral

Tópicos: 

1. Iluminação pública, postes apagados, falha na rede elétrica de logradouros: 

- O acesso ao posto de saúde está com vários postes apagados. Pacientes que saem de tratamentos noturnos relatam insegurança ao percorrer o trajeto. 

- Apagão deixa várias ruas da comunidade sem iluminação durante toda a noite. Moradores relatam ocorrência frequente de episódios de apagão que prejudica a circulação e gera insegurança. 

- O pai de um jovem atleta relata que a praça e a quadra de futebol próxima de sua residência estão sem iluminação há meses, o local está sempre vazio e tem aumentado a circulação de drogas e favorecido assaltos. 

- Idoso relata que sofreu um acidente no percurso ao supermercado devido à falta de iluminação na rua de sua casa. 

- Agentes comunitários de saúde relatam dificuldade para realizar visitas domiciliares no período noturno devido à falta de iluminação em algumas vielas, o que gera insegurança. 

- Universitária relata medo de assédio e abuso sexual devido à falta de iluminação no ponto de ônibus que faz parte do seu trajeto para a faculdade. A mulher relata que já faltou algumas aulas por esse motivo.   

- A passarela de acesso à comunidade está sem iluminação há meses, moradores relatam assaltos e sensação de insegurança 

- Alunos da modalidade EJA do período noturno relatam insegurança no trajeto de volta para casa devido à falta de iluminação na rua da escola. 

- Um ciclista relatou que sofreu um acidente devido à falta de iluminação de uma via. O rapaz passou em um buraco, estourou o pneu da bicicleta e por pouco não teve lesões graves.  

- Homem trans relata insegurança ao voltar do trabalho, com medo de agressões verbais e físicas, relata que pega um trajeto mais longo pois evitas essa avenida pouco iluminada. 

- O entorno do espaço cultural comunitário da região está com pouca iluminação e depredado há meses, o que reduziu a interação de moradores em atividades e apresentações culturais. 

 

2.  Trânsito e mobilidade, sinalização, semáforos, transporte público: 

- A faixa de pedestres em frente à escola municipal está apagada e sem sinalização adequada. Jovens relatam dificuldade para atravessar nos horários de entrada e saída. Pais relatam dificuldade para atravessar com crianças. 

- Moradores relatam que a falta de sinalização em um cruzamento já resultou em diversos acidentes envolvendo motociclistas e carros. 

- Cadeirantes relatam que as calçadas próximas ao ponto de ônibus estão danificadas e dificultam a circulação de pessoas que utilizam cadeira de rodas. 

- Moradores relatam que após chuvas intensas, uma rua utilizada como principal acesso à comunidade fica alagada, dificultando a circulação de veículos e pedestres. 

- Mulher grávida relata dificuldade para utilizar o transporte público porque o ponto de ônibus não possui assento nem cobertura. 

- Entregadores de aplicativo relatam risco constante de acidentes devido à má conservação da pavimentação em avenida com grande fluxo de entregas. A avenida é irregular e contém muitos buracos. 

- Moradores relatam que evitam atravessar determinada via porque os veículos não reduzem a velocidade devido à ausência de sinalização. 

- Ciclistas afirmam que a ausência de sinalização e falta de ciclovia em partes da região aumenta os riscos de acidentes e conflitos com motoristas. 

- Funcionários do comércio local relatam dificuldades para chegar ao trabalho por causa da redução de horários do transporte público. 

- A rampa de acesso à estação de transporte coletivo está quebrada há meses, comprometendo a acessibilidade de cadeirantes e pessoas com limitações físicas. 

- Moradores com deficiência visual relatam ausência de piso tátil e sinalização adequada nas vias principais.  

 

3. Conflito social, situações de conflito ou perturbação da ordem pública: 

- Meu filho perdeu várias aulas este mês porque houve muitos tiroteios entre policiais e facções próximos ao trajeto da escola e os moradores foram orientados a permanecer em casa. 

- Moradores relatam medo constante devido aos conflitos entre grupos armados que disputam o controle da região. 

- Moradores relatam a ocorrência incidente de assaltos a pedestres na região do viaduto próximo à comunidade. 

- Moradores da comunidade relatam abordagens policiais consideradas abusivas durante operações realizadas na comunidade. 

- Moradores e frequentadores da região relatam constrangimentos frequentes ao estacionar veículos em vias públicas devido à atuação de flanelinhas que cobram valores considerados abusivos para vigiar os carros. 

- Não consegui levar minha mãe para a consulta porque os acessos à comunidade ficaram fechados durante toda a manhã por causa de uma operação que acontece há dias. 

- A realização de bailes funks e demais eventos com som alto durante a madrugada tem provocado reclamações de moradores, dentre ele idosos e pessoas em tratamento de saúde. 

- Usuários da unidade de saúde relatam desentendimentos frequentes nas filas de atendimento causados pela falta de informações sobre a ordem de atendimento. 

- Moradores demonstram preocupação com o aumento do recrutamento de adolescentes pelo crime organizado na região. 

- Moradores relatam discussão e conflito entre ambulantes e policiamento local devido a utilização considerada inapropriada nas calçadas 

- Mulheres da comunidade relatam medo de utilizar esse determinado trajeto após casos recentes de tentativa de violência sexual. 

- Moradores relatam que jovens LGBTQIA+ evitam permanecer em determinadas áreas após episódios de violência e discriminação. 

- Moradores relatam que crianças e adolescentes têm evitado atividades esportivas e culturais por causa dos confrontos frequentes na região. 

- Motoristas de aplicativo se recusam a entrar em determinadas áreas após determinados horários por receio de situações de violência. 

- Moradores do mesmo logradouro relatam episódios de agressões e discussões envolvendo pessoas em situação de rua, indicando necessidade de acompanhamento especializado. 

- Moradores relatam que o transporte público deixou de circular temporariamente após um episódio de conflito armado na região. 

- Moradores relatam aumento da ansiedade e do medo após episódios recorrentes de troca de tiros próximos às residências. 

- Moradores do mesmo logradouro relatam episódios de agressões e discussões envolvendo pessoas em situação de rua, indicando necessidade de acompanhamento especializado. 

 

4. Lixo e conservação, acúmulo de lixo, entulho, limpeza urbana: 

- Um terreno com grande quantidade de entulho tem acumulado água após as chuvas, favorecendo a proliferação de insetos e doenças. 

- A praça utilizada por crianças e jovens está cercada por lixo acumulado e muitos moradores deixaram de frequentar o local. 

- Moradores relatam desentendimentos frequentes devido ao descarte irregular de lixo em uma área comum da comunidade. 

- Há semanas o lixo está acumulado próximo à unidade de saúde. O mau cheiro é forte e moradores relatam aumento da presença de ratos no local. 

- O caminhão de lixo deixou de passar com a frequência habitual e o acúmulo de resíduos já ocupa parte da via. Moradores afirmam que diversas reclamações foram feitas, mas o problema continua sem solução por parte do poder público. 

- Moradores relatam falta de lixeiras públicas em locais estratégicos de comércio e muita circulação de pessoas, o que favorece a poluição do ambiente. 

- Moradores em situação de vulnerabilidade convivem diariamente com pontos de descarte irregular próximos às suas residências. 

- Após a feira de domingo, resíduos permanecem espalhados pela via durante vários dias, dificultando a circulação e poluindo o ambiente. 

- Moradores reclamam que um terreno abandonado virou ponto frequente de descarte irregular de resíduos e contribui para a degradação da área, insegurança e poluição visual. 

- Sacolas de lixo e entulho ocupam parte da calçada, obrigando pedestres a caminhar pela rua, gerando sensação de abandono.  

- O lixo acumulado próximo ao canal tem causado mau cheiro constante e preocupação com enchentes durante períodos de chuva forte. 

- Bueiros estão constantemente obstruídos por lixo acumulado, causando alagamentos sempre que chove forte. 

 

5. Espaço público, calcadas, praças, parques, equipamentos urbanos: 

- Pessoas com deficiência relatam dificuldades para circular pelas calçadas devido à ausência de rampas e obstáculos espalhados pelo caminho. 

- Os bancos da praça estão quebrados há meses, dificultando o uso do espaço por idosos que costumavam frequentar o local. 

- A praça utilizada pelas crianças do bairro está com brinquedos quebrados e partes enferrujadas. Moradores relatam preocupação com a segurança dos pequenos. 

- Moradores relatam que a ausência de banheiros públicos e equipamentos urbanos adequados contribui para problemas sanitários em determinados espaços. 

- Moradores afirmam que uma praça antes frequentada pela comunidade está cada vez mais vazia devido à falta de conservação e iluminação. 

- Porteiro de um condomínio relata que as calçadas da rua estão repletas de pessoas em situação de rua e tem gerado conflitos ocasionais devido à ausência de políticas de assistência social. 

- A quadra esportiva apresenta traves quebradas e piso deteriorado, dificultando a realização de atividades esportivas e aumentando os riscos de acidentes. 

- A academia ao ar livre instalada na praça apresenta diversos aparelhos quebrados e sem manutenção. 

- O único espaço de lazer para crianças da região apresenta equipamentos danificados e acúmulo de lixo. 

- Moradores relatam que a praça deixou de ser um espaço de encontro da comunidade devido ao abandono e à falta de manutenção, favorecendo o uso de drogas e assaltos. 

- A comunidade reclama da falta de investimentos em espaços públicos e da sensação de que a região foi esquecida pelo poder público. 

- Moradores afirmam que cadeirantes não conseguem acessar determinados espaços públicos devido às condições precárias das calçadas. 

 

6. Vandalismo, depredação de patrimônio público ou privado: 

- Moradores relatam que o roubo recorrente de cabos de cobre tem deixado várias ruas da região sem iluminação e aumentando a sensação de insegurança. 

- Moradores relatam que os sinais de trânsito permanecem desligados há vários dias depois que cabos da fiação elétrica foram roubados durante a madrugada. 

- O ponto de ônibus da região teve sua estrutura depredada e permanece sem cobertura, prejudicando quem utiliza o transporte público diariamente. 

- Moradores da região relatam que há muitos ônibus circulando com bancos danificados e pichações no interior do veículo. 

- Moradores relatam que câmeras e painéis da estação foram destruídos e não foram substituídos até o momento. 

- Moradores relatam o aparecimento de pichações com referências a grupos criminosos em diferentes pontos da comunidade. 

- A depredação constante dos equipamentos da estação tem dificultado o uso do transporte por moradores e trabalhadores. 

- As lixeiras instaladas na praça foram arrancadas e destruídas. Desde então o lixo passou a se acumular nas calçadas. 

- Os aparelhos da academia ao ar livre foram depredados e atualmente não podem mais ser utilizados pela população. 

- O muro da escola foi pichado durante a madrugada e moradores reclamam da falta de conservação do entorno da unidade. 

 

7. Segurança e circulação, pontos de risco, iluminaçãoo de vias, segurança viária: 

- Quem trabalha em outras regiões da cidade precisa sair de casa ainda de madrugada para conseguir chegar pontualmente, moradores da comunidade relatam que o percurso à estação de ônibus é perigoso e pouco policiado nesse horário. 

- Levo quase duas horas para chegar ao trabalho todos os dias. As alternativas de transportes e os congestionamentos tornam o deslocamento cada vez mais difícil. 

- Estudantes da universidade relatam assaltos à mão armada próximo a pontos de ônibus. 

- Ciclistas entregadores da região afirmam que a ausência de sinalização e falta de ciclovia atrasa o percurso das entregas. 

- O trecho entre o ponto de ônibus e a entrada da comunidade permanece sem iluminação adequada. Moradores evitam passar pelo local após o anoitecer. 

- Moradores reclamam da redução de horários do transporte público, principalmente para quem trabalha em turnos noturnos. 

- Moradores relatam que quem retorna do trabalho à noite encontra dificuldades para circular em áreas com pouca iluminação e baixa movimentação. 

- Moradores relatam que confrontos na região frequentemente impedem a saída para o trabalho e causam atrasos ou faltas. 

- Moradores relatam dificuldade para atravessar uma avenida movimentada devido à inexistência de faixa de pedestres. 

- Moradores relatam confusão e riscos no embarque devido à falta de sinalização adequada próximo ao terminal de ônibus. 

 

 

 

 

 

 

 

 

 

## Cenários de agentes públicos — texto integral

Caso de Uso  — Política de Iluminação Pública  

Ator: Pesquisador/gestor da Secretaria Municipal de Conservação e Serviços Públicos 

Contexto: 
A prefeitura pretende ampliar investimentos em iluminação pública na região da Gávea. O pesquisador acessa a plataforma para identificar quais áreas concentram mais relatos relacionados à escuridão das vias, sensação de insegurança, dificuldades de circulação e demais impactos na vida dos moradores. 

 

Caso de Uso — Investimento Social 

Ator: Analista público 

Contexto: 
A prefeitura pretende investir em projetos de impacto social na Rocinha, mas deseja identificar prioridades apontadas pelos próprios moradores. O analista utiliza a plataforma para compreender problemas de segurança que apresentam maior recorrência e afetam múltiplas áreas da vida comunitária. 

 

Caso de Uso — Mobilidade e Acesso  

Ator: Pesquisador da Secretaria Municipal de Transportes 

Contexto: 
A prefeitura pretende revisar a oferta de transporte público e melhorar os deslocamentos entre a Rocinha, a Gávea e outras áreas da cidade. O pesquisador consulta a plataforma para identificar relatos sobre dificuldades de deslocamento, circulação, pontos de risco e barreiras de acesso. 

Caso de Uso – Política de educação 

Ator: Pesquisador da Secretaria da Educação 

Contexto: 
Pesquisador(a) responsável por acompanhar indicadores educacionais identifica um aumento da evasão escolar em determinadas áreas da Rocinha. Ele utiliza a plataforma para compreender como problemas de segurança, mobilidade, iluminação pública e violência podem estar afetando a frequência dos estudantes. 

 

Caso de Uso - Mulher e Direitos Humanos 

Ator: Pesquisadora da Secretaria de Políticas para as Mulheres 

Contexto: 
A secretaria pretende mapear obstáculos à circulação segura de mulheres no território. A pesquisadora consulta a plataforma para identificar relatos relacionados à iluminação pública, transporte, assédio e percepção de risco. 

 

Caso de Uso — Segurança Viária 

Ator: Técnico da CET-Rio 

Contexto: 
Após o aumento de acidentes em determinadas vias da região, o pesquisador busca identificar cruzamentos perigosos, falta de sinalização, problemas de travessia e locais frequentemente apontados pelos moradores como áreas de risco. 

 

Caso de Uso — Saúde (Mulher e Direitos Humanos) 

Ator: Pesquisador da Secretaria Municipal de Saúde 

Contexto: 
A secretaria observa aumento de notificações de atendimentos no SUS registrando casos de violência contra a mulher. O pesquisador(a) utiliza a plataforma para identificar se há incidência de relatos de abusos e tentativas de feminicídio. 

 

Caso de Uso  — Desenvolvimento Urbano 

Ator: Urbanista da Prefeitura 

Contexto: 
A prefeitura pretende realizar intervenções em espaços públicos da região. O urbanista utiliza a plataforma para identificar quais áreas concentram mais reclamações relacionadas à circulação, iluminação, barreiras arquitetônicas etc. 

 

Caso de Uso - Saúde 

Ator: Pesquisador(a) da Atenção Primária (SUS/SUAS) 

Contexto: 
Foi registrada uma queda na procura por serviços de unidades básicas de saúde no período noturno em região da Gávea. A gestora busca a plataforma para entender se problemas de mobilidade, iluminação ou segurança estão afetando a participação da população. 

 

Caso de Uso — Segurança Pública 

Ator: Pesquisador do Instituto de Segurança Pública 

Contexto: 
Pesquisas de opinião apontam aumento da sensação de insegurança entre os moradores da região. O pesquisador acessa a plataforma buscando compreender quais problemas urbanos estão contribuindo para essa percepção, e quais os problemas mais incidentes. 

 

Caso de Uso — Assistência Social 

Ator: Coordenadora do CRAS 

Contexto: 
A coordenação percebe redução na participação das famílias em oficinas e atividades comunitárias. A gestora acessa a plataforma para investigar se questões relacionadas à mobilidade e segurança podem estar dificultando o acesso aos serviços socioassistenciais. 

 

Caso de Uso — Segurança Pública 

Ator: Gestor da Guarda Municipal 

Contexto: 
A Guarda Municipal recebe demandas recorrentes relacionadas à ocupação de espaços públicos. O gestor utiliza a plataforma para identificar padrões territoriais e compreender quais fatores estão gerando conflitos e insegurança. 

 

Caso de Uso – Política de educação 

Ator: Pesquisador da Secretaria da Educação 

Contexto: 
Pesquisador(a) identifica um aumento da evasão escolar no período noturno da modalidade EJA na região, ele utiliza a plataforma para compreender como problemas de segurança, mobilidade, iluminação pública e violência podem estar afetando a frequência dos estudantes. 

 

Caso de Uso — Meio Ambiente e Saneamento 

Ator: Pesquisador da Fundação Rio-Águas 

Contexto: 
Após episódios de alagamento em determinadas áreas do território, o pesquisador busca compreender como os moradores percebem os impactos da drenagem urbana sobre a mobilidade, a segurança e o acesso a serviços públicos. 

 

 

Gere agora o CSV.
```
