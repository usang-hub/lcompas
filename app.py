import streamlit as st
import google.generativeai as genai

# 1. 페이지 기본 설정 (가장 위에 있어야 함)
st.set_page_config(page_title="나만의 AI 비서", page_icon="🤖", layout="wide")

# --- 사이드바: 공통 설정 (메뉴 & 모델 선택) ---
with st.sidebar:
    st.title("🤖 AI 비서실")
    
    # [핵심] 기능 선택 메뉴 만들기
    menu = st.radio(
        "어떤 비서를 부르시겠습니까?",
        ["🧭 인생 나침반 (고민 상담)", "💰 자산 비서 (투자 조언)"],
        index=0
    )
    
    st.markdown("---")
    
    # 모델 선택
    selected_model = st.selectbox(
        "사용할 두뇌(모델) 선택",
        ["gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro"],
        index=0
    )
    
    # API 키 확인
    if "GOOGLE_API_KEY" in st.secrets:
        st.success("API 키 인증 완료! ✅")
    else:
        st.error("API 키가 없습니다. 설정(Secrets)을 확인하세요.")

# --- API 설정 (공통) ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.stop()
except Exception as e:
    st.error(f"설정 오류: {e}")
    st.stop()

# =========================================================
# 기능 1: 인생 나침반 (기존 기능)
# =========================================================
if menu == "🧭 인생 나침반 (고민 상담)":
    st.title("🧭 인생 나침반")
    st.subheader("70년 인생의 지혜로 답해드립니다.")
    st.info("혼자 끙끙 앓지 마세요. 길을 찾아드립니다.")
    
    worry = st.text_area("어떤 고민이 있으신가요?", height=150, placeholder="예: 은퇴 후 시간이 너무 안 갑니다. 소일거리가 있을까요?")
    
    if st.button("지혜 구하기"):
        if not worry:
            st.warning("고민 내용을 적어주세요.")
        else:
            model = genai.GenerativeModel(selected_model)
            with st.spinner("👴 70대 멘토가 생각에 잠겼습니다..."):
                try:
                    prompt = f"""
                    당신은 지혜롭고 따뜻한 70대 인생 멘토입니다. 
                    아래 고민에 대해 경험에서 우러나오는 통찰력 있는 조언과 따뜻한 위로를 해주세요.
                    말투는 정중하고 인자하게('~하게나', '~라네' 등) 해주세요.
                    
                    고민: {worry}
                    """
                    res = model.generate_content(prompt)
                    st.write(res.text)
                except Exception as e:
                    st.error(f"에러 발생: {e}")

# =========================================================
# 기능 2: 자산 비서 (새로운 기능)
# =========================================================
elif menu == "💰 자산 비서 (투자 조언)":
    st.title("💰 AI 자산 관리 비서")
    st.subheader("주식, 코인, 경제 흐름을 분석해 드립니다.")
    st.info("보유 종목이나 시장 상황에 대해 물어보세요.")
    
    # 화면을 2단으로 나누기 (왼쪽: 입력 / 오른쪽: 결과)
    col1, col2 = st.columns([1, 1])
    
    with col1:
        asset_input = st.text_area(
            "질문이나 보유 종목을 입력하세요.", 
            height=200,
            placeholder="예: \n삼성전자랑 비트코인을 가지고 있어.\n지금 경제 상황에서 어떻게 대응하는 게 좋을까?\n아니면 추천할만한 ETF가 있어?"
        )
        ask_btn = st.button("분석 요청 📊")

    with col2:
        if ask_btn:
            if not asset_input:
                st.warning("분석할 내용을 입력해주세요.")
            else:
                model = genai.GenerativeModel(selected_model)
                with st.spinner("📈 시장 데이터를 분석하고 있습니다..."):
                    try:
                        # 자산 비서 페르소나 설정
                        prompt = f"""
                        당신은 냉철하고 데이터에 기반한 '전문 AI 투자 분석가'입니다.
                        사용자의 질문에 대해 거시 경제 상황과 투자 원칙에 입각하여 조언해주세요.
                        
                        1. 긍정적인 면과 리스크를 균형 있게 설명하세요.
                        2. 구체적인 수치나 예시를 들 수 있다면 드세요.
                        3. 투자의 최종 책임은 본인에게 있음을 짧게 명시하세요.
                        4. 말투는 전문적이고 신뢰감 있게('~입니다', '~판단됩니다') 해주세요.
                        
                        사용자 질문: {asset_input}
                        """
                        res = model.generate_content(prompt)
                        st.markdown(res.text)
                    except Exception as e:
                        st.error(f"에러 발생: {e}")
