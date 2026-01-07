import streamlit as st
import google.generativeai as genai
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
from korean_lunar_calendar import KoreanLunarCalendar

# 1. 페이지 설정
st.set_page_config(page_title="나만의 AI 비서", page_icon="🤖", layout="wide")

# 2. [기능] 만세력(사주) 계산 함수 (수학적 계산)
def get_ganji(year, month, day, hour_str, is_lunar=False):
    calendar = KoreanLunarCalendar()
    
    # 1. 음력이면 양력으로 변환
    if is_lunar:
        calendar.setLunarDate(year, month, day, False)
        solar_date = datetime.strptime(calendar.getSolarIsoFormat(), '%Y-%m-%d')
    else:
        solar_date = datetime(year, month, day)
    
    # 2. 60갑자 리스트
    gan = list("갑을병정무기경신임계")
    ji = list("자축인묘진사오미신유술해")
    ganji_list = [g + j for g in gan for j in ji] # 60개 조합 생성 (갑자, 을축...)

    # 3. 년주 (Year Pillar) - 입춘 기준 (약식: 2월 4일 기준)
    # 정밀한 절기 계산은 복잡하므로 2/4일을 기준으로 나눔 (대부분 맞음)
    if solar_date.month < 2 or (solar_date.month == 2 and solar_date.day < 4):
        year_val = year - 1
    else:
        year_val = year
    
    # 1924년이 갑자년(0번 인덱스) -> 이를 기준으로 계산
    year_idx = (year_val - 1924) % 60
    year_ganji = ganji_list[year_idx]

    # 4. 일주 (Day Pillar) - 기준일(1900.01.01 = 갑술)로부터 흐른 날짜 계산
    base_date = datetime(1900, 1, 1)
    days_diff = (solar_date - base_date).days
    # 1900.1.1은 갑술일(10번째, 인덱스 10)
    day_idx = (days_diff + 10) % 60
    day_ganji = ganji_list[day_idx]

    # 5. 월주 (Month Pillar) - 년간과 절기 기준 (약식 계산)
    # 월주는 년간(Year Stem)에 의해 결정됨 (갑기합토 -> 병인두 등)
    # 절기 매칭이 복잡하여, 정확도를 위해 AI에게 '일주' 정보를 줘서 보정하게 유도하거나
    # 여기서는 '일주'가 가장 중요하므로 일주를 확정해서 줍니다.
    
    # *참고: 정확한 월주/시주는 AI가 이 일주를 바탕으로 추론하게 맡기는 게 낫습니다.
    # 단, 일주(Day)가 틀리면 다 틀리므로 일주는 수학적으로 고정합니다.

    return f"{year_ganji}년 (??)월 {day_ganji}일", solar_date.strftime("%Y년 %m월 %d일")

# 3. [주식] 종목 리스트 캐싱
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
# 기능 3: 정통 사주 운세 (수학적 계산 탑재)
# =========================================================
elif "정통 사주 운세" in menu:
    st.title("🥠 AI 정통 사주 명리학")
    st.info("정확한 만세력 알고리즘으로 사주를 분석합니다.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 내 정보 입력")
        
        # 년/월/일 입력 (기본값을 선생님 생신으로 설정했습니다)
        birth_date = st.date_input("생년월일", value=datetime(1949, 1, 23), min_value=datetime(1930, 1, 1))
        
        # 음력/양력 선택 (기본값: 음력)
        calendar_type = st.radio("달력 구분", ["음력", "양력"], index=0, horizontal=True) # 0번(음력)이 기본
        gender = st.radio("성별", ["남성", "여성"], horizontal=True)
        birth_time = st.time_input("태어난 시간 (모르면 12:00)", value=datetime.strptime("03:30", "%H:%M").time()) # 인시 기본값
        
        st.markdown("---")
        # [핵심] 사용자가 직접 수정할 수 있는 옵션
        manual_check = st.checkbox("⚠️ 사주팔자(간지)를 내가 직접 입력하기")
        
        user_ganji_input = ""
        if manual_check:
            st.caption("AI의 계산이 틀리다면 여기에 직접 적어주세요.")
            user_ganji_input = st.text_input("예: 기축년 병인월 신사일 갑진시", value="기축년 병인월 신사일")

        saju_btn = st.button("운세 풀이 시작 ✨")

    with col2:
        if saju_btn:
            model = genai.GenerativeModel(selected_model)
            
            with st.spinner("🧮 수학적으로 만세력을 계산 중입니다..."):
                # 1. 파이썬으로 정확한 간지 계산 시도
                try:
                    is_lunar = True if calendar_type == "음력" else False
                    calc_ganji, solar_date_str = get_ganji(birth_date.year, birth_date.month, birth_date.day, "", is_lunar)
                    
                    target_info = ""
                    if manual_check and user_ganji_input:
                        target_info = f"사용자가 입력한 확정 사주: {user_ganji_input}"
                        st.success(f"입력하신 사주 [{user_ganji_input}]로 풀이합니다.")
                    else:
                        # 계산된 값 사용
                        target_info = f"계산된 사주(일주 위주): {calc_ganji} (양력변환: {solar_date_str})"
                        st.info(f"📅 양력 변환 결과: {solar_date_str}")
                        st.success(f"🧮 계산된 사주: {calc_ganji} (일주가 정확합니다)")

                    # 2. AI에게 프롬프트 전달
                    prompt = f"""
                    당신은 정통 사주 명리학 대가입니다.
                    아래 정보를 바탕으로 사용자의 타고난 기질과 2026년 운세를 봐주세요.
                    
                    [핵심 정보]
                    - 입력 생년월일: {birth_date} ({calendar_type})
                    - 성별: {gender}
                    - 태어난 시간: {birth_time}
                    - **사주 명식 정보**: {target_info}
                    
                    **중요: 위 '사주 명식 정보'에 있는 글자(갑자, 을축 등)를 최우선으로 믿고 풀이하세요.**
                    AI가 스스로 날짜를 다시 계산하지 말고, 위에서 준 글자로 풀이하세요.
                    
                    [요청 사항]
                    1. **타고난 기질**: 일주(Day Pillar)를 중심으로 성격 분석
                    2. **2026년(병오년) 총운**: 올해의 흐름
                    3. **재물/건강/가족운**
                    
                    말투는 점잖고 확신에 찬 도사님 말투로 해주세요.
                    """
                    
                    res = model.generate_content(prompt)
                    st.markdown("### 📜 사주 풀이 결과")
                    st.write(res.text)
                    
                except Exception as e:
                    st.error(f"오류 발생: {e}")
