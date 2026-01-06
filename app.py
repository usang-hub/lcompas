import streamlit as st
import google.generativeai as genai
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="나만의 AI 비서", page_icon="🤖", layout="wide")

# 2. [핵심] 한국 주식 종목 리스트 미리 가져오기 (캐싱으로 속도 최적화)
@st.cache_data
def get_krx_list():
    try:
        df = fdr.StockListing('KRX') # 한국거래소 상장 종목 전체
        return df[['Code', 'Name']]
    except:
        return pd.DataFrame(columns=['Code', 'Name'])

# --- 사이드바 ---
with st.sidebar:
    st.title("🤖 AI 비서실")
    menu = st.radio("기능 선택", ["🧭 인생 나침반", "💰 실시간 자산 비서"], index=1)
    st.markdown("---")
    
    # 모델 선택
    selected_model = st.selectbox(
        "사용 모델", 
        ["gemini-2.0-flash-exp", "gemini-1.5-flash"], 
        index=0
    )
    
    # API 키 확인
    if "GOOGLE_API_KEY" in st.secrets:
        st.success("시스템 가동 중... ✅")
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
            res = model.generate_content(f"70대 멘토로서 조언해주세요: {worry}")
            st.write(res.text)

# =========================================================
# 기능 2: 실시간 자산 비서 (최종 스마트 버전)
# =========================================================
elif menu == "💰 실시간 자산 비서":
    st.title("💰 실시간 투자 분석 비서")
    
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🔍 종목 검색")
        
        # 1. 사용자가 입력한 값
        user_input = st.text_input("종목명 또는 코드 입력", value="POSCO홀딩스", placeholder="예: sk하이닉스, posco홀딩스")
        
        # 2. 스마트 검색 로직 (대소문자/공백 무시)
        search_code = user_input.strip() # 기본값
        found_name = None
        
        # 입력값이 숫자가 아니고(이름이고), 영어/한글일 때
        if not user_input.isdigit():
            # KRX 리스트 가져오기
            krx_df = get_krx_list()
            
            if not krx_df.empty:
                # 검색어와 종목명을 모두 '대문자'로 바꾸고 '공백'을 없애서 비교함
                # 예: "sk 하이닉스" -> "SK하이닉스" == "SK하이닉스"
                clean_input = user_input.upper().replace(" ", "")
                
                # 데이터프레임에서 찾기
                # (종목명 리스트를 순회하며 비교)
                results = krx_df[krx_df['Name'].str.upper().str.replace(" ", "") == clean_input]
                
                if not results.empty:
                    search_code = results.iloc[0]['Code']
                    found_name = results.iloc[0]['Name']
                    st.success(f"찾았습니다! '{found_name}' (코드: {search_code})")
                else:
                    # 정확히 못 찾았을 경우, 포함된 글자라도 찾기 (보너스 기능)
                    partial = krx_df[krx_df['Name'].str.upper().str.contains(clean_input)]
                    if not partial.empty:
                        st.info(f"혹시 이걸 찾으시나요? : {partial.iloc[0]['Name']} ({partial.iloc[0]['Code']})")
                        search_code = partial.iloc[0]['Code'] # 첫 번째 추측값으로 자동 설정

        analyze_btn = st.button("시세 조회 및 분석")
        
        st.caption("팁: 'sk하이닉스'처럼 소문자로 써도 찾아줍니다.")

    with col2:
        if analyze_btn:
            try:
                # 해외 주식이나 코인은 그대로 둠, 한국 주식만 코드로 변환된 값 사용
                target_symbol = search_code 
                
                with st.spinner(f"데이터를 가져오는 중... ({target_symbol})"):
                    # 데이터 가져오기 (최근 60일)
                    df = fdr.DataReader(target_symbol, datetime.now() - timedelta(days=60))
                    
                    if df.empty:
                        st.error(f"❌ '{target_symbol}' 데이터를 찾을 수 없습니다.")
                        st.write("해외주식은 티커(AAPL), 코인은 (BTC/KRW)로 입력해주세요.")
                    else:
                        latest_close = df.iloc[-1]['Close']
                        latest_date = df.index[-1].strftime('%Y-%m-%d')
                        
                        # 종목 이름 보여주기 (찾은 이름이 있으면 그걸로, 없으면 코드)
                        display_name = found_name if found_name else target_symbol
                        
                        st.subheader(f"{display_name} 주가 차트")
                        st.line_chart(df['Close'])
                        st.metric(label=f"현재가 ({latest_date} 기준)", value=f"{latest_close:,.0f} 원/포인트")

                        # AI 분석
                        model = genai.GenerativeModel(selected_model)
                        with st.spinner("🤖 AI가 차트를 보고 분석 중입니다..."):
                            data_text = df.tail(10).to_string()
                            prompt = f"""
                            당신은 전문 투자 애널리스트입니다.
                            다음은 '{display_name}'의 최근 주가 데이터입니다.
                            
                            [최근 주가 데이터]
                            {data_text}
                            
                            1. 현재 추세 진단 (상승/하락/보합)
                            2. 기술적 분석 (이평선, 지지선 등 관점)
                            3. 투자 조언 (단기/중장기 관점)
                            
                            초보자도 알기 쉽게 설명해주세요.
                            """
                            res = model.generate_content(prompt)
                            st.markdown("### 📊 AI 투자 리포트")
                            st.write(res.text)

            except Exception as e:
                st.error("데이터 조회 중 오류가 발생했습니다.")
                st.error(f"내용: {e}")
