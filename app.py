import streamlit as st
import google.generativeai as genai
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
from korean_lunar_calendar import KoreanLunarCalendar

# 1. 페이지 설정
st.set_page_config(page_title="나만의 AI 비서", page_icon="🤖", layout="wide")

# 2. [함수] 만세력 (월두법/윤달 완벽 적용)
def get_ganji(year, month, day, hour_str, is_lunar=False, is_leap=False):
    calendar = KoreanLunarCalendar()
    if is_lunar:
        calendar.setLunarDate(year, month, day, is_leap)
        solar_date = datetime(calendar.solarYear, calendar.solarMonth, calendar.solarDay)
    else:
        solar_date = datetime(year, month, day)
    
    gan = list("갑을병정무기경신임계")
    ji = list("자축인묘진사오미신유술해")
    
    # 년주
    if solar_date.month < 2 or (solar_date.month == 2 and solar_date.day < 4):
        year_val = year - 1
    else:
        year_val = year
    year_gan_idx = (year_val - 1924) % 10 
    year_ji_idx = (year_val - 1924) % 12
    year_ganji = gan[year_gan_idx] + ji[year_ji_idx]

    # 월주
    month_ji_idx = solar_date.month - 2
    if solar_date.day < 5: month_ji_idx -= 1
    if month_ji_idx < 0: month_ji_idx += 12
    month_start_gan_idx = (year_gan_idx % 5 + 1) * 2
    month_gan_idx = (month_start_gan_idx + month_ji_idx) % 10
    month_ganji = gan[month_gan_idx] + ji[(month_ji_idx + 2) % 12]

    # 일주
    base_date = datetime(1900, 1, 1) 
    days_diff = (solar_date - base_date).days
    day_total_idx = (days_diff + 10) 
    day_ganji = gan[day_total_idx % 10] + ji[day_total_idx % 12]

    return f"{year_ganji}년 {month_ganji}월 {day_ganji}일", solar_date.strftime("%Y년 %m월 %d일")

# 3. [함수] 주식 리스트 (안전장치 포함)
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
    # 메뉴 4개로 확장됨
    menu = st.radio("기능 선택", 
        ["🧭 인생 나침반", "💰 만능 자산 비서", "🥠 정통 사주 운세", "🍽️ 미식가 비서"], 
        index=3 # 맛집 기능 바로 확인하시라고 기본 선택해둠
    )
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
if "인생 나침반" in menu:
    st.title("🧭 인생 나침반")
    worry = st.text_area("고민을 털어놓으세요", height=150)
    if st.button("조언 듣기") and worry:
        model = genai.GenerativeModel(selected_model)
        with st.spinner("생각 중..."):
            res = model.generate_content(f"70대 멘토로서 답변: {worry}")
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
        
        # 리스트 로딩 실패 시 수동 입력창 표시
        if stock_df.empty:
            st.warning("⚠ 목록 다운로드 지연. 코드를 입력하세요.")
            manual_input = st.text_input("종목코드 입력", value="005930")
            final_code = manual_input
            selected_name = "종목"
        else:
            stock_list = stock_df['Display'].tolist()
            default_idx = stock_list.index("삼성전자 (005930)") if "삼성전자 (005930)" in stock_list else 0
            selected_item = st.selectbox("종목 선택", stock_list, index=default_idx)
            selected_name = selected_item.split(' (')[0]
            final_code = selected_item.split('(')[-1].replace(')', '')
        
        with st.expander("🇺🇸 미국 주식 / 코인 입력"):
             direct_code = st.text_input("티커 (예: TSLA, BTC/KRW)")
             if direct_code:
                 final_code = direct_code
                 selected_name = direct_code

        btn = st.button("분석 실행 🚀")

    with col2:
        if btn:
            try:
                df = fdr.DataReader(final_code, datetime.now() - timedelta(days=100))
                if not df.empty:
                    latest_price = df.iloc[-1]['Close']
                    st.subheader(f"{selected_name} 주가 차트")
                    st.line_chart(df['Close'])
                    st.metric("현재가", f"{latest_price:,.0f}")
                    model = genai.GenerativeModel(selected_model)
                    with st.spinner("AI 분석 중..."):
                        res = model.generate_content(f"'{selected_name}' 주가 분석해줘. 데이터: {df.tail(5).to_string()}")
                        st.markdown("### 📊 AI 분석 리포트")
                        st.write(res.text)
                else:
                    st.error("데이터 없음. 코드를 확인하세요.")
            except Exception as e:
                st.error(f"오류: {e}")

