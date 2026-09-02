create table if not exists warehouse.google_maps_enrichment_runs (
    run_id uuid primary key,
    status text not null check (status in ('running', 'completed', 'failed', 'aborted')),
    requested_count integer not null check (requested_count > 0),
    enqueued_count integer not null default 0 check (enqueued_count >= 0),
    worker_count smallint not null check (worker_count > 0),
    website_worker_count smallint not null default 0 check (website_worker_count >= 0),
    review_provider text not null,
    started_at timestamptz not null default current_timestamp,
    completed_at timestamptz,
    summary jsonb,
    error text
);

create table if not exists warehouse.google_maps_enrichment (
    entity_id bigint primary key references warehouse.entities(entity_id) on delete cascade,
    run_id uuid not null references warehouse.google_maps_enrichment_runs(run_id) on delete cascade,
    status text not null check (
        status in ('queued', 'in_progress', 'matched', 'ambiguous', 'not_found', 'failed')
    ),
    search_query text,
    attempt_count smallint not null default 0 check (attempt_count >= 0),
    worker_number smallint,
    candidate_count integer check (candidate_count >= 0),
    exists_on_google_maps boolean,
    google_maps_searched boolean not null default false,
    google_website_found boolean,
    google_place_id text,
    google_cid text,
    google_name text,
    google_formatted_address text,
    google_latitude double precision,
    google_longitude double precision,
    google_maps_url text,
    website_url text,
    website_verified boolean,
    website_status text,
    website_checked_at timestamptz,
    website_check_state text not null default 'not_applicable' check (
        website_check_state in ('not_applicable', 'queued', 'in_progress', 'completed')
    ),
    website_worker_number smallint,
    website_check_attempt_count smallint not null default 0 check (
        website_check_attempt_count >= 0
    ),
    website_check_started_at timestamptz,
    review_count integer check (review_count >= 0),
    latest_review_at timestamptz,
    review_metadata_source text,
    has_operating_hours boolean,
    is_claimed_owner boolean,
    is_permanently_closed boolean,
    is_temporarily_closed boolean,
    regular_hours jsonb,
    match_score double precision check (match_score between 0 and 1),
    match_policy_version text,
    match_threshold double precision check (match_threshold between 0 and 1),
    name_score double precision check (name_score between 0 and 1),
    address_score double precision check (address_score between 0 and 1),
    distance_meters double precision check (distance_meters >= 0),
    match_reason text,
    candidate_snapshot jsonb not null default '[]'::jsonb,
    error text,
    started_at timestamptz,
    searched_at timestamptz,
    updated_at timestamptz not null default current_timestamp
);

-- Existing databases created before website verification need the new columns.
alter table warehouse.google_maps_enrichment
    add column if not exists google_maps_searched boolean not null default false,
    add column if not exists google_website_found boolean,
    add column if not exists website_verified boolean,
    add column if not exists website_status text,
    add column if not exists website_checked_at timestamptz,
    add column if not exists website_check_state text not null default 'not_applicable',
    add column if not exists website_worker_number smallint,
    add column if not exists website_check_attempt_count smallint not null default 0,
    add column if not exists website_check_started_at timestamptz,
    add column if not exists match_policy_version text,
    add column if not exists match_threshold double precision,
    add column if not exists has_operating_hours boolean,
    add column if not exists is_claimed_owner boolean,
    add column if not exists is_permanently_closed boolean,
    add column if not exists is_temporarily_closed boolean,
    add column if not exists regular_hours jsonb;

alter table warehouse.google_maps_enrichment_runs
    add column if not exists website_worker_count smallint not null default 0;

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'google_maps_enrichment_runs_website_worker_count_check'
          and conrelid = 'warehouse.google_maps_enrichment_runs'::regclass
    ) then
        alter table warehouse.google_maps_enrichment_runs
        add constraint google_maps_enrichment_runs_website_worker_count_check
        check (website_worker_count >= 0);
    end if;
end $$;

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'google_maps_enrichment_website_attempt_count_check'
          and conrelid = 'warehouse.google_maps_enrichment'::regclass
    ) then
        alter table warehouse.google_maps_enrichment
        add constraint google_maps_enrichment_website_attempt_count_check
        check (website_check_attempt_count >= 0);
    end if;
end $$;

-- Label historic decisions without pretending they used today's binary line.
update warehouse.google_maps_enrichment
set match_policy_version = 'legacy_multiclass_v1'
where match_policy_version is null
  and status in ('matched', 'ambiguous', 'not_found');

update warehouse.google_maps_enrichment
set match_score = 0.0
where match_score is null
  and google_maps_searched is true
  and candidate_count = 0;

-- Allow the controller to distinguish a protective throttle abort from a crash.
alter table warehouse.google_maps_enrichment_runs
    drop constraint if exists google_maps_enrichment_runs_status_check;

alter table warehouse.google_maps_enrichment_runs
    add constraint google_maps_enrichment_runs_status_check
    check (status in ('running', 'completed', 'failed', 'aborted'));

-- Backfill the successful-search signal for rows produced before these fields.
update warehouse.google_maps_enrichment
set google_maps_searched = true,
    google_website_found = case
        when status = 'matched' then website_url is not null
        when status = 'not_found' then false
        else null
    end
