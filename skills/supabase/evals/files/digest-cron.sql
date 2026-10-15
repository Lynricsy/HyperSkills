-- Nightly digest trigger.
-- Since last week the scheduler uses its own secret key, created in Project Settings -> API Keys
-- with the name "scheduler" and stored in Vault as digest_scheduler_key, so we can rotate it
-- without touching the app's default secret key.
-- supabase/config.toml already has:
--   [functions.send-digest]
--   verify_jwt = false

select cron.schedule(
  'nightly-digest',
  '0 3 * * *',
  $$
  select net.http_post(
    url := 'https://abcdefghijklmnop.supabase.co/functions/v1/send-digest',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'apikey', (select decrypted_secret from vault.decrypted_secrets where name = 'digest_scheduler_key')
    ),
    body := '{}'::jsonb
  );
  $$
);
