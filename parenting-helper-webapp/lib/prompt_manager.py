# lib/prompt_manager.py
import os, re, yaml
from typing import List, Dict, Any

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")

def get_prompts() -> List[Dict[str, Any]]:
    prompts = []
    for filename in os.listdir(PROMPTS_DIR):
        if filename.endswith((".yml", ".yaml")):
            filepath = os.path.join(PROMPTS_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            data.setdefault("id", os.path.splitext(filename)[0])
            prompts.append(data)
    return sorted(prompts, key=lambda x: x.get("name", ""))

def get_system_prompt(prompt_id: str) -> Dict[str, Any]:
    for p in get_prompts():
        if p.get("id") == prompt_id:
            return {"role": "system", "content": p.get("content", "")}
    # fallback (가능하면 사용되지 않도록)
    return {"role": "system", "content": "너는 유용한 육아 도우미 AI야."}

# === 간단 라우터 ===
_EMERGENCY = r"(응급|119|ER|호흡곤란|무호흡|청색증|탈수|경련|의식 소실)"
_SOOTHING_POS = r"(위로|격려|지쳐|힘들|자책|불안|좌절|위안|토닥|마음이|멘탈)"
_INFO_POS = r"(수유|분유|모유|낮잠|수면|스케줄|발진|아토피|예방접종|체온|변|가이드|권고|개월|주수)"

def select_prompt_id(user_text: str, history_text: str = "") -> str:
    text = f"{history_text}\n{user_text}".lower()
    if re.search(_EMERGENCY, text, flags=re.IGNORECASE):
        return "parenting_expert_v1"   # 응급 단어는 정보 전문가로 고정
    s_score = len(re.findall(_SOOTHING_POS, text))
    i_score = len(re.findall(_INFO_POS, text))
    if s_score > i_score:
        return "soothing_expert_v1"
    return "parenting_expert_v1"
