# Communication 000192 | ACD | 2026-07-01 14:15 UTC | Academics (relatório final)

> Seção em LaTeX para o relatório final da disciplina INF2921/CIS2114 — AI
> Systems Design (2026.1, PUC-Rio). Objetivo: overview com métricas do
> desenvolvimento do protótipo *fala,Gávea!*, do primeiro commit (17/jun/2026)
> ao estado atual (01/jul/2026). Métricas verificadas no repositório em
> 01/jul/2026 (393 commits; ~100 planos / 97 DONE; 26 research logs; 11
> reflections; 17 decisões D-001..D-017; 118 briefs; backend 137 arquivos /
> ~6.400 LOC / 41 endpoints / 322 testes pytest; frontend 92 arquivos /
> ~8.700 LOC / 134 testes vitest). O parágrafo de abertura foi fornecido pelo
> autor; o restante continua a narrativa e ancora-se na linha do tempo
> `communication-000191-academics.md`.

---

```latex
\subsubsection{fala,Gávea!}

O protótipo desenvolvido nesta fase, batizado de \emph{fala,Gávea!} durante o
estágio de confecção deste relatório, foi desenvolvido em um repositório git
dedicado usando o harness SEJA e o Claude Code como assistente de codificação.
Todo o aprendizado técnico absorvido durante os protótipos anteriores,
juntamente com os casos de uso e objetivos do sistema, foram codificados nas
intenções de design do harness SEJA. A escolha arquitetural e tecnológica
também estava clara: um backend expondo uma API REST e usando uma arquitetura
\emph{clean} para separar as regras de negócio das tecnologias utilizadas.

A construção não foi linear-\emph{ad hoc}: o harness SEJA impõe um ciclo de
quatro tempos --- \emph{pesquisa} $\rightarrow$ \emph{plano} $\rightarrow$
\emph{implementação} $\rightarrow$ \emph{reflexão} --- em que cada
funcionalidade entregue rastreia para trás até um registro de pesquisa que a
motivou e para a frente até uma reflexão que consolidou o aprendizado. Essa
propriedade, que chamamos de \emph{rastreabilidade bidirecional}, transforma a
própria trajetória de desenvolvimento em um artefato de estudo: não apenas
\emph{o que} foi construído, mas \emph{por que} cada escolha foi feita, fica
preservado e auditável. Reforça esse registro a separação deliberada entre o
que se \emph{pretendeu} (\texttt{product-design-as-intended.md}) e o que se de
fato \emph{codificou} (\texttt{product-design-as-coded.md}), e um \emph{namespace}
estável de decisões de projeto (D-001 a D-017) no estilo DRR (\emph{decision,
rationale, consequences}), em que decisões superadas não são apagadas mas
marcadas como tal (por exemplo, D-006 $\rightarrow$ D-007, quando a equipe
trocou HTML estático por um SPA React).

\paragraph{Métricas de desenvolvimento.} O sistema foi construído em uma janela
de aproximadamente treze dias (17 a 29 de junho de 2026), totalizando 393
\emph{commits}. A Tabela~\ref{tab:falagavea-metricas} sumariza o esforço, tanto
na dimensão de \emph{produto} (código entregue) quanto na dimensão
\emph{metodológica} (os artefatos versionados do ciclo SEJA).

\begin{table}[htbp]
  \centering
  \caption{Métricas de desenvolvimento do \emph{fala,Gávea!} (estado em
  01/jul/2026).}
  \label{tab:falagavea-metricas}
  \begin{tabular}{@{}lr@{}}
    \toprule
    \textbf{Dimensão / métrica} & \textbf{Valor} \\
    \midrule
    \multicolumn{2}{@{}l}{\emph{Processo (ciclo SEJA)}} \\
    \quad Janela de desenvolvimento & 17--29/jun/2026 ($\sim$13 dias) \\
    \quad \emph{Commits} git & 393 \\
    \quad Roadmaps estratégicos & 4 \\
    \quad Planos de implementação (97 \textsc{done}) & $\sim$100 \\
    \quad Registros de pesquisa (\emph{research logs}) & 26 \\
    \quad Reflexões (\emph{reflections}) & 11 \\
    \quad Decisões de projeto (D-001 a D-017) & 17 \\
    \quad Invocações de \emph{skill} registradas & 118 \\
    \midrule
    \multicolumn{2}{@{}l}{\emph{Backend (Python 3.13 / FastAPI)}} \\
    \quad Arquivos-fonte / linhas de código & 137 / $\sim$6.400 \\
    \quad Entidades de domínio & 8 \\
    \quad Casos de uso (\emph{use cases}) & 14 \\
    \quad \emph{Endpoints} REST (em 9 \emph{routers}) & 41 \\
    \quad Testes automatizados (\texttt{pytest}) & 322 \\
    \midrule
    \multicolumn{2}{@{}l}{\emph{Frontend (React 18 + Vite + TypeScript)}} \\
    \quad Arquivos-fonte / linhas de código & 92 / $\sim$8.700 \\
    \quad Testes automatizados (\texttt{vitest}) & 134 \\
    \midrule
    \multicolumn{2}{@{}l}{\emph{Camada de IA}} \\
    \quad Capacidades de IA em produção & 6 \\
    \bottomrule
  \end{tabular}
\end{table}

O \emph{backend} materializa a arquitetura \emph{clean} em quatro camadas
(\emph{domain} / \emph{application} / \emph{infrastructure} / \emph{presentation}),
com a regra da dependência apontando sempre para o domínio: nenhuma tecnologia
externa contamina as regras de negócio. Sobre SQLite/SQLAlchemy para
persistência e autenticação JWT com os papéis \emph{citizen}/\emph{agent}/%
\emph{admin}, o sistema expõe 41 \emph{endpoints} REST cobertos por 322 testes.
O \emph{frontend} é uma \emph{single-page application} React servida pelo próprio
FastAPI, com mapa interativo (react-leaflet) sobre coordenadas clusterizadas em
pontos de interesse reais da Gávea.

\paragraph{Trajetória em sete fases.} O desenvolvimento organizou-se em sete
fases, ancoradas em quatro \emph{roadmaps} estratégicos. As Fases 0 e 1
estabeleceram a fundação (arquitetura, domínio, autenticação) e o laço central
do domínio --- o \emph{relato} do cidadão e o \emph{encaminhamento} institucional,
modelado como agregação \emph{many-to-many} de relatos (D-004), codificando a
intuição de que $N$ mensagens sobre o mesmo problema devem gerar \emph{um} único
encaminhamento ao órgão competente. A Fase 2 introduziu a camada semântica
(ChromaDB, \emph{embeddings}, busca por similaridade e o primeiro chat RAG). A
Fase 3 enfrentou a produção e conteve o episódio mais ilustrativo do valor da
arquitetura: sob o teto de memória do ambiente de \emph{deploy}, a equipe trocou
\texttt{torch}-GPU por CPU, adotou o modelo de \emph{embedding} leve
\texttt{e5-small} e substituiu BERTopic por TF-IDF + K-means --- reconfiguração
que ocorreu \emph{sem tocar} no núcleo de casos de uso, precisamente porque a IA
vive atrás de portas com injeção de dependências. A Fase 4 redesenhou a
exploração de dados (API unificada de consulta, filtros salvos e o \emph{parser}
de linguagem natural para filtros). A Fase 5 fechou a terceira ponta do laço ---
a transparência para o cidadão (votos, comentários, relato anônimo). A Fase 6,
a mais ``meta'', tratou da \emph{comunicabilidade} da IA: um assistente da
plataforma por RAG sobre a própria documentação e o \texttt{AiBadge}, marcador
de proveniência que demarca, na interface, a fronteira entre conteúdo humano e
gerado. A Fase 7 cuidou do polimento e da prontidão para a demonstração.

\paragraph{Entregue \emph{vs.} idealizado.} Fiel ao rigor que a separação
\emph{as-intended}/\emph{as-coded} permite, registramos a fronteira honesta do
que foi construído. Em produção e verificáveis no código, seis capacidades de
IA: busca semântica de relatos, relatos similares, chat RAG com citação dos IDs
de fonte, \emph{parser} de linguagem natural que \emph{propõe} filtros mas nunca
os auto-aplica, extração de palavras-chave e o assistente da plataforma. Uma
decisão de projeto atravessa todas elas --- D-005: a IA como \emph{assistência},
não automação; o humano permanece no comando da curadoria, e a IA assiste, cita
suas fontes e nunca decide sozinha. Permanecem como hipótese de design,
pesquisadas e planejadas mas não implementadas neste ciclo, a sugestão
automática de tipo de relato e a síntese de comentários de encaminhamento ---
delimitação que constitui a agenda de pesquisa natural a partir desta base, e
não uma ressalva defensiva.
```
