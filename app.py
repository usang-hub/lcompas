import streamlit as st
import google.generativeai as genai
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="나만의 AI 비서", page_icon="🤖", layout="wide")

# 2. [핵심] 대한민국 전 종목 리스트 가져오기 (캐싱으로 속도 최적화)
# 이 함수는 앱이 처음 켜질 때 한 번만 실행되어 2,800개 리스트를 가져옵니다.
@st.cache_data
def get_all_stock_list():
    try:
        # 한국거래소(KRX)의 모든 종목(코스피+코스닥+코넥스) 불러오기
        df = fdr.StockListing('KRX')
        # 사용하기 편하게 "종목명 (코드)" 형태로 리스트를 만듦
        # 예: "삼성전자 (005930)"
        df['Display'] = df['Name'] + " (" + df['Code'] + ")"
        return df
    except Exception as e:
        return pd.DataFrame()

# --- 사이드바 ---
with st.sidebar:
    st.title("🤖 AI 비서실")
    menu = st.radio("기능 선택", ["🧭 인생 나침반", "💰 만능 자산 비서"], index=1)
    st.markdown("---")
    
    selected_model = st.selectbox(
        "사용 모델", 
        ["gemini-2.0-flash-exp", "gemini-1.5-flash"], 
        index=0
    )
    
    if "GOOGLE_API_KEY" in st.secrets:
        st.success("시스템 정상 가동 중 ✅")
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
            res = model.generate_content(f"70대 멘토로서 답변: {worry}")
            st.write(res.text)

# =========================================================
# 기능 2: 만능 자산 비서 (전 종목 검색 기능 탑재)
# =========================================================
elif menu == "💰 만능 자산 비서":
    st.title("💰 만능 투자 분석 비서")
    st.info("이제 대한민국 모든 주식(2,800여 개)을 검색할 수 있습니다.")
    
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🔍 종목 검색")
        
        # 1. 전 종목 리스트 불러오기
        with st.spinner("전국 주식 명부를 가져오는 중... (잠시만 기다려주세요)"):
            stock_df = get_all_stock_list()
        
        if stock_df.empty:
            st.error("종목 정보를 가져오지 못했습니다. 새로고침 해주세요.")
            final_code = ""
            selected_name = ""
        else:
            # 2. 검색 가능한 선택 상자 (Selectbox) 만들기
            # 사용자가 "삼"만 쳐도 삼성 관련주가 주르륵 나옵니다.
            stock_list = stock_df['Display'].tolist()
            
            # 기본값으로 삼성전자를 미리 선택해둠
            default_index = stock_list.index("삼성전자 (005930)") if "삼성전자 (005930)" in stock_list else 0
            
            selected_item = st.selectbox(
                "분석할 종목을 선택하거나 검색하세요 👇", 
                stock_list, 
                index=default_index
            )
            
            # 선택된 값에서 코드와 이름 분리하기
            # "삼성전자 (005930)" -> 이름: 삼성전자, 코드: 005930
            selected_name = selected_item.split(' (')[0]
            final_code = selected_item.split('(')[-1].replace(')', '')

        # 해외 주식/코인 입력 기능 (옵션)
        st.markdown("---")
        with st.expander("🇺🇸 미국 주식 / 🪙 코인 직접 입력"):
            manual_code = st.text_input("티커 입력 (예: TSLA, BTC/KRW)", placeholder="")
            if manual_code:
                final_code = manual_code
                selected_name = manual_code

        analyze_btn = st.button("차트 및 AI 분석 실행 🚀")

    with col2:
        if analyze_btn:
            try:
                with st.spinner(f"'{selected_name}' 데이터를 분석 중입니다..."):
                    # 데이터 가져오기 (최근 120일)
                    df = fdr.DataReader(final_code, datetime.now() - timedelta(days=120))
                    
                    if df.empty:
                        st.error(f"❌ 데이터가 없습니다. ({final_code})")
                        st.caption("상장 폐지되었거나 코드가 잘못되었습니다.")
                    else:
                        latest_close = df.iloc[-1]['Close']
                        latest_date = df.index[-1].strftime('%Y-%m-%d')
                        
                        st.subheader(f"📈 {selected_name} 주가 차트")
                        st.line_chart(df['Close'])
                        
                        # 깔끔한 지표 표시
                        c1, c2, c3 = st.columns(3)
                        c1.metric("기준일", latest_date)
                        c2.metric("현재가", f"{latest_close:,.0f}")
                        
                        # 등락폭 계산 (전일 대비)
                        if len(df) > 1:
                            prev_close = df.iloc[-2]['Close']
                            diff = latest_close - prev_close
                            diff_pct = (diff / prev_close) * 100
                            c3.metric("전일 대비", f"{diff:,.0f}", f"{diff_pct:.2f}%")

                        # AI 분석
                        model = genai.GenerativeModel(selected_model)
                        st.markdown("---")
                        st.subheader("🤖 Gemini 투자 리포트")
                        
                        with st.spinner("AI가 재무제표와 차트를 분석하고 있습니다..."):
                            data_text = df.tail(15).to_string()
                            prompt = f"""
                            당신은 냉철한 20년 경력의 펀드매니저입니다.
                            '{selected_name}' ({final_code}) 종목의 최근 주가 흐름을 분석해 주세요.
                            
                            [최근 15일 주가 데이터]
                            {data_text}
                            
                            다음 형식으로 보고서를 작성해 주세요:
                            1. **현재 추세 진단**: 상승세인지, 하락세인지, 횡보 중인지 명확히 판별
                            2. **주요 포인트**: 차트상 지지선이나 저항선, 혹은 특이사항
                            3. **투자자 행동 가이드**: 
                               - 보유자: (홀딩/매도/추가매수)
                               - 신규 진입: (진입 추천/관망/진입 금지)
                            
                            결론은 명확하고 직설적으로 말해주세요.
                            """
                            res = model.generate_content(prompt)
                            st.write(res.text)

            except Exception as e:
                st.error("일시적인 오류가 발생했습니다.")
                st.write(e)
