-- Persist the metadata already present in the September 2026 warehouse.
-- Safe for both a fresh database and the transferred warehouse snapshot.
alter table facebook_enrichment.profile_activity
    add column if not exists canonical_url text,
    add column if not exists likes_count integer,
    add column if not exists talking_about_count integer,
    add column if not exists was_here_count integer,
    add column if not exists page_category text;

alter table facebook_enrichment.profile_activity
    drop constraint if exists profile_activity_state_check;
alter table facebook_enrichment.profile_activity
    add constraint profile_activity_state_check check (state in (
        'pending', 'leased', 'retry', 'succeeded', 'no_data',
        'unavailable', 'blocked', 'restricted', 'failed'
    ));
