import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="인생 나침반", page_icon="🧭")

# 1. 사이드바(왼쪽 메뉴) 추가: 여기서 모델을 선택합니다.
with st.sidebar:
    st.header("설정")
    selected_model = st.selectbox(
        "사용할 모델 선택",
        [
            "gemini-2.0-flash-exp",  # 최신 Gemini 2.0 Flash
            "gemini-1.5-flash",      # 빠르고 가성비 좋은 모델
            "gemini-1.5-pro",        # 성능이 높은 모델
        ],
        index=0 # 첫 번째(2.0 Flash)를 기본값으로 설정
    )
    st.markdown(f"**현재 선택된 모델:** `{selected_model}`")

st.title("🧭 인생 나침반")
st.header("70년 인생의 지혜로 답해드립니다.")
st.markdown("---")

# [핵심] API 키 설정
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
        # 2. 선택된 모델(selected_model)을 사용하도록 변경
        model = genai.GenerativeModel(selected_model)
        
        with st.spinner(f"👴 70대 멘토가 생각 중입니다... (모델: {selected_model})"):
            try:
                # 3. 2.0 모델은 시스템 프롬프트를 더 잘 이해하므로 프롬프트를 약간 다듬었습니다.
                prompt = f"""
                당신은 산전수전 다 겪은 지혜롭고 따뜻한 70대 인생 멘토입니다.
                아래 고민에 대해 경험에서 우러나오는 통찰력 있는 조언과 따뜻한 위로를 해주세요.
                반말보다는 정중하고 인자한 말투('~하게나', '~라네' 등)를 사용해 주세요.
                
                고민 내용: {worry}
                """
                
                res = model.generate_content(prompt)
                st.write(res.text)
                
            except Exception as e:
                st.error(f"에러가 발생했습니다: {e}")
