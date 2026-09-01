create schema if not exists raw_overture;
create schema if not exists raw_foursquare;
create schema if not exists warehouse;

create table if not exists raw_overture.places (
    place_id text primary key,
    business_name text,
    primary_category text,
    basic_category text,
    industry_group text,
    taxonomy_hierarchy text[],
    alternate_categories text[],
    emails text[],
    phones text[],
    socials text[],
    websites text[],
    street_address text,
    city text,
    region text,
    postcode text,
    country text,
    longitude double precision,
    latitude double precision,
    brand_name text,
    is_known_brand boolean not null,
    is_probable_small_business boolean not null,
    confidence double precision,
    quality_tier text,
    operating_status text,
    all_names jsonb,
    all_addresses jsonb,
    brand jsonb,
    source_records jsonb,
    overture_release text not null,
    source_file text not null,
    ingested_at timestamptz not null
);

create table if not exists raw_overture.emails (
    place_id text not null references raw_overture.places(place_id) on delete cascade,
    email text not null,
    email_domain text,
    is_syntax_valid boolean not null,
    is_role_account boolean not null,
    source_file text not null,
    primary key (place_id, email)
);

create table if not exists raw_foursquare.places (
    place_id text primary key,
    name text,
    latitude double precision,
    longitude double precision,
    address text,
    locality text,
    region text,
    postcode text,
    admin_region text,
    post_town text,
    po_box text,
    country text,
    date_created date,
    date_refreshed date,
    date_closed date,
    telephone text,
    website text,
    email text,
    facebook_id text,
    instagram text,
    twitter text,
    category_ids text[],
    category_labels text[],
    placemaker_url text,
    unresolved_flags text[],
    has_noncommercial_category boolean not null,
    has_disqualifying_flag boolean not null,
    source_file text not null,
    foursquare_release text not null,
    ingested_at timestamptz not null
);

create table if not exists raw_foursquare.emails (
    place_id text primary key references raw_foursquare.places(place_id) on delete cascade,
    email text not null,
    normalized_email text not null,
    email_domain text,
    is_syntax_valid boolean not null,
    is_placeholder boolean not null,
    is_role_account boolean not null,
    is_usable boolean not null
);

create table if not exists raw_foursquare.categories (
    category_id text primary key,
    category_level integer,
    category_name text,
    category_label text,
    level1_category_id text,
    level1_category_name text,
    level2_category_id text,
    level2_category_name text,
    level3_category_id text,
    level3_category_name text,
    level4_category_id text,
    level4_category_name text,
    level5_category_id text,
    level5_category_name text,
    level6_category_id text,
    level6_category_name text
);

create table if not exists raw_foursquare.overture_matches (
    foursquare_place_id text not null references raw_foursquare.places(place_id) on delete cascade,
    overture_place_id text not null references raw_overture.places(place_id) on delete cascade,
    email_match boolean not null,
    phone_match boolean not null,
    name_match boolean not null,
    postcode_match boolean not null,
    is_high_confidence_duplicate boolean not null,
    primary key (foursquare_place_id, overture_place_id)
);

create table if not exists warehouse.entities (
    entity_id bigint generated always as identity primary key,
    primary_source text not null check (primary_source in ('overture', 'foursquare')),
    primary_source_place_id text not null,
    canonical_name text,
    street_address text,
    city text,
    region text,
    postcode text,
    country text,
    latitude double precision,
    longitude double precision,
    brand_name text,
    is_known_brand boolean not null default false,
    overture_confidence double precision,
    operating_status text,
    earliest_source_date date,
    latest_source_refresh date,
    source_count smallint not null default 1 check (source_count > 0),
    is_qualified_no_website_email_lead boolean not null default false,
    loaded_at timestamptz not null default current_timestamp,
    unique (primary_source, primary_source_place_id)
);

create table if not exists warehouse.source_places (
    source text not null check (source in ('overture', 'foursquare')),
    source_place_id text not null,
    entity_id bigint not null references warehouse.entities(entity_id) on delete cascade,
    source_qualified boolean not null,
    match_method text,
    match_confidence text check (match_confidence in ('high', 'source_primary') or match_confidence is null),
    primary key (source, source_place_id)
);

create table if not exists warehouse.entity_emails (
    entity_id bigint not null references warehouse.entities(entity_id) on delete cascade,
    normalized_email text not null,
    display_email text not null,
    email_domain text,
    is_usable boolean not null,
    is_role_account boolean not null,
    source_count smallint not null check (source_count > 0),
    sources text[] not null,
    primary key (entity_id, normalized_email)
);

create table if not exists warehouse.entity_phones (
    entity_id bigint not null references warehouse.entities(entity_id) on delete cascade,
    normalized_phone text not null,
    raw_values text[] not null,
    sources text[] not null,
    primary key (entity_id, normalized_phone)
);

create table if not exists warehouse.entity_socials (
    entity_id bigint not null references warehouse.entities(entity_id) on delete cascade,
    platform text not null,
    handle_or_url text not null,
    source text not null,
    primary key (entity_id, platform, handle_or_url, source)
);

create table if not exists warehouse.entity_categories (
    entity_id bigint not null references warehouse.entities(entity_id) on delete cascade,
    source text not null,
    category_id text not null,
    category_label text,
    hierarchy text[],
    is_primary boolean not null default false,
    primary key (entity_id, source, category_id)
);

create index if not exists raw_overture_emails_place_id_idx
    on raw_overture.emails(place_id);
create index if not exists raw_foursquare_matches_overture_idx
    on raw_foursquare.overture_matches(overture_place_id);
create index if not exists source_places_entity_id_idx
    on warehouse.source_places(entity_id);
create index if not exists entity_emails_normalized_idx
    on warehouse.entity_emails(normalized_email);
create index if not exists entity_phones_normalized_idx
    on warehouse.entity_phones(normalized_phone);
create index if not exists entity_categories_category_idx
    on warehouse.entity_categories(source, category_id);
