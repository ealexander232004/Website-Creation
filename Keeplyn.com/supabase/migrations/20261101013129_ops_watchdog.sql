-- Alerts for work that is stuck: failed builds, requests with no demo after a
-- day, change requests nobody picked up, approvals left waiting, and a PC
-- worker that stopped checking in. The worker (service role) reads the report
-- when it queues work; an hourly Vercel cron reads it through a token-checked
-- wrapper so a powered-off PC still gets noticed.
begin;

create table public.ops_worker_heartbeat (
  id smallint primary key default 1,
  seen_at timestamptz not null default now(),
  constraint ops_worker_heartbeat_single_row check (id = 1)
);
alter table public.ops_worker_heartbeat enable row level security;
-- No policies: only the worker's secret key (which bypasses RLS) writes it.
insert into public.ops_worker_heartbeat (id) values (1);

create or replace function public.ops_alert_report()
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
  with latest as (
    -- The newest item per request and kind; older failures were superseded by a retry.
    select distinct on (i.kind, coalesce(i.request_id, -i.id)) i.*
    from public.ops_items i
    where i.status <> 'superseded'
    order by i.kind, coalesce(i.request_id, -i.id), i.id desc
  )
  select jsonb_build_object(
    'worker_seen_at', (select h.seen_at from public.ops_worker_heartbeat h where h.id = 1),
    'pending', coalesce((
      select jsonb_agg(jsonb_build_object('id', i.id, 'kind', i.kind, 'title', i.title, 'since', i.updated_at) order by i.id)
      from public.ops_items i
      where i.status = 'pending'
    ), '[]'::jsonb),
    'failed', coalesce((
      select jsonb_agg(jsonb_build_object('id', l.id, 'kind', l.kind, 'title', l.title, 'since', l.updated_at, 'error', left(l.result, 200)) order by l.id)
      from latest l
      where l.status = 'failed'
        and l.updated_at > now() - case when l.kind = 'email_reply' then interval '2 days' else interval '14 days' end
    ), '[]'::jsonb),
    'stalled', coalesce((
      select jsonb_agg(jsonb_build_object('id', r.id, 'name', coalesce(r.business_name, r.customer_name, 'Request ' || r.id), 'since', r.created_at) order by r.id)
      from public.website_requests r
      where r.status in ('submitted', 'in_review', 'in_progress')
        and r.created_at < now() - interval '24 hours'
        and not exists (
          select 1 from latest l
          where l.request_id = r.id and l.kind = 'demo' and l.status in ('working', 'pending', 'approved', 'sent', 'failed')
        )
    ), '[]'::jsonb),
    'changes', coalesce((
      select jsonb_agg(jsonb_build_object('id', r.id, 'name', coalesce(r.business_name, r.customer_name, 'Request ' || r.id), 'since', r.updated_at) order by r.id)
      from public.website_requests r
      where r.status = 'changes_requested'
        and r.updated_at < now() - interval '2 hours'
        and not exists (
          select 1 from public.ops_items i
          where i.request_id = r.id and i.kind in ('demo', 'revision') and i.created_at > r.updated_at
        )
    ), '[]'::jsonb)
  );
$$;

revoke all on function public.ops_alert_report() from public, anon, authenticated;
grant execute on function public.ops_alert_report() to service_role;

-- The cron route has no database key, only its CRON_SECRET; the same value is
-- kept in Vault, so a matching token is the only way in.
create or replace function public.ops_watchdog_report(p_token text)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_expected text;
begin
  select s.decrypted_secret into v_expected
  from vault.decrypted_secrets s
  where s.name = 'ops_watchdog_token';
  if v_expected is null or p_token is null or length(p_token) < 32 or p_token <> v_expected then
    raise exception 'Not allowed.' using errcode = '42501';
  end if;
  return public.ops_alert_report();
end;
$$;

revoke all on function public.ops_watchdog_report(text) from public;
grant execute on function public.ops_watchdog_report(text) to anon, authenticated, service_role;

-- Lets the operator set the shared token without it passing through SQL logs.
create or replace function public.ops_set_watchdog_token(p_token text)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_id uuid;
begin
  if p_token is null or length(p_token) < 32 then
    raise exception 'Token too short.' using errcode = '22023';
  end if;
  select s.id into v_id from vault.secrets s where s.name = 'ops_watchdog_token';
  if v_id is null then
    perform vault.create_secret(p_token, 'ops_watchdog_token', 'Shared with the Vercel CRON_SECRET for /api/ops/watchdog');
  else
    perform vault.update_secret(v_id, p_token);
  end if;
end;
$$;

revoke all on function public.ops_set_watchdog_token(text) from public, anon, authenticated;
grant execute on function public.ops_set_watchdog_token(text) to service_role;

commit;
