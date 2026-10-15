# Security request: DLP and SSH auditing on Cloudflare One

Context: 800 employees, all on managed laptops with the Cloudflare One Client (traffic and DNS
mode, Exclude split tunnel). Gateway DNS and HTTP filtering are on. TLS decryption is **off**
today. We are on Zero Trust Enterprise. Google Workspace has been connected through API CASB
for a month; Microsoft 365 was connected this morning.

Asks from the CISO:

1. "Turn on DLP." We do not actually know which kinds of sensitive data (card numbers, national
   IDs, source code, customer exports) leave the company through the browser, or to which
   destinations. Legal wants to block uploads of customer exports to personal cloud storage
   eventually, but the helpdesk cannot absorb a wave of false positives.
2. "We need a log of every command engineers run over SSH on the production Linux hosts."
   Engineers currently reach those hosts through a Cloudflare Tunnel and a self-hosted Access
   application with their own static SSH keys. The previous consultant's notes say to add a
   Gateway Network policy with the **Audit SSH** action.
3. Someone asked why the CASB dashboard still shows no findings for Microsoft 365 a few hours
   after connecting it.

Give us the plan: what to enable in which order, what each step depends on, and what to tell
the CISO about each ask.
