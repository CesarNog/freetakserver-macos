import socket, ssl, sys, time, urllib.request

HOST = "127.0.0.1"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

def cot_ok():
    # Docker accepts on published ports before the service listens; a real listener keeps the socket open
    s = socket.create_connection((HOST, 8087), timeout=3)
    s.settimeout(1.5)
    try:
        return s.recv(1) != b""
    except socket.timeout:
        return True
    except OSError:
        return False
    finally:
        s.close()

def http_ok(url, **kw):
    return urllib.request.urlopen(url, timeout=3, **kw).status == 200

checks = {
    "cot 8087": cot_ok,
    "https 8443": lambda: http_ok(f"https://{HOST}:8443/", context=ctx),
    "api 19023": lambda: http_ok(f"http://{HOST}:19023/"),
}
deadline = time.time() + int(sys.argv[1] if len(sys.argv) > 1 else 180)
pending = dict(checks)
while pending and time.time() < deadline:
    for name, fn in list(pending.items()):
        try:
            if fn():
                del pending[name]
        except OSError:
            pass
    if pending:
        time.sleep(2)
if pending:
    print("not ready:", ", ".join(pending), file=sys.stderr)
    sys.exit(1)
print("ready")
