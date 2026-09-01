# Email extraction diagnostic report notes

- Question: Is the current lead-to-email ratio evidence that email scraping is malfunctioning?
- Audience: Product stakeholders (executive report specification).
- Delivery mode: Portable HTML.
- Snapshot: PostgreSQL audit generated September 1, 2026 at approximately 5:14 AM Pacific while campaign 5 remained active.
- Decision-useful standard: distinguish pipeline failure, search-cohort quality, acceptance-policy recall, and saved-email contamination.

## Required structure mapping

- Title: `Are we scraping emails correctly?`
- Executive summary: visible immediately after the title.
- Key findings with visual evidence: funnel reconciliation, campaign cohort chart, live probe table, and address-reuse table.
- Recommended next steps: source-ownership and cross-business reuse checks before recall relaxation.
- Further questions: false-negative rate and source ownership validation.
- Caveats and assumptions: fixed live snapshot, no SMTP verification, small probe sample.

## Chart map

- Section: `The decline is concentrated in later search cohorts`
- Question: How did unique-business email yield change by first-seen campaign?
- Family/type: Comparison / vertical bar.
- Fields: campaign label, unique businesses, businesses with email, hit-rate fraction.
- Takeaway: early cohorts returned 6.45%-6.92%; campaigns 4-5 returned about 0.2%-0.25%.
- Palette: single blue root, no legend, zero baseline.
- Surface: `email_scraping_diagnostic.html`.

## Validation notes

- Unique `place_id` is the business grain; queue rows are not used as the conversion denominator.
- All saved leads in the snapshot satisfy `NOT has_website`; all but a handful had an extraction outcome at snapshot time.
- `email_extraction_status` reconciles with `lead_emails`: no completed lead lacks a saved email, no `no_email` lead has a saved email, and saved row counts match status counts.
- The live probe returned 20/20 normal HTTP 200 search pages and no CAPTCHA/throttling markers. Across 10 recent campaign-5 misses, both the current phone-first query and the otherwise skipped name-city query found only one relevant result card and no email strings.
- Potential contamination remains: 297 exact addresses appear on more than one business, and one address appears on 86 businesses. Repeated domains and source hosts indicate directory or multi-location ownership can be mistaken for the target business.
- Quantitative visuals were included because the five campaign cohorts form a meaningful comparison. The small live probe is kept as a table because exact lookup and sample-size context matter more than shape.
- Confidence assessment: Share with caveats. Pipeline mechanics are verified; address ownership is not independently verified and the live probe is small.
