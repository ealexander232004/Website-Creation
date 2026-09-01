-- Match new FMCSA carriers conservatively. A match must be corroborated by
-- email plus phone, email plus exact normalized name, or phone plus exact
-- normalized name and ZIP5. Ambiguous top-scoring matches are not merged.
create temporary table fmcsa_entity_matches on commit drop as
with normalized_fmcsa as (
    select
        carrier.dot_number,
        email.normalized_email,
        case
            when length(regexp_replace(coalesce(carrier.telephone, ''), '[^0-9]', '', 'g')) >= 10
            then right(regexp_replace(carrier.telephone, '[^0-9]', '', 'g'), 10)
        end as normalized_phone,
        regexp_replace(lower(coalesce(carrier.legal_name, '')), '[^a-z0-9]', '', 'g') as legal_name_key,
        regexp_replace(lower(coalesce(carrier.dba_name, '')), '[^a-z0-9]', '', 'g') as dba_name_key,
        left(regexp_replace(coalesce(carrier.phy_zip, ''), '[^0-9]', '', 'g'), 5) as postcode_key
    from raw_fmcsa.carriers carrier
    join raw_fmcsa.emails email using (dot_number)
    where carrier.is_current
      and not exists (
          select 1
          from warehouse.source_places source_place
          where source_place.source = 'fmcsa'
            and source_place.source_place_id = carrier.dot_number::text
      )
),
email_candidates as (
    select
        fmcsa.dot_number,
        entity.entity_id,
        'email'::text as evidence,
        (
            regexp_replace(lower(coalesce(entity.canonical_name, '')), '[^a-z0-9]', '', 'g')
            in (fmcsa.legal_name_key, fmcsa.dba_name_key)
            and regexp_replace(lower(coalesce(entity.canonical_name, '')), '[^a-z0-9]', '', 'g') <> ''
        ) as name_match,
        (
            fmcsa.postcode_key <> ''
            and left(regexp_replace(coalesce(entity.postcode, ''), '[^0-9]', '', 'g'), 5)
                = fmcsa.postcode_key
        ) as postcode_match
    from normalized_fmcsa fmcsa
    join warehouse.entity_emails entity_email
      on entity_email.normalized_email = fmcsa.normalized_email
     and entity_email.is_usable
    join warehouse.entities entity using (entity_id)
    where entity.primary_source <> 'fmcsa'
),
phone_candidates as (
    select
        fmcsa.dot_number,
        entity.entity_id,
        'phone'::text as evidence,
        (
            regexp_replace(lower(coalesce(entity.canonical_name, '')), '[^a-z0-9]', '', 'g')
            in (fmcsa.legal_name_key, fmcsa.dba_name_key)
            and regexp_replace(lower(coalesce(entity.canonical_name, '')), '[^a-z0-9]', '', 'g') <> ''
        ) as name_match,
        (
            fmcsa.postcode_key <> ''
            and left(regexp_replace(coalesce(entity.postcode, ''), '[^0-9]', '', 'g'), 5)
                = fmcsa.postcode_key
        ) as postcode_match
    from normalized_fmcsa fmcsa
    join warehouse.entity_phones entity_phone
      on entity_phone.normalized_phone = fmcsa.normalized_phone
    join warehouse.entities entity using (entity_id)
    where fmcsa.normalized_phone is not null
      and entity.primary_source <> 'fmcsa'
),
evidence_rollup as (
    select
        candidate.dot_number,
        candidate.entity_id,
        bool_or(candidate.evidence = 'email') as has_email,
        bool_or(candidate.evidence = 'phone') as has_phone,
        bool_or(candidate.name_match) as has_name,
        bool_or(candidate.postcode_match) as has_postcode
    from (
        select * from email_candidates
        union all
        select * from phone_candidates
    ) candidate
    group by candidate.dot_number, candidate.entity_id
),
scored as (
    select
        evidence.*,
        case
            when has_email and has_phone then 100
            when has_email and has_name then 80
            when has_phone and has_name and has_postcode then 70
        end as match_score
    from evidence_rollup evidence
),
qualified as (
    select
        scored.*,
        max(match_score) over (partition by dot_number) as best_score
    from scored
    where match_score is not null
),
top_candidates as (
    select *
    from qualified
    where match_score = best_score
)
select
    dot_number,
    min(entity_id) as entity_id,
    max(match_score) as match_score
