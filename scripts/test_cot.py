import socket, sys, time, urllib.request, ssl
from datetime import datetime, timedelta, timezone

HOST = "127.0.0.1"

def event(uid, callsign):
    now = datetime.now(timezone.utc)
    f = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        f'<event version="2.0" uid="{uid}" type="a-f-G-U-C" how="m-g" '
        f'time="{f(now)}" start="{f(now)}" stale="{f(now + timedelta(hours=1))}">'
        '<point lat="38.7" lon="-9.1" hae="0" ce="9999999" le="9999999"/>'
        f'<detail><contact callsign="{callsign}"/></detail></event>'
    ).encode()

def drain(s):
    s.settimeout(1.5)
    out = b""
    try:
        while (d := s.recv(65536)):
            out += d
    except OSError:
        pass
    return out.decode(errors="replace")

a = socket.create_connection((HOST, 8087), timeout=5)
a.sendall(event("uid-A", "ALPHA")); time.sleep(2)
b = socket.create_connection((HOST, 8087), timeout=5)
b.sendall(event("uid-B", "BRAVO")); time.sleep(2)
drain(a); drain(b)
a.sendall(event("uid-A", "ALPHA")); time.sleep(2)
relay_ok = "uid-A" in drain(b)

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
https_ok = urllib.request.urlopen(f"https://{HOST}:8443/", context=ctx, timeout=5).status == 200
api_ok = urllib.request.urlopen(f"http://{HOST}:19023/", timeout=5).status == 200

print(f"CoT relay A->B: {relay_ok} | 8443 https: {https_ok} | 19023 api: {api_ok}")
sys.exit(0 if relay_ok and https_ok and api_ok else 1)
