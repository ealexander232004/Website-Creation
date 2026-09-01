begin;

create index website_request_updates_created_by_idx
  on public.website_request_updates (created_by);

create index stripe_events_request_id_idx
  on public.stripe_events (request_id)
  where request_id is not null;

drop policy "Customers can read their website requests" on public.website_requests;
drop policy "Admins can read all website requests" on public.website_requests;
create policy "Customers and admins can read website requests"
  on public.website_requests
  for select
  to authenticated
  using (user_id = (select auth.uid()) or (select public.is_keeplyn_admin()));

drop policy "Customers can read their request offerings" on public.website_request_offerings;
drop policy "Admins can read all request offerings" on public.website_request_offerings;
create policy "Customers and admins can read request offerings"
  on public.website_request_offerings
  for select
  to authenticated
  using (
    (select public.is_keeplyn_admin())
    or exists (
      select 1 from public.website_requests
      where website_requests.id = website_request_offerings.request_id
        and website_requests.user_id = (select auth.uid())
    )
  );

drop policy "Customers can read their request assets" on public.website_request_assets;
drop policy "Admins can read all request assets" on public.website_request_assets;
create policy "Customers and admins can read request assets"
  on public.website_request_assets
  for select
  to authenticated
  using (
    (select public.is_keeplyn_admin())
    or exists (
      select 1 from public.website_requests
      where website_requests.id = website_request_assets.request_id
        and website_requests.user_id = (select auth.uid())
    )
  );

drop policy "Customers can read their update tickets" on public.website_request_updates;
drop policy "Admins can read all update tickets" on public.website_request_updates;
create policy "Customers and admins can read update tickets"
  on public.website_request_updates
  for select
  to authenticated
  using (
    (select public.is_keeplyn_admin())
    or exists (
      select 1 from public.website_requests
      where website_requests.id = website_request_updates.request_id
        and website_requests.user_id = (select auth.uid())
    )
  );

drop policy "Customers can read their website request photos" on storage.objects;
drop policy "Admins can read request photos" on storage.objects;
create policy "Customers and admins can read request photos"
  on storage.objects
  for select
  to authenticated
  using (
    bucket_id = 'website-request-photos'
    and (owner_id = (select auth.uid())::text or (select public.is_keeplyn_admin()))
  );

drop policy "Customers can remove their website request photos" on storage.objects;
drop policy "Admins can remove request photos" on storage.objects;
create policy "Customers and admins can remove request photos"
  on storage.objects
  for delete
  to authenticated
  using (
    bucket_id = 'website-request-photos'
    and (owner_id = (select auth.uid())::text or (select public.is_keeplyn_admin()))
  );

create policy "Stripe events are private"
  on public.stripe_events
  for select
  to authenticated
  using (false);

commit;
