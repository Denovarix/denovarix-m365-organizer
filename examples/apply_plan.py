"""Apply a folder plan: create folders, add inbox rules for future mail, bulk-move the backlog.

    python examples/apply_plan.py examples/plan.example.json [--no-move]

Plan format: {"Folder/Subfolder": ["@domain.com", "person@example.com", ...], ...}
"""
import json, sys, time
from m365_organizer.graph import Graph
from m365_organizer import mail

plan = json.load(open(sys.argv[1]))
do_move = "--no-move" not in sys.argv
g = Graph()
folders = mail.list_folders(g)
existing_rules = {r["displayName"] for r in mail.list_rules(g)}
for path, senders in plan.items():
    fid = mail.ensure_folder(g, path, folders)
    name = "Auto: " + path.replace("/", " / ")
    if name not in existing_rules:
        mail.add_sender_rule(g, name, senders, path)
    print(f"[ok] folder+rule  {path}", flush=True)
if do_move:
    for path, senders in plan.items():
        t = time.time()
        n = mail.move_from_senders(g, senders, path)
        print(f"[moved] {n:6d} -> {path}  ({time.time()-t:.0f}s)", flush=True)
print("done", flush=True)
