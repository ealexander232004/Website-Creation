create table if not exists warehouse.entity_merge_log (
    merge_id bigint generated always as identity primary key,
    winner_entity_id bigint not null,
    merged_entity_id bigint not null unique,
    match_reasons text[] not null,
    merged_sources text[] not null,
    merged_at timestamptz not null default current_timestamp
);

create temporary table entity_source_sets on commit drop as
select
    entity_id,
    array_agg(distinct source order by source) as sources
from warehouse.source_places
group by entity_id;

create unique index entity_source_sets_entity_idx
    on entity_source_sets(entity_id);

create temporary table entity_identity_keys on commit drop as
select
    entity.entity_id,
    regexp_replace(lower(coalesce(entity.canonical_name, '')), '[^a-z0-9]', '', 'g') as name_key,
    left(regexp_replace(coalesce(entity.postcode, ''), '[^0-9]', '', 'g'), 5) as postcode_key
from warehouse.entities entity;

create unique index entity_identity_keys_entity_idx
    on entity_identity_keys(entity_id);
create index entity_identity_keys_name_postcode_idx
    on entity_identity_keys(name_key, postcode_key, entity_id);

create temporary table entity_duplicate_pairs on commit drop as
with phone_stats as (
    select normalized_phone
    from warehouse.entity_phones
    where length(normalized_phone) = 10
    group by normalized_phone
    having count(distinct entity_id) between 2 and 5
),
phone_pairs as (
    select
        least(left_phone.entity_id, right_phone.entity_id) as entity_a,
        greatest(left_phone.entity_id, right_phone.entity_id) as entity_b,
        'phone_exact'::text as reason
    from phone_stats stats
    join warehouse.entity_phones left_phone using (normalized_phone)
    join warehouse.entity_phones right_phone
      on right_phone.normalized_phone = stats.normalized_phone
     and right_phone.entity_id > left_phone.entity_id
    join entity_source_sets left_sources
      on left_sources.entity_id = left_phone.entity_id
    join entity_source_sets right_sources
      on right_sources.entity_id = right_phone.entity_id
    where not (left_sources.sources && right_sources.sources)
),
email_name_stats as (
    select email.normalized_email, identity.name_key
    from warehouse.entity_emails email
    join entity_identity_keys identity using (entity_id)
    where email.is_usable
      and length(identity.name_key) >= 5
    group by email.normalized_email, identity.name_key
    having count(distinct email.entity_id) between 2 and 5
),
email_name_pairs as (
    select
        least(left_email.entity_id, right_email.entity_id) as entity_a,
        greatest(left_email.entity_id, right_email.entity_id) as entity_b,
        'email+name_exact'::text as reason
    from email_name_stats stats
    join warehouse.entity_emails left_email
      on left_email.normalized_email = stats.normalized_email
     and left_email.is_usable
    join entity_identity_keys left_identity
      on left_identity.entity_id = left_email.entity_id
     and left_identity.name_key = stats.name_key
    join warehouse.entity_emails right_email
      on right_email.normalized_email = stats.normalized_email
     and right_email.is_usable
     and right_email.entity_id > left_email.entity_id
    join entity_identity_keys right_identity
      on right_identity.entity_id = right_email.entity_id
     and right_identity.name_key = stats.name_key
    join entity_source_sets left_sources
      on left_sources.entity_id = left_email.entity_id
    join entity_source_sets right_sources
      on right_sources.entity_id = right_email.entity_id
    where not (left_sources.sources && right_sources.sources)
),
name_postcode_stats as (
    select name_key, postcode_key
    from entity_identity_keys
    where length(name_key) >= 5
      and length(postcode_key) = 5
    group by name_key, postcode_key
    having count(*) between 2 and 10
),
name_postcode_pairs as (
    select
        least(left_identity.entity_id, right_identity.entity_id) as entity_a,
        greatest(left_identity.entity_id, right_identity.entity_id) as entity_b,
        'name+postcode_exact'::text as reason
    from name_postcode_stats stats
    join entity_identity_keys left_identity
      on left_identity.name_key = stats.name_key
     and left_identity.postcode_key = stats.postcode_key
    join entity_identity_keys right_identity
      on right_identity.name_key = stats.name_key
     and right_identity.postcode_key = stats.postcode_key
     and right_identity.entity_id > left_identity.entity_id
    join entity_source_sets left_sources
      on left_sources.entity_id = left_identity.entity_id
    join entity_source_sets right_sources
      on right_sources.entity_id = right_identity.entity_id
    where not (left_sources.sources && right_sources.sources)
),
all_pairs as (
    select * from phone_pairs
    union all
    select * from email_name_pairs
    union all
    select * from name_postcode_pairs
)
select
    entity_a,
    entity_b,
    array_agg(distinct reason order by reason) as reasons
