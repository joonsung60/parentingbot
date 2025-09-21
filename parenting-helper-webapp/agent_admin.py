# parenting-helper-webapp/agent_admin.py (debate 모드 UI 추가)
import os
import re
import sys

import streamlit as st

# --- Agent_I의 함수들을 가져오기 위한 경로 설정 ---
webapp_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(webapp_root)

# debate 모드 핸들러까지 import
from scripts.agent_i import handle_debate_mode, handle_debug_mode, handle_propose_mode

# --- 유틸리티 함수 ---
PROMPTS_DIR = os.path.join(webapp_root, "prompts")
AVAILABLE_MODELS = [
    "gpt-4o-mini",
    "claude-3-sonnet-20240229",
    "gemini-1.5-flash-latest",
    "deepseek-chat",
]


def get_persona_files():
    if not os.path.exists(PROMPTS_DIR):
        return []
    return [f for f in os.listdir(PROMPTS_DIR) if f.endswith((".yml", ".yaml"))]


# --- Streamlit UI 구성 ---
st.set_page_config(layout="wide")
st.title("🕵️ Agent_I: AI 페르소나 디버거 & 튜너")

# --- 1. 페르소나 및 실패 사례 입력 ---
st.header("1. 분석 대상 입력")
col_a, col_b = st.columns(2)
with col_a:
    persona_files = get_persona_files()
    if not persona_files:
        st.error(f"'{PROMPTS_DIR}' 폴더에 페르소나 파일이 없습니다.")
        st.stop()
    selected_persona_file = st.selectbox("페르소나 선택", options=persona_files)
    selected_persona_path = os.path.join(PROMPTS_DIR, selected_persona_file)

with col_b:
    # 이 부분은 나중에 debate 모드 UI에서 재사용됩니다.
    st.session_state.user_input = st.text_area(
        "사용자 입력 (Input)", height=100, key="user_input_main"
    )
    st.session_state.bad_output = st.text_area(
        "실제 출력물 (Bad Output)", height=150, key="bad_output_main"
    )

st.divider()

# --- 2. 진단 및 토론 실행 ---
st.header("2. 진단 실행")

# --- 2a. 단일 모델 진단 ---
st.subheader("단일 모델 빠른 진단")
selected_model = st.selectbox("진단할 모델 선택", options=AVAILABLE_MODELS)

if st.button("🕵️ 원인 진단 실행 (Debug)"):
    if not st.session_state.user_input or not st.session_state.bad_output:
        st.warning("사용자 입력과 실제 출력물을 모두 입력해주세요.")
    else:
        with st.spinner(f"{selected_model}(이)가 실패 원인을 분석 중입니다..."):
            report = handle_debug_mode(
                selected_persona_path,
                st.session_state.user_input,
                st.session_state.bad_output,
                selected_model,
            )
            st.session_state.diagnosis_report = report
            st.session_state.debate_report = None  # 다른 리포트는 초기화

# --- 2b. 전문가 패널 토론 ---
st.subheader("전문가 패널 토론")
selected_debaters = st.multiselect(
    "토론에 참여할 모델(코치진)을 모두 선택하세요.",
    options=AVAILABLE_MODELS,
    default=[
        "claude-3-5-haiku",
        "gemini-1.5-flash-latest",
        "gpt-4o-mini",
        "deepseek-chat",
    ],
)

if st.button("👨‍🏫 전문가 패널 토론 실행 (Debate)"):
    if not st.session_state.user_input or not st.session_state.bad_output:
        st.warning("사용자 입력과 실제 출력물을 모두 입력해주세요.")
    elif len(selected_debaters) < 2:
        st.warning("토론을 위해 최소 2개 이상의 모델을 선택해주세요.")
    else:
        # debate 모드를 실행하기 위한 args 객체 시뮬레이션
        class Args:
            pass

        args = Args()
        args.persona = selected_persona_path
        args.input = st.session_state.user_input
        args.output = st.session_state.bad_output
        args.models = selected_debaters

        with st.spinner("전문가 패널이 토론을 시작합니다... (시간이 걸릴 수 있습니다)"):
            # debate 핸들러는 직접 호출하지 않고, 결과물을 파일로 받거나 스트리밍하는 방식이 더 안정적일 수 있으나
            # 현재 구조에서는 print를 리디렉션하여 결과를 가져오는 방식으로 구현합니다.
            import contextlib
            from io import StringIO

            output_buffer = StringIO()
            with contextlib.redirect_stdout(output_buffer):
                handle_debate_mode(args)

            debate_report = output_buffer.getvalue()
            st.session_state.debate_report = debate_report
            st.session_state.diagnosis_report = None  # 다른 리포트는 초기화

# --- 3. 진단/토론 결과 확인 ---
st.header("3. 결과 확인")
if st.session_state.get("diagnosis_report"):
    st.subheader("단일 모델 진단 결과")
    st.info(st.session_state.diagnosis_report)

if st.session_state.get("debate_report"):
    st.subheader("전문가 패널 토론 결과")
    with st.expander("전체 토론 내용 보기", expanded=True):
        st.markdown(st.session_state.debate_report)
