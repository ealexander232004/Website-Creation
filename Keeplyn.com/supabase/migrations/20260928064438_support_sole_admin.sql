-- support@keeplyn.com is the only Keeplyn admin. Its user_id is bound
-- separately, after that account has signed up and confirmed its email.
delete from private.keeplyn_admins where email <> 'support@keeplyn.com';

insert into private.keeplyn_admins (email)
values ('support@keeplyn.com')
on conflict (email) do nothing;