from all_pairs
group by entity_a, entity_b;

create unique index entity_duplicate_pairs_idx
    on entity_duplicate_pairs(entity_a, entity_b);

-- Resolve transitive duplicate graphs to the lowest stable entity_id.
create temporary table entity_merge_map on commit drop as
with recursive edges as (
    select entity_a as from_entity, entity_b as to_entity
    from entity_duplicate_pairs
    union all
    select entity_b, entity_a
    from entity_duplicate_pairs
),
nodes as (
    select from_entity as entity_id from edges
    union
    select to_entity from edges
),
reach(entity_id, reachable_entity_id) as (
    select entity_id, entity_id
    from nodes
    union
    select reach.entity_id, edges.to_entity
    from reach
    join edges on edges.from_entity = reach.reachable_entity_id
),
components as (
    select
        entity_id,
        min(reachable_entity_id) as winner_entity_id
    from reach
    group by entity_id
)
select
    entity_id as merged_entity_id,
    winner_entity_id
from components
where entity_id <> winner_entity_id;

create unique index entity_merge_map_merged_idx
    on entity_merge_map(merged_entity_id);
create index entity_merge_map_winner_idx
    on entity_merge_map(winner_entity_id);

insert into warehouse.entity_merge_log (
    winner_entity_id,
    merged_entity_id,
    match_reasons,
    merged_sources
)
select
    merge_map.winner_entity_id,
    merge_map.merged_entity_id,
    coalesce(
        array_agg(distinct reason order by reason)
            filter (where reason is not null),
        array['transitive_component']::text[]
    ),
    source_set.sources
from entity_merge_map merge_map
join entity_source_sets source_set
  on source_set.entity_id = merge_map.merged_entity_id
left join entity_duplicate_pairs pair
  on merge_map.merged_entity_id in (pair.entity_a, pair.entity_b)
left join lateral unnest(pair.reasons) reason on true
group by
    merge_map.winner_entity_id,
    merge_map.merged_entity_id,
    source_set.sources
on conflict (merged_entity_id) do nothing;

