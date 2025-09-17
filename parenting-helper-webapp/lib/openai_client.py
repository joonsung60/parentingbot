# lib/openai_client.py 수정 제안
import os
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI, APIError # APIError 추가

load_dotenv()

# 모듈 레벨에서 클라이언트 인스턴스 생성
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except TypeError:
    raise RuntimeError("OPENAI_API_KEY가 없습니다. .env 또는 환경변수 설정을 확인하세요.")


def chat_completion(messages: List[Dict], model: str = "gpt-4o-mini", temperature: float = 0.0) -> str:
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()
    except APIError as e:
        # API 호출 실패 시 사용자에게 보여줄 에러 메시지 반환
        return f"OpenAI API 호출 중 오류가 발생했습니다: {e}"
    except Exception as e:
        return f"알 수 없는 오류가 발생했습니다: {e}"