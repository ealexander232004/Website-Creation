-- Admin access keyed to auth user IDs, not self-asserted email addresses.
-- Sign-ups are auto-confirmed, so an email match alone let anyone who
-- registered an admin address first become an admin.
alter table private.keeplyn_admins
  add column if not exists user_id uuid unique references auth.users (id) on delete cascade;

create or replace function public.is_keeplyn_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from private.keeplyn_admins
    where user_id is not null
      and user_id = (select auth.uid())
  );
$$;

revoke all on function public.is_keeplyn_admin() from public, anon;
grant execute on function public.is_keeplyn_admin() to authenticated;
