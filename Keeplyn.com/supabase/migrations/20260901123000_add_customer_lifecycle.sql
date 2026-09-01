begin;

create extension if not exists pgcrypto with schema extensions;

create schema if not exists private;
revoke all on schema private from public, anon, authenticated;

create table private.keeplyn_admins (
  email text primary key,
  created_at timestamptz not null default now(),
  constraint keeplyn_admins_email_lowercase_check check (email = lower(email)),
  constraint keeplyn_admins_email_length_check check (char_length(email) between 3 and 254)
);

insert into private.keeplyn_admins (email)
values
  ('ealexander23@mail.wou.edu'),
  ('support@keeplyn.com')
on conflict (email) do nothing;

create table private.webhook_secrets (
  provider text primary key,
  secret_sha256 text not null,
  rotated_at timestamptz not null default now(),
  constraint webhook_secrets_hash_check check (secret_sha256 ~ '^[a-f0-9]{64}$')
);

insert into private.webhook_secrets (provider, secret_sha256)
values ('stripe', '610c0d602452cb7ef14dbe40c1b6fc76869f480d84da1cedbe74577a796f60a3')
on conflict (provider) do update
set secret_sha256 = excluded.secret_sha256,
    rotated_at = now();

create or replace function public.is_keeplyn_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from private.keeplyn_admins
    where email = lower(coalesce(auth.jwt() ->> 'email', ''))
  );
$$;

revoke all on function public.is_keeplyn_admin() from public, anon;
grant execute on function public.is_keeplyn_admin() to authenticated;

alter table public.website_requests
  drop constraint website_requests_status_check;

update public.website_requests
set status = 'demo_ready'
where status = 'completed';

alter table public.website_requests
  add column customer_name text,
  add column customer_email text,
  add column demo_url text,
  add column demo_ready_at timestamptz,
  add column approved_at timestamptz,
  add column domain_name text,
  add column domain_submitted_at timestamptz,
  add column hosting_selected boolean not null default false,
  add column hosting_status text not null default 'not_selected',
  add column payment_status text not null default 'not_ready',
  add column stripe_checkout_session_id text,
  add column stripe_customer_id text,
  add column stripe_subscription_id text,
  add column paid_at timestamptz,
  add column live_url text,
  add column live_at timestamptz,
  add column updated_at timestamptz not null default now(),
  add constraint website_requests_status_check check (
    status in (
      'submitted',
      'in_review',
      'in_progress',
      'demo_ready',
      'changes_requested',
      'approved',
      'domain_pending',
      'payment_pending',
      'paid',
      'launching',
      'live',
      'cancelled'
    )
  ),
  add constraint website_requests_customer_name_length check (
    customer_name is null or char_length(customer_name) between 1 and 100
  ),
  add constraint website_requests_customer_email_length check (
    customer_email is null or char_length(customer_email) between 3 and 254
  ),
  add constraint website_requests_demo_url_check check (
    demo_url is null or (char_length(demo_url) <= 2048 and demo_url ~ '^https://')
  ),
  add constraint website_requests_domain_name_check check (
    domain_name is null or (
      char_length(domain_name) <= 253
      and domain_name ~ '^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$'
    )
  ),
  add constraint website_requests_hosting_status_check check (
    hosting_status in ('not_selected', 'pending', 'active', 'past_due', 'cancelled')
  ),
  add constraint website_requests_payment_status_check check (
    payment_status in ('not_ready', 'ready', 'pending', 'paid', 'failed', 'refunded')
  ),
  add constraint website_requests_live_url_check check (
    live_url is null or (char_length(live_url) <= 2048 and live_url ~ '^https://')
  );

update public.website_requests as request
set
  customer_email = auth_user.email,
  customer_name = nullif(btrim(auth_user.raw_user_meta_data ->> 'full_name'), '')
from auth.users as auth_user
where auth_user.id = request.user_id;

create unique index website_requests_checkout_session_uidx
  on public.website_requests (stripe_checkout_session_id)
  where stripe_checkout_session_id is not null;

