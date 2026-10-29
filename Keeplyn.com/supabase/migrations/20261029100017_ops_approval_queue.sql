-- Approval queue for work prepared by the build/drafting worker on the ops PC.
-- The worker (service role) creates and progresses items; an admin approves or
-- rejects them from /admin/approvals. Nothing reaches a customer or lead
-- without an admin decision.
begin;

create table public.ops_items (
  id bigint generated always as identity primary key,
  kind text not null,
  status text not null default 'pending',
  request_id bigint references public.website_requests (id) on delete cascade,
  ticket_id bigint references public.website_request_updates (id) on delete cascade,
  title text not null,
  summary text,
  demo_url text,
  email_to text,
  email_subject text,
  inbound_body text,
  draft_body text,
  final_body text,
  reviewer_note text,
  source jsonb not null default '{}'::jsonb,
  result text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  decided_at timestamptz,
  decided_by uuid references auth.users (id) on delete set null,
  constraint ops_items_kind_check check (kind in ('demo', 'revision', 'email_reply')),
  constraint ops_items_status_check check (status in ('working', 'pending', 'approved', 'sent', 'rejected', 'failed', 'superseded')),
  constraint ops_items_title_length check (char_length(title) between 1 and 300),
  constraint ops_items_demo_url_check check (demo_url is null or (demo_url ~ '^https://' and char_length(demo_url) <= 2048)),
  constraint ops_items_body_lengths check (
    coalesce(char_length(summary), 0) <= 8000
    and coalesce(char_length(inbound_body), 0) <= 20000
    and coalesce(char_length(draft_body), 0) <= 10000
    and coalesce(char_length(final_body), 0) <= 10000
    and coalesce(char_length(reviewer_note), 0) <= 4000
  )
);

create index ops_items_status_created_idx on public.ops_items (status, created_at desc);
create index ops_items_request_idx on public.ops_items (request_id);
-- One item per external source event (e.g. an Instantly reply id).
create unique index ops_items_source_key_idx on public.ops_items ((source ->> 'key')) where source ? 'key';

create trigger ops_items_touch_updated_at
before update on public.ops_items
for each row execute function private.touch_updated_at();

alter table public.ops_items enable row level security;

create policy "Admins can read the approval queue"
on public.ops_items for select
to authenticated
using ((select public.is_keeplyn_admin()));

revoke all on public.ops_items from anon, authenticated;
grant select on public.ops_items to authenticated;

-- Approve or reject a pending item. Approving an email reply requires the
-- final text; demo/revision approvals are completed by the server action.
create or replace function public.admin_decide_ops_item(
  p_item_id bigint,
  p_decision text,
  p_final_body text default null,
  p_note text default null
)
returns public.ops_items
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_item public.ops_items;
  v_body text := nullif(btrim(coalesce(p_final_body, '')), '');
  v_note text := nullif(btrim(coalesce(p_note, '')), '');
begin
  if not public.is_keeplyn_admin() then
    raise exception 'Administrator access is required.' using errcode = '42501';
  end if;
  if p_decision not in ('approve', 'reject') then
    raise exception 'Unknown decision.' using errcode = '22023';
  end if;

  select * into v_item from public.ops_items where id = p_item_id for update;
  if not found then
    raise exception 'Approval item not found.' using errcode = 'P0002';
  end if;
  if v_item.status <> 'pending' then
    raise exception 'This item was already handled.' using errcode = '55000';
  end if;
  if p_decision = 'approve' and v_item.kind in ('email_reply', 'revision') and v_body is null then
    raise exception 'Add the message before approving.' using errcode = '22023';
  end if;
  if char_length(coalesce(v_body, '')) > 10000 or char_length(coalesce(v_note, '')) > 4000 then
    raise exception 'Text is too long.' using errcode = '22023';
  end if;

  update public.ops_items
  set status = case when p_decision = 'approve' then 'approved' else 'rejected' end,
      final_body = coalesce(v_body, final_body),
      reviewer_note = v_note,
      decided_at = now(),
      decided_by = (select auth.uid())
  where id = p_item_id
  returning * into v_item;
  return v_item;
end;
$$;

-- Record the outcome of an approved demo/revision after the site action ran.
create or replace function public.admin_finish_ops_item(p_item_id bigint, p_status text, p_result text default null)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if not public.is_keeplyn_admin() then
    raise exception 'Administrator access is required.' using errcode = '42501';
  end if;
  if p_status not in ('sent', 'failed') then
    raise exception 'Unknown status.' using errcode = '22023';
  end if;
  update public.ops_items
  set status = p_status, result = left(p_result, 2000)
  where id = p_item_id and status = 'approved';
  if not found then
    raise exception 'Approved item not found.' using errcode = 'P0002';
  end if;
end;
$$;

revoke all on function public.admin_decide_ops_item(bigint, text, text, text) from public, anon;
grant execute on function public.admin_decide_ops_item(bigint, text, text, text) to authenticated;
revoke all on function public.admin_finish_ops_item(bigint, text, text) from public, anon;
grant execute on function public.admin_finish_ops_item(bigint, text, text) to authenticated;

commit;
