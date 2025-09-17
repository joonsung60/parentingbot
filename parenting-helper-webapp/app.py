import streamlit as st
import yaml
import os
from datetime import datetime
from lib.openai_client import chat_completion
from lib.storage import (
    list_conversations, create_conversation, load_conversation,
    save_conversation, rename_conversation, delete_conversation,
    export_conversation
)
from lib.prompt_manager import get_system_prompt

PROMPT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")

def get_prompts() -> List[Dict]:
    prompts = []
    for file in os.listdir(PROMPT_DIR):
        if file.endswith(".yml"):
            with open(os.path.join(PROMPT_DIR, file), "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                prompts.append({
                    "id": data.get("id", file.split(".")[0]),
                    "name": data.get("name", "Unnamed"),
                    "description": data.get("description", ""),
                    "content": data.get("content", "")
                })
    return prompts

def get_system_prompt(prompt_id: str) -> Dict:
    prompts = get_prompts()
    selected = next((p for p in prompts if p["id"] == prompt_id), None)
    if selected:
        return {"role": "system", "content": selected["content"]}
    return {"role": "system", "content": "기본 프롬프트입니다."}  # 폴백

st.set_page_config(page_title="육아 도우미 (Powered by ChatGPT)", layout="wide")

# ---------- 초기 세팅 ----------
if "active_cid" not in st.session_state:
    convs = list_conversations()
    if convs:
        st.session_state.active_cid = convs[0]["id"]
    else:
        st.session_state.active_cid = create_conversation("처음 대화")
if "messages" not in st.session_state:
    st.session_state.messages = load_conversation(st.session_state.active_cid)

# ---------- 사이드바 ----------
with st.sidebar:
    st.header("설정")
    
    # --- 프롬프트 선택기 (개발용) ---
    with st.expander("개발자 도구: 프롬프트 선택", expanded=False):
        prompts = get_prompts()
        prompt_options = {p['id']: p['name'] for p in prompts}

        selected_prompt_id = st.selectbox(
            "시스템 프롬프트 선택",
            options=list(prompt_options.keys()),
            format_func=lambda x: prompt_options[x],
            index=0, # 첫 번째 프롬프트를 기본값으로 설정
            key="prompt_selector"
        )
        # 선택된 프롬프트의 설명 표시
        selected_prompt_info = next((p for p in prompts if p['id'] == selected_prompt_id), None)
        if selected_prompt_info:
            st.caption(f"ℹ️ {selected_prompt_info.get('description', '설명 없음')}")
    
    age_months = st.number_input("아기 개월 수", 0, 72, 3)
    model = st.selectbox("OpenAI 모델 선택", ["gpt-4o-mini", "gpt-4o"])
    st.caption("의료 응급은 119/응급실 이용. 본 도구는 일반 정보용입니다.")

    st.divider()
    st.subheader("대화")
    convs = list_conversations()
    # 표시 문자열을 '제목'만 사용
    title_only = [c["title"] for c in convs] or ["(대화 없음)"]

    # 선택 인덱스 계산은 그대로
    idx = 0 if not convs else max(
        0,
        next(
            (i for i,c in enumerate(convs) if c["id"] == st.session_state.active_cid),
            0,
        )
    )

    sel = st.selectbox(
        "대화 선택",
        options=list(range(len(title_only))) or [0],
        format_func=lambda i: title_only[i] if convs else title_only[0],
        index=idx,
        key="conv_select"
    )

    if convs:
        chosen = convs[sel]
        if chosen["id"] != st.session_state.active_cid:
            st.session_state.active_cid = chosen["id"]
            st.session_state.messages = load_conversation(chosen["id"])
            st.rerun()

    colA, colB = st.columns(2)
    with colA:
        if st.button("🆕 새 대화"):
            new_id = create_conversation("새 대화")
            st.session_state.active_cid = new_id
            st.session_state.messages = load_conversation(new_id)
            st.rerun()
    with colB:
        if convs and st.button("🗑️ 삭제"):
            delete_conversation(st.session_state.active_cid)
            # 남은 대화로 이동 or 새로 생성
            left = list_conversations()
            if left:
                st.session_state.active_cid = left[0]["id"]
                st.session_state.messages = load_conversation(left[0]["id"])
            else:
                st.session_state.active_cid = create_conversation("처음 대화")
                st.session_state.messages = load_conversation(st.session_state.active_cid)
            st.rerun()

    if convs:
        new_title = st.text_input("제목 바꾸기", value=convs[sel]["title"], key="rename_title")
        if st.button("✏️ 이름 변경"):
            rename_conversation(st.session_state.active_cid, new_title)
            st.rerun()

# ---------- 본문 ----------
st.title("육아 도우미 (Powered by ChatGPT)")

# 기록 출력
for m in st.session_state.messages:
    role = "user" if m["role"] == "user" else ("assistant" if m["role"] == "assistant" else "assistant")
    with st.chat_message(role):
        st.markdown(m["content"])
        # 내가 입력한 메시지라면 시간 표시
        if m.get("role") == "user" and m.get("ts"):
            st.markdown(f"<div style='font-size:12px;color:#888'>{m.get('ts')}</div>", unsafe_allow_html=True)

# 입력/응답
prompt = st.chat_input("예) 15주차, 밤중수유 간격과 낮잠 패턴이 궁금해요")
if prompt:
    user_text = f"[아기 {age_months}개월]\n{prompt}"
    ts = add_message("user", user_text)   # append+save (사용자 메시지)
    with st.chat_message("user"):
        st.markdown(user_text)
        st.caption(ts)

    system_prompt_message = get_system_prompt(st.session_state.prompt_selector)
    messages_for_api = [system_prompt_message] + st.session_state.messages[-12:]

    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            answer = chat_completion(messages_for_api, model=model)
        st.markdown(answer)

    add_message("assistant", answer)      # append+save (어시스턴트 메시지)