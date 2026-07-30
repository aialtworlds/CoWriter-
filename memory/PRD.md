# CoWriter V1 — PRD

## Problem Statement (original, verbatim summary)
Web app responsivo (PWA) chamado CoWriter — editor assistente de ficção focado EXCLUSIVAMENTE em revisão de capítulos de ficção. Não escreve nada pelo usuário; analisa texto existente, aponta problemas e sugere reescritas cirúrgicas, com arquitetura de confiabilidade explícita (determinístico vs. julgamento de IA) e suporte multi-idioma (7 locales Tier 1: PT-BR, PT-PT, EN, ES, IT, FR, DE). Monetização por créditos de palavra em pacotes avulsos (não assinatura): 1 crédito = 1.000 palavras, bônus inicial de 5.000 palavras (5 créditos). 14 checks totais: 8 determinísticos (gratuitos, ilimitados) + 6 de julgamento de IA (consomem crédito). Full schema Postgres/Supabase com RLS por posse (subqueries até `projects`), auth via Supabase (email/senha + Google), pagamentos via Stripe (USD) + Mercado Pago (BRL).

## Architecture
- **Frontend**: React + Tailwind (PWA, manifest.json + sw.js), react-i18next (7 locales, zero hardcoded), mammoth.js client-side for .docx parsing, Supabase JS client for Auth only.
- **Backend**: FastAPI, asyncpg direct connection to Supabase Postgres (DATABASE_URL), Supabase JWT verified via JWKS (`/app/backend/auth.py`). All ownership enforced explicitly in SQL WHERE/JOIN by `user_id` from JWT `sub` claim (defense-in-depth alongside DB-level RLS which is also enabled).
- **DB**: Supabase Postgres — full schema from spec (`projects`, `chapters`, `analysis_runs`, `check_results`, `banned_patterns`, `credit_wallet`, `credit_transactions`, `payments`) + RLS policies with ownership subqueries exactly as specified + a `handle_new_user()` trigger on `auth.users` granting the 5-credit signup bonus automatically. Migration file: `/app/backend/migrations/schema.sql`, applied via `/app/backend/run_migration.py`.
- **Checks (deterministic 1-8)**: isolated Python modules in `/app/backend/checks/`, embedded lexicons for pt/en (`verificado` reliability) and es/it/fr/de (`generico` reliability), aggregated by `runner.py`.
- **AI checks (9-14)**: NOT yet implemented — placeholder "coming soon" in the Critical Reading tab. Requires user's own Anthropic API key (`ANTHROPIC_API_KEY` env var, currently empty) — user explicitly declined the Emergent Universal Key to keep 1:1 cost control with Anthropic pricing for their credit-pack margins.
- **Payments**: NOT yet implemented (Fase 6).

## User Personas
- Escritor de ficção amador/profissional com capítulos já escritos, buscando revisão sistemática (repetições, ritmo, clichês) antes de considerar reescrita — não quer que a IA escreva por ele.

## Core Requirements (static)
See full spec in conversation history — 14 checks, credit-based monetization (no subscription), Supabase Auth + Postgres + RLS, i18n from day 1, PWA, dark mode.

## Implemented (as of 2026-07-30)
- **Fase 1 — Fundação**: Supabase Auth (email/password working end-to-end incl. Google OAuth wired but not E2E-testable), Postgres schema + RLS policies + ownership triggers, CRUD projetos/capítulos, paste + upload (.docx/.txt/.md via mammoth), PWA manifest+SW, react-i18next 7 locales with browser-language auto-detect + manual selector, `credit_wallet`/`credit_transactions` with global header counter, 5,000-word signup bonus via DB trigger.
- **Fase 2 — Checks Determinísticos (1-8)**: all 8 implemented (ai_fingerprint, gesture_cooldown, descriptor_cooldown, prose_rhythm, sensory_rotation, filter_words, dialogue_tag_variety, paragraph_opening_monotony), free/unlimited, "Fatos" section with highlighted excerpts + suggestions + copy button, reliability badges (verificado pt/en, genérico es/it/fr/de).
- Confirmation modal with word-count + credit estimate before analysis; 2-column desktop / tabbed mobile results layout; project history list; full credit statement page.
- Tested: 15/15 backend pytest cases pass, RLS/ownership boundary verified secure (cross-user 404s confirmed), full frontend flow verified via testing agent (login→project→chapter→analyze→result→history→statement, i18n switch, mobile layout).

## Backlog (prioritized)
- **P0 (Fase 3)**: Minhas Regras (banned_patterns CRUD, per-project/global scope, import/export texto simples, contador de disparos, integração com checks determinísticos).
- **P0 (Fase 4)**: Checks de IA 9-14 via Anthropic (needs user's `ANTHROPIC_API_KEY` + prompts user said they'd provide), transactional credit debit + analysis_run insert, insufficient-balance block + purchase CTA, non-PT/EN fallback to ⚠️ AI judgment for checks 1-3/5.
- **P1 (Fase 5)**: Export relatório .md/.pdf (ReportLab), PDF to Supabase Storage.
- **P1 (Fase 6)**: Stripe (USD) + Mercado Pago (BRL/Pix) package purchase, webhooks with idempotent crediting via `external_id`.
- **P2 (Fase 7)**: Final translation polish across 7 locales, locale-aware date/number/currency formatting, PWA install prompt polish.

## Next Tasks
1. Ask user for Anthropic API key + the 9-14 check prompts to start Fase 4.
2. Build Minhas Regras (Fase 3) — straightforward CRUD, can be done independently of the AI key.
3. Payments (Fase 6) — Stripe test key available in pod env; ask user for Mercado Pago credentials when ready.
