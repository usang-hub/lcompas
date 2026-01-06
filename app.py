import streamlit as st
import google.generativeai as genai
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="나만의 AI 비서", page_icon="🤖", layout="wide")

# 2. [핵심] VIP 종목 코드 미리 정의 (다운로드 없이 즉시 실행됨)
VIP_STOCKS = {
    "삼성전자": "005930",
    "SK하이닉스": "000660",
    "LG에너지솔루션": "373220",
    "POSCO홀딩스": "005490", "포스코홀딩스": "005490",
    "현대차": "005380",
    "기아": "000270",
    "NAVER": "035420", "네이버": "035420",
    "카카오": "035720",
    "삼성SDI": "006400",
    "LG화학": "051910",
    "셀트리온": "068270",
    "KB금융": "105560",
    "신한지주": "055550",
}

# 3. 전체 리스트 가져오기 (VIP에 없을 때만 사용)
@st.cache_data
def get_krx_list():
    try:
        # KOSPI, KOSDAQ 종목 모두 가져오기
        df = fdr.StockListing('KRX') 
        return df[['Code', 'Name']]
    except:
        return pd.DataFrame()

# --- 사이드바 ---
with st.sidebar:
    st.title("🤖 AI 비서실")
    menu = st.radio("기능 선택", ["🧭 인생 나침반", "💰 실시간 자산 비서"], index=1)
    st.markdown("---")
    selected_model = st.selectbox("사용 모델", ["gemini-2.0-flash-exp", "gemini-1.5-flash"], index=0)
    
    if "GOOGLE_API_KEY" in st.secrets:
        st.success("시스템 정상 가동 중 ✅")
    else:
        st.error("API 키가 필요합니다.")

try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.stop()

# =========================================================
# 기능 1: 인생 나침반
# =========================================================
if menu == "🧭 인생 나침반":
    st.title("🧭 인생 나침반")
    worry = st.text_area("고민을 털어놓으세요", height=150)
    if st.button("조언 듣기") and worry:
        model = genai.GenerativeModel(selected_model)
        with st.spinner("생각 중..."):
            res = model.generate_content(f"70대 멘토로서 답변: {worry}")
            st.write(res.text)

# =========================================================
# 기능 2: 실시간 자산 비서 (VIP 업그레이드)
# =========================================================
elif menu == "💰 실시간 자산 비서":
    st.title("💰 실시간 투자 분석 비서")
    
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🔍 종목 검색")
        user_input = st.text_input("종목명 또는 코드", value="SK하이닉스")
        
        # 검색 로직 시작
        search_code = ""
        found_name = ""
        
        # 1. 사용자가 코드를 직접 입력했는지 확인 (숫자 6자리)
        if user_input.isdigit() and len(user_input) == 6:
            search_code = user_input
            found_name = user_input # 이름은 모름
            
        # 2. VIP 명단에서 먼저 찾기 (가장 빠름)
        elif user_input.upper().replace(" ", "") in VIP_STOCKS:
            key = user_input.upper().replace(" ", "")
            search_code = VIP_STOCKS[key]
            found_name = user_input
            st.success(f"⭐ 주요 종목 확인됨: {search_code}")
            
        # 3. VIP에 없으면 전체 리스트에서 검색
        elif not user_input.isdigit():
            with st.spinner("전체 종목 리스트 검색 중..."):
                krx_df = get_krx_list()
                if not krx_df.empty:
                    clean_input = user_input.upper().replace(" ", "")
                    # 정확히 일치하는 이름 찾기
                    results = krx_df[krx_df['Name'].str.upper().str.replace(" ", "") == clean_input]
                    
                    if not results.empty:
                        search_code = results.iloc[0]['Code']
                        found_name = results.iloc[0]['Name']
                        st.success(f"종목 코드 발견: {search_code}")
                    else:
                        st.warning("⚠️ 정확한 종목명을 찾지 못했습니다.")
                        st.caption("인식 불가 시 코드로 입력해주세요. (예: 005930)")
                else:
                    st.error("서버 문제로 리스트를 불러오지 못했습니다. 코드로 입력해주세요.")

        # 최종 코드 확정 (못 찾았으면 입력값 그대로 사용해 해외주식 등 시도)
        if not search_code:
            search_code = user_input 

        analyze_btn = st.button("시세 조회 및 분석")

    with col2:
        if analyze_btn:
            # 한글 이름이 그대로 넘어가면 에러나므로, 코드가 없을 땐 실행 막기
            if not search_code.isdigit() and not search_code.encode().isalpha():
                 st.error(f"⛔ '{search_code}'는 올바른 코드가 아닙니다.")
                 st.info("한국 주식은 '종목코드(6자리 숫자)'가 필요합니다.")
            else:
                try:
                    with st.spinner(f"데이터 불러오는 중... ({search_code})"):
                        # 데이터 가져오기
                        df = fdr.DataReader(search_code, datetime.now() - timedelta(days=90))
                        
                        if df.empty:
                            st.error("데이터가 없습니다. 상장 폐지되었거나 코드가 틀렸습니다.")
                        else:
                            latest_close = df.iloc[-1]['Close']
                            latest_date = df.index[-1].strftime('%Y-%m-%d')
                            
                            st.subheader(f"{found_name if found_name else search_code} 주가 차트")
                            st.line_chart(df['Close'])
                            st.metric("현재가", f"{latest_close:,.0f} 원/포인트")

                            # AI 분석
                            model = genai.GenerativeModel(selected_model)
                            with st.spinner("🤖 AI가 분석 리포트를 작성 중입니다..."):
                                prompt = f"""
                                당신은 20년 경력의 펀드매니저입니다.
                                '{found_name}' ({search_code})의 최근 3개월 주가 데이터를 분석해주세요.
                                
                                [데이터]
                                {df.tail(10).to_string()}
                                
                                1. 현재 추세 (상승/하락/횡보)
                                2. 주요 지지선과 저항선 분석
                                3. 매수/매도/관망 의견과 그 이유
                                
                                초보자도 이해하기 쉽게 설명해주세요.
                                """
                                res = model.generate_content(prompt)
                                st.markdown("### 📊 AI 투자 리포트")
                                st.write(res.text)

                except Exception as e:
                    st.error("데이터 조회 실패 (해외주식은 티커, 국내주식은 코드 확인)")
                    st.caption(f"에러 내용: {e}")