from top_candidates
group by dot_number
having count(*) = 1;

-- Create a canonical entity for each carrier that did not match an existing
-- Overture/Foursquare entity. The no-website qualification stays false because
-- FMCSA does not provide a website-presence field.
insert into warehouse.entities (
    primary_source,
    primary_source_place_id,
    canonical_name,
    street_address,
    city,
    region,
    postcode,
    country,
    operating_status,
    earliest_source_date,
    latest_source_refresh,
    source_count,
    is_qualified_no_website_email_lead
)
select
    'fmcsa',
    carrier.dot_number::text,
    coalesce(nullif(carrier.dba_name, ''), carrier.legal_name),
    carrier.phy_street,
    carrier.phy_city,
    carrier.phy_state,
    carrier.phy_zip,
    carrier.phy_country,
    'active',
    carrier.add_date,
    carrier.snapshot_date,
    1,
    false
from raw_fmcsa.carriers carrier
left join fmcsa_entity_matches match using (dot_number)
where carrier.is_current
  and match.dot_number is null
  and not exists (
      select 1
      from warehouse.source_places source_place
      where source_place.source = 'fmcsa'
        and source_place.source_place_id = carrier.dot_number::text
  )
on conflict (primary_source, primary_source_place_id) do update
set canonical_name = excluded.canonical_name,
    street_address = excluded.street_address,
    city = excluded.city,
    region = excluded.region,
    postcode = excluded.postcode,
    country = excluded.country,
    operating_status = excluded.operating_status,
    earliest_source_date = excluded.earliest_source_date,
    latest_source_refresh = excluded.latest_source_refresh;

insert into warehouse.source_places (
    source,
    source_place_id,
    entity_id,
    source_qualified,
    match_method,
    match_confidence
)
select
    'fmcsa',
    carrier.dot_number::text,
    coalesce(match.entity_id, fmcsa_entity.entity_id),
    false,
    case
        when match.entity_id is not null then
            case match.match_score
                when 100 then 'email+phone'
                when 80 then 'email+exact_name'
                when 70 then 'phone+exact_name+postcode'
            end
        else 'source record'
    end,
    case when match.entity_id is not null then 'high' else 'source_primary' end
from raw_fmcsa.carriers carrier
left join fmcsa_entity_matches match using (dot_number)
left join warehouse.entities fmcsa_entity
  on fmcsa_entity.primary_source = 'fmcsa'
 and fmcsa_entity.primary_source_place_id = carrier.dot_number::text
where carrier.is_current
on conflict (source, source_place_id) do update
set source_qualified = excluded.source_qualified,
    match_method = excluded.match_method,
    match_confidence = excluded.match_confidence;

-- Refresh FMCSA-primary entity fields and only fill missing values on entities
-- whose canonical identity came from another source.
update warehouse.entities entity
set canonical_name = coalesce(nullif(carrier.dba_name, ''), carrier.legal_name),
    street_address = carrier.phy_street,
    city = carrier.phy_city,
    region = carrier.phy_state,
    postcode = carrier.phy_zip,
    country = carrier.phy_country,
    operating_status = 'active',
    earliest_source_date = carrier.add_date,
    latest_source_refresh = carrier.snapshot_date
from warehouse.source_places source_place
join raw_fmcsa.carriers carrier
  on carrier.dot_number::text = source_place.source_place_id
where source_place.source = 'fmcsa'
  and carrier.is_current
  and entity.entity_id = source_place.entity_id
  and entity.primary_source = 'fmcsa';

update warehouse.entities entity
set canonical_name = coalesce(entity.canonical_name, nullif(carrier.dba_name, ''), carrier.legal_name),
    street_address = coalesce(entity.street_address, carrier.phy_street),
    city = coalesce(entity.city, carrier.phy_city),
    region = coalesce(entity.region, carrier.phy_state),
    postcode = coalesce(entity.postcode, carrier.phy_zip),
    country = coalesce(entity.country, carrier.phy_country),
    earliest_source_date = coalesce(entity.earliest_source_date, carrier.add_date),
    latest_source_refresh = greatest(entity.latest_source_refresh, carrier.snapshot_date)
from warehouse.source_places source_place
join raw_fmcsa.carriers carrier
  on carrier.dot_number::text = source_place.source_place_id
