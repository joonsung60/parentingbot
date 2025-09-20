from datetime import datetime

import streamlit as st

# --- 내부 모듈 임포트 ---
from lib.openai_client import chat_completion
from lib.prompt_manager import get_prompts, get_system_prompt, select_prompt_id
from lib.storage import (
    create_conversation,
    delete_conversation,
    export_conversation,
    list_conversations,
    load_conversation,
    rename_conversation,
    save_conversation,
)

# =========================
# Session bootstrap
# =========================
# 대화 ID / 메시지 초기화
if "active_cid" not in st.session_state:
    convs = list_conversations()
    if convs:
        st.session_state.active_cid = convs[0]["id"]
        st.session_state.messages = load_conversation(st.session_state.active_cid)
    else:
        st.session_state.active_cid = create_conversation("새 대화")
        st.session_state.messages = []

if "messages" not in st.session_state or not isinstance(
    st.session_state.messages, list
):
    st.session_state.messages = []

# 라우팅 기본값
st.session_state.setdefault("router_prompt_id", None)
st.session_state.setdefault("auto_route", True)


# =========================
# 유틸
# =========================
def _safe_rerun():
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()


def add_message(role: str, content: str) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    st.session_state.messages.append({"role": role, "content": content, "ts": ts})
    save_conversation(st.session_state.active_cid, st.session_state.messages)
    return ts


def ua_only(msgs):
    return [m for m in msgs if m.get("role") in ("user", "assistant")]


# =========================
# 사이드바
# =========================
with st.sidebar:
    st.header("설정")

    # 프롬프트 목록 (비어 있어도 안전하게 동작)
    prompts = get_prompts()  # [{id,name,content}, ...]
    prompt_ids = [p["id"] for p in prompts] or ["parenting_expert_v1"]
    prompt_names = {p["id"]: p.get("name", p["id"]) for p in prompts}

    with st.expander("개발자 도구: 프롬프트 선택", expanded=False):
        st.selectbox(
            "시스템 프롬프트(수동)",
            options=prompt_ids,
            format_func=lambda x: prompt_names.get(x, x),
            key="prompt_selector",
            index=0,
        )
        st.checkbox("자동 선택(추천)", value=True, key="auto_route")
        # 현재 자동 선택 결과 표시(있을 때만)
        if st.session_state.get("router_prompt_id"):
            st.caption(f"자동 선택: {st.session_state['router_prompt_id']}")

    age_months = st.number_input("아기 개월 수", min_value=0, max_value=72, value=3)
    st.caption("의료 응급은 119/응급실 이용. 본 도구는 일반 정보용입니다.")

    # === 사이드바: 대화 ===
    st.divider()
    st.subheader("대화")

    convs = list_conversations()
    options = {
        c["id"]: f'{c.get("title","새 대화")} · {c.get("updated_at","")}' for c in convs
    }

    if convs:
        try:
            default_idx = next(
                i for i, c in enumerate(convs) if c["id"] == st.session_state.active_cid
            )
        except StopIteration:
            default_idx = 0

        selected_cid = st.selectbox(
            "대화 선택",
            options=list(options.keys()),
            format_func=lambda cid: options[cid],
            index=default_idx,
            label_visibility="collapsed",
            key="conv_selector",
        )
        if selected_cid != st.session_state.active_cid:
            st.session_state.active_cid = selected_cid
            st.session_state.messages = load_conversation(selected_cid)
            _safe_rerun()
    else:
        st.caption("저장된 대화가 없습니다.")

    # ---- 버튼: 2줄(2×2) 배치 ----
    # 1줄: 새 대화 | 이름 변경
    r1c1, r1c2 = st.columns(2, gap="small")
    with r1c1:
        if st.button("새 대화", use_container_width=True, key="btn_new"):
            new_id = create_conversation("새 대화")
            st.session_state.active_cid = new_id
            st.session_state.messages = []
            _safe_rerun()
    with r1c2:
        if st.button("이름 변경", use_container_width=True, key="btn_rename_toggle"):
            st.session_state["show_rename"] = not st.session_state.get(
                "show_rename", False
            )

    # 2줄: 내보내기 | 삭제
    r2c1, r2c2 = st.columns(2, gap="small")
    with r2c1:
        if st.button("내보내기", use_container_width=True, key="btn_export"):
            out = export_conversation(st.session_state.active_cid)
            st.success(f"아카이브로 저장됨: {out}")
    with r2c2:
        if st.button(
            "삭제", use_container_width=True, type="secondary", key="btn_delete"
        ):
            st.session_state["confirm_delete"] = True

    # ---- 이름 변경 폼(토글 시 노출) ----
    if st.session_state.get("show_rename", False) and convs:
        current_title = next(
            (c["title"] for c in convs if c["id"] == st.session_state.active_cid),
            "새 대화",
        )
        with st.form("rename_form", clear_on_submit=True):
            new_title = st.text_input("새 제목", value=current_title)
            cc1, cc2 = st.columns(2, gap="small")
            save = cc1.form_submit_button("저장")
            cancel = cc2.form_submit_button("취소", type="secondary")
            if save:
                rename_conversation(
                    st.session_state.active_cid, new_title.strip() or "새 대화"
                )
                st.session_state["show_rename"] = False
                _safe_rerun()
            elif cancel:
                st.session_state["show_rename"] = False

    # ---- 삭제 확인(간단 확인 폼) ----
    if st.session_state.get("confirm_delete"):
        with st.form("confirm_delete_form", clear_on_submit=True):
            st.write("이 대화를 삭제할까요? 되돌릴 수 없습니다.")
            dc1, dc2 = st.columns(2, gap="small")
            yes = dc1.form_submit_button("삭제")
            no = dc2.form_submit_button("취소", type="secondary")
            if yes:
                delete_conversation(st.session_state.active_cid)
                left = list_conversations()
                if left:
                    st.session_state.active_cid = left[0]["id"]
                    st.session_state.messages = load_conversation(left[0]["id"])
                else:
                    st.session_state.active_cid = create_conversation("새 대화")
                    st.session_state.messages = []
                st.session_state["confirm_delete"] = False
                _safe_rerun()
            elif no:
                st.session_state["confirm_delete"] = False

