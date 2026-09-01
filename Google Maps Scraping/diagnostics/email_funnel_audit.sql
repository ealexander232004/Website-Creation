-- Email extraction funnel audit
-- Snapshot population: all rows in the current PostgreSQL database.
-- Grain: unique Google Maps business (place_id) unless explicitly labeled queue-row or email-row.

-- 1) Headline funnel and correct denominators.
SELECT
    count(*) AS saved_businesses,
    count(*) FILTER (WHERE NOT has_website) AS eligible_no_website_businesses,
    count(*) FILTER (WHERE has_website) AS ineligible_website_businesses,
    count(*) FILTER (WHERE phone IS NOT NULL AND btrim(phone) <> '') AS businesses_with_phone,
    count(*) FILTER (WHERE city IS NOT NULL AND btrim(city) <> '') AS businesses_with_city,
    count(*) FILTER (
        WHERE EXISTS (SELECT 1 FROM email_queue q WHERE q.place_id = leads.place_id)
    ) AS unique_businesses_queued,
    count(*) FILTER (
        WHERE EXISTS (SELECT 1 FROM email_extraction_status s WHERE s.place_id = leads.place_id)
    ) AS unique_businesses_processed,
    count(*) FILTER (
        WHERE EXISTS (
            SELECT 1 FROM email_extraction_status s
            WHERE s.place_id = leads.place_id AND s.status = 'completed'
        )
    ) AS unique_businesses_marked_with_email,
    count(*) FILTER (
        WHERE EXISTS (SELECT 1 FROM lead_emails e WHERE e.place_id = leads.place_id)
    ) AS unique_businesses_with_saved_email
FROM leads;

-- 2) Unique-business status distribution (the true email-processing funnel).
SELECT
    coalesce(s.status, 'not_processed') AS extraction_status,
    count(*) AS businesses,
    round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS pct_of_saved_businesses
FROM leads l
LEFT JOIN email_extraction_status s ON s.place_id = l.place_id
GROUP BY coalesce(s.status, 'not_processed')
ORDER BY businesses DESC;

-- 3) Queue duplication and work-state audit.
SELECT
    count(*) AS queue_rows,
    count(DISTINCT place_id) AS unique_queued_businesses,
    count(*) - count(DISTINCT place_id) AS repeated_campaign_queue_rows,
    round(count(*)::numeric / nullif(count(DISTINCT place_id), 0), 3) AS queue_rows_per_business,
    count(*) FILTER (WHERE status = 'pending') AS pending_rows,
    count(*) FILTER (WHERE status = 'in_progress') AS in_progress_rows,
    count(*) FILTER (WHERE status = 'completed') AS completed_rows,
    count(*) FILTER (WHERE status = 'no_email') AS no_email_rows,
    count(*) FILTER (WHERE status = 'failed') AS failed_rows
FROM email_queue;

-- 4) Outcome by first campaign in which a unique business entered the email queue.
WITH first_queue AS (
    SELECT DISTINCT ON (place_id)
        place_id,
        campaign_id,
        created_at
    FROM email_queue
    ORDER BY place_id, created_at, id
)
SELECT
    f.campaign_id,
    c.name AS campaign_name,
    count(*) AS unique_businesses,
    count(*) FILTER (WHERE s.status IN ('completed', 'no_email')) AS processed_businesses,
    count(*) FILTER (WHERE s.status = 'completed') AS businesses_with_email,
    count(*) FILTER (WHERE s.status = 'no_email') AS businesses_without_email,
    count(*) FILTER (WHERE s.status = 'error') AS businesses_with_error,
    round(
        100.0 * count(*) FILTER (WHERE s.status = 'completed')
        / nullif(count(*) FILTER (WHERE s.status IN ('completed', 'no_email')), 0),
        2
    ) AS email_hit_rate_pct
FROM first_queue f
JOIN campaigns c ON c.id = f.campaign_id
LEFT JOIN email_extraction_status s ON s.place_id = f.place_id
GROUP BY f.campaign_id, c.name
ORDER BY f.campaign_id;

