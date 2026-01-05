import streamlit as st
import google.generativeai as genai

# --- [1] 화면 설정 ---
st.set_page_config(page_title="인생 나침반", page_icon="🧭")

# --- [2] 사이드바: API 키 입력받기 ---
with st.sidebar:
    st.header("🔑 설정")
    # 아까 성공하신 그 API 키를 여기에 입력하시면 됩니다.
    api_key = st.text_input("Google API Key를 입력하세요", type="password")
    st.markdown("---")
    st.caption("선생님의 키는 정상입니다! (Gemini 2.0 Flash 사용 중)")

# --- [3] 메인 화면 디자인 ---
st.title("🧭 인생 나침반")
st.header("혼자 끙끙 앓지 마세요. 길을 찾아드립니다.")
st.markdown("---")

# --- [4] 사용자 고민 입력 ---
st.write("### 📝 어떤 고민이 있으신가요?")
worry = st.text_area(
    label="고민 입력",
    height=150,
    placeholder="예: 퇴직하고 나니 하루가 너무 무료하고 자식들 눈치가 보입니다. 어떻게 살아야 할까요?",
    label_visibility="collapsed"
)

# --- [5] AI 상담 로직 (모델 이름 수정 완료!) ---
def get_ai_advice(user_worry, key):
    if not key:
        return "⚠️ 왼쪽 사이드바에 API 키를 먼저 넣어주세요."
    
    try:
        genai.configure(api_key=key)
        
        # [중요] 선생님의 명단에 있던 'gemini-2.0-flash'로 교체했습니다!
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        system_prompt = f"""
        당신은 70년 인생의 산전수전을 다 겪은 지혜롭고 따뜻한 '인생 멘토'입니다.
        사용자의 고민을 듣고, 차가운 분석보다는 따뜻한 공감과 함께 현실적인 조언을 해주세요.
        
        [답변 규칙]
        1. 첫마디는 사용자의 마음에 깊이 공감해주세요.
        2. 해결책은 반드시 '3가지'로 요약해서 번호를 매겨 제시하세요.
        3. 마지막에는 용기를 주는 명언이나 사자성어를 하나 인용해주세요.
        4. 말투는 정중하고 온화하게 해주세요.
        
        사용자의 고민: {user_worry}
        """
        
        response = model.generate_content(system_prompt)
        return response.text
        
    except Exception as e:
        return f"에러가 발생했습니다: {str(e)}"

# --- [6] 버튼 클릭 시 동작 ---
if st.button("🚀 지혜 구하기"):
    if not worry:
        st.warning("고민 내용을 먼저 적어주세요.")
    else:
        with st.spinner("🤔 곰곰이 생각하는 중입니다..."):
            advice = get_ai_advice(worry, api_key)
            
            st.success("조언이 도착했습니다.")
            st.markdown("### 💌 당신을 위한 편지")
            st.write(advice)
            st.markdown("---")