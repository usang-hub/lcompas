import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="인생 나침반", page_icon="🧭")
st.title("🧭 인생 나침반")
st.header("70년 인생의 지혜로 답해드립니다.")
st.markdown("---")

# [핵심] 입력창 삭제! 금고에서 키 바로 꺼내기
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    else:
        st.error("🚨 금고(Secrets)에 키가 없습니다.")
        st.stop()
except Exception as e:
    st.error(f"설정 오류: {e}")
    st.stop()

worry = st.text_area("고민을 털어놓으세요", height=150)

if st.button("조언 듣기"):
    if not worry:
        st.warning("고민을 적어주세요.")
    else:
        model = genai.GenerativeModel('gemini-pro')
        with st.spinner("생각 중..."):
            try:
                res = model.generate_content(f"70대 멘토로서 답변해주세요. 고민: {worry}")
                st.write(res.text)
            except Exception as e:
                st.error(f"에러: {e}")
