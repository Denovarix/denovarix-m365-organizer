"""Thin Microsoft Graph client for personal (consumer) Microsoft accounts.

Auth: MSAL device-code flow, public client, token cache on disk.
Everything else is plain requests against https://graph.microsoft.com/v1.0.
"""
import atexit, json, os, sys, time
import msal, requests

GRAPH = "https://graph.microsoft.com/v1.0"
SCOPES = ["Mail.ReadWrite", "MailboxSettings.ReadWrite", "Files.ReadWrite.All", "User.Read"]
CONFIG_DIR = os.path.expanduser(os.environ.get("M365_ORGANIZER_DIR", "~/.m365-organizer"))


def _config():
    p = os.path.join(CONFIG_DIR, "config.json")
    cfg = json.load(open(p)) if os.path.exists(p) else {}
    cid = os.environ.get("M365_CLIENT_ID") or cfg.get("client_id")
    if not cid:
        sys.exit(f"Set client_id in {p} or M365_CLIENT_ID (Entra app, 'Personal Microsoft accounts only', public client flows on).")
    return cid, cfg.get("tenant_id", "consumers")


class Graph:
    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        cid, tenant = _config()
        self.cache_path = os.path.join(CONFIG_DIR, "token_cache.bin")
        self.cache = msal.SerializableTokenCache()
        if os.path.exists(self.cache_path):
            self.cache.deserialize(open(self.cache_path).read())
        atexit.register(self._save)
        self.app = msal.PublicClientApplication(cid, authority=f"https://login.microsoftonline.com/{tenant}", token_cache=self.cache)
        self.s = requests.Session()

    def _save(self):
        if self.cache.has_state_changed:
            open(self.cache_path, "w").write(self.cache.serialize())

    def token(self):
        acc = self.app.get_accounts()
        r = self.app.acquire_token_silent(SCOPES, account=acc[0]) if acc else None
        if not r:
            flow = self.app.initiate_device_flow(scopes=SCOPES)
            print(flow["message"], file=sys.stderr, flush=True)
            r = self.app.acquire_token_by_device_flow(flow)
        if "access_token" not in r:
            sys.exit(json.dumps(r, indent=1))
        self._save()
        return r["access_token"]

    def req(self, method, url, **kw):
        if not url.startswith("http"):
            url = GRAPH + url
        for attempt in range(6):
            r = self.s.request(method, url, headers={"Authorization": "Bearer " + self.token(), **kw.pop("headers", {})}, **kw)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(float(r.headers.get("Retry-After", 2 ** attempt)))
                continue
            if r.status_code >= 400:
                raise RuntimeError(f"{method} {url} -> {r.status_code}: {r.text[:500]}")
            return r.json() if r.content else {}
        raise RuntimeError(f"gave up on {url}")

    def get(self, url, **kw):  return self.req("GET", url, **kw)
    def post(self, url, body):  return self.req("POST", url, json=body)
    def patch(self, url, body): return self.req("PATCH", url, json=body)
    def delete(self, url):      return self.req("DELETE", url)

    def pages(self, url, limit=None):
        """Iterate every item of a paged collection."""
        n = 0
        while url:
            data = self.get(url)
            for item in data.get("value", []):
                yield item
                n += 1
                if limit and n >= limit:
                    return
            url = data.get("@odata.nextLink")

    def batch(self, requests_, size=20):
        """Run JSON-batch requests ([{id,method,url,body?}]), 20 per call. Returns list of responses."""
        out = []
        for i in range(0, len(requests_), size):
            chunk = requests_[i:i + size]
            for c in chunk:
                if "body" in c:
                    c["headers"] = {"Content-Type": "application/json"}
            res = self.post("/$batch", {"requests": chunk})
            out.extend(res["responses"])
            retry = [c for c, r in zip(chunk, res["responses"]) if r["status"] == 429]
            if retry:
                time.sleep(3)
                out.extend(self.batch(retry, size))
        return out
