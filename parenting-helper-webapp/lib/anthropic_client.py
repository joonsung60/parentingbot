# lib/anthropic_client.py
import os

import anthropic

try:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
except Exception as e:
    print(f" Anthropic 클라이언트 초기화 실패: {e}")
    client = None


def get_completion(messages: list) -> str:
    """Anthropic Claude API를 호출하여 응답을 반환합니다."""
    if not client:
        return (
            "오류: Anthropic 클라이언트가 초기화되지 않았습니다. API 키를 확인하세요."
        )

    system_prompt = ""
    user_messages = messages
    if messages and messages[0]["role"] == "system":
        system_prompt = messages[0]["content"]
        user_messages = messages[1:]

    try:
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",  # 범용 채팅 모델
            max_tokens=4096,
            system=system_prompt,
            messages=user_messages,
        )
        return message.content[0].text
    except Exception as e:
        return f"오류: Anthropic API 호출 중 문제가 발생했습니다: {e}"
