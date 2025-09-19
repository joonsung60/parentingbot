# lib/storage.py
import json, os, uuid, datetime
from typing import List, Dict, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CONV_DIR = os.path.join(DATA_DIR, "conversations")
INDEX_PATH = os.path.join(CONV_DIR, "index.json")

os.makedirs(CONV_DIR, exist_ok=True)

SYSTEM_MSG = {
    "role": "system",
    "content": ("당신의 육아 고민을 해결해드리겠습니다. 육아와 관련된 거라면 뭐든지 말해주세요.")
}

# ---------- 내부 유틸 ----------
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
        # 파일이 손상되었을 경우, 빈 인덱스를 반환하여 앱이 멈추지 않게 함
        return {"order": [], "conversations": {}}

def _save_index(idx: Dict) -> None:
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)

# ---------- 공개 API ----------
def list_conversations() -> List[Dict]:
    """대화 목록 반환 (최근순). [{id,title,updated_at,last_preview}]"""
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
    """새 대화 생성 후 ID 반환"""
    cid = uuid.uuid4().hex[:12]
    messages = [SYSTEM_MSG]
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
        return [SYSTEM_MSG]
    with open(_conv_path(cid), "r", encoding="utf-8") as f:
        return json.load(f)

def save_conversation(cid: str, messages: List[Dict]) -> None:
    with open(_conv_path(cid), "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    # 인덱스 메타 업데이트
    preview = ""
    for m in reversed(messages):
        if m["role"] == "user":
            preview = m["content"].replace("\n", " ")[:80]
            break
    idx = _load_index()
    meta = idx["conversations"].setdefault(cid, {"title": "새 대화"})
    meta["updated_at"] = _now_iso()
    meta["last_preview"] = preview
    _save_index(idx)

def rename_conversation(cid: str, new_title: str) -> None:
    idx = _load_index()
    if cid in idx["conversations"]:
        idx["conversations"][cid]["title"] = new_title.strip() or "제목 없음"
        _save_index(idx)

def delete_conversation(cid: str) -> None:
    # 파일 삭제
    path = _conv_path(cid)
    if os.path.exists(path):
        os.remove(path)
    # 인덱스에서 제거
    idx = _load_index()
    if cid in idx["conversations"]:
        del idx["conversations"][cid]
    if cid in idx.get("order", []):
        idx["order"].remove(cid)
    _save_index(idx)

def export_conversation(cid: str, fmt: str = "md") -> str:
    """대화를 Markdown 또는 JSON 파일로 내보내고 경로 반환"""
    msgs = load_conversation(cid)
    export_dir = os.path.join(DATA_DIR, "export")
    os.makedirs(export_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    if fmt == "json":
        out = os.path.join(export_dir, f"chat-{cid}-{ts}.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(msgs, f, ensure_ascii=False, indent=2)
    else:
        out = os.path.join(export_dir, f"chat-{cid}-{ts}.md")
        with open(out, "w", encoding="utf-8") as f:
            for m in msgs:
                role = m["role"]
                if role == "system":
                    f.write(f"### system\n{m['content']}\n\n")
                elif role == "user":
                    f.write(f"**User:** {m['content']}\n\n")
                else:
                    f.write(f"**Assistant:**\n{m['content']}\n\n")
    return out
