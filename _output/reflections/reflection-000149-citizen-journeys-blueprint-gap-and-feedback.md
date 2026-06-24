# Reflection 000149 | 2026-06-23 23:12 UTC | Citizen journeys blueprint gap and feedback mechanism
spawned: research-000150

## Artifacts reflected on

- [reflection-000144](_output/reflections/reflection-000144-transparency-journeys-cesta-de-relatos.md) — Transparency journeys: citizen relatos + agent cesta de relatos
- [research-000147](_output/research-logs/research-000147-spec-drift-all.md) — Spec-drift all (conceptual-design + metacommunication)

## Summary

**reflection-000144** anchored on six plans/researches (forwarding CRUD, grid jornada, SPA, workspace, left panel + filters). The backend plumbing for the agent journey was in place, but the most recent block had optimized the *exploration surface* rather than the *decision/forwarding surface*. The user's own words at that point sketched the cesta de relatos concept (basket-as-widget, count badge in header, similar-open-reports check, inline encaminhamento creation). Four open questions remained: basket vs. existing SelectionBar, basket-as-view vs. persistent affordance, per-set similarity computation, and the citizen inline map-click form.

**research-000147** was a spec-drift analysis. The two spec files had drifted substantially — as-coded was the primary laggard. The entire roadmap-000146 work (cesta de relatos + citizen transparency, Waves 0–2) is in code but absent from as-coded. Seven Decisions (D-007–D-013) are implemented but carry no `STATUS: implemented` marker. Secondary issues: §16/§17 of as-intended still say "nenhuma implementada ainda" (false); BERTopic references persist after TF-IDF replaced it; `SavedFilter` and the NL filter/admin seed endpoints have no design-intent anchor.

## Reflection

