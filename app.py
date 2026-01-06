import streamlit as st
import google.generativeai as genai

# [1] 화면 설정
st.set_page_config(page_title="인생 나침반", page_icon="🧭")
st.title("🧭 인생 나침반")
st.header("70년 인생의 지혜로 답해드립니다.")
st.markdown("---")

# [2] ★핵심★ 입력창 없이 금고에서 키 꺼내기
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    else:
        st.error("🚨 비밀 금고(Secrets)에 키가 없습니다.")
        st.stop()
except Exception as e:
    st.error(f"설정 오류: {e}")
    st.stop()

# [3] 고민 입력받기
worry = st.text_area("고민을 털어놓으세요", height=150)

if st.button("조언 듣기"):
    if not worry:
        st.warning("고민을 적어주세요.")
    else:
        model = genai.GenerativeModel('gemini-pro')
        system_prompt = f"당신은 70대 멘토입니다. 고민: {worry} 에 대해 조언해주세요."
        try:
            with st.spinner("생각 중..."):
                response = model.generate_content(system_prompt)
                st.write(response.text)
        except Exception as e:
            st.error(f"에러: {e}")
