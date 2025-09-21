# lib/openai_client.py (표준화된 최종 버전)
import os

from openai import OpenAI

try:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except Exception as e:
    print(f" OpenAI 클라이언트 초기화 실패: {e}")
    client = None


def get_completion(messages: list) -> str:
    """OpenAI ChatGPT API를 호출하여 응답을 반환합니다. (표준 함수명)"""
    if not client:
        return "오류: OpenAI 클라이언트가 초기화되지 않았습니다. API 키를 확인하세요."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages  # 범용 채팅 모델
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"오류: OpenAI API 호출 중 문제가 발생했습니다: {e}"


def chat_completion(messages: list) -> str:
    """기존 코드와의 호환성을 위한 함수"""
    print("Warning: chat_completion() is deprecated. Please use get_completion().")
    return get_completion(messages)