create index website_requests_status_updated_at_idx
  on public.website_requests (status, updated_at desc);

create table public.website_request_updates (
  id bigint generated always as identity primary key,
  request_id bigint not null references public.website_requests (id) on delete cascade,
  created_by uuid not null references auth.users (id) on delete cascade default auth.uid(),
  title text not null,
  description text not null,
  status text not null default 'new',
  admin_response text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz,
  constraint website_request_updates_title_length check (char_length(title) between 2 and 120),
  constraint website_request_updates_description_length check (char_length(description) between 2 and 5000),
  constraint website_request_updates_status_check check (status in ('new', 'in_progress', 'completed')),
  constraint website_request_updates_admin_response_length check (
    admin_response is null or char_length(admin_response) <= 5000
  )
);

create index website_request_updates_request_created_idx
  on public.website_request_updates (request_id, created_at desc);

create index website_request_updates_status_updated_idx
  on public.website_request_updates (status, updated_at desc);

create table public.stripe_events (
  event_id text primary key,
  event_type text not null,
  request_id bigint references public.website_requests (id) on delete set null,
  processed_at timestamptz not null default now(),
  constraint stripe_events_event_id_length check (char_length(event_id) between 3 and 255),
  constraint stripe_events_event_type_length check (char_length(event_type) between 3 and 255)
);

alter table public.website_request_updates enable row level security;
alter table public.stripe_events enable row level security;

create policy "Customers can read their update tickets"
  on public.website_request_updates
  for select
  to authenticated
  using (
    exists (
      select 1
      from public.website_requests
      where website_requests.id = website_request_updates.request_id
        and website_requests.user_id = (select auth.uid())
    )
  );

create policy "Customers can create update tickets"
  on public.website_request_updates
  for insert
  to authenticated
  with check (
    created_by = (select auth.uid())
    and exists (
      select 1
      from public.website_requests
      where website_requests.id = website_request_updates.request_id
        and website_requests.user_id = (select auth.uid())
        and (
          website_requests.status in ('demo_ready', 'changes_requested')
          or (
            website_requests.status = 'live'
            and website_requests.hosting_selected
          )
        )
    )
  );

create policy "Admins can read all website requests"
  on public.website_requests
  for select
  to authenticated
  using ((select public.is_keeplyn_admin()));

create policy "Admins can read all request offerings"
  on public.website_request_offerings
  for select
  to authenticated
  using ((select public.is_keeplyn_admin()));

create policy "Admins can read all request assets"
  on public.website_request_assets
  for select
  to authenticated
  using ((select public.is_keeplyn_admin()));

create policy "Admins can read all update tickets"
  on public.website_request_updates
  for select
  to authenticated
  using ((select public.is_keeplyn_admin()));

create policy "Admins can read request photos"
  on storage.objects
  for select
  to authenticated
  using (
    bucket_id = 'website-request-photos'
    and (select public.is_keeplyn_admin())
  );

create policy "Admins can remove request photos"
  on storage.objects
  for delete
  to authenticated
  using (
    bucket_id = 'website-request-photos'
    and (select public.is_keeplyn_admin())
  );

create or replace function private.touch_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create trigger website_requests_touch_updated_at
before update on public.website_requests
for each row execute function private.touch_updated_at();

create trigger website_request_updates_touch_updated_at
before update on public.website_request_updates
for each row execute function private.touch_updated_at();

create or replace function private.mark_request_changes_requested()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  update public.website_requests
  set status = case when status = 'demo_ready' then 'changes_requested' else status end
  where id = new.request_id;
  return new;
end;
$$;

create trigger website_request_updates_mark_request
after insert on public.website_request_updates
for each row execute function private.mark_request_changes_requested();

