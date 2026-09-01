-- Social-handle coverage across the two Foursquare Parquet exports and the
-- Overture probable-small-business view. Run from the workspace root.

ATTACH 'Overture/overture_smb_leads.duckdb' AS overture (READ_ONLY);

-- Coverage by dataset. A Foursquare business has a social handle when at least
-- one nonblank Facebook, Instagram, or Twitter field is populated. An Overture
-- business has a social handle when its socials array contains at least one URL.
WITH foursquare_qualified AS (
    SELECT
        'Foursquare qualified leads' AS dataset,
        fsq_place_id AS business_id,
        nullif(trim(facebook_id), '') IS NOT NULL AS has_facebook,
        nullif(trim(instagram), '') IS NOT NULL AS has_instagram,
        nullif(trim(twitter), '') IS NOT NULL AS has_twitter
    FROM read_parquet('Foursquare/exports/qualified_leads.parquet')
),
foursquare_unique AS (
    SELECT
        'Foursquare unique vs Overture' AS dataset,
        fsq_place_id AS business_id,
        nullif(trim(facebook_id), '') IS NOT NULL AS has_facebook,
        nullif(trim(instagram), '') IS NOT NULL AS has_instagram,
        nullif(trim(twitter), '') IS NOT NULL AS has_twitter
    FROM read_parquet('Foursquare/exports/foursquare_unique_vs_overture.parquet')
),
foursquare_all AS (
    SELECT * FROM foursquare_qualified
    UNION ALL
    SELECT * FROM foursquare_unique
),
foursquare_coverage AS (
    SELECT
        dataset,
        count(*) AS total_businesses,
        count_if(has_facebook OR has_instagram OR has_twitter) AS businesses_with_social
    FROM foursquare_all
    GROUP BY dataset
),
overture_coverage AS (
    SELECT
        'Overture probable SMB leads' AS dataset,
        count(*) AS total_businesses,
        count_if(coalesce(array_length(socials), 0) > 0) AS businesses_with_social
    FROM overture.main.small_business_leads
)
SELECT
    dataset,
    total_businesses,
    businesses_with_social,
    businesses_with_social::DOUBLE / total_businesses AS coverage_rate
FROM (
    SELECT * FROM foursquare_coverage
    UNION ALL
    SELECT * FROM overture_coverage
)
ORDER BY dataset;

-- Platform distribution. Platform-presence share uses each populated
-- platform/URL as one presence; a business can contribute to multiple platforms.
WITH foursquare_platforms AS (
    SELECT
        'Foursquare qualified leads' AS dataset,
        fsq_place_id AS business_id,
        platform
    FROM read_parquet('Foursquare/exports/qualified_leads.parquet'),
    LATERAL (
        SELECT unnest([
            CASE WHEN nullif(trim(facebook_id), '') IS NOT NULL THEN 'Facebook' END,
            CASE WHEN nullif(trim(instagram), '') IS NOT NULL THEN 'Instagram' END,
            CASE WHEN nullif(trim(twitter), '') IS NOT NULL THEN 'Twitter' END
        ]) AS platform
    )
    WHERE platform IS NOT NULL
),
foursquare_unique_platforms AS (
    SELECT
        'Foursquare unique vs Overture' AS dataset,
        fsq_place_id AS business_id,
        platform
    FROM read_parquet('Foursquare/exports/foursquare_unique_vs_overture.parquet'),
    LATERAL (
        SELECT unnest([
            CASE WHEN nullif(trim(facebook_id), '') IS NOT NULL THEN 'Facebook' END,
            CASE WHEN nullif(trim(instagram), '') IS NOT NULL THEN 'Instagram' END,
            CASE WHEN nullif(trim(twitter), '') IS NOT NULL THEN 'Twitter' END
        ]) AS platform
    )
    WHERE platform IS NOT NULL
),
overture_platforms AS (
    SELECT DISTINCT
        'Overture probable SMB leads' AS dataset,
        id AS business_id,
        CASE lower(regexp_extract(url, '^(?:https?://)?(?:www\.)?([^/]+)', 1))
            WHEN 'facebook.com' THEN 'Facebook'
            WHEN 'instagram.com' THEN 'Instagram'
            WHEN 'twitter.com' THEN 'Twitter'
            WHEN 'linkedin.com' THEN 'LinkedIn'
            ELSE lower(regexp_extract(url, '^(?:https?://)?(?:www\.)?([^/]+)', 1))
        END AS platform
    FROM overture.main.small_business_leads,
    unnest(socials) AS social(url)
),
all_platforms AS (
    SELECT * FROM foursquare_platforms
    UNION ALL
    SELECT * FROM foursquare_unique_platforms
    UNION ALL
    SELECT * FROM overture_platforms
),
platform_counts AS (
    SELECT dataset, platform, count(DISTINCT business_id) AS businesses
    FROM all_platforms
    GROUP BY dataset, platform
)
SELECT
    dataset,
    platform,
    businesses,
    sum(businesses) OVER (PARTITION BY dataset) AS platform_presences,
    businesses::DOUBLE / sum(businesses) OVER (PARTITION BY dataset) AS presence_share
FROM platform_counts
ORDER BY dataset, businesses DESC, platform;
