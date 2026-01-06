import streamlit as st
import google.generativeai as genai
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="나만의 AI 비서", page_icon="🤖", layout="wide")

# 2. [핵심] 한국 주식 종목 리스트 미리 가져오기 (속도 획기적 개선)
@st.cache_data
def get_krx_list():
    df = fdr.StockListing('KRX') # 한국거래소 상장 종목 전체 가져오기
    return df[['Code', 'Name']]

# --- 사이드바 ---
with st.sidebar:
    st.title("🤖 AI 비서실")
    menu = st.radio("기능 선택", ["🧭 인생 나침반", "💰 실시간 자산 비서"], index=1)
    st.markdown("---")
    selected_model = st.selectbox("사용 모델", ["gemini-2.0-flash-exp", "gemini-1.5-flash"], index=0)
    
    # API 키 확인
    if "GOOGLE_API_KEY" in st.secrets:
        st.success("시스템 가동 중... ✅")
    else:
        st.error("API 키가 필요합니다.")

# API 설정
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
            res = model.generate_content(f"70대 멘토로서 조언해주세요: {worry}")
            st.write(res.text)

# =========================================================
# 기능 2: 실시간 자산 비서 (스마트 버전!)
# =========================================================
elif menu == "💰 실시간 자산 비서":
    st.title("💰 실시간 투자 분석 비서")
    
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🔍 종목 검색")
        
        # 1. 사용자가 입력한 값
        user_input = st.text_input("종목명 또는 코드 입력", value="삼성전자", placeholder="예: 삼성전자, 005930, TSLA, BTC/KRW")
        
        # 2. 한글 이름을 코드로 변환하는 로직
        search_code = user_input # 기본은 입력값 그대로 사용
        
        # 입력값이 숫자가 아니고(이름이고), 영어도 아닐 때 (즉, 한글 종목명일 때)
        if not user_input.isdigit() and not user_input.encode().isalpha():
            with st.spinner("종목 코드를 찾는 중..."):
                try:
                    krx_df = get_krx_list() # 전체 리스트 가져옴
                    # 이름이 정확히 일치하는 것 찾기
                    found = krx_df[krx_df['Name'] == user_input]
                    
                    if not found.empty:
                        search_code = found.iloc[0]['Code'] # 코드로 변환 (예: 삼성전자 -> 005930)
                        st.success(f"'{user_input}'의 코드를 찾았습니다: {search_code}")
                    else:
                        st.warning("정확한 종목명을 찾지 못했습니다. 코드로 입력해보세요.")
                except:
                    pass

        analyze_btn = st.button("시세 조회 및 분석")
        
        st.info("💡 팁: '삼성전자', '카카오' 처럼 한글 이름을 입력해도 됩니다.")
        st.caption("미국주식(TSLA)이나 코인(BTC/KRW)은 코드로 입력해주세요.")

    with col2:
        if analyze_btn:
            try:
                with st.spinner(f"'{user_input}({search_code})' 데이터 불러오는 중..."):
                    # 데이터 가져오기
                    df = fdr.DataReader(search_code, datetime.now() - timedelta(days=60))
                    
                    if df.empty:
                        st.error("데이터를 가져올 수 없습니다. 종목명이나 코드를 확인해주세요.")
                    else:
                        latest_close = df.iloc[-1]['Close']
                        latest_date = df.index[-1].strftime('%Y-%m-%d')
                        
                        # 차트
                        st.line_chart(df['Close'])
                        st.metric(label="현재가 (종가 기준)", value=f"{latest_close:,.0f} 원/포인트")

                        # AI 분석
                        model = genai.GenerativeModel(selected_model)
                        with st.spinner("🤖 AI가 차트를 보고 분석 중입니다..."):
                            data_text = df.tail(10).to_string()
                            prompt = f"""
                            당신은 전문 투자 애널리스트입니다.
                            다음은 '{user_input}'의 최근 주가 데이터입니다.
                            
                            [최근 주가 데이터]
                            {data_text}
                            
                            1. 현재 추세 (상승/하락/보합)
                            2. 기술적 분석 요약
                            3. 투자자 대응 전략 (매수/매도/관망)
                            
                            쉽고 명확하게 설명해주세요.
                            """
                            res = model.generate_content(prompt)
                            st.markdown("### 📊 AI 투자 리포트")
                            st.write(res.text)

            except Exception as e:
                st.error(f"오류: {e}")
                st.write("해외 주식이나 코인은 티커(예: AAPL, BTC/KRW)로 입력해야 정확합니다.")
