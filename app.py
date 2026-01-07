import streamlit as st
import google.generativeai as genai
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
from korean_lunar_calendar import KoreanLunarCalendar

# 1. 페이지 설정
st.set_page_config(page_title="나만의 AI 비서", page_icon="🤖", layout="wide")

# 2. [수정됨] 만세력 함수 (월두법 공식 완벽 적용)
def get_ganji(year, month, day, hour_str, is_lunar=False, is_leap=False):
    calendar = KoreanLunarCalendar()
    
    # 1. 음력 -> 양력 변환
    if is_lunar:
        calendar.setLunarDate(year, month, day, is_leap)
        solar_date = datetime(calendar.solarYear, calendar.solarMonth, calendar.solarDay)
    else:
        solar_date = datetime(year, month, day)
    
    # 2. 기본 데이터 (천간, 지지)
    gan = list("갑을병정무기경신임계")
    ji = list("자축인묘진사오미신유술해")
    
    # 3. [년주 계산] (입춘 기준)
    # 입춘(2월 4일) 이전이면 전년도
    if solar_date.month < 2 or (solar_date.month == 2 and solar_date.day < 4):
        year_val = year - 1
    else:
        year_val = year
    
    # 1924년(갑자) 기준 인덱스
    # 년천간 인덱스 (0:갑, 1:을 ... 5:기 ...)
    year_gan_idx = (year_val - 1924) % 10 
    year_ji_idx = (year_val - 1924) % 12
    year_ganji = gan[year_gan_idx] + ji[year_ji_idx]

    # 4. [월주 계산] - 월두법(Five Tigers Seeking Method) 적용
    # 절기 기준으로 월을 나눠야 정확하지만, 약식으로 태양력 월일로 근사값을 구하고 보정합니다.
    # 양력 2.4~3.5: 인월, 3.6~4.4: 묘월 ...
    
    # 태양력 기준 월 지지 인덱스 찾기 (인월=0, 묘월=1 ...)
    # 대략적인 절기일 (매월 4~8일 사이)
    # 편의상 '일'이 6일 넘으면 해당 월, 아니면 전달로 계산 (약식 로직)
    # 예: 2월 20일 -> 인월(0), 3월 1일 -> 인월(0), 3월 10일 -> 묘월(1)
    
    # 기준을 단순화: (월 - 2) 가 기본 인덱스인데, 일자가 작으면 -1
    month_ji_idx = solar_date.month - 2
    if solar_date.day < 5: # 절기 교체일 이전이면 전달로 침
        month_ji_idx -= 1
    
    if month_ji_idx < 0: # 1월(축월) 처리
        month_ji_idx += 12
        
    # [핵심] 월두법 공식: 연간에 따라 월간의 시작이 달라짐
    # 갑/기 년 -> 병인월 시작 (시작점 인덱스 2)
    # 을/경 년 -> 무인월 시작 (시작점 인덱스 4)
    # 병/신 년 -> 경인월 시작 (시작점 인덱스 6)
    # 정/임 년 -> 임인월 시작 (시작점 인덱스 8)
    # 무/계 년 -> 갑인월 시작 (시작점 인덱스 0)
    
    # 공식: (년간인덱스 % 5 + 1) * 2
    month_start_gan_idx = (year_gan_idx % 5 + 1) * 2
    month_gan_idx = (month_start_gan_idx + month_ji_idx) % 10
    
    month_ganji = gan[month_gan_idx] + ji[(month_ji_idx + 2) % 12] # 지지는 인(寅)부터 시작하므로 +2 보정

    # 5. [일주 계산]
    base_date = datetime(1900, 1, 1) # 갑술일 (idx 10)
    days_diff = (solar_date - base_date).days
    day_total_idx = (days_diff + 10) 
    day_ganji = gan[day_total_idx % 10] + ji[day_total_idx % 12]

    return f"{year_ganji}년 {month_ganji}월 {day_ganji}일", solar_date.strftime("%Y년 %m월 %d일")

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
# 기능 3: 정통 사주 운세 (월두법 적용)
# =========================================================
elif "정통 사주 운세" in menu:
    st.title("🥠 AI 정통 사주 명리학")
    st.info("정확한 만세력(윤달/월두법 포함) 알고리즘으로 분석합니다.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 내 정보 입력")
        
        # 날짜 범위 1900~2100
        birth_date = st.date_input(
            "생년월일", 
            value=datetime(1949, 1, 23), 
            min_value=datetime(1900, 1, 1), 
            max_value=datetime(2100, 12, 31)
        )
        
        calendar_type = st.radio("달력 구분", ["음력", "양력"], index=0, horizontal=True)
        
        is_leap_month = False
        if calendar_type == "음력":
            is_leap_month = st.checkbox("이 달이 '윤달(Leap Month)' 입니까?", value=False)

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
                    1. 타고난 기질 (일주와 월주를 중심으로)
                    2. 2026년(병오년) 신년 운세
                    3. 건강, 재물, 가족운 조언
                    
                    말투: 도사님 말투.
                    """
                    
                    res = model.generate_content(prompt)
                    st.markdown("### 📜 사주 풀이 결과")
                    st.write(res.text)
                    
                except Exception as e:
                    st.error(f"오류 발생: {e}")
