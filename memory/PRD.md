# CoWriter V1 — PRD

## Problem Statement (original, verbatim summary)
Web app responsivo (PWA) chamado CoWriter — editor assistente de ficção focado EXCLUSIVAMENTE em revisão de capítulos de ficção. Não escreve nada pelo usuário; analisa texto existente, aponta problemas e sugere reescritas cirúrgicas, com arquitetura de confiabilidade explícita (determinístico vs. julgamento de IA) e suporte multi-idioma (7 locales Tier 1: PT-BR, PT-PT, EN, ES, IT, FR, DE). Monetização por créditos de palavra em pacotes avulsos (não assinatura): 1 crédito = 1.000 palavras, bônus inicial de 5.000 palavras (5 créditos). 14 checks totais: 8 determinísticos (gratuitos, ilimitados) + 6 de julgamento de IA (consomem crédito). Full schema Postgres/Supabase com RLS por posse (subqueries até `projects`), auth via Supabase (email/senha + Google), pagamentos via Stripe (USD) + Mercado Pago (BRL).

## Architecture
- **Frontend**: React + Tailwind (PWA, manifest.json + sw.js), react-i18next (7 locales, zero hardcoded), mammoth.js client-side for .docx parsing, Supabase JS client for Auth only.
- **Backend**: FastAPI, asyncpg direct connection to Supabase Postgres (DATABASE_URL), Supabase JWT verified via JWKS (`/app/backend/auth.py`). All ownership enforced explicitly in SQL WHERE/JOIN by `user_id` from JWT `sub` claim (defense-in-depth alongside DB-level RLS which is also enabled).
- **DB**: Supabase Postgres — full schema from spec (`projects`, `chapters`, `analysis_runs`, `check_results`, `banned_patterns`, `credit_wallet`, `credit_transactions`, `payments`) + RLS policies with ownership subqueries exactly as specified + a `handle_new_user()` trigger on `auth.users` granting the 5-credit signup bonus automatically. Migration file: `/app/backend/migrations/schema.sql`, applied via `/app/backend/run_migration.py`.
- **Checks (deterministic 1-8)**: isolated Python modules in `/app/backend/checks/`, embedded lexicons for pt/en (`verificado` reliability) and es/it/fr/de (`generico` reliability), aggregated by `runner.py`.
- **AI checks (9-13)**: implemented in `/app/backend/checks/ai_checks.py`, calls Anthropic directly (5 parallel judgment prompts) using the user's own `ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL` — user explicitly declined the Emergent Universal Key to keep 1:1 cost control with Anthropic pricing for their credit-pack margins.
- **Payments**: NOT yet implemented (Fase 6, about to start).

## User Personas
- Escritor de ficção amador/profissional com capítulos já escritos, buscando revisão sistemática (repetições, ritmo, clichês) antes de considerar reescrita — não quer que a IA escreva por ele.

## Core Requirements (static)
See full spec in conversation history — 14 checks, credit-based monetization (no subscription), Supabase Auth + Postgres + RLS, i18n from day 1, PWA, dark mode.

## Implemented (as of 2026-02, merge consolidation)
- **Fase 1 — Fundação**: Supabase Auth (email/password + Google OAuth, provider habilitado e redirect testado), Postgres schema + RLS policies + ownership triggers, CRUD projetos/capítulos, paste + upload (.docx/.txt/.md via mammoth), PWA manifest+SW (ícones 192/512 incluídos), react-i18next 7 locales com auto-detect + seletor manual, `credit_wallet`/`credit_transactions` com contador global no header, bônus de 5.000 palavras (5 créditos) via trigger no DB.
- **Fase 2 — Checks Determinísticos (1-8)**: todos os 8 implementados em `/app/backend/checks/` (ai_fingerprint, gesture_cooldown, descriptor_cooldown, prose_rhythm, sensory_rotation, filter_words, dialogue_tag_variety, paragraph_opening_monotony), gratuitos/ilimitados, seção "Fatos" com trechos destacados + sugestões + botão copiar, badges de confiabilidade (verificado pt/en, genérico es/it/fr/de).
- **Fase 3 — Minhas Regras**: CRUD completo de `banned_patterns` (frase/gesto/descritor/estrutura), escopo por projeto ou global, import (colar multi-linha) + export (.txt), `disparos_count` incrementa atomicamente durante análise. Integrado aos checks determinísticos. Router `/app/backend/routers/rules.py` + página `/app/frontend/src/pages/RulesPage.jsx`.
- **Fase 4 — Checks de IA (9-13)**: implementados em `/app/backend/checks/ai_checks.py` via Anthropic direto (chamadas paralelas com `AsyncAnthropic`, chave própria do usuário em `ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL`), débito transacional de créditos, bloqueio de saldo insuficiente (402), leitura crítica sempre separada de "Fatos". Consolidado via merge das mudanças enviadas pelo usuário no GitHub (commits `35be968`/`474e71d`) preservando a integração com Minhas Regras (Fase 3).
- **Fase 5 — Exportação**: router `/app/backend/routers/export.py` gera relatório em .md e .pdf (ReportLab, import lazy) suportando os 7 idiomas; botões de exportar na tela de resultado.
- Confirmation modal com contagem de palavras + estimativa de créditos antes da análise; layout 2 colunas desktop / abas mobile; histórico de projetos; página de extrato de créditos.
- **Merge GitHub↔local (2026-02)**: reconciliados conflitos entre a implementação local (Fase 3) e os commits externos do usuário (Fase 4/5), mantendo ambos os routers (`rules` + `export`) registrados em `server.py`. Commit de merge: `9f919d1` (parent `6fa36df`, que já incorporava `474e71d`/`35be968`). **Push para `origin/main` NÃO realizado** — ambiente não possui credenciais Git para push HTTPS; usuário deve usar a opção "Save to Github" no chat para sincronizar o commit de merge.
- Testado anteriormente (pré-merge, por fase): Fase 1/2 — 15/15 backend + RLS ok; Fase 3 — 33/33 backend + RLS ok; Fase 4 — 5/5 backend + chamada real Claude confirmada (saldo 5→4, 402 em saldo zero). **Pós-merge (2026-02): consolidação feita, mas SEM re-execução de testes automatizados ou testing agent, por decisão explícita do usuário — regressão completa das Fases 1-5 ainda pendente.**

