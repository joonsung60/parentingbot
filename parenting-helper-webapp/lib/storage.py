# lib/storage.py
import json, os, uuid, datetime
from typing import List, Dict

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CONV_DIR = os.path.join(DATA_DIR, "conversations")
INDEX_PATH = os.path.join(CONV_DIR, "index.json")
os.makedirs(CONV_DIR, exist_ok=True)

def _now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _conv_path(cid: str) -> str:
    return os.path.join(CONV_DIR, f"{cid}.json")

def _load_index() -> Dict:
    if not os.path.exists(INDEX_PATH):
        return {"order": [], "conversations": {}}
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"order": [], "conversations": {}}

def _save_index(idx: Dict) -> None:
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)

def list_conversations() -> List[Dict]:
    idx = _load_index()
    res = []
    for cid in idx.get("order", [])[::-1]:
        meta = idx["conversations"].get(cid, {})
        res.append({
            "id": cid,
            "title": meta.get("title", "새 대화"),
            "updated_at": meta.get("updated_at", ""),
            "last_preview": meta.get("last_preview", ""),
        })
    return res

def create_conversation(title: str = "새 대화") -> str:
    cid = uuid.uuid4().hex[:12]
    messages: List[Dict] = []  # <<-- 시스템 메시지 제거
    with open(_conv_path(cid), "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    idx = _load_index()
    idx["conversations"][cid] = {
        "title": title,
        "updated_at": _now_iso(),
        "last_preview": "",
    }
    idx["order"] = list(dict.fromkeys(idx.get("order", []) + [cid]))
    _save_index(idx)
    return cid

def load_conversation(cid: str) -> List[Dict]:
    if not os.path.exists(_conv_path(cid)):
        return []
    with open(_conv_path(cid), "r", encoding="utf-8") as f:
        return json.load(f)

def save_conversation(cid: str, messages: List[Dict]) -> None:
    with open(_conv_path(cid), "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

    preview = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            preview = m.get("content", "").replace("\n", " ")[:80]
            break
    idx = _load_index()
    meta = idx["conversations"].setdefault(cid, {"title": "새 대화"})
    meta["updated_at"] = _now_iso()
    meta["last_preview"] = preview
    _save_index(idx)