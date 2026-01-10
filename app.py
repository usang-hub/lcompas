import streamlit as st
import google.generativeai as genai
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
from korean_lunar_calendar import KoreanLunarCalendar

# 1. 페이지 설정
st.set_page_config(page_title="나만의 AI 비서", page_icon="🤖", layout="wide")

# 2. [함수] 만세력 및 주식 데이터
def get_ganji(year, month, day, hour_str, is_lunar=False, is_leap=False):
    calendar = KoreanLunarCalendar()
    if is_lunar:
        calendar.setLunarDate(year, month, day, is_leap)
        solar_date = datetime(calendar.solarYear, calendar.solarMonth, calendar.solarDay)
    else:
        solar_date = datetime(year, month, day)
    
    gan = list("갑을병정무기경신임계")
    ji = list("자축인묘진사오미신유술해")
    
    if solar_date.month < 2 or (solar_date.month == 2 and solar_date.day < 4):
        year_val = year - 1
    else:
        year_val = year
    year_gan_idx = (year_val - 1924) % 10 
    year_ji_idx = (year_val - 1924) % 12
    year_ganji = gan[year_gan_idx] + ji[year_ji_idx]

    month_ji_idx = solar_date.month - 2
    if solar_date.day < 5: month_ji_idx -= 1
    if month_ji_idx < 0: month_ji_idx += 12
    month_start_gan_idx = (year_gan_idx % 5 + 1) * 2
    month_gan_idx = (month_start_gan_idx + month_ji_idx) % 10
    month_ganji = gan[month_gan_idx] + ji[(month_ji_idx + 2) % 12]

    base_date = datetime(1900, 1, 1) 
    days_diff = (solar_date - base_date).days
    day_total_idx = (days_diff + 10) 
    day_ganji = gan[day_total_idx % 10] + ji[day_total_idx % 12]

    return f"{year_ganji}년 {month_ganji}월 {day_ganji}일", solar_date.strftime("%Y년 %m월 %d일")

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
    
    st.subheader("🌟 라이프스타일")
    menu_life = st.radio("즐겨찾기", 
        ["🧭 인생 나침반", "💰 만능 자산 비서", "🥠 정통 사주 운세", "🍽️ 미식가 비서", "🏨 숙박/여행 비서", "🚍 교통/예매 비서"], 
        index=0)
    
    st.markdown("---")
    st.subheader("🛡️ 안심 케어")
    menu_safe = st.radio("건강/안전", ["선택안함", "🏥 건강검진 비서", "👮‍♂️ 스팸/피싱 탐지관"], index=0)
    
    if menu_safe != "선택안함":
        current_menu = menu_safe
    else:
        current_menu = menu_life

    st.markdown("---")
    
    # [수정됨] 모델 선택 기능 부활! (에러 방지용)
    st.caption("⚙️ 설정")
    selected_model = st.selectbox("AI 모델 선택", ["gemini-1.5-flash", "gemini-pro"], index=0)
    
    api_key = None
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("API Key 입력", type="password")
        
    if api_key:
        genai.configure(api_key=api_key)
        st.success("시스템 정상 가동 중 ✅")

# =========================================================
# 화면 표시 로직
# =========================================================

if current_menu == "🧭 인생 나침반":
    st.title("🧭 인생 나침반")
    worry = st.text_area("고민을 털어놓으세요", height=150)
    if st.button("조언 듣기") and worry:
        # [수정] selected_model 변수 사용
        model = genai.GenerativeModel(selected_model)
        with st.spinner("생각 중..."):
            st.write(model.generate_content(f"70대 멘토로서 답변: {worry}").text)

elif current_menu == "💰 만능 자산 비서":
    st.title("💰 만능 투자 분석 비서")
    col1, col2 = st.columns([1, 2])
    with col1:
        stock_df = get_all_stock_list()
        if stock_df.empty:
            manual_input = st.text_input("종목코드", value="005930")
            final_code = manual_input
            selected_name = "종목"
        else:
            stock_list = stock_df['Display'].tolist()
            idx = stock_list.index("삼성전자 (005930)") if "삼성전자 (005930)" in stock_list else 0
            selected_item = st.selectbox("종목 선택", stock_list, index=idx)
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
                    st.write(model.generate_content(f"'{selected_name}' 주가 분석. 데이터: {df.tail(5).to_string()}").text)
            except: st.error("데이터 조회 실패")

