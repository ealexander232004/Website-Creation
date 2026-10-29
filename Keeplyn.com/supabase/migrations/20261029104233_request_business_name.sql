-- The sign-up form collects the owner's name; the business name is asked for
-- separately so demos, emails and admin views use the right name.
-- p_business_name is optional at the database level so older clients keep working;
-- the form requires it.
begin;

alter table public.website_requests
  add column business_name text,
  add constraint website_requests_business_name_length
    check (business_name is null or char_length(business_name) between 2 and 120);

drop function public.submit_website_request(text, jsonb, text, text, text, jsonb);

create function public.submit_website_request(
  p_plan_id text,
  p_offerings jsonb,
  p_photo_brief text default null,
  p_theme_description text default null,
  p_additional_notes text default null,
  p_assets jsonb default '[]'::jsonb,
  p_business_name text default null
)
returns bigint
language plpgsql
security definer
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
  v_business_name text := nullif(btrim(p_business_name), '');
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

  if char_length(v_business_name) not between 2 and 120 then
    raise exception 'Enter your business name (2–120 characters).' using errcode = '22023';
  end if;

  insert into public.website_requests (
    user_id,
    customer_name,
    customer_email,
    business_name,
    plan_id,
    photo_brief,
    theme_description,
    additional_notes
  )
  values (
    v_user_id,
    left(v_customer_name, 100),
    left(v_customer_email, 254),
    v_business_name,
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
      or char_length(btrim(v_offering ->> 'description')) not between 2 and 1000 then
      raise exception 'Each offering needs a valid title and description.' using errcode = '22023';
    end if;

    insert into public.website_request_offerings (request_id, title, description, price, position)
    values (
      v_request_id,
      btrim(v_offering ->> 'title'),
      btrim(v_offering ->> 'description'),
      private.offering_price(v_offering),
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

    insert into public.website_request_assets (request_id, storage_path, original_filename, mime_type, size_bytes)
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

drop function public.update_website_request(bigint, text, jsonb, text, text, text);

create function public.update_website_request(
  p_request_id bigint,
  p_plan_id text,
  p_offerings jsonb,
  p_photo_brief text default null,
  p_theme_description text default null,
  p_additional_notes text default null,
  p_business_name text default null
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
  v_business_name text := nullif(btrim(p_business_name), '');
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

  if char_length(v_business_name) not between 2 and 120 then
    raise exception 'Enter your business name (2–120 characters).' using errcode = '22023';
  end if;

  update public.website_requests
  set
    plan_id = p_plan_id,
    business_name = coalesce(v_business_name, business_name),
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
      or char_length(btrim(v_offering ->> 'description')) not between 2 and 1000 then
      raise exception 'Each offering needs a valid title and description.' using errcode = '22023';
    end if;

    insert into public.website_request_offerings (request_id, title, description, price, position)
    values (
      p_request_id,
      btrim(v_offering ->> 'title'),
      btrim(v_offering ->> 'description'),
      private.offering_price(v_offering),
      v_position
    );
    v_position := v_position + 1;
  end loop;
end;
$$;

revoke all on function public.submit_website_request(text, jsonb, text, text, text, jsonb, text) from public, anon;
grant execute on function public.submit_website_request(text, jsonb, text, text, text, jsonb, text) to authenticated;
revoke all on function public.update_website_request(bigint, text, jsonb, text, text, text, text) from public, anon;
grant execute on function public.update_website_request(bigint, text, jsonb, text, text, text, text) to authenticated;

commit;
