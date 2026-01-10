import streamlit as st
import google.generativeai as genai
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
from korean_lunar_calendar import KoreanLunarCalendar

# 1. 페이지 설정
st.set_page_config(page_title="나만의 AI 비서", page_icon="🤖", layout="wide")

# 2. [함수] 만세력 (월두법 적용)
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

    # 월주 (월두법)
    month_ji_idx = solar_date.month - 2
    if solar_date.day < 5: 
        month_ji_idx -= 1
    if month_ji_idx < 0: 
        month_ji_idx += 12
        
    month_start_gan_idx = (year_gan_idx % 5 + 1) * 2
    month_gan_idx = (month_start_gan_idx + month_ji_idx) % 10
    month_ganji = gan[month_gan_idx] + ji[(month_ji_idx + 2) % 12]

    # 일주
    base_date = datetime(1900, 1, 1) 
    days_diff = (solar_date - base_date).days
    day_total_idx = (days_diff + 10) 
    day_ganji = gan[day_total_idx % 10] + ji[day_total_idx % 12]

    return f"{year_ganji}년 {month_ganji}월 {day_ganji}일", solar_date.strftime("%Y년 %m월 %d일")

# 3. [함수] 주식 리스트 캐싱 (실패 시 빈 데이터프레임 반환)
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
    menu = st.radio("기능 선택", ["🧭 인생 나침반", "💰 만능 자산 비서", "🥠 정통 사주 운세"], index=1) # 자산비서 기본 선택
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
# 기능 2: 만능 자산 비서 (안전장치 추가됨!)
# =========================================================
elif "만능 자산 비서" in menu:
    st.title("💰 만능 투자 분석 비서")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("🔍 종목 검색")
        
        # 주식 리스트 가져오기 시도
        stock_df = get_all_stock_list()
        
        # [핵심 수정] 리스트가 비어있으면(에러나면) -> 수동 입력창 보여주기
        if stock_df.empty:
            st.warning("⚠ 전체 목록 다운로드 지연. 코드를 직접 입력하세요.")
            # 수동 입력창
            manual_input = st.text_input("종목코드 입력", value="005930")
            final_code = manual_input
            selected_name = "종목" # 이름은 모름
        else:
            # 리스트가 잘 왔으면 -> 콤보박스 보여주기
            stock_list = stock_df['Display'].tolist()
            default_idx = stock_list.index("삼성전자 (005930)") if "삼성전자 (005930)" in stock_list else 0
            selected_item = st.selectbox("종목 선택", stock_list, index=default_idx)
            selected_name = selected_item.split(' (')[0]
            final_code = selected_item.split('(')[-1].replace(')', '')
        
        # 해외 주식 옵션
        with st.expander("🇺🇸 미국 주식 / 코인 직접 입력"):
             direct_code = st.text_input("티커 (예: TSLA, BTC/KRW)")
             if direct_code:
                 final_code = direct_code
                 selected_name = direct_code

        btn = st.button("분석 실행 🚀")

    with col2:
        if btn:
            try:
                # 차트 그리기
                df = fdr.DataReader(final_code, datetime.now() - timedelta(days=100))
                if not df.empty:
                    latest_price = df.iloc[-1]['Close']
                    st.subheader(f"{selected_name} 주가 차트")
                    st.line_chart(df['Close'])
                    st.metric("현재가", f"{latest_price:,.0f}")
                    
                    # AI 분석
                    model = genai.GenerativeModel(selected_model)
                    with st.spinner("AI가 분석 중입니다..."):
                        prompt = f"'{selected_name}' 주가 분석해줘. 데이터: {df.tail(5).to_string()}"
                        res = model.generate_content(prompt)
                        st.markdown("### 📊 AI 분석 리포트")
                        st.write(res.text)
                else:
                    st.error("데이터를 가져올 수 없습니다. 코드를 확인해주세요.")
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")

# =========================================================
# 기능 3: 정통 사주 운세
# =========================================================
elif "정통 사주 운세" in menu:
    st.title("🥠 AI 정통 사주 명리학")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 내 정보 입력")
        birth_date = st.date_input(
            "생년월일", value=datetime(1949, 1, 23), 
            min_value=datetime(1900, 1, 1), max_value=datetime(2100, 12, 31)
        )
        calendar_type = st.radio("달력 구분", ["음력", "양력"], horizontal=True)
        is_leap_month = False
        if calendar_type == "음력":
            is_leap_month = st.checkbox("이 달이 '윤달' 입니까?")
        gender = st.radio("성별", ["남성", "여성"], index=1, horizontal=True)
        birth_time = st.time_input("태어난 시간", value=datetime.strptime("04:15", "%H:%M").time())
        
        st.markdown("---")
        manual_check = st.checkbox("⚠️ 사주팔자 직접 입력하기 (옵션)")
        user_ganji_input = ""
        if manual_check:
            user_ganji_input = st.text_input("직접 입력:", value="기축년 병인월 신사일")

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

                    prompt = f"""
                    당신은 조선 최고의 명리학자입니다.
                    사용자 정보: {birth_date} ({calendar_type}), {gender}, {birth_time}
                    **사주 명식**: {target_info}
                    요청: 1.타고난 기질 2.2026년 운세 3.조언
                    """
                    res = model.generate_content(prompt)
                    st.write(res.text)
                except Exception as e:
                    st.error(f"오류: {e}")
