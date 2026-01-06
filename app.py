import streamlit as st
import google.generativeai as genai
import os

# --- [1] 화면 설정 ---
st.set_page_config(page_title="인생 나침반", page_icon="🧭")

# --- [2] API 키 자동 감지 로직 (핵심!) ---
# 1. 비밀 금고(secrets)에 키가 있는지 확인
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    # 2. 금고에 키가 없으면(오류 상황) 직접 입력받기
    with st.sidebar:
        st.header("🔑 설정")
        api_key = st.text_input("Google API Key를 입력하세요", type="password")

# --- [3] 메인 화면 ---
st.title("🧭 인생 나침반")
st.header("혼자 끙끙 앓지 마세요. 길을 찾아드립니다.")
st.markdown("---")

# --- [4] 사용자 고민 입력 ---
st.write("### 📝 어떤 고민이 있으신가요?")
worry = st.text_area(
    label="고민 입력",
    height=150,
    placeholder="예: 나이가 드니 건강이 걱정되고 자식들에게 짐이 될까 두렵습니다.",
    label_visibility="collapsed"
)

# --- [5] AI 상담 및 버튼 ---
if st.button("🚀 지혜 구하기"):
    if not api_key:
        st.warning("⚠️ API 키가 없습니다. (설정이 필요해요)")
    elif not worry:
        st.warning("고민 내용을 먼저 적어주세요.")
    else:
        try:
            # 설정된 키로 구글 AI 연결
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            # AI에게 역할 부여
            system_prompt = f"""
            당신은 70년 인생의 지혜를 가진 따뜻한 멘토입니다.
            사용자의 고민: {worry}
            
            [답변 가이드]
            1. 따뜻한 공감으로 시작하세요.
            2. 현실적인 조언 3가지를 번호를 매겨 제시하세요.
            3. 마지막은 용기를 주는 명언으로 끝내주세요.
            """
            
            with st.spinner("🤔 곰곰이 생각하는 중입니다..."):
                response = model.generate_content(system_prompt)
                
                st.success("조언이 도착했습니다.")
                st.markdown("### 💌 당신을 위한 편지")
                st.write(response.text)
                
        except Exception as e:
            st.error(f"에러가 발생했습니다: {e}")
