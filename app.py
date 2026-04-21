import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# 1. 앱 설정: 제목 설정 및 모바일 화면 최적화
st.set_page_config(page_title="송수학", layout="centered")

# 2. 강력한 모바일 커스텀 디자인 (CSS)
# 버튼 강제 가로 배치 + 전체 화면 스크롤 금지 + 여백 제거
st.markdown("""
    <style>
    /* 1. 모바일에서도 버튼 3개를 강제로 가로 나란히 배치 */
    [data-testid="column"] {
        width: 33% !important;
        flex: 1 1 33% !important;
        min-width: 33% !important;
    }
    
    /* 2. 전체 앱 높이를 스마트폰 화면 하나(100vh)에 고정 (스크롤 방지) */
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 0rem !important;
        height: 100vh;
        overflow: hidden;
    }

    /* 3. 네비게이션 버튼 디자인: 터치하기 편한 크기와 둥근 모서리 */
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3.2em;
        font-size: 13px !important;
        font-weight: bold;
        background-color: #f8f9fa;
        border: 1px solid #d1d5db;
    }

    /* 4. 제목 크기 최적화 (모바일에서 한눈에 들어오게) */
    h1 {
        font-size: 1.6rem !important;
        margin-bottom: 0.5rem !important;
        text-align: center;
    }

    /* 5. 아이폰/안드로이드 특유의 '당겨서 새로고침' 기능 강제 차단 */
    html, body, [data-testid="stAppViewContainer"] {
        overscroll-behavior-y: none !important;
        overflow: hidden !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 및 세션 관리 (앱을 조작해도 데이터 유지)
if 'student_data' not in st.session_state:
    today = datetime.now().date()
    sample_names = ["김철수", "이영희", "박지민", "최하늘", "정민수", "강다은", "조세호", "윤서아", "한가람", "임재현"]
    sample_data = []
    for i, name in enumerate(sample_names):
        sample_data.append({
            "Name": name, 
            "Class": ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"][i%3], 
            "Last Payment": today - timedelta(days=i*3)
        })
    st.session_state.student_data = pd.DataFrame(sample_data)

# 현재 어떤 탭이 눌려있는지 저장
if 'page' not in st.session_state:
    st.session_state.page = "📍현황"

# 데이터 가공 함수
def get_processed_df():
    df = st.session_state.student_data.copy()
    df['Next Due'] = pd.to_datetime(df['Last Payment']).dt.date + timedelta(days=30)
    df['D-Day'] = (df['Next Due'] - datetime.now().date()).apply(lambda x: x.days)
    return df

# --- 메인 인터페이스 구성 ---
st.title("🏫 송수학 통합 관리")

# 4. 상단 메뉴 버튼 (강제 가로 3칸)
m1, m2, m3 = st.columns(3)
with m1:
    if st.button("📍현황"): st.session_state.page = "📍현황"
with m2:
    if st.button("👤관리"): st.session_state.page = "👤관리"
with m3:
    if st.button("💰회계"): st.session_state.page = "💰회계"

st.write("") # 버튼과 본문 사이 간격

current_df = get_processed_df()

# --- 5. 탭(페이지) 전환 로직 ---

# [1번 페이지: 인원 현황]
if st.session_state.page == "📍현황":
    target_class = st.selectbox("반 선택", ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"], label_visibility="collapsed")
    filtered = current_df[current_df['Class'] == target_class]
    st.write(f"현재 인원: **{len(filtered)}명**")
    # 높이를 제한하여 앱 전체가 길어지는 것을 방지 (내부 스크롤)
    st.dataframe(filtered[['Name', 'Next Due', 'D-Day']], height=260, use_container_width=True)

# [2번 페이지: 원생 관리]
elif st.session_state.page == "👤관리":
    sub1, sub2 = st.tabs(["➕ 등록", "❌ 퇴원"])
    with sub1:
        with st.form("add_form", clear_on_submit=True):
            n_name = st.text_input("이름", placeholder="성함 입력")
            n_class = st.selectbox("반", ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"])