where source_place.source = 'fmcsa'
  and carrier.is_current
  and entity.entity_id = source_place.entity_id
  and entity.primary_source <> 'fmcsa';

insert into warehouse.entity_emails (
    entity_id,
    normalized_email,
    display_email,
    email_domain,
    is_usable,
    is_role_account,
    source_count,
    sources
)
select
    source_place.entity_id,
    email.normalized_email,
    min(email.email),
    min(email.email_domain),
    bool_or(email.is_syntax_valid),
    bool_or(email.is_role_account),
    1,
    array['fmcsa']::text[]
from warehouse.source_places source_place
join raw_fmcsa.emails email
  on email.dot_number::text = source_place.source_place_id
join raw_fmcsa.carriers carrier using (dot_number)
where source_place.source = 'fmcsa'
  and carrier.is_current
  and email.normalized_email <> ''
group by source_place.entity_id, email.normalized_email
on conflict (entity_id, normalized_email) do update
set is_usable = warehouse.entity_emails.is_usable or excluded.is_usable,
    is_role_account = warehouse.entity_emails.is_role_account or excluded.is_role_account,
    sources = case
        when 'fmcsa' = any(warehouse.entity_emails.sources)
            then warehouse.entity_emails.sources
        else array_append(warehouse.entity_emails.sources, 'fmcsa')
    end,
    source_count = case
        when 'fmcsa' = any(warehouse.entity_emails.sources)
            then warehouse.entity_emails.source_count
        else warehouse.entity_emails.source_count + 1
    end;

insert into warehouse.entity_phones (
    entity_id,
    normalized_phone,
    raw_values,
    sources
)
select
    source_place.entity_id,
    right(regexp_replace(carrier.telephone, '[^0-9]', '', 'g'), 10),
    array_agg(distinct carrier.telephone order by carrier.telephone),
    array['fmcsa']::text[]
from warehouse.source_places source_place
join raw_fmcsa.carriers carrier
  on carrier.dot_number::text = source_place.source_place_id
where source_place.source = 'fmcsa'
  and carrier.is_current
  and length(regexp_replace(coalesce(carrier.telephone, ''), '[^0-9]', '', 'g')) >= 10
group by
    source_place.entity_id,
    right(regexp_replace(carrier.telephone, '[^0-9]', '', 'g'), 10)
on conflict (entity_id, normalized_phone) do update
set raw_values = (
        select array_agg(distinct value order by value)
        from unnest(warehouse.entity_phones.raw_values || excluded.raw_values) value
    ),
    sources = case
        when 'fmcsa' = any(warehouse.entity_phones.sources)
            then warehouse.entity_phones.sources
        else array_append(warehouse.entity_phones.sources, 'fmcsa')
    end;

insert into warehouse.entity_categories (
    entity_id,
    source,
    category_id,
    category_label,
    hierarchy,
    is_primary
)
select distinct
    source_place.entity_id,
    'fmcsa',
    'operation:' || carrier.carrier_operation,
    case carrier.carrier_operation
        when 'A' then 'Interstate carrier'
        when 'B' then 'Intrastate hazmat carrier'
        when 'C' then 'Intrastate non-hazmat carrier'
    end,
    array['FMCSA', 'Motor carrier operation']::text[],
    true
from warehouse.source_places source_place
join raw_fmcsa.carriers carrier
  on carrier.dot_number::text = source_place.source_place_id
where source_place.source = 'fmcsa'
  and carrier.is_current
  and carrier.carrier_operation is not null
on conflict do nothing;

with source_rollup as (
    select
        source_place.entity_id,
        count(*)::smallint as source_count
    from warehouse.source_places source_place
    where exists (
        select 1
        from warehouse.source_places fmcsa_source
        where fmcsa_source.entity_id = source_place.entity_id
          and fmcsa_source.source = 'fmcsa'
    )
    group by source_place.entity_id
)
update warehouse.entities entity
set source_count = rollup.source_count
from source_rollup rollup
where entity.entity_id = rollup.entity_id;

analyze raw_fmcsa.carriers;
analyze raw_fmcsa.emails;
analyze warehouse.entities;
analyze warehouse.source_places;
analyze warehouse.entity_emails;
analyze warehouse.entity_phones;
analyze warehouse.entity_categories;