# =========================================================
# 기능 3: 정통 사주 운세
# =========================================================
elif "정통 사주 운세" in menu:
    st.title("🥠 AI 정통 사주 명리학")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("📝 내 정보 입력")
        birth_date = st.date_input("생년월일", value=datetime(1949, 1, 23), min_value=datetime(1900, 1, 1), max_value=datetime(2100, 12, 31))
        calendar_type = st.radio("달력 구분", ["음력", "양력"], horizontal=True)
        is_leap_month = False
        if calendar_type == "음력": is_leap_month = st.checkbox("이 달이 '윤달' 입니까?")
        gender = st.radio("성별", ["남성", "여성"], index=1, horizontal=True)
        birth_time = st.time_input("태어난 시간", value=datetime.strptime("04:15", "%H:%M").time())
        manual_check = st.checkbox("⚠️ 사주팔자 직접 입력하기 (옵션)")
        user_ganji_input = ""
        if manual_check: user_ganji_input = st.text_input("직접 입력:", value="기축년 병인월 신사일")
        saju_btn = st.button("운세 풀이 시작 ✨")

    with col2:
        if saju_btn:
            model = genai.GenerativeModel(selected_model)
            with st.spinner("만세력 계산 중..."):
                try:
                    is_lunar = True if calendar_type == "음력" else False
                    calc_ganji, solar_date_str = get_ganji(birth_date.year, birth_date.month, birth_date.day, "", is_lunar, is_leap_month)
                    target_info = user_ganji_input if (manual_check and user_ganji_input) else calc_ganji
                    st.success(f"🧮 분석 대상: {target_info}")
                    prompt = f"당신은 명리학자입니다. 생년월일: {birth_date}({calendar_type}), {gender}, {birth_time}, 사주명식: {target_info}. 타고난 기질과 2026년 운세, 조언을 해주세요."
                    res = model.generate_content(prompt)
                    st.write(res.text)
                except Exception as e:
                    st.error(f"오류: {e}")

# =========================================================
# 기능 4: 미식가 비서 (신규 기능!)
# =========================================================
elif "미식가 비서" in menu:
    st.title("🍽️ 우리 동네 미식가 비서")
    st.info("AI가 맛집을 추천하고, 네이버 검색으로 검증까지 도와줍니다!")

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("😋 어디서 무엇을 드실까요?")
        location = st.text_input("지역 입력", placeholder="예: 종로3가, 강남역, 우리집 근처")
        food_type = st.text_input("메뉴 입력", placeholder="예: 김치찌개, 파스타, 보양식")
        
        st.markdown("##### 📌 선호하는 분위기")
        option1 = st.checkbox("👨‍👩‍👧‍👦 가족 모임")
        option2 = st.checkbox("🍷 조용한/분위기 있는")
        option3 = st.checkbox("💰 가성비 좋은")
        
        food_btn = st.button("맛집 찾아줘! 🔍")

    with col2:
        if food_btn:
            if not location or not food_type:
                st.warning("지역과 메뉴를 모두 입력해주세요.")
            else:
                model = genai.GenerativeModel(selected_model)
                
                # 옵션 텍스트 만들기
                options = []
                if option1: options.append("가족 모임하기 좋은")
                if option2: options.append("조용하고 분위기 있는")
                if option3: options.append("가격이 합리적인(가성비)")
                option_str = ", ".join(options)
                
                with st.spinner(f"AI가 '{location}'의 '{food_type}' 맛집을 찾는 중..."):
                    try:
                        prompt = f"""
                        당신은 맛집 전문 가이드입니다.
                        사용자가 '{location}' 지역에서 '{food_type}'을(를) 찾고 있습니다.
                        특별 요청: {option_str}
                        
                        1
