# What the images in install-server.md show

Transcribed by the support team so reviewers do not need the image files.

- `img/welcome-email.png`: the welcome e-mail. The licence key is highlighted; its format is
  `LDG-XXXX-XXXX-XXXX` (letters and digits).
- `img/installer-type.png`: the installer's "Installation type" page with **Server (all
  components)** selected, not the default **Workstation**.
- `img/service-page.png`: the Service page. Fields: Service account `NT SERVICE\Ledgerly`;
  HTTPS port `8443`; the checkbox **Start automatically** ticked; the checkbox **Open
  firewall port** ticked.
- `img/ledgerly-conf.png`: Notepad showing three lines:
  `listen = 0.0.0.0:8443`, `data_dir = D:\LedgerlyData`, `backup_retention_days = 30`.
- `img/first-login.png`: a browser at `https://<server-name>:8443` showing the sign-in page
  with the heading "Welcome to Ledgerly".
- `img/troubleshooting-flowchart.png`: a flowchart. "Page does not load?" → "Is the
  Ledgerly service running in services.msc?" → no: "Start it; check the Windows event log
  for source Ledgerly" / yes: "Is port 8443 open in Windows Firewall?" → no: "Re-run the
  installer and tick Open firewall port".
