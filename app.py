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
    # 메뉴 5개로 확장!
    menu = st.radio("기능 선택", 
        ["🧭 인생 나침반", "💰 만능 자산 비서", "🥠 정통 사주 운세", "🍽️ 미식가 비서", "🏨 숙박/여행 비서"], 
        index=4 # 바로 테스트해보시라고 숙박 비서 선택
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
# 기능 4: 미식가 비서
# =========================================================
elif "미식가 비서" in menu:
    st.title("🍽️ 우리 동네 미식가 비서")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("😋 맛집 검색")
        location = st.text_input("지역 (예: 종로3가)", key="food_loc")
        food_type = st.text_input("메뉴 (예: 설렁탕)", key="food_menu")
        food_btn = st.button("맛집 찾기 🔍")

    with col2:
        if food_btn:
            if location and food_type:
                model = genai.GenerativeModel(selected_model)
                with st.spinner("맛집 검색 중..."):
                    # [주의] 따옴표 3개 잘 닫았습니다!
                    prompt = f"""
                    '{location}' 지역의 '{food_type}' 맛집 3곳을 추천해줘.
                    특징, 가격대, 추천 이유를 솔직하게 알려줘.
                    """
                    res = model.generate_content(prompt)
                    st.markdown(f"### 🍴 {location} 추천 맛집")
                    st.write(res.text)
                    
                    query = f"{location} {food_type} 맛집"
                    st.link_button(f"🟢 네이버 후기 확인 ({query})", f"https://search.naver.com/search.naver?query={query}")
            else:
                st.warning("지역과 메뉴를 입력해주세요.")

# =========================================================
# 기능 5: 숙박/여행 비서 (신규 추가!)
# =========================================================
elif "숙박/여행 비서" in menu:
    st.title("🏨 든든한 숙박/여행 비서")
    st.info("여행지 숙소 고민, 이제 AI에게 맡기세요. 최저가 검색까지 한 번에!")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("✈️ 어디로 떠나시나요?")
        travel_dest = st.text_input("여행지 입력", placeholder="예: 부산 해운대, 강원도 속초, 제주도")
        
        # 날짜와 인원
        c1, c2 = st.columns(2)
        with c1:
            people = st.number_input("인원 (명)", min_value=1, value=2)
        with c2:
            travel_type = st.selectbox("숙소 취향", ["호텔 (깔끔함)", "펜션/리조트 (가족)", "한옥/게스트하우스", "가성비 모텔"])
            
        # 추가 요청사항
        requests = st.text_input("특별 요청 (예: 오션뷰, 조식 포함, 10만원대)", placeholder="가격대나 원하시는 조건을 적어주세요")
        
        hotel_btn = st.button("숙소 추천해줘! 🛏️")

    with col2:
        if hotel_btn:
            if not travel_dest:
                st.warning("여행지를 입력해주세요!")
            else:
                model = genai.GenerativeModel(selected_model)
                
                with st.spinner(f"AI가 '{travel_dest}'의 좋은 숙소를 고르고 있습니다..."):
                    try:
                        # 숙박 전문 프롬프트
                        prompt = f"""
                        당신은 20년 경력의 여행사 가이드입니다.
                        손님이 '{travel_dest}'로 여행을 갑니다.
                        
                        [조건]
                        - 인원: {people}명
                        - 숙소 형태: {travel_type}
                        - 특별 요청: {requests}
                        
                        1. 조건에 맞는 추천 숙소 3곳을 뽑아주세요.
                        2. 각 숙소의 장점, 대략적인 1박 가격, 추천 이유를 설명해주세요.
                        3. 너무 비싼 곳만 추천하지 말고, 가성비 좋은 곳도 섞어주세요.
                        """
                        
                        res = model.generate_content(prompt)
                        
                        st.markdown(f"### 🏨 {travel_dest} 추천 숙소")
                        st.write(res.text)
                        
                        st.markdown("---")
                        st.success("마음에 드는 곳이 있나요? 실제 가격과 빈방을 확인해보세요!")
                        
                        # 네이버 호텔 검색 링크
                        query = f"{travel_dest} {travel_type} 추천"
                        naver_hotel_url = f"https://search.naver.com/search.naver?query={query}"
                        
                        # 아고다/부킹닷컴 같은 느낌을 주기 위한 버튼 배치
                        st.link_button(f"🟢 네이버에서 '{travel_dest}' 숙소 실시간 최저가 보기", naver_hotel_url)
                        
                    except Exception as e:
                        st.error("숙소를 찾는 중 문제가 발생했습니다.")