elif current_menu == "🥠 정통 사주 운세":
    st.title("🥠 AI 정통 사주 명리학")
    col1, col2 = st.columns([1,1])
    with col1:
        b_date = st.date_input("생년월일", value=datetime(1949, 1, 23), min_value=datetime(1900,1,1))
        cal_type = st.radio("달력", ["양력", "음력"], horizontal=True)
        is_leap = st.checkbox("윤달") if cal_type == "음력" else False
        gender = st.radio("성별", ["남성", "여성"], horizontal=True)
        b_time = st.time_input("태어난 시간", value=datetime.strptime("04:15", "%H:%M").time())
        if st.button("운세 풀이 ✨"):
            model = genai.GenerativeModel(selected_model)
            ganji, _ = get_ganji(b_date.year, b_date.month, b_date.day, "", (cal_type=="음력"), is_leap)
            st.success(f"사주: {ganji}")
            st.write(model.generate_content(f"명리학자로서 {b_date}({cal_type}), {gender}, {b_time}, 사주:{ganji}인 사람의 기질과 2026년 운세, 조언을 해주세요.").text)

elif current_menu == "🍽️ 미식가 비서":
    st.title("🍽️ 미식가 비서")
    loc = st.text_input("지역 (예: 종로3가)")
    menu = st.text_input("메뉴 (예: 한정식)")
    if st.button("맛집 찾기") and loc and menu:
        model = genai.GenerativeModel(selected_model)
        res = model.generate_content(f"'{loc}'의 '{menu}' 맛집 3곳 추천. 특징, 가격대 설명.").text
        st.write(res)
        st.link_button("네이버 후기 보기", f"https://search.naver.com/search.naver?query={loc} {menu} 맛집")

elif current_menu == "🏨 숙박/여행 비서":
    st.title("🏨 숙박/여행 비서")
    dest = st.text_input("여행지 (예: 속초)")
    if st.button("숙소 추천") and dest:
        model = genai.GenerativeModel(selected_model)
        st.write(model.generate_content(f"'{dest}' 여행 숙소(호텔,펜션) 3곳 추천. 특징과 가격대.").text)
        st.link_button("네이버 최저가 보기", f"https://search.naver.com/search.naver?query={dest} 숙소 추천")

elif current_menu == "🚍 교통/예매 비서":
    st.title("🚍 교통/예매 비서")
    st.info("출발지와 도착지를 입력하면, AI가 여행 팁을 드리고 시간표 검색을 연결해 드립니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        departure = st.text_input("출발지", placeholder="예: 서울")
        arrival = st.text_input("도착지", placeholder="예: 부산")
    with col2:
        transport_type = st.radio("교통 수단", ["KTX/열차", "고속버스/시외버스"], horizontal=True)
        
    if st.button("시간표 및 노선 확인 🔍"):
        if departure and arrival:
            # [수정] 여기서 에러가 났었습니다. selected_model로 교체 완료!
            model = genai.GenerativeModel(selected_model)
            with st.spinner("경로 분석 중..."):
                try:
                    msg = model.generate_content(f"{departure}에서 {arrival}까지 {transport_type}로 이동할 때 걸리는 대략적인 시간과 70대 어르신을 위한 여행/건강 팁을 한 문단으로 짧게 알려줘.").text
                    st.success("🤖 AI의 여행 조언")
                    st.write(msg)
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")
                    st.caption("사이드바에서 AI 모델을 'gemini-pro'로 변경해보세요.")
                
                st.markdown("---")
                st.subheader("🎫 실시간 시간표/예매 바로가기")
                
                query = f"{departure}에서 {arrival} {transport_type} 시간표"
                naver_url = f"https://search.naver.com/search.naver?query={query}"
                st.link_button(f"📅 네이버에서 '{query}' 실시간 확인", naver_url, use_container_width=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.link_button("🚆 레츠코레일 (기차 예매)", "https://www.letskorail.com", use_container_width=True)
                with c2:
                    st.link_button("🚌 코버스 (고속버스 예매)", "https://www.kobus.co.kr", use_container_width=True)
        else:
            st.warning("출발지와 도착지를 모두 입력해주세요.")

elif current_menu == "🏥 건강검진 비서":
    st.title("🏥 건강검진 결과 해석")
    h_data = st.text_area("결과표 내용 입력", height=150)
    age = st.number_input("나이", value=60)
    if st.button("분석하기") and h_data:
        model = genai.GenerativeModel(selected_model)
        st.write(model.generate_content(f"의사로서 분석해줘. 나이:{age}, 데이터:{h_data}. 쉬운 설명과 조언.").text)

elif current_menu == "👮‍♂️ 스팸/피싱 탐지관":
    st.title("👮‍♂️ 스팸/피싱 탐지관")
    msg = st.text_area("의심 문자 입력", height=150)
    if st.button("사기 판별") and msg:
        model = genai.GenerativeModel(selected_model)
        st.write(model.generate_content(f"사이버수사관으로서 분석해줘. 메시지:{msg}. 위험도와 대처법.").text)
