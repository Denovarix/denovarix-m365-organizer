"""Mailbox organisation: folder trees, sender statistics, bulk moves, inbox rules."""
from collections import Counter
from .graph import Graph

WELL_KNOWN = {"inbox", "archive", "deleteditems", "junkemail", "sentitems", "drafts"}


def _fid(folder):
    return folder if folder.lower() in WELL_KNOWN or len(folder) > 40 else None


def list_folders(g: Graph, parent="msgFolderRoot"):
    """Return the whole folder tree as a flat list with 'path'."""
    out = []
    def walk(pid, prefix):
        for f in g.pages(f"/me/mailFolders/{pid}/childFolders?$top=200"):
            path = prefix + f["displayName"]
            out.append({"id": f["id"], "path": path, "total": f["totalItemCount"], "unread": f["unreadItemCount"]})
            if f["childFolderCount"]:
                walk(f["id"], path + "/")
    walk(parent, "")
    return out


def ensure_folder(g: Graph, path: str, folders=None):
    """Create 'A/B/C' (each level if missing). Returns the leaf folder id."""
    folders = folders if folders is not None else list_folders(g)
    by_path = {f["path"]: f["id"] for f in folders}
    parent, cur = "msgFolderRoot", ""
    for part in path.split("/"):
        cur = f"{cur}/{part}" if cur else part
        if cur not in by_path:
            f = g.post(f"/me/mailFolders/{parent}/childFolders", {"displayName": part})
            by_path[cur] = f["id"]
            folders.append({"id": f["id"], "path": cur, "total": 0, "unread": 0})
        parent = by_path[cur]
    return parent


def sender_stats(g: Graph, folder="inbox", limit=None):
    """Count messages per sender address and per domain. Returns (addresses, domains)."""
    addrs, domains = Counter(), Counter()
    url = f"/me/mailFolders/{folder}/messages?$select=from&$top=1000"
    for m in g.pages(url, limit):
        a = ((m.get("from") or {}).get("emailAddress") or {}).get("address", "").lower()
        if a:
            addrs[a] += 1
            domains[a.rsplit("@", 1)[-1]] += 1
    return addrs, domains


def message_ids(g: Graph, folder="inbox", filter=None, search=None):
    """Yield message ids in a folder matching an OData $filter or a $search string."""
    q = f"/me/mailFolders/{folder}/messages?$select=id&$top=1000"
    if filter:
        q += "&$filter=" + filter
    if search:
        q += f'&$search="{search}"'
    for m in g.pages(q):
        yield m["id"]


def move_messages(g: Graph, ids, dest_folder_id):
    """Move messages by id in JSON batches of 20. Returns count moved."""
    ids = list(ids)
    reqs = [{"id": str(i), "method": "POST", "url": f"/me/messages/{mid}/move", "body": {"destinationId": dest_folder_id}} for i, mid in enumerate(ids)]
    res = g.batch(reqs)
    return sum(1 for r in res if r["status"] in (200, 201))


def move_from_senders(g: Graph, senders, dest_path, folder="inbox"):
    """Move every message from any of `senders` (addresses or '@domain') into dest_path."""
    dest = ensure_folder(g, dest_path)
    moved = 0
    for s in senders:
        if s.startswith("@"):
            flt = f"contains(from/emailAddress/address,'{s}')"
        else:
            flt = f"from/emailAddress/address eq '{s}'"
        moved += move_messages(g, message_ids(g, folder, filter=flt), dest)
    return moved


def list_rules(g: Graph):
    return list(g.pages("/me/mailFolders/inbox/messageRules"))


def add_sender_rule(g: Graph, name, senders, dest_path, mark_read=False, stop=True):
    """Inbox rule: mail from senders/domains -> folder. Domains as '@example.com'."""
    dest = ensure_folder(g, dest_path)
    addresses = [s for s in senders if not s.startswith("@")]
    domains = [s for s in senders if s.startswith("@")]
    conditions = {}
    if addresses:
        conditions["fromAddresses"] = [{"emailAddress": {"address": a}} for a in addresses]
    if domains:
        conditions["senderContains"] = domains
    actions = {"moveToFolder": dest, "stopProcessingRules": stop}
    if mark_read:
        actions["markAsRead"] = True
    return g.post("/me/mailFolders/inbox/messageRules", {"displayName": name, "sequence": 1, "isEnabled": True, "conditions": conditions, "actions": actions})


def delete_rule(g: Graph, rule_id):
    g.delete(f"/me/mailFolders/inbox/messageRules/{rule_id}")