# =========================
# 본문
# =========================
st.title("육아 도우미")

# 과거 메시지 렌더링
for m in st.session_state.get("messages", []):
    if m.get("role") not in ("user", "assistant"):
        continue  # system 등은 표시 안 함
    role = "user" if m["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(m.get("content", ""))
        if m["role"] == "user" and m.get("ts"):
            st.caption(m["ts"])

# 입력/응답
prompt = st.chat_input("예) 15주차, 밤중수유 간격과 낮잠 패턴이 궁금해요")
if prompt:
    user_text = f"[아기 {age_months}개월]\n{prompt}"
    ts = add_message("user", user_text)
    with st.chat_message("user"):
        st.markdown(user_text)
        st.caption(ts)

    # 라우팅: 자동 vs 수동
    if st.session_state.get("auto_route", True):
        hist = "\n".join(
            [
                m["content"]
                for m in st.session_state.messages[-6:]
                if m.get("role") == "user"
            ]
        )
        last_route = st.session_state.get("router_prompt_id")
        chosen_id = select_prompt_id(user_text, hist, last_route=last_route)
    else:
        chosen_id = st.session_state["prompt_selector"]

    st.session_state["router_prompt_id"] = chosen_id  # 동점 시 이전 선택 유지용
    system_msg = get_system_prompt(chosen_id)

    messages_for_api = [system_msg] + ua_only(st.session_state.messages[-12:])

    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            answer = chat_completion(messages_for_api)
        st.markdown(answer)
    add_message("assistant", answer)