-- Preserve the best available canonical attributes on the surviving entity.
with merged_attributes as (
    select
        merge_map.winner_entity_id,
        min(entity.canonical_name) filter (where entity.canonical_name is not null) as canonical_name,
        min(entity.street_address) filter (where entity.street_address is not null) as street_address,
        min(entity.city) filter (where entity.city is not null) as city,
        min(entity.region) filter (where entity.region is not null) as region,
        min(entity.postcode) filter (where entity.postcode is not null) as postcode,
        min(entity.country) filter (where entity.country is not null) as country,
        min(entity.latitude) filter (where entity.latitude is not null) as latitude,
        min(entity.longitude) filter (where entity.longitude is not null) as longitude,
        min(entity.brand_name) filter (where entity.brand_name is not null) as brand_name,
        bool_or(entity.is_known_brand) as is_known_brand,
        max(entity.overture_confidence) as overture_confidence,
        min(entity.operating_status) filter (where entity.operating_status is not null) as operating_status,
        min(entity.earliest_source_date) as earliest_source_date,
        max(entity.latest_source_refresh) as latest_source_refresh,
        bool_or(entity.is_qualified_no_website_email_lead) as is_qualified
    from entity_merge_map merge_map
    join warehouse.entities entity
      on entity.entity_id = merge_map.merged_entity_id
    group by merge_map.winner_entity_id
)
update warehouse.entities winner
set canonical_name = coalesce(winner.canonical_name, attributes.canonical_name),
    street_address = coalesce(winner.street_address, attributes.street_address),
    city = coalesce(winner.city, attributes.city),
    region = coalesce(winner.region, attributes.region),
    postcode = coalesce(winner.postcode, attributes.postcode),
    country = coalesce(winner.country, attributes.country),
    latitude = coalesce(winner.latitude, attributes.latitude),
    longitude = coalesce(winner.longitude, attributes.longitude),
    brand_name = coalesce(winner.brand_name, attributes.brand_name),
    is_known_brand = winner.is_known_brand or attributes.is_known_brand,
    overture_confidence = greatest(winner.overture_confidence, attributes.overture_confidence),
    operating_status = coalesce(winner.operating_status, attributes.operating_status),
    earliest_source_date = least(winner.earliest_source_date, attributes.earliest_source_date),
    latest_source_refresh = greatest(winner.latest_source_refresh, attributes.latest_source_refresh),
    is_qualified_no_website_email_lead =
        winner.is_qualified_no_website_email_lead or attributes.is_qualified
from merged_attributes attributes
where winner.entity_id = attributes.winner_entity_id;

with email_evidence as (
    select
        merge_map.winner_entity_id,
        email.normalized_email,
        email.display_email,
        email.email_domain,
        email.is_usable,
        email.is_role_account,
        source
    from entity_merge_map merge_map
    join warehouse.entity_emails email
      on email.entity_id = merge_map.merged_entity_id
    cross join lateral unnest(email.sources) source
),
email_rollup as (
    select
        winner_entity_id,
        normalized_email,
        min(display_email) as display_email,
        min(email_domain) as email_domain,
        bool_or(is_usable) as is_usable,
        bool_or(is_role_account) as is_role_account,
        count(distinct source)::smallint as source_count,
        array_agg(distinct source order by source) as sources
    from email_evidence
    group by winner_entity_id, normalized_email
)
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
    winner_entity_id,
    normalized_email,
    display_email,
    email_domain,
    is_usable,
    is_role_account,
    source_count,
    sources
from email_rollup
on conflict (entity_id, normalized_email) do update
set is_usable = warehouse.entity_emails.is_usable or excluded.is_usable,
    is_role_account = warehouse.entity_emails.is_role_account or excluded.is_role_account,
    sources = (
        select array_agg(distinct source order by source)
        from unnest(warehouse.entity_emails.sources || excluded.sources) source
    ),
    source_count = (
        select count(distinct source)::smallint
        from unnest(warehouse.entity_emails.sources || excluded.sources) source
    );

with phone_raw_values as (
    select
        merge_map.winner_entity_id,
        phone.normalized_phone,
        raw_value
    from entity_merge_map merge_map
    join warehouse.entity_phones phone
      on phone.entity_id = merge_map.merged_entity_id
    cross join lateral unnest(phone.raw_values) raw_value
),
phone_sources as (
    select
        merge_map.winner_entity_id,
        phone.normalized_phone,
        source
    from entity_merge_map merge_map
    join warehouse.entity_phones phone
      on phone.entity_id = merge_map.merged_entity_id
    cross join lateral unnest(phone.sources) source
),
raw_rollup as (
    select
        winner_entity_id,
        normalized_phone,
        array_agg(distinct raw_value order by raw_value) as raw_values
    from phone_raw_values
    group by winner_entity_id, normalized_phone
),
source_rollup as (
    select
        winner_entity_id,
        normalized_phone,
        array_agg(distinct source order by source) as sources
    from phone_sources
    group by winner_entity_id, normalized_phone
)
insert into warehouse.entity_phones (
    entity_id,
    normalized_phone,
    raw_values,
    sources
)
select
    raw_rollup.winner_entity_id,
    raw_rollup.normalized_phone,
    raw_rollup.raw_values,
    source_rollup.sources
