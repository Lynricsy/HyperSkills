# Network diagnosis and recoverable remote changes

Verified against: systemd 261.2; OpenSSH sshd(8); nftables nft(8).

## Contents

- Observe the path the client actually uses
- SSH configuration and fresh-session verification
- Firewall transaction and rollback
- Routing and resolver persistence
- TLS is an endpoint property

## Observe the path the client actually uses

Separate name resolution, route selection, packet filtering, listening socket,
TLS and application response. A failure at one layer does not justify changing
all of them. Bind results to client, destination IP, family, port and time.

Start with the application's resolver view (`getent ahosts NAME` for an NSS
consumer), active resolver configuration, listeners (`ss -lntp` with permitted
visibility), addresses and routes (`ip address`, `ip route`, `ip -6 route`).
For policy routing, include rules and route lookup toward the management client
with the relevant source. An application's private network namespace or its own
DNS cache may differ from the host shell.

A direct DNS query and an NSS lookup measure different paths. Compare the
configured resolver's A/AAAA responses, search domains and split-DNS routing;
a public resolver giving a different answer is not proof of local corruption.
Do not overwrite resolv.conf before identifying whether NetworkManager,
systemd-resolved or another manager owns it. Redact internal topology when
reporting externally; do not query public resolvers with private names casually.

Capture a bounded packet trace only when the path remains ambiguous and capture
is authorized. Limit interface, endpoint, duration and payload exposure; store
it as sensitive evidence. Avoid broad indefinite capture as the default probe.

## SSH configuration and fresh-session verification

[community] Preserve the useful distinctions from the SSH upstream: configured
HostName, User, Port, IdentityFile and ProxyJump form the connection path. A
local-forward destination is reached from the SSH server, not from the client.
Do not enable agent forwarding or expose a forwarded listener to all interfaces
as a shortcut. Keep host-key verification; an unexpected changed key needs a
trusted out-of-band fingerprint check, not automatic known_hosts deletion.

[official] `sshd -t -f CANDIDATE` checks syntax and host-key sanity;
`sshd -T -f CANDIDATE -C user=USER,addr=CLIENT_IP,host=CLIENT_NAME,laddr=SERVER_IP,lport=PORT`
checks effective configuration for the supplied connection, including Match.
Use actual installed paths and supported flags. This is validation, not proof
that authentication, PAM, authorized_keys or firewall access works.

Before disabling password/root access or changing ports, prove the replacement
non-root login and required privilege escalation in a new session. Inspect
socket activation and command-line overrides: a socket unit or sshd `-p` may own
the listener instead of the edited Port setting. Choose the distribution's actual
unit name rather than assuming sshd.service.

After authorized activation, keep the original session and open a distinct new
TCP connection; disable connection multiplexing for the probe, for example with
`ssh -o ControlMaster=no -o ControlPath=none` and the verified host configuration.
Preserve all identity checks. Reuse of a ControlMaster or an established firewall
flow does not test a new login. Exercise each intended management family/path.

## Firewall transaction and rollback

Use the existing firewall manager. A host with firewalld/UFW-generated rules is
not an invitation to install a competing direct nft ruleset. Identify other
writers and shared NAT/forwarding rules before editing. The relevant permission
is the host's network namespace, not whatever namespace a diagnostic shell has.

Before any policy, port or address change that can remove remote access:

1. Confirm host, interface, current SSH port, permitted source ranges and both
   address families; record required forwarding/NAT and business listeners.
2. Test an independent console/rescue path with credentials and a reachable
   operator. Another SSH window shares the failure path and is not sufficient.
3. Save both runtime rules and persistent files/includes with permissions and
   ownership, plus the manager's loading procedure. Confirm saved artifacts are
   complete and accessible to recovery, not only to the current SSH session.
4. Build a complete rollback transaction that restores the previous state,
   including removal of newly introduced objects. Replaying a listing over
   existing rules can duplicate or retain new rules; it is not necessarily a
   replacement. Restrict the rollback to the owned scope when others share it.
5. Arm a privileged local scheduler or manager job independent of the SSH
   process tree. Record job identity, deadline, exact saved artifact and log
   location; prove the job is pending and can execute. Rehearse restoration on
   an isolated equivalent ruleset or host. A shell sleep is not enough.
6. Validate the candidate and rollback with the installed manager. For direct
   nftables ownership, `nft -c -f CANDIDATE` checks validity without applying it;
   a check does not prove reachability. Apply the reviewed transaction, not an
   interactive flush followed by a sequence that leaves an unfiltered interval.
7. Test new SSH and required business connections externally on IPv4 and IPv6.
   Verify prohibited traffic remains prohibited, then validate persistent load
   inputs and only then disarm rollback and remove superseded access rules.

[official] nft `inet` tables can handle IPv4 and IPv6; family-specific address
expressions still need appropriate rules. Preserve loopback, established/related
traffic, intended new management/business access and required ICMP/ICMPv6,
including neighbor discovery and path-MTU control traffic. Do not apply an IPv6
default-drop policy copied from IPv4 without its control-plane requirements.

Syntax success and existing sessions are only partial evidence. A transient
rollback job may not survive reboot: defer reboot until committed configuration
is validated, or provide a boot-persistent recovery design and console procedure.
If rollback fires, verify both restored runtime and disk state before retrying.
Do not cancel it simply because the apply command returned zero.

## Routing and resolver persistence

Record routes, policy rules, addresses, DNS selection and their owning files or
profiles. An `ip route` runtime fix alone can disappear on restart; a profile
edit alone may leave the live path unchanged. Do not bounce a remote interface
to see what happens. Follow the same external-access and independent-rollback
contract as for a firewall change, including reactivation of the saved profile.

A rollback must restore the old address/routes/resolver configuration, not merely
bring the interface down. Where the installed manager offers timed confirmation,
use its supported mechanism and verify restoration afterward; do not assume its
existence guarantees recovery under every link, bridge or reboot condition.

## TLS is an endpoint property

[official] Verify each advertised A and AAAA endpoint with the same hostname and
SNI, checking SAN, validity time, trusted chain and the served certificate identity.
A IPv4-only check cannot exonerate a stale IPv6 listener. Use a validating client
with an address override that preserves the hostname; do not switch the URL to
an IP and then disable certificate verification. Check server time if validity
errors disagree with expected dates.

A TLS connection carrying SNI selects a certificate before HTTP Host processing.
A leaf file on disk or a helper reporting its serial is not proof of what the
long-running listener serves. Check complete chain delivery without relying on
an already cached intermediate. Keep private keys unreadable to unrelated users.

For renewal, record how publication changes file objects and what reload really
reloads. A single-file namespace bind can keep the old object despite a new host
pathname. Verify the main/worker process view and fresh, non-resumed handshakes
after activation. Do not repair endpoint identity with `curl -k`, blanket trust
changes or long-lived HSTS/preload before every affected name is known healthy.

<!-- sources: terminal-ssh, openssh-sshd, nft-manual, nginx-tls, systemd-exec -->
