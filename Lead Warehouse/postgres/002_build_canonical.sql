truncate table
    warehouse.entity_categories,
    warehouse.entity_socials,
    warehouse.entity_phones,
    warehouse.entity_emails,
    warehouse.source_places,
    warehouse.entities
restart identity cascade;

-- Overture candidates seed canonical entities. This preserves even candidates
-- that fail the probable-SMB view; qualification is tracked independently.
insert into warehouse.entities (
    primary_source, primary_source_place_id, canonical_name,
    street_address, city, region, postcode, country, latitude, longitude,
    brand_name, is_known_brand, overture_confidence, operating_status,
    is_qualified_no_website_email_lead
)
select
    'overture', p.place_id, p.business_name,
    p.street_address, p.city, p.region, p.postcode, p.country,
    p.latitude, p.longitude, p.brand_name, p.is_known_brand,
    p.confidence, p.operating_status,
    p.is_probable_small_business
        and coalesce(p.operating_status, 'open') <> 'permanently_closed'
        and exists (
            select 1 from raw_overture.emails e
            where e.place_id = p.place_id and e.is_syntax_valid
        )
from raw_overture.places p;

insert into warehouse.source_places (
    source, source_place_id, entity_id, source_qualified,
    match_method, match_confidence
)
select
    'overture', p.place_id, e.entity_id,
    p.is_probable_small_business
        and coalesce(p.operating_status, 'open') <> 'permanently_closed'
        and exists (
            select 1 from raw_overture.emails m
            where m.place_id = p.place_id and m.is_syntax_valid
        ),
    'source record', 'source_primary'
from raw_overture.places p
join warehouse.entities e
  on e.primary_source = 'overture'
 and e.primary_source_place_id = p.place_id;

create temporary table best_foursquare_match on commit drop as
select * from (
    select
        m.*,
        row_number() over (
            partition by m.foursquare_place_id
            order by
                m.phone_match desc,
                m.name_match desc,
                m.postcode_match desc,
                m.email_match desc,
                m.overture_place_id
        ) as match_rank
    from raw_foursquare.overture_matches m
    where m.is_high_confidence_duplicate
) ranked
where match_rank = 1;

-- Every unmatched Foursquare candidate gets its own entity. Matched candidates
-- attach to the existing Overture entity instead.
insert into warehouse.entities (
    primary_source, primary_source_place_id, canonical_name,
    street_address, city, region, postcode, country, latitude, longitude,
    operating_status, earliest_source_date, latest_source_refresh,
    is_qualified_no_website_email_lead
)
select
    'foursquare', p.place_id, p.name,
    p.address, p.locality, p.region, p.postcode, p.country,
    p.latitude, p.longitude,
    case when p.date_closed is null then 'open_or_unknown' else 'closed' end,
    p.date_created, p.date_refreshed,
    p.date_closed is null
        and not p.has_noncommercial_category
        and not p.has_disqualifying_flag
        and exists (
            select 1 from raw_foursquare.emails e
            where e.place_id = p.place_id and e.is_usable
        )
from raw_foursquare.places p
left join best_foursquare_match m on m.foursquare_place_id = p.place_id
where m.foursquare_place_id is null;

insert into warehouse.source_places (
    source, source_place_id, entity_id, source_qualified,
    match_method, match_confidence
)
select
    'foursquare', p.place_id,
    coalesce(o_entity.entity_id, f_entity.entity_id),
    p.date_closed is null
        and not p.has_noncommercial_category
        and not p.has_disqualifying_flag
        and exists (
            select 1 from raw_foursquare.emails e
            where e.place_id = p.place_id and e.is_usable
        ),
    case
        when m.foursquare_place_id is null then 'source record'
        else concat_ws('+',
            case when m.phone_match then 'phone' end,
            case when m.name_match and m.postcode_match then 'name_postcode' end,
            case when m.email_match and m.name_match then 'email_name' end
        )
    end,
    case when m.foursquare_place_id is null then 'source_primary' else 'high' end
from raw_foursquare.places p
left join best_foursquare_match m on m.foursquare_place_id = p.place_id
left join warehouse.entities o_entity
  on o_entity.primary_source = 'overture'
 and o_entity.primary_source_place_id = m.overture_place_id
