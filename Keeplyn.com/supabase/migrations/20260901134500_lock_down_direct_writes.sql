begin;

alter function public.submit_website_request(text, jsonb, text, text, text, jsonb)
  security definer;

revoke insert on public.website_requests from authenticated;
revoke insert on public.website_request_offerings from authenticated;
revoke insert on public.website_request_assets from authenticated;

drop policy "Customers can create their website requests" on public.website_requests;
drop policy "Customers can create their request offerings" on public.website_request_offerings;
drop policy "Customers can create their request assets" on public.website_request_assets;

revoke insert on public.website_request_updates from authenticated;
grant insert (request_id, title, description) on public.website_request_updates to authenticated;

commit;