from raw_rollup
join source_rollup using (winner_entity_id, normalized_phone)
on conflict (entity_id, normalized_phone) do update
set raw_values = (
        select array_agg(distinct value order by value)
        from unnest(warehouse.entity_phones.raw_values || excluded.raw_values) value
    ),
    sources = (
        select array_agg(distinct source order by source)
        from unnest(warehouse.entity_phones.sources || excluded.sources) source
    );

insert into warehouse.entity_socials (
    entity_id, platform, handle_or_url, source
)
select distinct
    merge_map.winner_entity_id,
    social.platform,
    social.handle_or_url,
    social.source
from entity_merge_map merge_map
join warehouse.entity_socials social
  on social.entity_id = merge_map.merged_entity_id
on conflict do nothing;

insert into warehouse.entity_categories (
    entity_id, source, category_id, category_label, hierarchy, is_primary
)
select distinct
    merge_map.winner_entity_id,
    category.source,
    category.category_id,
    category.category_label,
    category.hierarchy,
    category.is_primary
from entity_merge_map merge_map
join warehouse.entity_categories category
  on category.entity_id = merge_map.merged_entity_id
on conflict do nothing;

delete from warehouse.google_maps_enrichment loser
using entity_merge_map merge_map
where loser.entity_id = merge_map.merged_entity_id
  and exists (
      select 1
      from warehouse.google_maps_enrichment winner
      where winner.entity_id = merge_map.winner_entity_id
  );

update warehouse.google_maps_enrichment enrichment
set entity_id = merge_map.winner_entity_id
from entity_merge_map merge_map
where enrichment.entity_id = merge_map.merged_entity_id;

delete from facebook_enrichment.profile_activity loser
using entity_merge_map merge_map
where loser.entity_id = merge_map.merged_entity_id
  and exists (
      select 1
      from facebook_enrichment.profile_activity winner
      where winner.entity_id = merge_map.winner_entity_id
        and winner.source = loser.source
        and winner.normalized_url = loser.normalized_url
  );

update facebook_enrichment.profile_activity activity
set entity_id = merge_map.winner_entity_id
from entity_merge_map merge_map
where activity.entity_id = merge_map.merged_entity_id;

update warehouse.source_places source_place
set entity_id = merge_map.winner_entity_id
from entity_merge_map merge_map
where source_place.entity_id = merge_map.merged_entity_id;

delete from warehouse.entity_emails email
using entity_merge_map merge_map
where email.entity_id = merge_map.merged_entity_id;

delete from warehouse.entity_phones phone
using entity_merge_map merge_map
where phone.entity_id = merge_map.merged_entity_id;

delete from warehouse.entity_socials social
using entity_merge_map merge_map
where social.entity_id = merge_map.merged_entity_id;

delete from warehouse.entity_categories category
using entity_merge_map merge_map
where category.entity_id = merge_map.merged_entity_id;

delete from warehouse.entities entity
using entity_merge_map merge_map
where entity.entity_id = merge_map.merged_entity_id;

with source_rollup as (
    select
        source_place.entity_id,
        count(*)::smallint as source_count
    from warehouse.source_places source_place
    where source_place.entity_id in (
        select winner_entity_id from entity_merge_map
    )
    group by source_place.entity_id
)
update warehouse.entities entity
set source_count = rollup.source_count
from source_rollup rollup
where entity.entity_id = rollup.entity_id;

analyze warehouse.entities;
analyze warehouse.source_places;
analyze warehouse.entity_emails;
analyze warehouse.entity_phones;
analyze warehouse.entity_socials;
analyze warehouse.entity_categories;
