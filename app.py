import streamlit as st
import google.generativeai as genai
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
from korean_lunar_calendar import KoreanLunarCalendar

# 1. 페이지 설정
st.set_page_config(page_title="나만의 AI 비서", page_icon="🤖", layout="wide")

# 2. 만세력 함수 (윤달 기능 포함)
def get_ganji(year, month, day, hour_str, is_lunar=False, is_leap=False):
    calendar = KoreanLunarCalendar()
    
    # 1. 음력 -> 양력 변환
    if is_lunar:
        calendar.setLunarDate(year, month, day, is_leap)
        solar_date = datetime(calendar.solarYear, calendar.solarMonth, calendar.solarDay)
    else:
        solar_date = datetime(year, month, day)
    
    # 2. 60갑자 리스트
    gan = list("갑을병정무기경신임계")
    ji = list("자축인묘진사오미신유술해")
    ganji_list = [gan[i % 10] + ji[i % 12] for i in range(60)]

    # 3. 년주 (입춘 기준)
    if solar_date.month < 2 or (solar_date.month == 2 and solar_date.day < 4):
        year_val = year - 1
    else:
        year_val = year
    
    year_idx = (year_val - 1924) % 60
    year_ganji = ganji_list[year_idx]

    # 4. 일주
    base_date = datetime(1900, 1, 1) # 갑술일
    days_diff = (solar_date - base_date).days
    day_idx = (days_diff + 10) % 60
    day_ganji = ganji_list[day_idx]

    return f"{year_ganji}년 (생략)월 {day_ganji}일", solar_date.strftime("%Y년 %m월 %d일")

# 3. 주식 리스트 캐싱
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
    menu = st.radio("기능 선택", ["🧭 인생 나침반", "💰 만능 자산 비서", "🥠 정통 사주 운세"], index=2)
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
        stock_df = get_all_stock_list()
        if stock_df.empty:
            selected_name, final_code = "", ""
        else:
            stock_list = stock_df['Display'].tolist()
            default_idx = stock_list.index("삼성전자 (005930)") if "삼성전자 (005930)" in stock_list else 0
            selected_item = st.selectbox("종목 선택", stock_list, index=default_idx)
            selected_name = selected_item.split(' (')[0]
            final_code = selected_item.split('(')[-1].replace(')', '')
        
        btn = st.button("분석 실행 🚀")

    with col2:
        if btn:
            try:
                df = fdr.DataReader(final_code, datetime.now() - timedelta(days=100))
                if not df.empty:
                    st.line_chart(df['Close'])
                    model = genai.GenerativeModel(selected_model)
                    prompt = f"'{selected_name}' 주가 분석해줘. 데이터: {df.tail(5).to_string()}"
                    res = model.generate_content(prompt)
                    st.write(res.text)
            except:
                st.error("데이터 조회 실패")

# =========================================================
# 기능 3: 정통 사주 운세 (날짜 범위 확장)
# =========================================================
elif "정통 사주 운세" in menu:
    st.title("🥠 AI 정통 사주 명리학")
    st.info("정확한 만세력(윤달 포함) 알고리즘으로 분석합니다.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 내 정보 입력")
        
        # [수정] 날짜 범위를 1900년 ~ 2100년으로 대폭 확장
        birth_date = st.date_input(
            "생년월일", 
            value=datetime(1949, 7, 10), 
            min_value=datetime(1900, 1, 1), 
            max_value=datetime(2100, 12, 31)
        )
        
        calendar_type = st.radio("달력 구분", ["음력", "양력"], index=0, horizontal=True)
        
        # 윤달 체크박스
        is_leap_month = False
        if calendar_type == "음력":
            is_leap_month = st.checkbox("이 달이 '윤달(Leap Month)' 입니까?", value=True)

        gender = st.radio("성별", ["남성", "여성"], index=1, horizontal=True)
        birth_time = st.time_input("태어난 시간", value=datetime.strptime("17:15", "%H:%M").time())
        
        st.markdown("---")
        manual_check = st.checkbox("⚠️ 사주팔자 직접 입력하기 (옵션)")
        user_ganji_input = ""
        if manual_check:
            user_ganji_input = st.text_input("직접 입력:", value="기축년 신미월 을미일")

        saju_btn = st.button("운세 풀이 시작 ✨")

    with col2:
        if saju_btn:
            model = genai.GenerativeModel(selected_model)
            
            with st.spinner("🧮 만세력 계산 중..."):
                try:
                    is_lunar = True if calendar_type == "음력" else False
                    
                    calc_ganji, solar_date_str = get_ganji(
                        birth_date.year, birth_date.month, birth_date.day, 
                        "", is_lunar, is_leap_month
                    )
                    
                    target_info = ""
                    if manual_check and user_ganji_input:
                        target_info = f"사용자 입력 사주: {user_ganji_input}"
                        st.success(f"입력하신 사주 [{user_ganji_input}]로 풀이합니다.")
                    else:
                        target_info = f"계산된 사주: {calc_ganji} (양력변환: {solar_date_str})"
                        month_type = "윤달" if is_leap_month else "평달"
                        st.info(f"📅 변환: {birth_date} ({month_type}) → 양력 {solar_date_str}")
                        st.success(f"🧮 간지: {calc_ganji}")

                    prompt = f"""
                    당신은 조선 최고의 명리학자입니다.
                    
                    [사용자 정보]
                    - 생년월일: {birth_date} ({calendar_type}, { "윤달" if is_leap_month else "평달" })
                    - 성별: {gender}
                    - 태어난 시간: {birth_time}
                    - **사주 명식**: {target_info}
                    
                    [요청 사항]
                    1. 타고난 기질 (일주 중심)
                    2. 2026년(병오년) 신년 운세
                    3. 건강, 재물, 가족운 조언
                    
                    말투: 도사님 말투.
                    """
                    
                    res = model.generate_content(prompt)
                    st.markdown("### 📜 사주 풀이 결과")
                    st.write(res.text)
                    
                except Exception as e:
                    st.error(f"오류 발생: {e}")