*(User's words, verbatim.)*

Im thinking aboute the user journeys. este texto abaixo foi tirado de um blueprint feito pela equipe de designt, contando sobre 2 perfils de cidadao e sobre as jornadas e o que pde fazer no aplicativo. quero refletir o quanto falta para conseguir implementar isso no fala-gavea. Alem disso tenho pensado em um mecanismo de feedback cidadao. ele pode votar nos relatos de outros cidadaos, tipo um +1 e -1, o mesmo em encaminhamentos. ter comentarios em encaminhamentos seria interessante tambem.

---

Frustrações
34 anos
Cuidadora de Idosos
Ensino médio
Smartphone Android
Internet móvel
Frustrações
Os canais oficiais são lentos e opacos não há feedback sobre o que foi feito
As melhorias chegam ao asfalto mas raramente chegam à comunidade ao lado
55 anos
Arquiteta
Pós- graduação
Iphone
Fibra ótica
Sente que denúncias da favela são tratadas com menos urgência
Não tem tempo para burocracia depois de um dia longo de trabalho
Objetivos
Objetivos
Garantir que o beco onde mora seja iluminado e seguro para seus filhos voltarem da escola em paz.
Ser ouvida pelas autoridades sem precisar se expor.
Ter um canal direto e transparente com o poder público sem depender de "conhecidos"
Ver o bairro funcionar bem para todos, não apenas para os moradores do asfalto
Mora na Rocinha toda sua vida. Trabalha como cuidadora de idosos na mesma familia já há anos. Sobe e desce a comunidade a pé, dia e noite.
"Meu sonho é ver meus filhos caminhando livres pelas ruas da comunidade, tendo as mesmas oportunidades de qualquer criança do bairro."
"Meu sonho recuperar a confiança nas instituições públicas e voltar a utilizar os espaços públicos com tranquilidade."
Mora na Gávea há 12 anos. Trabalha no próprio escritório. Usa o Parque da Cidade para correr e é ativa em grupos de moradores no WhatsApp.
Ludmila
Moradora da Rocinha
Maria Alice
Moradora da Gávea
Decide relatar
Registra a ocorrência
Acompanha a demanda
Percebe resultados e fortalece  a confiança
Percebe um problema no território

Ludmila e Maria Alice percebem que um poste de iluminação está apagado em uma rua de muito movimento.
Avaliam se vale a pena fazer uma denúncia.
Fotografam o poste apagado e enviam a ocorrência.
Recebem atualizações sobre a ocorrência.
O poste é reparado e ambas percebem a melhoria.
Atividades

Entender se o problema representa um risco e se vale a pena reportá-lo.
Ter visibilidade do andamento.
Recuperar a sensação de segurança.
Encontrar um canal confiável e seguro.
Registrar o problema de forma prática.
Objetivos

Notificações do aplicativo e mapa de ocorrências.
Espaço urbano, aplicativo e comunidade.
Rua, vizinhos, grupos de WhatsApp, redes sociais.
Aplicativo Fala Gávea.
Aplicativo, câmera e GPS do celular.
Touchpoints

Histórico das ações e indicadores de impacto.
Cadastro simplificado, anonimização e geolocalização.
IA para categorização automática e georreferenciamento.
Dashboard, IA para agrupamento e notificações.
Technologia  IA

Quando a luz voltou, senti que nossa comunidade também pode ser ouvida.
praticidade, expectativa, confiança.
surpresa, confiança crescente, pertencimento
Experiência
Pela primeira vez sinto que alguém está ouvindo a comunidade

Isso me faz acreditar mais na colaboração entre moradores e poder público
Percebo que outras pessoas também reportaram problemas parecidos."

Achei simples registrar. Não precisei explicar tudo em detalhes.
Gostei de saber que a localização foi registrada automaticamente.

orgulho, esperança, pertencimento

Neutral

Já tentei outros canais antes e não tive retorno. Talvez dessa vez seja diferente

Tenho receio de me expor, mas se puder fazer isso em sigilo talvez valha a pena.
"É estranho ver esse problema continuar sem solução em um bairro tão movimentado."

"Esse trecho fica perigoso quando escurece. As pessoas comentam, mas parece que ninguém faz nada."
cautela, desconfiança, esperança
expectativa, curiosidade, esperança
Perceber a falha → Associar ao risco → Conversar com outras pessoas.
Abrir o aplicativo → Escolher categoria → Iniciar relato.
Tirar foto → Descrever → Confirmar localização → Enviar.
Receber atualização → Ver status → Acompanhar progresso.
Observar a mudança → Associar à participação → Continuar usando a plataforma.
Steps

---

## Gap analysis (blueprint vs. fala-gavea as-coded)

The blueprint defines a 5-step citizen journey (Percebe → Decide → Registra → Acompanha → Percebe resultados). Mapping each step to what is currently in code:

| Blueprint step | What the blueprint needs | Status in fala-gavea |
|---|---|---|
| **1. Percebe o problema** | Map of existing occurrences visible before login; community signal ("outras pessoas reportaram") | Partial — public `GET /reports/geojson` exists; no pre-login map view wired in frontend; no count-of-similar signal surfaced to anonymous users |
| **2. Decide relatar** | Risk/urgency evaluation, anonimização option, canal confiável | Urgency field exists on the form; anonymization not implemented; trust signal (track record of past resolutions) not shown |
| **3. Registra a ocorrência** | Foto upload, GPS auto-confirm, categoria selection, simplified form, no detailed write-up required | Category (tipo), description, lat/lon confirmed from map click exist; **photo upload not implemented**; geolocation auto-confirm from device GPS not implemented (user clicks map manually) |
| **4. Acompanha a demanda** | Push/in-app notifications, status updates, progress visibility on the encaminhamento linked to the relato | `GET /reports/{id}/forwardings` (public) exists since roadmap-000146; frontend citizen view of forwarding status not wired; **no notification system** |
| **5. Percebe resultados e confiança** | Histórico das ações, indicadores de impacto, closure signal | Forwarding status field exists; no impact indicators, no closure notification, no history timeline surfaced to citizen |

**Largest gaps:** photo upload (step 3), GPS auto-confirm (step 3), notification system (step 4), and the full "Acompanha" + "Percebe resultados" frontend surfaces for citizens.

**What is solid:** the relato form with map-click geolocation, category + urgency selection, the public forwarding read endpoints (D-011), and the citizen relatos list with "Meus relatos" toggle (D-012) — these map onto steps 2–3 and partially onto step 4.

## New idea noted: citizen feedback mechanism

The user introduced a citizen feedback idea not yet present in any artifact: upvote/downvote on relatos, upvote/downvote on encaminhamentos, and comments on encaminhamentos. This maps onto the blueprint's "comunidade ao lado" frustration (Ludmila) and the "IA para agrupamento" touchpoint — collective signal from votes could reinforce semantic clustering and help agents prioritize.

## Follow-ups

- The blueprint names "anonimização" as a key trust lever for Ludmila; no anonymization mode exists in the current data model — open question of how to model pseudonymous reporting alongside the current `author_id` requirement.
- Photo upload is absent from all plans to date; the blueprint lists it as step 3 infrastructure.
- The "Percebe resultados" step requires a closure/resolution signal surfaced to citizens; the current `ForwardingStatus` enum has the state but no citizen-facing timeline or notification pathway.
- The citizen feedback idea (votes + comments) is new and unanchored in any artifact; it raises its own sub-questions: vote weight, whether votes are public or aggregated-only, comment moderation, and how vote counts feed into agent prioritization or semantic search.
- The two personas (Ludmila, Rocinha, Android/mobile, concerned about anonymity; Maria Alice, Gávea, iPhone/fiber, concerned about bureaucracy) suggest the UX should handle both low-bandwidth and time-poor contexts — not yet a documented constraint.
