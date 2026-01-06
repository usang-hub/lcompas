import streamlit as st
import google.generativeai as genai

# [1] 화면 기본 설정
st.set_page_config(page_title="인생 나침반", page_icon="🧭")

# [2] 제목 설정
st.title("🧭 인생 나침반")
st.header("70년 인생의 지혜로 답해드립니다.")
st.markdown("---")

# [3] ★핵심★ 입력창 없이 바로 키 가져오기
# 금고(Secrets)에서 키를 꺼냅니다. 없으면 에러가 납니다.
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("🚨 비밀 금고 설정이 안 되어 있습니다.")
    st.stop()

# [4] 고민 입력받기
worry = st.text_area("고민을 털어놓으세요", height=150)

# [5] 버튼 클릭 시 작동
if st.button("조언 듣기"):
    if not worry:
        st.warning("고민을 적어주세요.")
    else:
        model = genai.GenerativeModel('gemini-pro')
        system_prompt = f"당신은 70대 인생 멘토입니다. 고민: {worry} 에 대해 따뜻하게 조언해주세요."
        
        with st.spinner("생각을 정리하는 중입니다..."):
            try:
                response = model.generate_content(system_prompt)
                st.success("답변이 도착했습니다.")
                st.write(response.text)
            except Exception as e:
                st.error(f"에러 발생: {e}")