where google_maps_searched is false
  and status in ('matched', 'ambiguous', 'not_found');

-- A confident matched listing without a URL and a completed not-found search
-- are explicit negative observations, not unchecked NULLs.
update warehouse.google_maps_enrichment
set website_verified = false,
    website_status = case
        when status = 'matched' then 'not_listed_on_google'
        else 'business_not_found_on_google'
    end,
    website_checked_at = coalesce(searched_at, updated_at, current_timestamp)
where website_status is null
  and (
      (status = 'matched' and website_url is null)
      or status = 'not_found'
  );

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'google_maps_enrichment_search_observation_check'
          and conrelid = 'warehouse.google_maps_enrichment'::regclass
    ) then
        alter table warehouse.google_maps_enrichment
        add constraint google_maps_enrichment_search_observation_check
        check (
            (google_maps_searched is false and google_website_found is null)
            or google_maps_searched is true
        );
    end if;
end $$;

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'google_maps_enrichment_match_threshold_check'
          and conrelid = 'warehouse.google_maps_enrichment'::regclass
    ) then
        alter table warehouse.google_maps_enrichment
        add constraint google_maps_enrichment_match_threshold_check
        check (match_threshold is null or match_threshold between 0 and 1);
    end if;
end $$;

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'google_maps_enrichment_website_check_state_check'
          and conrelid = 'warehouse.google_maps_enrichment'::regclass
    ) then
        alter table warehouse.google_maps_enrichment
        add constraint google_maps_enrichment_website_check_state_check
        check (
            website_check_state in ('not_applicable', 'queued', 'in_progress', 'completed')
        );
    end if;
end $$;

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'google_maps_enrichment_website_queue_consistency_check'
          and conrelid = 'warehouse.google_maps_enrichment'::regclass
    ) then
        alter table warehouse.google_maps_enrichment
        add constraint google_maps_enrichment_website_queue_consistency_check
        check (
            website_check_state = 'not_applicable'
            or (
                google_maps_searched is true
                and google_website_found is true
                and website_url is not null
                and (
                    (
                        website_check_state in ('queued', 'in_progress')
                        and website_verified is null
                        and website_status is null
                        and website_checked_at is null
                    )
                    or (
                        website_check_state = 'completed'
                        and website_verified is not null
                        and website_status is not null
                        and website_checked_at is not null
                    )
                )
            )
        );
    end if;
end $$;

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'google_maps_enrichment_binary_policy_check'
          and conrelid = 'warehouse.google_maps_enrichment'::regclass
    ) then
        alter table warehouse.google_maps_enrichment
        add constraint google_maps_enrichment_binary_policy_check
        check (
            match_policy_version <> 'binary_name85_location15_v1'
            or (
                status in ('queued', 'in_progress', 'matched', 'not_found', 'failed')
                and match_threshold = 0.65
            )
        );
    end if;
end $$;

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'google_maps_enrichment_website_found_url_check'
          and conrelid = 'warehouse.google_maps_enrichment'::regclass
    ) then
        alter table warehouse.google_maps_enrichment
        add constraint google_maps_enrichment_website_found_url_check
        check (google_website_found is distinct from true or website_url is not null);
    end if;
end $$;

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'google_maps_enrichment_website_verification_check'
          and conrelid = 'warehouse.google_maps_enrichment'::regclass
    ) then
        alter table warehouse.google_maps_enrichment
        add constraint google_maps_enrichment_website_verification_check
        check (
            (
                website_verified is null
                and website_status is null
                and website_checked_at is null
            )
            or (
                website_verified is true
                and website_status = 'live'
                and website_checked_at is not null
            )
            or (
                website_verified is false
                and website_status is not null
                and website_status <> 'live'
                and website_checked_at is not null
            )
        );
    end if;
end $$;

create index if not exists google_maps_enrichment_run_queue_idx
    on warehouse.google_maps_enrichment(run_id, entity_id)
    where status = 'queued';

create index if not exists google_maps_enrichment_run_status_idx
    on warehouse.google_maps_enrichment(run_id, status);

create index if not exists google_maps_enrichment_place_id_idx
    on warehouse.google_maps_enrichment(google_place_id)
    where google_place_id is not null;

create index if not exists google_maps_enrichment_website_status_idx
    on warehouse.google_maps_enrichment(website_status)
    where website_status is not null;

create index if not exists google_maps_enrichment_website_queue_idx
    on warehouse.google_maps_enrichment(run_id, entity_id)
    where website_check_state = 'queued';

create index if not exists google_maps_enrichment_refresh_idx
    on warehouse.google_maps_enrichment(searched_at, entity_id)
    where status in ('matched', 'not_found');

-- Candidate identity fields are associations, not merely search observations.
-- Keep rejected/ambiguous candidates only in candidate_snapshot so downstream
-- queries cannot accidentally treat them as the warehouse entity.
update warehouse.google_maps_enrichment
set google_place_id = null,
    google_cid = null,
    google_name = null,
    google_formatted_address = null,
    google_latitude = null,
    google_longitude = null,
    google_maps_url = null,
    website_url = null,
    review_count = null,
    latest_review_at = null
where status not in ('matched', 'queued', 'in_progress');
