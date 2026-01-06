import streamlit as st
import google.generativeai as genai
import FinanceDataReader as fdr  # 주식 정보 가져오는 도구
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="나만의 AI 비서", page_icon="🤖", layout="wide")

# --- 사이드바 ---
with st.sidebar:
    st.title("🤖 AI 비서실")
    menu = st.radio("기능 선택", ["🧭 인생 나침반", "💰 실시간 자산 비서"], index=1) # 자산 비서를 기본으로 설정
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
# 기능 2: 실시간 자산 비서 (업그레이드 버전!)
# =========================================================
elif menu == "💰 실시간 자산 비서":
    st.title("💰 실시간 투자 분석 비서")
    st.info("종목 코드를 입력하면 '현재 주가'를 조회해서 AI가 분석해줍니다.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🔍 종목 조회")
        # 종목 코드 입력 받기
        symbol = st.text_input("종목 코드 입력 (예: 005930, TSLA, BTC/KRW)", value="005930")
        st.caption("삼성전자: 005930 / 테슬라: TSLA / 비트코인: BTC/KRW")
        
        analyze_btn = st.button("시세 조회 및 분석")

    with col2:
        if analyze_btn:
            # 1. 주식 데이터 가져오기 (FinanceDataReader)
            try:
                with st.spinner(f"'{symbol}' 시세 정보를 가져오는 중..."):
                    # 최근 30일치 데이터 가져오기
                    df = fdr.DataReader(symbol, datetime.now() - timedelta(days=60))
                    
                    if df.empty:
                        st.error("데이터를 찾을 수 없습니다. 코드를 확인해주세요.")
                    else:
                        # 최신 데이터 정리
                        latest_close = df.iloc[-1]['Close'] # 현재가
                        latest_date = df.index[-1].strftime('%Y-%m-%d')
                        
                        # 차트 그리기 (간단하게)
                        st.line_chart(df['Close'])
                        st.success(f"기준일: {latest_date} | 현재가: {latest_close:,.0f} (단위: 해당통화)")

                        # 2. AI에게 데이터 먹여서 분석 요청하기
                        model = genai.GenerativeModel(selected_model)
                        with st.spinner("🤖 AI가 차트와 데이터를 분석 중입니다..."):
                            
                            # 데이터(CSV 형태)를 텍스트로 변환
                            data_text = df.tail(10).to_string()
                            
                            prompt = f"""
                            당신은 전문 투자 애널리스트입니다.
                            다음은 '{symbol}' 종목의 최근 주가 데이터입니다.
                            
                            [최근 주가 데이터]
                            {data_text}
                            
                            위 데이터를 바탕으로 다음을 분석해주세요:
                            1. 현재 추세 (상승세인지 하락세인지)
                            2. 기술적 분석에 따른 단기 전망
                            3. 투자자를 위한 조언 (매수/매도/관망 등 의견)
                            
                            전문적이지만 이해하기 쉽게 설명해주세요.
                            """
                            
                            res = model.generate_content(prompt)
                            st.markdown("### 📊 AI 분석 리포트")
                            st.write(res.text)

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
                st.caption("종목 코드가 정확한지 확인해주세요.")
