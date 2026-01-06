import streamlit as st
import google.generativeai as genai

# 페이지 설정
st.set_page_config(page_title="인생 나침반", page_icon="🧭")

# --- 사이드바 (모델 선택 기능) ---
with st.sidebar:
    st.header("⚙️ 설정")
    
    # 모델 선택 박스 만들기
    selected_model = st.selectbox(
        "사용할 모델을 선택하세요",
        [
            "gemini-2.0-flash-exp",  # 최신 모델 (기본값)
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ],
        index=0
    )
    
    # 선택된 모델 보여주기
    st.info(f"현재 **{selected_model}** 모델이 연결되었습니다.")
    
    # API 키 상태 확인 (입력창 아님)
    if "GOOGLE_API_KEY" in st.secrets:
        st.success("API 키가 정상적으로 인식되었습니다! ✅")
    else:
        st.error("API 키가 없습니다. Secrets를 확인해주세요.")

# --- 메인 화면 ---
st.title("🧭 인생 나침반")
st.header("70년 인생의 지혜로 답해드립니다.")
st.markdown("---")

# API 키 설정 (secrets에서 가져오기)
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.stop() # 키가 없으면 여기서 멈춤
except Exception as e:
    st.error(f"설정 오류: {e}")
    st.stop()

# 고민 입력 받기
worry = st.text_area("고민을 털어놓으세요", height=150, placeholder="예: 은퇴 후의 삶이 너무 막막합니다. 어떻게 살아야 할까요?")

if st.button("조언 듣기"):
    if not worry:
        st.warning("고민 내용을 적어주세요.")
    else:
        # 선택된 모델로 AI 설정
        model = genai.GenerativeModel(selected_model)
        
        with st.spinner(f"👴 70대 멘토가 생각 중입니다... (사용 모델: {selected_model})"):
            try:
                prompt = f"""
                당신은 지혜로운 70대 인생 멘토입니다. 
                아래 고민에 대해 따뜻하고 통찰력 있는 조언을 해주세요.
                말투는 정중하고 인자하게 부탁하네.
                
                고민: {worry}
                """
                res = model.generate_content(prompt)
                st.write(res.text)
            except Exception as e:
                st.error(f"에러가 발생했습니다: {e}")
