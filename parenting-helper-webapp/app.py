# app.py (변경 핵심 부분만)
import streamlit as st
from datetime import datetime
from lib.openai_client import chat_completion
from lib.storage import (
    list_conversations, create_conversation, load_conversation,
    save_conversation, rename_conversation, delete_conversation, export_conversation
)
from lib.prompt_manager import get_prompts, get_system_prompt, select_prompt_id  # <<-- get_prompts 재사용

def add_message(role: str, content: str) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = {"role": role, "content": content, "ts": ts}
    st.session_state.messages.append(message)
    save_conversation(st.session_state.active_cid, st.session_state.messages)
    return ts

# --- 사이드바 ---
with st.sidebar:
    st.header("설정")
    with st.expander("개발자 도구: 프롬프트 선택", expanded=False):
        prompts = get_prompts()
        options = {p["id"]: p["name"] for p in prompts}
        selected_prompt_id = st.selectbox(
            "시스템 프롬프트(수동)",
            options=list(options.keys()),
            format_func=lambda x: options[x],
            index=0,
            key="prompt_selector"
        )
        st.checkbox("자동 선택(추천)", value=True, key="auto_route")
    age_months = st.number_input("아기 개월 수", 0, 72, 3)
    model = st.selectbox("OpenAI 모델 선택", ["gpt-4o-mini", "gpt-4o"])
    st.caption("의료 응급은 119/응급실 이용. 본 도구는 일반 정보용입니다.")

st.title("육아 도우미")

# --- 과거 메시지 렌더링 (system 제외 저장 구조라 그대로 표시) ---
for m in st.session_state.messages:
    role = "user" if m["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(m["content"])
        if m["role"] == "user" and m.get("ts"):
            st.caption(m["ts"])

# --- 입력/응답 ---
prompt = st.chat_input("예) 15주차, 밤중수유 간격과 낮잠 패턴이 궁금해요")
if prompt:
    user_text = f"[아기 {age_months}개월]\n{prompt}"
    ts = add_message("user", user_text)
    with st.chat_message("user"):
        st.markdown(user_text); st.caption(ts)

    # 라우팅: 자동 선택이 켜져 있으면 select_prompt_id, 아니면 수동 선택
    if st.session_state.get("auto_route", True):
        # 최근 6개 정도만 히스토리 텍스트로
        hist = "\n".join([m["content"] for m in st.session_state.messages[-6:] if m["role"] == "user"])
        last_route = st.session_state.get("router_prompt_id")
        chosen_id = select_prompt_id(user_text, hist, last_route=last_route)
    else:
        chosen_id = st.session_state["prompt_selector"]

    # 선택 결과를 세션에 저장(동점 시 이전 선택 유지용)
    st.session_state["router_prompt_id"] = chosen_id

    system_msg = get_system_prompt(chosen_id)

    # 저장된 메시지(사용자/어시스턴트만)를 붙임
    def _ua_only(msgs):
        return [m for m in msgs if m.get("role") in ("user", "assistant")]
    messages_for_api = [system_msg] + _ua_only(st.session_state.messages[-12:])

    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            answer = chat_completion(messages_for_api, model=model)
        st.markdown(answer)
    add_message("assistant", answer)
