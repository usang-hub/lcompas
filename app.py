import streamlit as st
import google.generativeai as genai

# [1] 화면 기본 설정
st.set_page_config(page_title="인생 나침반", page_icon="🧭")

# [2] 제목과 설명
st.title("🧭 인생 나침반")
st.header("70년 인생의 지혜로 답해드립니다.")
st.markdown("---")

# [3] 비밀번호 무조건 가져오기 (입력창 삭제함!)
# 만약 여기서 에러가 나면, Secrets 설정이 100% 틀린 겁니다.
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("🚨 비밀 금고(Secrets) 설정이 아직 안 되었습니다.")
    st.error(f"에러 내용: {e}")
    st.stop() # 에러 나면 여기서 멈춤

# [4] 고민 입력받기
worry = st.text_area("고민을 털어놓으세요", height=150)

# [5] 버튼 누르면 답변하기
if st.button("조언 듣기"):
    if not worry:
        st.warning("고민을 적어주세요.")
    else:
        model = genai.GenerativeModel('gemini-pro')
        
        # 선생님이 심어둔 페르소나 (영혼)
        system_prompt = f"""
        당신은 인생의 산전수전을 다 겪은 현명하고 따뜻한 70대 멘토입니다.
        아래 고민에 대해 공감해주고, 현실적인 조언을 해주세요.
        
        고민: {worry}
        """
        
        with st.spinner("생각을 정리하는 중입니다..."):
            try:
                response = model.generate_content(system_prompt)
                st.success("답변이 도착했습니다.")
                st.write(response.text)
            except Exception as e:
                st.error(f"AI 호출 중 에러 발생: {e}")