create or replace function public.submit_website_request(
  p_plan_id text,
  p_offerings jsonb,
  p_photo_brief text default null,
  p_theme_description text default null,
  p_additional_notes text default null,
  p_assets jsonb default '[]'::jsonb
)
returns bigint
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_user_id uuid := auth.uid();
  v_request_id bigint;
  v_offering jsonb;
  v_asset jsonb;
  v_position smallint := 0;
  v_photo_brief text := nullif(btrim(p_photo_brief), '');
  v_theme_description text := nullif(btrim(p_theme_description), '');
  v_additional_notes text := nullif(btrim(p_additional_notes), '');
  v_customer_name text := nullif(btrim(auth.jwt() -> 'user_metadata' ->> 'full_name'), '');
  v_customer_email text := lower(nullif(btrim(auth.jwt() ->> 'email'), ''));
begin
  if v_user_id is null or v_customer_email is null then
    raise exception 'Authentication is required.' using errcode = '42501';
  end if;

  if p_plan_id not in ('starter', 'pro') then
    raise exception 'Choose a valid website plan.' using errcode = '22023';
  end if;

  if jsonb_typeof(p_offerings) is distinct from 'array'
    or jsonb_array_length(p_offerings) not between 1 and 20 then
    raise exception 'Add between 1 and 20 offerings.' using errcode = '22023';
  end if;

  if p_assets is null
    or jsonb_typeof(p_assets) is distinct from 'array'
    or jsonb_array_length(p_assets) > 8 then
    raise exception 'Upload no more than 8 photos.' using errcode = '22023';
  end if;

  if char_length(v_photo_brief) > 3000
    or char_length(v_theme_description) > 3000
    or char_length(v_additional_notes) > 5000 then
    raise exception 'One or more request notes are too long.' using errcode = '22023';
  end if;

  insert into public.website_requests (
    user_id,
    customer_name,
    customer_email,
    plan_id,
    photo_brief,
    theme_description,
    additional_notes
  )
  values (
    v_user_id,
    left(v_customer_name, 100),
    left(v_customer_email, 254),
    p_plan_id,
    v_photo_brief,
    v_theme_description,
    v_additional_notes
  )
  returning id into v_request_id;

  for v_offering in select value from jsonb_array_elements(p_offerings)
  loop
    if jsonb_typeof(v_offering) is distinct from 'object'
      or char_length(btrim(v_offering ->> 'title')) not between 2 and 100
      or char_length(btrim(v_offering ->> 'description')) not between 2 and 1000
      or coalesce(v_offering ->> 'price', '') !~ '^\d{1,10}(\.\d{1,2})?$'
      or (v_offering ->> 'price')::numeric > 9999999999.99 then
      raise exception 'Each offering needs a valid title, description, and price.' using errcode = '22023';
    end if;

    insert into public.website_request_offerings (
      request_id,
      title,
      description,
      price,
      position
    )
    values (
      v_request_id,
      btrim(v_offering ->> 'title'),
      btrim(v_offering ->> 'description'),
      (v_offering ->> 'price')::numeric,
      v_position
    );

    v_position := v_position + 1;
  end loop;

  for v_asset in select value from jsonb_array_elements(p_assets)
  loop
    if jsonb_typeof(v_asset) is distinct from 'object'
      or char_length(v_asset ->> 'original_filename') not between 1 and 255
      or (v_asset ->> 'mime_type') not in ('image/jpeg', 'image/png', 'image/webp', 'image/avif')
      or coalesce(v_asset ->> 'size_bytes', '') !~ '^\d+$'
      or (v_asset ->> 'size_bytes')::bigint not between 1 and 8388608
      or (v_asset ->> 'storage_path') not like v_user_id::text || '/%'
      or not exists (
        select 1
        from storage.objects
        where storage.objects.bucket_id = 'website-request-photos'
          and storage.objects.name = v_asset ->> 'storage_path'
          and storage.objects.owner_id = v_user_id::text
      ) then
      raise exception 'One or more uploaded photos are invalid.' using errcode = '22023';
    end if;

    insert into public.website_request_assets (
      request_id,
      storage_path,
      original_filename,
      mime_type,
      size_bytes
    )
    values (
      v_request_id,
      v_asset ->> 'storage_path',
      v_asset ->> 'original_filename',
      v_asset ->> 'mime_type',
      (v_asset ->> 'size_bytes')::bigint
    );
  end loop;

  return v_request_id;
