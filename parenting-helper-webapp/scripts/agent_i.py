# scripts/agent_i.py (리팩토링 최종 완료)
import argparse
import os
import sys
import textwrap

from dotenv import load_dotenv

# --- 'lib' 디렉터리의 모듈을 가져오기 위한 경로 설정 ---
webapp_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(webapp_root, ".env")
load_dotenv(dotenv_path)
sys.path.append(webapp_root)

# --- 4개의 LLM 클라이언트 임포트 ---
from lib.anthropic_client import get_completion as anthropic_completion
from lib.deepseek_client import get_completion as deepseek_completion
from lib.gemini_client import get_completion as gemini_completion
from lib.openai_client import get_completion as openai_completion


def call_llm_by_name(model_name: str, messages: list):
    """모델 이름에 따라 적절한 클라이언트를 호출하는 라우터 함수"""
    print(f" M 모델 호출: {model_name}...")

    # 모델 이름에 따라 적절한 함수를 매핑
    if "gpt" in model_name.lower() or "openai" in model_name.lower():
        return openai_completion(messages)
    elif "claude" in model_name.lower():
        return anthropic_completion(messages)
    elif "gemini" in model_name.lower():
        return gemini_completion(messages)
    elif "deepseek" in model_name.lower():
        return deepseek_completion(messages)
    else:
        # 알 수 없는 모델명이면 기본값(OpenAI)으로 호출
        print(
            f"경고: 알 수 없는 모델 '{model_name}'. 기본값인 OpenAI GPT-4o-mini로 호출합니다."
        )
        return openai_completion(messages)


# --- [수정됨] 함수가 인자를 개별적으로 받도록 변경 ---
def handle_debug_mode(persona_path, user_input, bad_output, model_name):
    """'debug' 모드의 핵심 로직. 진단 리포트를 '반환'합니다."""
    print(f"🕵️  'debug' 모드 실행... {model_name}이 원인 진단을 시작합니다.")
    try:
        with open(persona_path, "r", encoding="utf-8") as f:
            persona_content = f.read()
    except FileNotFoundError:
        return f"❌ 오류: 페르소나 파일을 찾을 수 없습니다 -> {persona_path}"

    system_prompt = """
    당신은 LLM 페르소나의 문제점을 진단하는 '프롬프트 디버깅 전문 AI'입니다.
    주어진 정보를 바탕으로, 아래 [분석 단계]를 반드시 순서대로 따라 깊이 있게 사고하여 '진단 리포트'를 작성해야 합니다.
    [분석 단계]
    1. **사용자 의도 파악**: [사용자 입력]을 먼저 분석합니다. 이것이 긴급한 의학적 질문인지, 일반적인 정보 문의인지, 감정적 위로를 구하는 것인지 핵심 의도를 파악합니다.
    2. **출력물과 규칙 비교**: [사용자 의도]를 염두에 두고, [실제 출력물]이 [페르소나 규칙]의 각 항목(역할, 톤, 출력 형식 등)을 얼마나 잘 따랐는지, 혹은 위반했는지 구체적인 근거를 들어 비교 분석합니다.
    3. **핵심 원인 진단**: 1, 2단계 분석을 종합하여, 왜 이런 부정확하거나 아쉬운 결과가 나왔는지 근본적인 원인을 추론합니다. (예: 규칙 간의 충돌, 지시의 모호성, 불필요한 정보 포함 등)
    4. **실용적인 권장 조치**: 진단된 원인을 해결할 수 있는, 가장 효과적이고 구체적인 페르소나 수정안을 한 문장의 명확한 지시 형태로 제안합니다.
    [진단 리포트]
    (위 분석 단계에 따라 작성된 결과만 출력)
    """
    user_prompt = f"[페르소나 규칙]\n---\n{persona_content}\n---\n\n[사용자 입력]\n---\n{user_input}\n---\n\n[실제 출력물]\n---\n{bad_output}\n---"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    diagnosis_report = call_llm_by_name(model_name, messages)
    return diagnosis_report


