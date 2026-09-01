create schema if not exists raw_fmcsa;

create table if not exists raw_fmcsa.carriers (
    dot_number bigint primary key,
    legal_name text not null,
    dba_name text,
    carrier_operation text check (carrier_operation in ('A', 'B', 'C')),
    hm_flag boolean,
    pc_flag boolean,
    phy_street text,
    phy_city text,
    phy_state text,
    phy_zip text,
    phy_country text,
    mailing_street text,
    mailing_city text,
    mailing_state text,
    mailing_zip text,
    mailing_country text,
    telephone text,
    fax text,
    email_address text not null,
    mcs150_date date,
    mcs150_mileage bigint check (mcs150_mileage >= 0),
    mcs150_mileage_year smallint check (mcs150_mileage_year >= 0),
    add_date date,
    oic_state text,
    nbr_power_unit integer not null check (nbr_power_unit >= 0),
    driver_total integer not null check (driver_total >= 0),
    recent_mileage bigint check (recent_mileage >= 0),
    recent_mileage_year smallint check (recent_mileage_year >= 0),
    vmt_source_id smallint check (vmt_source_id >= 0),
    private_only boolean,
    authorized_for_hire boolean,
    exempt_for_hire boolean,
    private_property boolean,
    private_passenger_business boolean,
    private_passenger_nonbusiness boolean,
    migrant boolean,
    us_mail boolean,
    federal_government boolean,
    state_government boolean,
    local_government boolean,
    indian_tribe boolean,
    op_other text,
    snapshot_date date not null,
    is_current boolean not null default true,
    source_file text not null,
    source_sha256 text not null check (source_sha256 ~ '^[0-9A-F]{64}$'),
    ingested_at timestamptz not null default current_timestamp
);

create table if not exists raw_fmcsa.emails (
    dot_number bigint primary key references raw_fmcsa.carriers(dot_number) on delete cascade,
    email text not null,
    normalized_email text not null,
    email_domain text,
    is_syntax_valid boolean not null,
    is_role_account boolean not null,
    source_file text not null
);

create table if not exists raw_fmcsa.import_runs (
    run_id bigint generated always as identity primary key,
    source_file text not null,
    source_sha256 text not null check (source_sha256 ~ '^[0-9A-F]{64}$'),
    snapshot_date date not null,
    status text not null check (status in ('running', 'completed', 'failed')),
    row_count bigint check (row_count >= 0),
    valid_email_count bigint check (valid_email_count >= 0),
    matched_existing_entities bigint check (matched_existing_entities >= 0),
    new_entities bigint check (new_entities >= 0),
    started_at timestamptz not null default current_timestamp,
    finished_at timestamptz,
    error text
);

create index if not exists raw_fmcsa_carriers_current_region_idx
    on raw_fmcsa.carriers(phy_state, phy_city, dot_number)
    where is_current;

create index if not exists raw_fmcsa_carriers_current_operation_idx
    on raw_fmcsa.carriers(carrier_operation, dot_number)
    where is_current;

create index if not exists raw_fmcsa_emails_normalized_idx
    on raw_fmcsa.emails(normalized_email);

-- Expand canonical source checks without rebuilding the existing tables.
do $$
declare
    constraint_definition text;
begin
    select pg_get_constraintdef(oid)
    into constraint_definition
    from pg_constraint
    where conrelid = 'warehouse.entities'::regclass
      and conname = 'entities_primary_source_check';

    if constraint_definition is null
       or position('fmcsa' in constraint_definition) = 0 then
        alter table warehouse.entities
            drop constraint if exists entities_primary_source_check;
        alter table warehouse.entities
            add constraint entities_primary_source_check
            check (primary_source in ('overture', 'foursquare', 'fmcsa'))
            not valid;
        alter table warehouse.entities
            validate constraint entities_primary_source_check;
    end if;
end $$;

do $$
declare
    constraint_definition text;
begin
    select pg_get_constraintdef(oid)
    into constraint_definition
    from pg_constraint
    where conrelid = 'warehouse.source_places'::regclass
      and conname = 'source_places_source_check';

    if constraint_definition is null
       or position('fmcsa' in constraint_definition) = 0 then
        alter table warehouse.source_places
            drop constraint if exists source_places_source_check;
        alter table warehouse.source_places
            add constraint source_places_source_check
            check (source in ('overture', 'foursquare', 'fmcsa'))
            not valid;
        alter table warehouse.source_places
            validate constraint source_places_source_check;
    end if;
end $$;

create or replace view warehouse.fmcsa_small_business_email_leads as
select
    carrier.*,
    email.normalized_email,
    email.email_domain,
    email.is_syntax_valid,
    email.is_role_account
from raw_fmcsa.carriers carrier
join raw_fmcsa.emails email using (dot_number)
where carrier.is_current;
