"""MCP server exposing the organiser as tools. Run: m365-organizer serve"""
import json
from mcp.server.fastmcp import FastMCP
from .graph import Graph
from . import mail, drive

mcp = FastMCP("m365-organizer")
_g = None
def g():
    global _g
    if _g is None:
        _g = Graph()
    return _g


@mcp.tool()
def mail_folder_tree() -> str:
    """List every mail folder with its path, total and unread counts."""
    return json.dumps(mail.list_folders(g()), indent=1)

@mcp.tool()
def mail_create_folder(path: str) -> str:
    """Create a nested mail folder path like 'Work/Clients/Acme'. Returns the leaf id."""
    return mail.ensure_folder(g(), path)

@mcp.tool()
def mail_sender_stats(folder: str = "inbox", top: int = 40, sample: int = 0) -> str:
    """Top senders and domains in a folder. `sample` limits how many messages to scan (0 = all)."""
    a, d = mail.sender_stats(g(), folder, sample or None)
    return json.dumps({"addresses": a.most_common(top), "domains": d.most_common(top)}, indent=1)

@mcp.tool()
def mail_move_from_senders(senders: list[str], dest_path: str, folder: str = "inbox") -> str:
    """Bulk-move existing mail from addresses or '@domain' entries into dest_path (created if missing)."""
    return f"moved {mail.move_from_senders(g(), senders, dest_path, folder)}"

@mcp.tool()
def mail_list_rules() -> str:
    """List inbox rules."""
    return json.dumps(mail.list_rules(g()), indent=1)

@mcp.tool()
def mail_add_sender_rule(name: str, senders: list[str], dest_path: str, mark_read: bool = False) -> str:
    """Create an inbox rule routing future mail from senders/domains into dest_path."""
    return json.dumps(mail.add_sender_rule(g(), name, senders, dest_path, mark_read), indent=1)

@mcp.tool()
def mail_delete_rule(rule_id: str) -> str:
    """Delete an inbox rule."""
    mail.delete_rule(g(), rule_id); return "deleted"

@mcp.tool()
def drive_list(path: str = "") -> str:
    """List OneDrive items at a folder path ('' = root)."""
    return json.dumps(drive.list_items(g(), path), indent=1)

@mcp.tool()
def drive_create_folder(path: str) -> str:
    """Create a nested OneDrive folder path. Returns id."""
    return drive.ensure_folder(g(), path)

@mcp.tool()
def drive_move(item_id: str, dest_path: str, new_name: str = "") -> str:
    """Move a OneDrive item into dest_path (created if missing)."""
    return json.dumps(drive.move_item(g(), item_id, drive.ensure_folder(g(), dest_path), new_name or None), indent=1)


def main():
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "serve"
    if cmd == "auth":
        g().token(); print("authenticated")
    elif cmd == "serve":
        mcp.run()
    else:
        sys.exit("usage: m365-organizer [auth|serve]")

if __name__ == "__main__":
    main()