# --- [수정됨] 함수가 인자를 개별적으로 받도록 변경 ---
def handle_propose_mode(goal, target_path, model_name):
    """'propose' 모드의 핵심 로직. 제안 내용과 저장 경로를 '반환'합니다."""
    print("✍️  'propose' 모드 실행... LLM이 수정안 제안을 시작합니다.")
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            original_content = f.read()
    except FileNotFoundError:
        return f"❌ 오류: 대상 파일을 찾을 수 없습니다 -> {target_path}", None

    system_prompt = """
    당신은 YAML 형식의 LLM 프롬프트 파일을 수정하는 전문 AI입니다.
    사용자의 '수정 목표'와 '원본 YAML 파일 내용'을 바탕으로, 목표를 가장 잘 달성할 수 있는 새로운 YAML 파일 내용을 생성해야 합니다.
    다른 설명 없이, 수정된 YAML 파일의 전체 내용만 코드 블록 없이 바로 출력해야 합니다.
    [ 매우 중요한 규칙 ]
    - '# 역할', '# 톤', '# 출력 형식' 등은 LLM에게 내리는 '지시문' 섹션입니다.
    - 절대로 이 '지시문' 섹션을 실제 응답 예시로 채우지 마십시오.
    - 당신의 임무는 지시문의 '내용'을 목표에 맞게 개선하는 것이지, 지시문을 수행한 예시를 작성하는 것이 아닙니다.
    """
    user_prompt = (
        f"[수정 목표]\n{goal}\n\n[원본 YAML 파일 내용]\n---\n{original_content}\n---"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    proposed_content = call_llm_by_name(model_name, messages)
    output_path = target_path + ".proposed"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(proposed_content)

    return proposed_content, output_path


def handle_debate_mode(args):
    """'debate' 모드. 여러 모델의 진단을 받고 교차 검증을 수행합니다."""
    print("🤖 'debate' 모드 실행... 전문가 패널 토론을 시작합니다.")

    # --- 1. 개별 의견 취합 ---
    initial_reports = {}
    print("\n--- [1단계: 개별 진단 리포트 취합] ---")
    # 참고: 실제 구현에서는 이 부분을 비동기(asyncio)나 멀티스레딩으로 처리하면 더 빠릅니다.
    for model_name in args.models:
        print(f"\n>> {model_name} 코치에게 진단 요청...")
        report = handle_debug_mode(args.persona, args.input, args.output, model_name)
        initial_reports[model_name] = report

    # --- 2. 교차 검증 및 최종 보고서 생성 ---
    final_report = "## 🤖 Agent I 최종 토론 보고서\n\n"
    final_report += "### 1. 개별 진단 리포트\n\n"

    for model_name, report in initial_reports.items():
        final_report += f"#### 📄 **진단 by {model_name}**\n"
        final_report += textwrap.indent(report, "> ") + "\n\n"

    # 교차 검증 (가장 첫 번째 리포트를 기준으로 다른 모델들에게 비평 요청)
    if len(args.models) > 1:
        final_report += "### 2. 교차 검증 (Cross-Examination)\n\n"

        base_model = args.models[0]
        base_report = initial_reports[base_model]
        critique_models = args.models[1:]

        final_report += f"#### 🎯 **주요 검토 대상: {base_model}의 진단**\n"
        final_report += textwrap.indent(base_report, "> ") + "\n\n"

        critique_system_prompt = """
        당신은 다른 AI의 분석을 날카롭게 비평하는 '수석 분석가'입니다.
        아래에 제시된 [다른 AI의 진단 리포트]를 읽고, 그 진단의 논리적 허점, 놓치고 있는 부분, 또는 더 나은 대안이 있다면 무엇인지 비평해 주세요.
        비평은 간결하고 핵심만 짚어야 합니다.
        """

        for critique_model in critique_models:
            print(
                f"\n>> {critique_model} 코치에게 {base_model}의 진단에 대한 비평 요청..."
            )
            critique_user_prompt = f"[다른 AI의 진단 리포트]\n---\n{base_report}"
            messages = [
                {"role": "system", "content": critique_system_prompt},
                {"role": "user", "content": critique_user_prompt},
            ]
            critique = call_llm_by_name(critique_model, messages)
            final_report += f"#### 💬 **비평 by {critique_model}**\n"
            final_report += textwrap.indent(critique, "> ") + "\n\n"

    # 최종 보고서 출력
    print("\n" + "=" * 20 + " 토론 완료 " + "=" * 20)
    print(final_report)
    print("=" * 52)


def main_cli():
    """터미널에서 직접 실행될 때 사용되는 CLI 핸들러"""
    parser = argparse.ArgumentParser(description="Agent_I: AI 핵심 로직 관리 에이전트")
    subparsers = parser.add_subparsers(dest="mode", required=True, help="실행 모드")

    # --- 'debug' 모드 설정 ---
    parser_debug = subparsers.add_parser(
        "debug", help="페르소나의 실패 원인을 진단합니다."
    )
    parser_debug.add_argument("--persona", type=str, required=True)
    parser_debug.add_argument("--input", type=str, required=True)
    parser_debug.add_argument("--output", type=str, required=True)
    parser_debug.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="사용할 LLM 모델 (예: gpt-4o-mini, claude-3-5-haiku, gemini-1.5-flash, deepseek-chat)",
    )
    parser_debug.set_defaults(
        func=lambda args: handle_debug_mode(
            args.persona, args.input, args.output, args.model
        )
    )

    # --- 'propose' 모드 설정 ---
    parser_propose = subparsers.add_parser(
        "propose", help="페르소나 수정안을 제안합니다."
    )
    parser_propose.add_argument("--goal", type=str, required=True)
    parser_propose.add_argument("--target", type=str, required=True)
    parser_propose.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="사용할 LLM 모델 (예: gpt-4o-mini, claude-3-5-hakiu, gemini-1.5-flash, deepseek-chat)",
    )
    parser_propose.set_defaults(
        func=lambda args: handle_propose_mode(args.goal, args.target, args.model)
    )

    # --- 'debate' 모드 서브파서 생성 ---
    parser_debate = subparsers.add_parser(
        "debate", help="여러 모델이 토론하여 페르소나를 진단합니다."
    )
    parser_debate.add_argument("--persona", type=str, required=True)
    parser_debate.add_argument("--input", type=str, required=True)
    parser_debate.add_argument("--output", type=str, required=True)
    parser_debate.add_argument(
        "--models",
        nargs="+",
        required=True,
        help="토론에 참여할 모델 목록 (공백으로 구분)",
    )
    parser_debate.set_defaults(func=handle_debate_mode)

    args = parser.parse_args()

    result = args.func(args)
    if args.mode in ["debug", "propose"]:
        print("\n" + "=" * 20 + " 결과 " + "=" * 20)
        if args.mode == "propose":
            content, path = result
            if path:
                print(f"✅ 제안된 수정안이 '{path}'에 저장되었습니다.")
            print(content)
        else:
            print(result)
        print("=" * 52)


if __name__ == "__main__":
    main_cli()
