import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# 1. 앱 설정 및 모바일 최적화
st.set_page_config(page_title="송수학", layout="centered")

# 2. 커스텀 디자인 (CSS)
st.markdown("""
    <style>
    div[data-testid="stRadio"] > div {
        flex-direction: row !important;
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 3px;
        border: 1px solid #d1d5db;
        display: flex;
        justify-content: space-between;
    }
    div[data-testid="stRadio"] label {
        flex: 1;
        text-align: center;
        padding: 8px 2px !important;
        margin: 0 1px !important;
        font-size: 11px !important;
        font-weight: bold;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background-color: white !important;
        border-radius: 7px;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
        color: #007BFF;
    }
    div[data-testid="stRadio"] input { display: none; }
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    h1 { font-size: 1.5rem !important; text-align: center; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 및 세션 초기화
if 'student_data' not in st.session_state:
    today = datetime.now().date()
    st.session_state.student_data = pd.DataFrame([
        {"Name": "김철수", "Class": "17:00", "Last Payment": today - timedelta(days=5)},
        {"Name": "이영희", "Class": "19:00", "Last Payment": today - timedelta(days=10)},
        {"Name": "박지민", "Class": "21:00", "Last Payment": today - timedelta(days=15)}
    ])

# 지출 및 반별 학원비 초기값 설정
if 'rent_cost' not in st.session_state: st.session_state.rent_cost = 800000
if 'other_cost' not in st.session_state: st.session_state.other_cost = 300000
if 'fee_17' not in st.session_state: st.session_state.fee_17 = 300000
if 'fee_19' not in st.session_state: st.session_state.fee_19 = 350000
if 'fee_21' not in st.session_state: st.session_state.fee_21 = 400000

def get_processed_df():
    df = st.session_state.student_data.copy()
    if df.empty: return pd.DataFrame(columns=['Name', 'Class', 'Last Payment', 'Next Due', 'D-Day'])
    df['Last Payment'] = pd.to_datetime(df['Last Payment']).dt.date
    df['Next Due'] = df['Last Payment'] + timedelta(days=30)
    df['D-Day'] = (df['Next Due'] - datetime.now().date()).apply(lambda x: x.days)
    return df

# --- 메인 인터페이스 ---
st.title("🏫 송수학 통합 관리")

menu_choice = st.radio(
    "메뉴", 
    ["📍현황", "👤관리", "💰수익", "⚙️설정", "🔔알림", "🗓️연장"], 
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()
current_df = get_processed_df()

# --- 5. 페이지 전환 로직 ---

if menu_choice == "📍현황":
    target_class = st.selectbox("반", ["17:00", "19:00", "21:00"], label_visibility="collapsed")
    filtered = current_df[current_df['Class'].str.contains(target_class)]
    st.write(f"현재: **{len(filtered)}명**")
    st.dataframe(filtered[['Name', 'Next Due', 'D-Day']], use_container_width=True, height=350)

elif menu_choice == "👤관리":
    sub1, sub2 = st.tabs(["➕등록", "❌퇴원"])
    with sub1:
        with st.form("add_form", clear_on_submit=True):
            n_name = st.text_input("학생이름")
            n_class = st.selectbox("반", ["17:00", "19:00", "21:00"])
            if st.form_submit_button("등록"):
                if n_name:
                    new_row = pd.DataFrame([{"Name": n_name, "Class": n_class, "Last Payment": datetime.now().date()}])
                    st.session_state.student_data = pd.concat([st.session_state.student_data, new_row], ignore_index=True)
                    st.rerun()
    with sub2:
        del_target = st.selectbox("삭제", [""] + current_df['Name'].tolist())
        if st.button("삭제 수행"):
            if del_target:
                st.session_state.student_data = st.session_state.student_data[st.session_state.student_data['Name'] != del_target]
                st.rerun()

elif menu_choice == "💰수익":
    st.subheader("이번 달 예상 수익")
    # 반별 매출 계산
    rev_17 = len(current_df[current_df['Class'] == "17:00"]) * st.session_state.fee_17
    rev_19 = len(current_df[current_df['Class'] == "19:00"]) * st.session_state.fee_19
    rev_21 = len(current_df[current_df['Class'] == "21:00"]) * st.session_state.fee_21
    
    total_rev = rev_17 + rev_19 + rev_21
    total_exp = st.session_state.rent_cost + st.session_state.other_cost
    
    st.metric("총 매출", f"{total_rev:,.0f}원")
    st.metric("예상 순수익", f"{total_rev - total_exp:,.0f}원")
    st.caption(f"반별 매출: 17시({rev_17:,.0f}) / 19시({rev_19:,.0f}) / 21시({rev_21:,.0f})")

elif menu_choice == "⚙️설정":
    st.subheader("⚙️ 단가 및 지출 설정")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**[반별 학원비]**")
        st.session_state.fee_17 = st.number_input("17:00반 (원)", value=st.session_state.fee_17, step=10000)
        st.session_state.fee_19 = st.number_input("19:00반 (원)", value=st.session_state.fee_19, step=10000)
        st.session_state.fee_21 = st.number_input("21:00반 (원)", value=st.session_state.fee_21, step=10000)
    with col2:
        st.write("**[고정 지출]**")
        st.session_state.rent_cost = st.number_input("월세 (원)", value=st.session_state.rent_cost, step=10000)
        st.session_state.other_cost = st.number_input("기타 (원)", value=st.session_state.other_cost, step=5000)

elif menu_choice == "🔔알림":
    st.subheader("결제 알림 목록")
    alerts = current_df[current_df['D-Day'] <= 5].sort_values('D-Day')
    if not alerts.empty:
        st.dataframe(alerts[['Name', 'Class', 'D-Day']], use_container_width=True, height=350)
    else:
        st.success("결제 임박 학생 없음")

elif menu_choice == "🗓️연장":
    st.subheader("일정 연장")
    target_s = st.selectbox("학생 선택", current_df['Name'].tolist())
    days = st.number_input("연장 일수", value=1, min_value=1)
    if st.button("적용"):
        idx = st.session_state.student_data.index[st.session_state.student_data['Name'] == target_s][0]
        st.session_state.student_data.at[idx, 'Last Payment'] += timedelta(days=days)
        st.rerun()