## Backlog (prioritized)
- **P0**: Regressão pós-merge (testes backend + testing agent) das Fases 1-5, ainda pendente por escolha do usuário de pular testes nesta rodada.
- **P2 (Fase 7)**: Polish visual, dark mode, QA responsivo em navegador real (não confirmado ainda), formatação locale-aware de data/número/moeda.

## Fase 6 — Monetização (Stripe-only) — implementado em 2026-02
- 3 pacotes fixos pré-pagos, sem assinatura, sem top-up avulso: Conto/novela curta (40 créditos, R$29,90), Romance médio (80 créditos, R$49,90), Romance longo (150 créditos, R$79,90). Créditos não expiram.
- Stripe Checkout hospedado (sandbox reivindicável do Emergent, conta BR, moeda BRL). Fluxo: `/comprar-creditos` (3 cards + saldo) → Stripe Checkout → `/pagamento/sucesso` (polling de status + crédito automático na carteira) ou `/pagamento/cancelado`.
- Backend: `backend/routers/payments.py` — `GET /payments/packages`, `POST /payments/checkout`, `GET /payments/status/{session_id}`, `POST /stripe/webhook`. Idempotência via `UPDATE payments SET status='paid' WHERE status != 'paid' RETURNING ...` dentro de transação atômica junto com `credit_transactions` (tipo=`compra_pacote`) e `credit_wallet`.
- **Tax mode = DIY (forçado)**: Stripe Tax não é suportado para contas de país BR (confirmado via API — erro `stripe_tax_inactive`), então não há automatic_tax/billing_address_collection. Isso é uma restrição técnica do Stripe, não uma escolha de simplicidade.
- **Pix**: tentado, mas não está ativado neste sandbox (`payment method type pix is invalid`); apenas cartão disponível por enquanto. Usuário pode ativar Pix no dashboard Stripe quando completar o KYC da conta.
- CTAs de "Comprar créditos" adicionados no Header, na tela de resultado (quando `leitura_critica.status === 'sem_credito'`) e no modal de confirmação de análise (quando saldo insuficiente).
- i18n completo para os 7 locales (namespace `payments`).
- **Testado**: pagamento real completo no Stripe Sandbox via browser (cartão de teste 4242...) confirmado ponta a ponta (carteira creditada corretamente, extrato mostra a compra). `testing_agent_v3_fork` validou 11/11 testes backend (pacotes, checkout válido/inválido, status, segurança cross-user, rejeição de webhook sem assinatura válida) — `/app/backend/tests/test_payments.py`. Um bug de overflow horizontal no header mobile (375px), meio agravado pelo novo link "Comprar créditos", foi encontrado e corrigido (`Header.jsx` agora usa `flex-wrap`).
- **Push para GitHub pendente**: usuário deve usar "Save to Github" para sincronizar todos os commits locais (merge Fase 4/5 + esta Fase 6).

## Next Tasks
1. Sincronizar todos os commits locais com GitHub via "Save to Github" (push manual não é possível pelo agente).
2. Quando o usuário decidir, rodar regressão completa (testes + testing agent) das Fases 1-5 que ficou pendente na consolidação do merge.
3. Considerar ativar Pix no dashboard Stripe após o usuário completar o KYC da conta sandbox/produção.