left join warehouse.entities f_entity
  on f_entity.primary_source = 'foursquare'
 and f_entity.primary_source_place_id = p.place_id;

-- Fill missing canonical fields from the most complete Foursquare member of a
-- matched entity, without overwriting richer Overture values.
with ranked_foursquare as (
    select
        sp.entity_id, p.*,
        row_number() over (
            partition by sp.entity_id
            order by
                ((p.name is not null)::integer
                 + (p.address is not null)::integer
                 + (p.telephone is not null)::integer
                 + (p.postcode is not null)::integer) desc,
                p.date_refreshed desc nulls last,
                p.place_id
        ) as member_rank
    from warehouse.source_places sp
    join raw_foursquare.places p
      on sp.source = 'foursquare' and sp.source_place_id = p.place_id
)
update warehouse.entities e
set canonical_name = coalesce(e.canonical_name, f.name),
    street_address = coalesce(e.street_address, f.address),
    city = coalesce(e.city, f.locality),
    region = coalesce(e.region, f.region),
    postcode = coalesce(e.postcode, f.postcode),
    country = coalesce(e.country, f.country),
    latitude = coalesce(e.latitude, f.latitude),
    longitude = coalesce(e.longitude, f.longitude),
    earliest_source_date = f.date_created,
    latest_source_refresh = f.date_refreshed
from ranked_foursquare f
where f.member_rank = 1 and f.entity_id = e.entity_id;

with source_rollup as (
    select
        entity_id,
        count(*)::smallint as source_count,
        bool_or(source_qualified) as is_qualified
    from warehouse.source_places
    group by entity_id
)
update warehouse.entities e
set source_count = r.source_count,
    is_qualified_no_website_email_lead = r.is_qualified
from source_rollup r
where r.entity_id = e.entity_id;

insert into warehouse.entity_emails (
    entity_id, normalized_email, display_email, email_domain,
    is_usable, is_role_account, source_count, sources
)
with evidence as (
    select
        sp.entity_id,
        lower(btrim(e.email)) as normalized_email,
        e.email as display_email,
        e.email_domain,
        e.is_syntax_valid as is_usable,
        e.is_role_account,
        'overture'::text as source
    from warehouse.source_places sp
    join raw_overture.emails e
      on sp.source = 'overture' and sp.source_place_id = e.place_id

    union all

    select
        sp.entity_id,
        e.normalized_email,
        e.email,
        e.email_domain,
        e.is_usable,
        e.is_role_account,
        'foursquare'::text
    from warehouse.source_places sp
    join raw_foursquare.emails e
      on sp.source = 'foursquare' and sp.source_place_id = e.place_id
)
select
    entity_id,
    normalized_email,
    min(display_email),
    min(email_domain),
    bool_or(is_usable),
    bool_or(is_role_account),
    count(distinct source)::smallint,
    array_agg(distinct source order by source)
from evidence
where normalized_email is not null and normalized_email <> ''
group by entity_id, normalized_email;

insert into warehouse.entity_phones (
    entity_id, normalized_phone, raw_values, sources
)
with evidence as (
    select
        sp.entity_id,
        right(regexp_replace(phone, '[^0-9]', '', 'g'), 10) as normalized_phone,
        phone as raw_value,
        'overture'::text as source
    from warehouse.source_places sp
    join raw_overture.places p
      on sp.source = 'overture' and sp.source_place_id = p.place_id
    cross join lateral unnest(coalesce(p.phones, array[]::text[])) as phone

    union all

    select
        sp.entity_id,
        right(regexp_replace(p.telephone, '[^0-9]', '', 'g'), 10),
        p.telephone,
        'foursquare'::text
    from warehouse.source_places sp
    join raw_foursquare.places p
      on sp.source = 'foursquare' and sp.source_place_id = p.place_id
    where p.telephone is not null
)
select
    entity_id,
    normalized_phone,
    array_agg(distinct raw_value order by raw_value),
    array_agg(distinct source order by source)
from evidence
where length(normalized_phone) = 10
group by entity_id, normalized_phone;

