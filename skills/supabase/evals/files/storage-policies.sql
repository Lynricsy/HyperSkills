-- supabase/migrations/20260802141500_receipts_storage.sql
-- Bucket created in the dashboard with "Public bucket" left OFF.

insert into storage.buckets (id, name)
values ('receipts', 'receipts')
on conflict (id) do nothing;

create policy "users upload receipts"
  on storage.objects
  for insert
  to authenticated
  with check (
    bucket_id = 'receipts'
    and (storage.foldername(name))[1] = auth.uid()::text
  );
