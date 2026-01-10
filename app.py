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
    
    st.caption("⚙️ 설정")
    selected_model = st.selectbox("AI 모델 선택", ["gemini-pro", "gemini-1.5-flash"], index=0)
    
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
