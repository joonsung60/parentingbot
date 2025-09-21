# lib/gemini_client.py
import os

import google.generativeai as genai

try:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")  # 범용 채팅 모델
except Exception as e:
    print(f" Gemini 클라이언트 초기화 실패: {e}")
    model = None


def get_completion(messages: list) -> str:
    """Gemini API를 호출하여 응답을 반환합니다."""
    if not model:
        return "오류: Gemini 클라이언트가 초기화되지 않았습니다. API 키를 확인하세요."

    # OpenAI/Anthropic 형식의 messages를 Gemini 형식으로 변환
    gemini_messages = []
    system_instruction = ""
    for msg in messages:
        if msg["role"] == "system":
            system_instruction = msg["content"]
            continue
        gemini_messages.append(
            {
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [msg["content"]],
            }
        )

    # 마지막 메시지는 프롬프트로 사용하므로 히스토리에서 제거
    last_user_prompt = ""
    if gemini_messages and gemini_messages[-1]["role"] == "user":
        last_user_prompt = gemini_messages.pop()["parts"][0]

    try:
        chat_session = model.start_chat(history=gemini_messages)
        full_prompt = (
            (system_instruction + "\n\n---\n\n" + last_user_prompt)
            if system_instruction
            else last_user_prompt
        )

        response = chat_session.send_message(full_prompt)
        return response.text
    except Exception as e:
        return f"오류: Gemini API 호출 중 문제가 발생했습니다: {e}"