end;
$$;

create or replace function public.update_website_request(
  p_request_id bigint,
  p_plan_id text,
  p_offerings jsonb,
  p_photo_brief text default null,
  p_theme_description text default null,
  p_additional_notes text default null
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_user_id uuid := auth.uid();
  v_offering jsonb;
  v_position smallint := 0;
  v_status text;
begin
  select status into v_status
  from public.website_requests
  where id = p_request_id and user_id = v_user_id
  for update;

  if v_status is null then
    raise exception 'Website request not found.' using errcode = 'P0002';
  end if;

  if v_status in ('approved', 'domain_pending', 'payment_pending', 'paid', 'launching', 'live', 'cancelled') then
    raise exception 'This request can no longer be edited directly.' using errcode = '22023';
  end if;

  if p_plan_id not in ('starter', 'pro')
    or jsonb_typeof(p_offerings) is distinct from 'array'
    or jsonb_array_length(p_offerings) not between 1 and 20 then
    raise exception 'Choose a valid plan and add between 1 and 20 offerings.' using errcode = '22023';
  end if;

  if char_length(nullif(btrim(p_photo_brief), '')) > 3000
    or char_length(nullif(btrim(p_theme_description), '')) > 3000
    or char_length(nullif(btrim(p_additional_notes), '')) > 5000 then
    raise exception 'One or more request notes are too long.' using errcode = '22023';
  end if;

  update public.website_requests
  set
    plan_id = p_plan_id,
    photo_brief = nullif(btrim(p_photo_brief), ''),
    theme_description = nullif(btrim(p_theme_description), ''),
    additional_notes = nullif(btrim(p_additional_notes), ''),
    status = case when status = 'demo_ready' then 'changes_requested' else status end
  where id = p_request_id;

  delete from public.website_request_offerings where request_id = p_request_id;

  for v_offering in select value from jsonb_array_elements(p_offerings)
  loop
    if jsonb_typeof(v_offering) is distinct from 'object'
      or char_length(btrim(v_offering ->> 'title')) not between 2 and 100
      or char_length(btrim(v_offering ->> 'description')) not between 2 and 1000
      or coalesce(v_offering ->> 'price', '') !~ '^\d{1,10}(\.\d{1,2})?$'
      or (v_offering ->> 'price')::numeric > 9999999999.99 then
      raise exception 'Each offering needs a valid title, description, and price.' using errcode = '22023';
    end if;

    insert into public.website_request_offerings (request_id, title, description, price, position)
    values (
      p_request_id,
      btrim(v_offering ->> 'title'),
      btrim(v_offering ->> 'description'),
      (v_offering ->> 'price')::numeric,
      v_position
    );
    v_position := v_position + 1;
  end loop;
end;
$$;

create or replace function public.add_request_assets(p_request_id bigint, p_assets jsonb)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_user_id uuid := auth.uid();
  v_asset jsonb;
  v_existing_count integer;
  v_status text;
begin
  select status into v_status
  from public.website_requests
  where id = p_request_id and user_id = v_user_id;

  if v_status is null then
    raise exception 'Website request not found.' using errcode = 'P0002';
  end if;

  if v_status in ('approved', 'domain_pending', 'payment_pending', 'paid', 'launching', 'live', 'cancelled') then
    raise exception 'Photos can no longer be edited for this request.' using errcode = '22023';
  end if;

  if p_assets is null or jsonb_typeof(p_assets) is distinct from 'array' then
    raise exception 'Provide a valid photo list.' using errcode = '22023';
  end if;

  select count(*) into v_existing_count
  from public.website_request_assets
  where request_id = p_request_id;

  if v_existing_count + jsonb_array_length(p_assets) > 8 then
    raise exception 'Upload no more than 8 photos.' using errcode = '22023';
  end if;

  for v_asset in select value from jsonb_array_elements(p_assets)
  loop
    if jsonb_typeof(v_asset) is distinct from 'object'
      or char_length(v_asset ->> 'original_filename') not between 1 and 255
      or (v_asset ->> 'mime_type') not in ('image/jpeg', 'image/png', 'image/webp', 'image/avif')
      or coalesce(v_asset ->> 'size_bytes', '') !~ '^\d+$'
      or (v_asset ->> 'size_bytes')::bigint not between 1 and 8388608
      or (v_asset ->> 'storage_path') not like v_user_id::text || '/%'
      or not exists (
        select 1 from storage.objects
        where bucket_id = 'website-request-photos'
          and name = v_asset ->> 'storage_path'
          and owner_id = v_user_id::text
      ) then
      raise exception 'One or more uploaded photos are invalid.' using errcode = '22023';
    end if;

    insert into public.website_request_assets (
      request_id, storage_path, original_filename, mime_type, size_bytes
    ) values (
      p_request_id,
      v_asset ->> 'storage_path',
      v_asset ->> 'original_filename',
      v_asset ->> 'mime_type',
      (v_asset ->> 'size_bytes')::bigint
    );
  end loop;

  if jsonb_array_length(p_assets) > 0 then
    update public.website_requests
    set status = case when status = 'demo_ready' then 'changes_requested' else status end
    where id = p_request_id;
  end if;
end;
$$;

create or replace function public.remove_request_asset(p_asset_id bigint)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_path text;
begin
  delete from public.website_request_assets as asset
  using public.website_requests as request
  where asset.id = p_asset_id
    and request.id = asset.request_id
    and request.user_id = auth.uid()
    and request.status not in ('approved', 'domain_pending', 'payment_pending', 'paid', 'launching', 'live', 'cancelled')
  returning asset.storage_path into v_path;

  if v_path is null then
    raise exception 'Photo not found or cannot be removed.' using errcode = 'P0002';
  end if;

  return v_path;
end;
$$;

create or replace function public.approve_website_request(p_request_id bigint)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if exists (
    select 1 from public.website_request_updates
    where request_id = p_request_id and status <> 'completed'
  ) then
    raise exception 'Complete open update tickets before approving the website.' using errcode = '22023';
  end if;

  update public.website_requests
  set
    status = 'domain_pending',
    approved_at = coalesce(approved_at, now()),
    payment_status = 'not_ready'
  where id = p_request_id
    and user_id = auth.uid()
    and status in ('demo_ready', 'changes_requested');

  if not found then
    raise exception 'This website is not ready for approval.' using errcode = '22023';
  end if;
end;
$$;

create or replace function public.set_request_domain(
  p_request_id bigint,
  p_domain_name text,
  p_hosting_selected boolean
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_domain text := lower(btrim(p_domain_name));
begin
  if char_length(v_domain) > 253
    or v_domain !~ '^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$' then
    raise exception 'Enter a valid domain name.' using errcode = '22023';
  end if;

  update public.website_requests
  set
    domain_name = v_domain,
    domain_submitted_at = now(),
    hosting_selected = p_hosting_selected,
    hosting_status = case when p_hosting_selected then 'pending' else 'not_selected' end,
    status = 'payment_pending',
    payment_status = 'ready'
  where id = p_request_id
    and user_id = auth.uid()
    and approved_at is not null
    and status in ('approved', 'domain_pending', 'payment_pending');

  if not found then
    raise exception 'Approve your website before adding a domain.' using errcode = '22023';
  end if;
end;
$$;

create or replace function public.begin_request_checkout(
  p_request_id bigint,
  p_checkout_session_id text,
  p_customer_id text default null
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  update public.website_requests
  set
    stripe_checkout_session_id = p_checkout_session_id,
    stripe_customer_id = coalesce(p_customer_id, stripe_customer_id),
    status = 'payment_pending',
    payment_status = 'pending'
  where id = p_request_id
    and user_id = auth.uid()
    and approved_at is not null
    and domain_name is not null
    and status = 'payment_pending'
    and payment_status in ('ready', 'pending', 'failed');

  if not found then
    raise exception 'This request is not ready for checkout.' using errcode = '22023';
  end if;
end;
$$;

create or replace function public.admin_set_demo(p_request_id bigint, p_demo_url text)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_url text := btrim(p_demo_url);
begin
  if not public.is_keeplyn_admin() then
    raise exception 'Administrator access is required.' using errcode = '42501';
  end if;

  if char_length(v_url) > 2048 or v_url !~ '^https://' then
    raise exception 'Enter a secure demo URL.' using errcode = '22023';
  end if;

  update public.website_requests
  set status = 'demo_ready', demo_url = v_url, demo_ready_at = now()
  where id = p_request_id and status not in ('paid', 'launching', 'live', 'cancelled');

  if not found then
    raise exception 'Website request not found.' using errcode = 'P0002';
  end if;
end;
$$;

create or replace function public.admin_set_request_status(
  p_request_id bigint,
  p_status text,
  p_live_url text default null
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if not public.is_keeplyn_admin() then
    raise exception 'Administrator access is required.' using errcode = '42501';
  end if;

  if p_status not in ('in_review', 'in_progress', 'launching', 'live', 'cancelled') then
    raise exception 'Choose a valid administrative status.' using errcode = '22023';
  end if;

  if p_status = 'live' and (p_live_url is null or btrim(p_live_url) !~ '^https://') then
    raise exception 'A secure live URL is required.' using errcode = '22023';
  end if;

  update public.website_requests
  set
    status = p_status,
    live_url = case when p_status = 'live' then btrim(p_live_url) else live_url end,
    live_at = case when p_status = 'live' then now() else live_at end
  where id = p_request_id;

  if not found then
    raise exception 'Website request not found.' using errcode = 'P0002';
  end if;
end;
$$;

create or replace function public.admin_set_update_ticket(
  p_ticket_id bigint,
  p_status text,
  p_admin_response text default null
)
returns bigint
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_request_id bigint;
begin
  if not public.is_keeplyn_admin() then
    raise exception 'Administrator access is required.' using errcode = '42501';
  end if;

  if p_status not in ('in_progress', 'completed') then
    raise exception 'Choose a valid update status.' using errcode = '22023';
  end if;

  update public.website_request_updates
  set
    status = p_status,
    admin_response = nullif(btrim(p_admin_response), ''),
    completed_at = case when p_status = 'completed' then now() else null end
  where id = p_ticket_id
  returning request_id into v_request_id;

  if v_request_id is null then
    raise exception 'Update ticket not found.' using errcode = 'P0002';
  end if;

  if p_status = 'completed' and not exists (
    select 1 from public.website_request_updates
    where request_id = v_request_id and status <> 'completed'
  ) then
    update public.website_requests
    set status = 'demo_ready', demo_ready_at = now()
    where id = v_request_id and status = 'changes_requested';
  end if;

  return v_request_id;
end;
$$;

create or replace function public.record_stripe_event(
  p_secret text,
  p_event_id text,
  p_event_type text,
  p_request_id bigint default null,
  p_checkout_session_id text default null,
  p_customer_id text default null,
  p_subscription_id text default null,
  p_payment_status text default null,
  p_subscription_status text default null
)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_expected_hash text;
  v_target_request_id bigint;
begin
  select secret_sha256 into v_expected_hash
  from private.webhook_secrets
  where provider = 'stripe';

  if v_expected_hash is null
    or encode(extensions.digest(convert_to(coalesce(p_secret, ''), 'UTF8'), 'sha256'), 'hex') <> v_expected_hash then
    raise exception 'Invalid webhook database credential.' using errcode = '42501';
  end if;

  select id into v_target_request_id
  from public.website_requests
  where (p_request_id is not null and id = p_request_id)
     or (p_checkout_session_id is not null and stripe_checkout_session_id = p_checkout_session_id)
     or (p_subscription_id is not null and stripe_subscription_id = p_subscription_id)
  order by case when p_request_id is not null and id = p_request_id then 0 else 1 end
  limit 1;

  insert into public.stripe_events (event_id, event_type, request_id)
  values (p_event_id, p_event_type, v_target_request_id)
  on conflict (event_id) do nothing;

  if not found then
    return false;
  end if;

  if v_target_request_id is null then
    return true;
  end if;

  if p_event_type in ('checkout.session.completed', 'checkout.session.async_payment_succeeded')
    and p_payment_status in ('paid', 'no_payment_required') then
    update public.website_requests
    set
      status = 'paid',
      payment_status = 'paid',
      paid_at = coalesce(paid_at, now()),
      stripe_checkout_session_id = coalesce(p_checkout_session_id, stripe_checkout_session_id),
      stripe_customer_id = coalesce(p_customer_id, stripe_customer_id),
      stripe_subscription_id = coalesce(p_subscription_id, stripe_subscription_id),
      hosting_status = case when hosting_selected then 'active' else hosting_status end
    where id = v_target_request_id;
  elsif p_event_type = 'checkout.session.async_payment_failed' then
    update public.website_requests
    set payment_status = 'failed'
    where id = v_target_request_id and payment_status <> 'paid';
  elsif p_event_type = 'invoice.paid' then
    update public.website_requests
    set hosting_status = case when hosting_selected then 'active' else hosting_status end
    where id = v_target_request_id;
  elsif p_event_type = 'invoice.payment_failed' then
    update public.website_requests
    set hosting_status = case when hosting_selected then 'past_due' else hosting_status end
    where id = v_target_request_id;
  elsif p_event_type = 'customer.subscription.deleted' then
    update public.website_requests
    set hosting_status = 'cancelled'
    where id = v_target_request_id and hosting_selected;
  elsif p_event_type = 'customer.subscription.updated' and p_subscription_status is not null then
    update public.website_requests
    set hosting_status = case
      when p_subscription_status in ('active', 'trialing') then 'active'
      when p_subscription_status in ('past_due', 'unpaid') then 'past_due'
      when p_subscription_status in ('canceled', 'incomplete_expired') then 'cancelled'
      else hosting_status
    end
    where id = v_target_request_id and hosting_selected;
  end if;

  return true;
end;
$$;

revoke all on public.website_request_updates from anon;
revoke all on public.stripe_events from public, anon, authenticated;

grant select, insert on public.website_request_updates to authenticated;
grant usage, select on sequence public.website_request_updates_id_seq to authenticated;

revoke execute on function public.update_website_request(bigint, text, jsonb, text, text, text) from public, anon;
revoke execute on function public.add_request_assets(bigint, jsonb) from public, anon;
revoke execute on function public.remove_request_asset(bigint) from public, anon;
revoke execute on function public.approve_website_request(bigint) from public, anon;
revoke execute on function public.set_request_domain(bigint, text, boolean) from public, anon;
revoke execute on function public.begin_request_checkout(bigint, text, text) from public, anon;
revoke execute on function public.admin_set_demo(bigint, text) from public, anon;
revoke execute on function public.admin_set_request_status(bigint, text, text) from public, anon;
revoke execute on function public.admin_set_update_ticket(bigint, text, text) from public, anon;
revoke execute on function public.record_stripe_event(text, text, text, bigint, text, text, text, text, text) from public, authenticated;

grant execute on function public.update_website_request(bigint, text, jsonb, text, text, text) to authenticated;
grant execute on function public.add_request_assets(bigint, jsonb) to authenticated;
grant execute on function public.remove_request_asset(bigint) to authenticated;
grant execute on function public.approve_website_request(bigint) to authenticated;
grant execute on function public.set_request_domain(bigint, text, boolean) to authenticated;
grant execute on function public.begin_request_checkout(bigint, text, text) to authenticated;
grant execute on function public.admin_set_demo(bigint, text) to authenticated;
grant execute on function public.admin_set_request_status(bigint, text, text) to authenticated;
grant execute on function public.admin_set_update_ticket(bigint, text, text) to authenticated;
grant execute on function public.record_stripe_event(text, text, text, bigint, text, text, text, text, text) to anon;

commit;
