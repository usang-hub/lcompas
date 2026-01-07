import streamlit as st
import google.generativeai as genai
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="나만의 AI 비서", page_icon="🤖", layout="wide")

# 2. [주식] 전 종목 리스트 가져오기 (캐싱)
@st.cache_data
def get_all_stock_list():
    try:
        df = fdr.StockListing('KRX')
        df['Display'] = df['Name'] + " (" + df['Code'] + ")"
        return df
    except:
        return pd.DataFrame()

# --- 사이드바 ---
with st.sidebar:
    st.title("🤖 AI 비서실")
    
    # 메뉴가 3개로 늘어났습니다!
    menu = st.radio("기능 선택", 
        ["🧭 인생 나침반 (고민)", "💰 만능 자산 비서 (주식)", "🥠 신년 운세 (사주)"], 
        index=2 # 기본으로 운세가 먼저 뜨게 설정 (자랑하기 좋게)
    )
    st.markdown("---")
    
    selected_model = st.selectbox("사용 모델", ["gemini-2.0-flash-exp", "gemini-1.5-flash"], index=0)
    
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
if "인생 나침반" in menu:
    st.title("🧭 인생 나침반")
    st.subheader("70년 인생의 지혜로 답해드립니다.")
    worry = st.text_area("고민을 털어놓으세요", height=150)
    if st.button("조언 듣기") and worry:
        model = genai.GenerativeModel(selected_model)
        with st.spinner("생각 중..."):
            res = model.generate_content(f"70대 멘토로서 정중하고 지혜롭게 답변해주세요: {worry}")
            st.write(res.text)

# =========================================================
# 기능 2: 만능 자산 비서
# =========================================================
elif "만능 자산 비서" in menu:
    st.title("💰 만능 투자 분석 비서")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("🔍 종목 검색")
        stock_df = get_all_stock_list()
        
        if stock_df.empty:
            st.error("종목 정보를 가져오지 못했습니다.")
            selected_name, final_code = "", ""
        else:
            stock_list = stock_df['Display'].tolist()
            # 기본값 설정
            default_idx = stock_list.index("삼성전자 (005930)") if "삼성전자 (005930)" in stock_list else 0
            selected_item = st.selectbox("종목 선택/검색", stock_list, index=default_idx)
            selected_name = selected_item.split(' (')[0]
            final_code = selected_item.split('(')[-1].replace(')', '')

        with st.expander("🇺🇸 미국 주식 / 🪙 코인 입력"):
            manual = st.text_input("티커 입력 (예: TSLA, BTC/KRW)")
            if manual:
                final_code = manual
                selected_name = manual

        btn = st.button("분석 실행 🚀")

    with col2:
        if btn:
            try:
                with st.spinner(f"'{selected_name}' 분석 중..."):
                    df = fdr.DataReader(final_code, datetime.now() - timedelta(days=100))
                    if df.empty:
                        st.error("데이터가 없습니다.")
                    else:
                        cur_price = df.iloc[-1]['Close']
                        st.subheader(f"{selected_name} 주가 차트")
                        st.line_chart(df['Close'])
                        st.metric("현재가", f"{cur_price:,.0f}")
                        
                        model = genai.GenerativeModel(selected_model)
                        st.markdown("---")
                        prompt = f"""
                        당신은 전문 애널리스트입니다. '{selected_name}'의 최근 100일 차트 데이터를 보고
                        추세(상승/하락)와 투자 전략(매수/매도/관망)을 명확히 조언해주세요.
                        데이터: {df.tail(10).to_string()}
                        """
                        res = model.generate_content(prompt)
                        st.write(res.text)
            except Exception as e:
                st.error(f"오류: {e}")

# =========================================================
# 기능 3: 신년 운세 (대박 기능 추가!)
# =========================================================
elif "신년 운세" in menu:
    st.title("🥠 AI 사주 명리학자")
    st.info("당신의 생년월일을 입력하면, AI가 사주팔자를 분석해 드립니다.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 사주 정보 입력")
        
        # 날짜 입력
        birth_date = st.date_input("생년월일", min_value=datetime(1940, 1, 1), max_value=datetime(2025, 12, 31))
        
        # 시간 입력
        birth_time = st.time_input("태어난 시간")
        
        # 성별 및 양/음력
        gender = st.radio("성별", ["남성", "여성"], horizontal=True)
        calendar_type = st.radio("양력/음력", ["양력", "음력"], horizontal=True)
        
        saju_btn = st.button("2026년 운세 보기 ✨")

    with col2:
        if saju_btn:
            model = genai.GenerativeModel(selected_model)
            with st.spinner("📜 만세력을 펼치고 운명을 분석하는 중입니다..."):
                try:
                    # AI에게 '도사' 페르소나 부여
                    prompt = f"""
                    당신은 조선 최고의 사주 명리학자이자 도사입니다.
                    아래 정보를 가진 사람의 사주와 2026년(병오년) 신년 운세를 봐주세요.
                    
                    [사용자 정보]
                    - 생년월일: {birth_date.strftime('%Y년 %m월 %d일')}
                    - 태어난 시간: {birth_time.strftime('%H시 %M분')}
                    - 성별: {gender}
                    - 양/음력: {calendar_type}
                    
                    [요청 사항]
                    1. **타고난 기질**: 이 사람은 어떤 성향(오행)을 타고났는지 설명해주세요.
                    2. **2026년 총운**: 올해 전반적인 흐름이 어떤지 설명해주세요.
                    3. **재물운 & 직업운**: 돈과 일에 관련된 운세를 구체적으로.
                    4. **건강 & 연애운**: 조심해야 할 점이나 좋은 인연.
                    5. **행운의 조언**: 마음가짐이나 행운의 색/숫자 등.
                    
                    말투는 신비롭지만 친절하게("~하게나", "~보이는군" 등) 해주세요.
                    """
                    
                    res = model.generate_content(prompt)
                    
                    st.success("분석이 완료되었습니다!")
                    st.markdown("### 📜 2026년 운세 풀이")
                    st.write(res.text)
                    st.caption("※ 재미로 보는 AI 운세입니다.")
                    
                except Exception as e:
                    st.error(f"운세를 보는 중 기운이 막혔습니다: {e}")
