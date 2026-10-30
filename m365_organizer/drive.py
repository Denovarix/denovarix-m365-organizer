"""OneDrive helpers: list, make folders, move items."""
from .graph import Graph


def list_items(g: Graph, path=""):
    url = "/me/drive/root/children" if not path else f"/me/drive/root:/{path}:/children"
    return [{"id": i["id"], "name": i["name"], "folder": "folder" in i, "size": i.get("size", 0),
             "modified": i.get("lastModifiedDateTime"), "children": i.get("folder", {}).get("childCount")}
            for i in g.pages(url + "?$top=200")]


def ensure_folder(g: Graph, path: str):
    """Create nested folder path under root; returns id."""
    parent_url, parent_id = "/me/drive/root", "root"
    cur = ""
    for part in path.strip("/").split("/"):
        cur = f"{cur}/{part}" if cur else part
        try:
            item = g.get(f"/me/drive/root:/{cur}")
        except RuntimeError:
            item = g.post(f"/me/drive/items/{parent_id}/children", {"name": part, "folder": {}, "@microsoft.graph.conflictBehavior": "fail"})
        parent_id = item["id"]
    return parent_id


def move_item(g: Graph, item_id, dest_folder_id, new_name=None):
    body = {"parentReference": {"id": dest_folder_id}}
    if new_name:
        body["name"] = new_name
    return g.patch(f"/me/drive/items/{item_id}", body)
