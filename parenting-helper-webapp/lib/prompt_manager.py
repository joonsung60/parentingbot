# lib/prompt_manager.py
import os
import yaml
from typing import List, Dict, Any

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")

def get_prompts() -> List[Dict[str, Any]]:
    """prompts 폴더의 모든 프롬프트 파일 정보를 불러옵니다."""
    prompts = []
    for filename in os.listdir(PROMPTS_DIR):
        if filename.endswith(".yml") or filename.endswith(".yaml"):
            filepath = os.path.join(PROMPTS_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    prompt_data = yaml.safe_load(f)
                    # 파일명에서 확장자를 제거하여 기본 id로 사용 가능
                    prompt_data.setdefault('id', os.path.splitext(filename)[0])
                    prompts.append(prompt_data)
                except yaml.YAMLError as e:
                    print(f"Error loading prompt file {filename}: {e}")
    # 이름순으로 정렬하여 일관된 순서 유지
    return sorted(prompts, key=lambda x: x.get('name', ''))

def get_system_prompt(prompt_id: str) -> Dict[str, Any]:
    """주어진 ID에 해당하는 시스템 프롬프트 내용을 반환합니다."""
    prompts = get_prompts()
    for p in prompts:
        if p.get('id') == prompt_id:
            return {"role": "system", "content": p.get('content', '')}
    # 기본 프롬프트 반환 또는 에러 처리
    return {"role": "system", "content": "너는 유용한 육아 도우미 AI야."}