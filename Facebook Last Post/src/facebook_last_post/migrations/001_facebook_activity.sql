create schema if not exists facebook_enrichment;

create table if not exists facebook_enrichment.profile_activity (
    profile_id bigint generated always as identity primary key,
    entity_id bigint not null references warehouse.entities(entity_id) on delete cascade,
    source text not null check (char_length(source) between 1 and 100),
    input_handle_or_url text not null,
    normalized_url text not null check (char_length(normalized_url) between 1 and 500),
    state text not null default 'pending'
        check (state in (
            'pending', 'leased', 'retry', 'succeeded', 'no_data',
            'unavailable', 'blocked', 'failed'
        )),
    fetch_status text,
    last_post_at timestamptz,
    checked_at timestamptz,
    next_attempt_at timestamptz default current_timestamp,
    last_http_status integer
        check (last_http_status between 100 and 599 or last_http_status is null),
    extraction_method text,
    document_bytes bigint not null default 0 check (document_bytes >= 0),
    duration_ms integer not null default 0 check (duration_ms >= 0),
    attempt_count integer not null default 0 check (attempt_count >= 0),
    lease_owner text,
    lease_expires_at timestamptz,
    error_code text,
    error_detail text,
    proxy_label text,
    created_at timestamptz not null default current_timestamp,
    updated_at timestamptz not null default current_timestamp,
    constraint profile_activity_source_unique
        unique (entity_id, source, normalized_url)
);

create index if not exists profile_activity_claimable_idx
    on facebook_enrichment.profile_activity (next_attempt_at, profile_id)
    where state in ('pending', 'retry');

create index if not exists profile_activity_expired_lease_idx
    on facebook_enrichment.profile_activity (lease_expires_at, profile_id)
    where state = 'leased';

create index if not exists profile_activity_entity_idx
    on facebook_enrichment.profile_activity (entity_id)
    include (state, last_post_at, checked_at);

create index if not exists profile_activity_last_post_idx
    on facebook_enrichment.profile_activity (last_post_at desc)
    where state = 'succeeded';

create or replace view facebook_enrichment.entity_last_post as
select
    entity_id,
    max(last_post_at) as last_facebook_post_at,
    max(checked_at) as last_facebook_checked_at,
    count(*) filter (where state = 'succeeded') as successful_profile_count,
    count(*) as facebook_profile_count
from facebook_enrichment.profile_activity
group by entity_id;

comment on schema facebook_enrichment is
    'Anonymous public Facebook page activity checks; no authenticated/private endpoint data.';

comment on table facebook_enrichment.profile_activity is
    'Durable queue and latest public post timestamp for each warehouse Facebook account reference.';
