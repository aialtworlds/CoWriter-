create extension if not exists pgcrypto;

create table if not exists projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  nome text not null,
  idioma text not null default 'pt-BR',
  genero text,
  criado_em timestamptz not null default now()
);

create table if not exists chapters (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  titulo text not null,
  texto_bruto text not null,
  idioma_detectado text,
  criado_em timestamptz not null default now()
);

create table if not exists analysis_runs (
  id uuid primary key default gen_random_uuid(),
  chapter_id uuid not null references chapters(id) on delete cascade,
  "timestamp" timestamptz not null default now(),
  palavras_analisadas int not null,
  creditos_consumidos numeric not null default 0,
  resultados_json jsonb
);

create table if not exists check_results (
  id uuid primary key default gen_random_uuid(),
  analysis_run_id uuid not null references analysis_runs(id) on delete cascade,
  check_type text not null,
  numero int,
  tipo text not null check (tipo in ('deterministico','julgamento')),
  confiabilidade text,
  score numeric,
  contagem int,
  detalhes_json jsonb,
  trechos_destacados jsonb
);

create table if not exists banned_patterns (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  project_id uuid references projects(id) on delete cascade,
  tipo text not null check (tipo in ('frase','gesto','descritor','estrutura')),
  idioma text,
  texto_padrao text not null,
  cooldown_max int not null default 1,
  janela_capitulos int not null default 1,
  disparos_count int not null default 0,
  criado_em timestamptz not null default now()
);

create table if not exists credit_wallet (
  user_id uuid primary key references auth.users(id) on delete cascade,
  saldo_creditos numeric not null default 0,
  atualizado_em timestamptz not null default now()
);

create table if not exists credit_transactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  tipo text not null check (tipo in ('bonus_inicial','compra_pacote','consumo')),
  quantidade numeric not null,
  referencia_id uuid,
  criado_em timestamptz not null default now()
);

create table if not exists payments (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  provider text not null check (provider in ('stripe','mercadopago')),
  external_id text not null,
  moeda text not null,
  valor numeric not null,
  pacote text not null,
  creditos_concedidos numeric not null,
  status text not null default 'pending',
  criado_em timestamptz not null default now(),
  unique (provider, external_id)
);

create index if not exists idx_projects_user on projects(user_id);
create index if not exists idx_chapters_project on chapters(project_id);
create index if not exists idx_analysis_runs_chapter on analysis_runs(chapter_id);
create index if not exists idx_check_results_run on check_results(analysis_run_id);
create index if not exists idx_banned_patterns_user on banned_patterns(user_id);
create index if not exists idx_banned_patterns_project on banned_patterns(project_id);
create index if not exists idx_credit_transactions_user on credit_transactions(user_id);
create index if not exists idx_payments_user on payments(user_id);

alter table projects enable row level security;
alter table chapters enable row level security;
alter table analysis_runs enable row level security;
alter table check_results enable row level security;
alter table banned_patterns enable row level security;
alter table credit_wallet enable row level security;
alter table credit_transactions enable row level security;
alter table payments enable row level security;

drop policy if exists projects_owner on projects;
create policy projects_owner on projects for all
  using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists chapters_owner on chapters;
create policy chapters_owner on chapters for all
  using (exists (select 1 from projects p where p.id = chapters.project_id and p.user_id = auth.uid()))
  with check (exists (select 1 from projects p where p.id = chapters.project_id and p.user_id = auth.uid()));

drop policy if exists analysis_runs_owner on analysis_runs;
create policy analysis_runs_owner on analysis_runs for all
  using (exists (select 1 from chapters c join projects p on p.id = c.project_id
                 where c.id = analysis_runs.chapter_id and p.user_id = auth.uid()))
  with check (exists (select 1 from chapters c join projects p on p.id = c.project_id
                      where c.id = analysis_runs.chapter_id and p.user_id = auth.uid()));

drop policy if exists check_results_owner on check_results;
create policy check_results_owner on check_results for all
  using (exists (select 1 from analysis_runs a
                 join chapters c on c.id = a.chapter_id
                 join projects p on p.id = c.project_id
                 where a.id = check_results.analysis_run_id and p.user_id = auth.uid()))
  with check (exists (select 1 from analysis_runs a
                      join chapters c on c.id = a.chapter_id
                      join projects p on p.id = c.project_id
                      where a.id = check_results.analysis_run_id and p.user_id = auth.uid()));

drop policy if exists banned_patterns_owner on banned_patterns;
create policy banned_patterns_owner on banned_patterns for all
  using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists credit_wallet_owner on credit_wallet;
create policy credit_wallet_owner on credit_wallet for select
  using (user_id = auth.uid());

drop policy if exists credit_transactions_owner on credit_transactions;
create policy credit_transactions_owner on credit_transactions for select
  using (user_id = auth.uid());

drop policy if exists payments_owner on payments;
create policy payments_owner on payments for select
  using (user_id = auth.uid());

-- Auto-provision wallet + 5000-word (5 credit) bonus on new signup
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.credit_wallet (user_id, saldo_creditos)
  values (new.id, 5)
  on conflict (user_id) do nothing;

  insert into public.credit_transactions (user_id, tipo, quantidade, referencia_id)
  values (new.id, 'bonus_inicial', 5, new.id);

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
