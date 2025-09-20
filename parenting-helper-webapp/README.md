# Parenting Helper Webapp
이 프로젝트는 Streamlit과 OpenAI API를 활용한 육아 도우미 앱입니다.

## 실행 방법
pip install -r requirements.txt
streamlit run app.py

## 환경 변수
.env 파일에 아래 변수를 추가하세요.
OPENAI_API_KEY="your-key"

## 폴더 구조
app.py : 메인 앱 (Streamlit UI)
lib/ : 핵심 로직 (OpenAI 호출, 프롬프트 관리, 스토리지)
prompts/ : 프롬프트 템플릿
data/ : 대화 데이터(JSON)
