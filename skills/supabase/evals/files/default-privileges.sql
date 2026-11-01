-- 20261101_lock_down_new_objects.sql
-- Goal: new tables and functions in public must NOT be reachable through the Data API until a later
-- migration grants them explicitly. Existing objects keep their current grants.

alter default privileges for role postgres in schema public
  revoke select, insert, update, delete on tables from anon, authenticated;

alter default privileges for role postgres in schema public
  revoke execute on functions from public;

alter default privileges for role postgres in schema public
  revoke execute on functions from anon, authenticated;

-- Sanity check we ran after applying it:
--   create table public.probe (id int);
--   select grantee, privilege_type from information_schema.role_table_grants where table_name = 'probe';
-- returned nothing for SELECT/INSERT/UPDATE/DELETE, so we considered it done.