-- 5) Email record quality and provenance (aggregate only; no addresses exposed).
SELECT
    count(*) AS email_rows,
    count(DISTINCT place_id) AS businesses_with_email,
    count(DISTINCT lower(btrim(email))) AS unique_email_addresses,
    round(avg(confidence)::numeric, 3) AS mean_confidence,
    round(percentile_cont(0.5) WITHIN GROUP (ORDER BY confidence)::numeric, 3) AS median_confidence,
    count(*) FILTER (WHERE is_free_provider) AS free_provider_email_rows,
    round(100.0 * count(*) FILTER (WHERE is_free_provider) / nullif(count(*), 0), 2) AS free_provider_pct,
    count(*) FILTER (WHERE source_type = 'search_snippet') AS search_snippet_rows,
    count(*) FILTER (WHERE source_type = 'contextual_landing_page') AS landing_page_rows
FROM lead_emails;

-- 6) Potential contamination: one exact address attached to multiple businesses.
WITH repeated AS (
    SELECT lower(btrim(email)) AS normalized_email, count(DISTINCT place_id) AS businesses
    FROM lead_emails
    GROUP BY lower(btrim(email))
    HAVING count(DISTINCT place_id) > 1
)
SELECT
    count(*) AS repeated_email_addresses,
    coalesce(sum(businesses), 0) AS business_assignments_using_repeated_addresses,
    coalesce(max(businesses), 0) AS max_businesses_for_one_address
FROM repeated;

-- 7) Email domain concentration without exposing addresses.
SELECT
    lower(split_part(email, '@', 2)) AS email_domain,
    count(*) AS email_rows,
    count(DISTINCT place_id) AS businesses
FROM lead_emails
GROUP BY lower(split_part(email, '@', 2))
ORDER BY businesses DESC, email_domain
LIMIT 15;

-- 8) Terminal/retryable error distribution.
SELECT
    coalesce(error_message, '(none)') AS error_message,
    count(*) AS queue_rows,
    count(DISTINCT place_id) AS businesses
FROM email_queue
WHERE status = 'failed'
GROUP BY coalesce(error_message, '(none)')
ORDER BY queue_rows DESC
LIMIT 20;

-- 9) Search campaign novelty: each campaign currently repeats the same job definitions.
SELECT
    count(*) AS search_queue_rows,
    count(DISTINCT (keyword, location_name)) AS distinct_keyword_location_jobs,
    count(DISTINCT campaign_id) AS campaigns,
    round(
        count(*)::numeric / nullif(count(DISTINCT (keyword, location_name)), 0),
        3
    ) AS queue_rows_per_distinct_search
FROM search_queue;

-- 10) Email hit rate by how often Maps rediscovered the business across campaigns.
WITH business_recurrence AS (
    SELECT place_id, count(DISTINCT campaign_id) AS campaigns_seen
    FROM email_queue
    GROUP BY place_id
)
SELECT
    recurrence.campaigns_seen,
    count(*) AS businesses,
    count(*) FILTER (WHERE status.status = 'completed') AS businesses_with_email,
    round(
        100.0 * count(*) FILTER (WHERE status.status = 'completed') / count(*),
        2
    ) AS email_hit_rate_pct
FROM business_recurrence AS recurrence
LEFT JOIN email_extraction_status AS status USING (place_id)
GROUP BY recurrence.campaigns_seen
ORDER BY recurrence.campaigns_seen;

-- 11) Quality-adjusted yield after excluding addresses assigned to many businesses.
WITH email_reuse AS (
    SELECT
        lower(btrim(email)) AS normalized_email,
        count(DISTINCT place_id) AS businesses_using_address
    FROM lead_emails
    GROUP BY lower(btrim(email))
), per_business AS (
    SELECT
        email.place_id,
        bool_or(reuse.businesses_using_address = 1) AS has_unique_address,
        bool_or(reuse.businesses_using_address <= 3) AS has_address_used_by_at_most_three_businesses
    FROM lead_emails AS email
    JOIN email_reuse AS reuse
      ON reuse.normalized_email = lower(btrim(email.email))
    GROUP BY email.place_id
)
SELECT
    count(*) AS businesses_with_any_email,
    count(*) FILTER (WHERE has_unique_address) AS businesses_with_unique_address,
    count(*) FILTER (WHERE has_address_used_by_at_most_three_businesses)
        AS businesses_with_low_reuse_address
FROM per_business;
