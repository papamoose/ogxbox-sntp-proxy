# ogxbox-sntp-proxy
Proxies SNTP to an NTP server. The purpose of this was to allow original Xboxes to get time updates without them having a proper NTP client.

I'm not sure I'd recommend anyone actually use this. This is more of a proof of concept than a real tool.

## Install

On a linux system with systemd.

1. Create an `sntpd` user
1. Deploy `sntp_proxy.py` to wherever you want. e.g. `/usr/local/sbin/sntp_proxy.py`
1. Deploy the systemd unit file to `/etc/systemd/system/sntp-proxy.service`
1. Edit `ExecStart=` to the path you deployed the proxy to.
1. Edit the NTP server variable at the top of `sntp_proxy.py` to a real NTP server.
1. `systemctl daemon-reload`
1. `systemctl enable --now sntp-proxy.service`
