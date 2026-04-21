import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# 1. 앱 기본 설정 및 모바일 화면 최적화 (여백 최소화)
st.set_page_config(page_title="송수학", layout="centered")

# 2. 강력한 모바일 최적화 디자인 (CSS)
st.markdown("""
    <style>
    /* 상단 여백 극한으로 제거 */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    
    /* 네비게이션 버튼 디자인: 큼직하고 누르기 편하게 */
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        font-weight: bold;
        background-color: #f0f2f6;
        border: 1px solid #d1d5db;
    }
    
    /* 스마트폰 '당겨서 새로고침' 방지 및 전체 스크롤 고정 */
    html, body, [data-testid="stAppViewContainer"] {
        overscroll-behavior-y: none !important;
        overflow: hidden !important;
    }

    /* 표(Dataframe) 안의 텍스트 정렬 */
    .stDataFrame {
        border: 1px solid #e6e9ef;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 초기화 및 세션 상태 관리
if 'student_data' not in st.session_state:
    # 초기 샘플 데이터 (실제 데이터로 교체 가능)
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

# 어떤 페이지를 보여줄지 기억하는 변수
if 'page' not in st.session_state:
    st.session_state.page = "📍 현황"

# 상수 설정
FEE = 300000
EXPENSES = 1100000 # 임대료 + 관리비

# 헬퍼 함수: 데이터 가공
def get_processed_df():
    df = st.session_state.student_data.copy()
    df['Next Due'] = pd.to_datetime(df['Last Payment']).dt.date + timedelta(days=30)
    df['D-Day'] = (df['Next Due'] - datetime.now().date()).apply(lambda x: x.days)
    return df

# --- 4. 상단 네비게이션 메뉴 (가장 중요) ---
m1, m2, m3 = st.columns(3)
with m1:
    if st.button("📍 현황"): st.session_state.page = "📍 현황"
with m2:
    if st.button("👤 관리"): st.session_state.page = "👤 관리"
with m3:
    if st.button("💰 회계"): st.session_state.page = "💰 회계"

st.divider()

# 최신 데이터 불러오기
current_df = get_processed_df()

# --- 5. 페이지별 화면 렌더링 ---

# [페이지 1: 인원 현황]
if st.session_state.page == "📍 현황":
    st.write("### 📍 타임별 수강 현황")
    target_class = st.selectbox("반 선택", ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"])
    filtered = current_df[current_df['Class'] == target_class]
    
    st.write(f"현재 인원: **{len(filtered)}명**")
    # height=300으로 고정하여 앱 전체가 길어지는 것을 방지
    st.dataframe(filtered[['Name', 'Next Due', 'D-Day']], height=300, use_container_width=True)

# [페이지 2: 원생 관리]
elif st.session_state.page == "👤 관리":
    st.write("### 👤 원생 등록 및 삭제")
    
    # 추가 폼
    with st.expander("➕ 신규 원생 등록", expanded=True):
        with st.form("add_student_form", clear_on_submit=True):
            n_name = st.text_input("이름")
            n_class = st.selectbox("반 선택", ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"])
            if st.form_submit_button("등록 완료"):
                if n_name:
                    new_student = pd.DataFrame([{"Name": n_name, "Class": n_class, "Last Payment": datetime.now().date()}])
                    st.session_state.student_data = pd.concat([st.session_state.student_data, new_student], ignore_index=True)
                    st.success(f"{n_name} 등록 성공!")
                    st.rerun()
    
    st.divider()
    
    # 삭제 섹션
    with st.expander("❌ 퇴원 처리"):
        del_target = st.selectbox("삭제할 학생", [""] + current_df['Name'].tolist())
        if st.button("영구 삭제"):
            if del_target:
                st.session_state.student_data = st.session_state.student_data[st.session_state.student_data['Name'] != del_target]
                st.rerun()

# [페이지 3: 회계 및 알림]
elif st.session_state.page == "💰 회계":
    st.write("### 💰 회계 및 일정")
    
    # 1. 결제일 연장 기능
    with st.expander("🗓️ 결제일 연장 (휴강 등)"):
        target_s = st.selectbox("대상 학생", current_df['Name'].tolist())
        add_days = st.number_input("연장할 일수", value=1, min_value=1)
        if st.button("기간 연장 적용"):
            idx = st.session_state.student_data.index[st.session_state.student_data['Name'] == target_s][0]
            st.session_state.student_data.at[idx, 'Last Payment'] += timedelta(days=add_days)
            st.success("연장 완료!")
            st.rerun()

    # 2. 수익 지표
    total_revenue = len(current_df) * FEE
    profit = total_revenue - EXPENSES
    st.metric("예상 순수익", f"{profit:,.0f}원", delta=f"매출 {total_revenue:,.0f}원")

    # 3. 미납/임박 리스트 (표 안에서 스크롤)
    st.write("**🔔 결제 알림 (D-5 이내)**")
    alerts = current_df[current_df['D-Day'] <= 5].sort_values('D-Day')
    st.dataframe(alerts[['Class', 'Name', 'D-Day']], height=200, use_container_width=True)