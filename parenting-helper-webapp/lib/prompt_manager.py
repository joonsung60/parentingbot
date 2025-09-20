# lib/prompt_manager.py
import os
import re
from typing import Any, Dict, List

import yaml

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
_EMERGENCY = r"(응급|119|ER|호흡곤란|무호흡|청색증|탈수|경련|의식\s*소실|심한\s*구토|피\s*섞인\s*변|35(\.\d+)?°?이하|40(\.\d+)?°?이상)"
_SOOTHING_POS = (
    r"(위로|격려|지쳐|힘들|버거워|자책|불안|좌절|멘탈|울컥|토닥|감정\s*정리)"
)
_INFO_POS = r"(모유|분유|수유|수면|낮잠|밤중수유|스케줄|계획|발진|아토피|체온|예방접종|변\s*색|트림|토|\b개월\b|\b주차\b|가이드|권고|루틴|졸업|스트랩|쪽쪽이)"


def select_prompt_id(
    user_text: str, history_text: str = "", last_route: str | None = None
) -> str:
    text = f"{history_text}\n{user_text}".lower()

    # 1) 응급 오버라이드
    if re.search(_EMERGENCY, text, flags=re.IGNORECASE):
        return "parenting_expert_v1"

    # 2) 점수 계산(가중치 가능)
    s_score = len(re.findall(_SOOTHING_POS, text, flags=re.IGNORECASE))
    i_score = len(re.findall(_INFO_POS, text, flags=re.IGNORECASE))

    # 3) 차이 기준
    if i_score - s_score >= 1:
        return "parenting_expert_v1"
    if s_score - i_score >= 1:
        return "soothing_expert_v1"

    # 4) 동점이면 직전 라우트 유지, 없으면 정보 도우미
    return last_route or "parenting_expert_v1"