insert into warehouse.entity_socials (entity_id, platform, handle_or_url, source)
select distinct
    sp.entity_id,
    case
        when lower(social) like '%facebook%' then 'facebook'
        when lower(social) like '%instagram%' then 'instagram'
        when lower(social) like '%twitter%' or lower(social) like '%x.com%' then 'twitter'
        else 'other'
    end,
    social,
    'overture'
from warehouse.source_places sp
join raw_overture.places p
  on sp.source = 'overture' and sp.source_place_id = p.place_id
cross join lateral unnest(coalesce(p.socials, array[]::text[])) as social
where social <> ''
on conflict do nothing;

insert into warehouse.entity_socials (entity_id, platform, handle_or_url, source)
select sp.entity_id, v.platform, v.handle_or_url, 'foursquare'
from warehouse.source_places sp
join raw_foursquare.places p
  on sp.source = 'foursquare' and sp.source_place_id = p.place_id
cross join lateral (
    values
        ('facebook', p.facebook_id),
        ('instagram', p.instagram),
        ('twitter', p.twitter)
) as v(platform, handle_or_url)
where v.handle_or_url is not null and btrim(v.handle_or_url) <> ''
on conflict do nothing;

insert into warehouse.entity_categories (
    entity_id, source, category_id, category_label, hierarchy, is_primary
)
select
    sp.entity_id,
    'overture',
    coalesce(p.primary_category, p.basic_category, p.industry_group),
    coalesce(p.primary_category, p.basic_category, p.industry_group),
    p.taxonomy_hierarchy,
    true
from warehouse.source_places sp
join raw_overture.places p
  on sp.source = 'overture' and sp.source_place_id = p.place_id
where coalesce(p.primary_category, p.basic_category, p.industry_group) is not null
on conflict do nothing;

insert into warehouse.entity_categories (
    entity_id, source, category_id, category_label, hierarchy, is_primary
)
select distinct
    sp.entity_id,
    'foursquare',
    category.category_id,
    category.category_label,
    regexp_split_to_array(category.category_label, ' > '),
    category.ordinality = 1
from warehouse.source_places sp
join raw_foursquare.places p
  on sp.source = 'foursquare' and sp.source_place_id = p.place_id
cross join lateral unnest(
    coalesce(p.category_ids, array[]::text[]),
    coalesce(p.category_labels, array[]::text[])
) with ordinality as category(category_id, category_label, ordinality)
where category.category_id is not null
on conflict do nothing;

create or replace view warehouse.qualified_no_website_email_leads as
select e.*
from warehouse.entities e
where e.is_qualified_no_website_email_lead
  and exists (
      select 1
      from warehouse.entity_emails email
      where email.entity_id = e.entity_id and email.is_usable
  );

create or replace view warehouse.lead_summary as
select
    (select count(*) from raw_overture.places) as overture_contact_candidates,
    (select count(*) from raw_foursquare.places) as foursquare_contact_candidates,
    (select count(*) from warehouse.entities) as canonical_entities,
    (select count(*) from warehouse.entities where source_count > 1) as cross_source_entities,
    (select count(*) from warehouse.qualified_no_website_email_leads) as total_no_website_yes_email_leads,
    (select count(distinct email.normalized_email)
     from warehouse.entity_emails email
     join warehouse.entities entity using (entity_id)
     where email.is_usable
       and entity.is_qualified_no_website_email_lead) as unique_usable_email_addresses;

create index if not exists entities_qualified_region_idx
    on warehouse.entities(region, entity_id)
    where is_qualified_no_website_email_lead;
create index if not exists entities_qualified_city_idx
    on warehouse.entities(city, entity_id)
    where is_qualified_no_website_email_lead;
create index if not exists entities_qualified_postcode_idx
    on warehouse.entities(postcode, entity_id)
    where is_qualified_no_website_email_lead;

analyze raw_overture.places;
analyze raw_overture.emails;
analyze raw_foursquare.places;
analyze raw_foursquare.emails;
analyze warehouse.entities;
analyze warehouse.source_places;
analyze warehouse.entity_emails;
