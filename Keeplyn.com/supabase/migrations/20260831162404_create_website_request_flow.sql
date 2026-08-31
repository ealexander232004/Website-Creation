begin;

create table public.website_requests (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  plan_id text not null constraint website_requests_plan_id_check check (plan_id in ('starter', 'pro')),
  photo_brief text constraint website_requests_photo_brief_length check (char_length(photo_brief) <= 3000),
  theme_description text constraint website_requests_theme_description_length check (char_length(theme_description) <= 3000),
  additional_notes text constraint website_requests_additional_notes_length check (char_length(additional_notes) <= 5000),
  status text not null default 'submitted' constraint website_requests_status_check check (status in ('submitted', 'in_review', 'in_progress', 'completed')),
  created_at timestamptz not null default now()
);

create table public.website_request_offerings (
  id bigint generated always as identity primary key,
  request_id bigint not null references public.website_requests (id) on delete cascade,
  title text not null constraint website_request_offerings_title_length check (char_length(title) between 2 and 100),
  description text not null constraint website_request_offerings_description_length check (char_length(description) between 2 and 1000),
  price numeric(12, 2) not null constraint website_request_offerings_price_check check (price >= 0 and price <= 9999999999.99),
  position smallint not null constraint website_request_offerings_position_check check (position between 0 and 19)
);

create table public.website_request_assets (
  id bigint generated always as identity primary key,
  request_id bigint not null references public.website_requests (id) on delete cascade,
  storage_path text not null,
  original_filename text not null constraint website_request_assets_filename_length check (char_length(original_filename) between 1 and 255),
  mime_type text not null constraint website_request_assets_mime_type_check check (mime_type in ('image/jpeg', 'image/png', 'image/webp', 'image/avif')),
  size_bytes bigint not null constraint website_request_assets_size_check check (size_bytes between 1 and 8388608),
  created_at timestamptz not null default now(),
  unique (storage_path)
);

create index website_requests_user_id_created_at_idx
  on public.website_requests (user_id, created_at desc);

create index website_request_offerings_request_id_idx
  on public.website_request_offerings (request_id);

create index website_request_assets_request_id_idx
  on public.website_request_assets (request_id);

alter table public.website_requests enable row level security;
alter table public.website_request_offerings enable row level security;
alter table public.website_request_assets enable row level security;

create policy "Customers can read their website requests"
  on public.website_requests
  for select
  to authenticated
  using ((select auth.uid()) = user_id);

create policy "Customers can create their website requests"
  on public.website_requests
  for insert
  to authenticated
  with check ((select auth.uid()) = user_id);

create policy "Customers can read their request offerings"
  on public.website_request_offerings
  for select
  to authenticated
  using (
    exists (
      select 1
      from public.website_requests
      where website_requests.id = website_request_offerings.request_id
        and website_requests.user_id = (select auth.uid())
    )
  );

create policy "Customers can create their request offerings"
  on public.website_request_offerings
  for insert
  to authenticated
  with check (
    exists (
      select 1
      from public.website_requests
      where website_requests.id = website_request_offerings.request_id
        and website_requests.user_id = (select auth.uid())
    )
  );

create policy "Customers can read their request assets"
  on public.website_request_assets
  for select
  to authenticated
  using (
    exists (
      select 1
      from public.website_requests
      where website_requests.id = website_request_assets.request_id
        and website_requests.user_id = (select auth.uid())
    )
  );

create policy "Customers can create their request assets"
  on public.website_request_assets
  for insert
  to authenticated
  with check (
    exists (
      select 1
      from public.website_requests
      where website_requests.id = website_request_assets.request_id
        and website_requests.user_id = (select auth.uid())
    )
  );

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'website-request-photos',
  'website-request-photos',
  false,
  8388608,
  array['image/jpeg', 'image/png', 'image/webp', 'image/avif']
)
on conflict (id) do update
set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

create policy "Customers can upload their website request photos"
  on storage.objects
  for insert
  to authenticated
  with check (
    bucket_id = 'website-request-photos'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );

create policy "Customers can read their website request photos"
  on storage.objects
  for select
  to authenticated
  using (
    bucket_id = 'website-request-photos'
    and owner_id = (select auth.uid())::text
  );

create policy "Customers can remove their website request photos"
  on storage.objects
  for delete
  to authenticated
  using (
    bucket_id = 'website-request-photos'
    and owner_id = (select auth.uid())::text
  );

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
begin
  if v_user_id is null then
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
    plan_id,
    photo_brief,
    theme_description,
    additional_notes
  )
  values (
    v_user_id,
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

revoke all on public.website_requests from anon;
revoke all on public.website_request_offerings from anon;
revoke all on public.website_request_assets from anon;

grant select, insert on public.website_requests to authenticated;
grant select, insert on public.website_request_offerings to authenticated;
grant select, insert on public.website_request_assets to authenticated;
grant usage, select on sequence public.website_requests_id_seq to authenticated;
grant usage, select on sequence public.website_request_offerings_id_seq to authenticated;
grant usage, select on sequence public.website_request_assets_id_seq to authenticated;

revoke execute on function public.submit_website_request(text, jsonb, text, text, text, jsonb) from public, anon;
grant execute on function public.submit_website_request(text, jsonb, text, text, text, jsonb) to authenticated;

commit;
