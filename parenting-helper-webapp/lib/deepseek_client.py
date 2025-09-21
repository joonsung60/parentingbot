# lib/deepseek_client.py
import os

from openai import OpenAI

try:
    client = OpenAI(
        api_key=os.environ.get("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com"
    )
except Exception as e:
    print(f" DeepSeek 클라이언트 초기화 실패: {e}")
    client = None


def get_completion(messages: list) -> str:
    """DeepSeek API를 호출하여 응답을 반환합니다."""
    if not client:
        return "오류: DeepSeek 클라이언트가 초기화되지 않았습니다. API 키를 확인하세요."

    try:
        response = client.chat.completions.create(
            model="deepseek-chat", messages=messages  # 범용 채팅 모델
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"오류: DeepSeek API 호출 중 문제가 발생했습니다: {e}"
