
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="HighSchool Math Academy Manager", layout="wide")
# --- 스크롤 끼임 방지 마법의 코드 ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        overflow-y: auto;
    }
    </style>
""", unsafe_allow_html=True)
# --- 1. Data Initialization ---
if 'student_data' not in st.session_state:
    today = datetime.now().date()
    names = ["김철수", "이영희", "박지민", "최하늘", "정민수", "강다은", "조세호", "윤서아", "한가람", "임재현"]
    times = ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"]
    data = []
    for i, name in enumerate(names):
        data.append({
            "Name": name,
            "Class": times[i % 3],
            "Last Payment": today - timedelta(days=np.random.randint(5, 35))
        })
    st.session_state.student_data = pd.DataFrame(data)

# Financial Constants
RENT = 800000
UTILITY = 300000
FEE = 300000

# --- 2. Helper Functions ---
def get_processed_df():
    df = st.session_state.student_data.copy()
    df['Last Payment'] = pd.to_datetime(df['Last Payment']).dt.date
    df['Next Due'] = df['Last Payment'] + timedelta(days=30)
    df['Days Left'] = (df['Next Due'] - datetime.now().date()).apply(lambda x: x.days)
    return df

st.title("🏫 고등수학 학원 통합 관리 시스템")

# --- 3. Interface Layout ---
# Row 1: Time Slot Monitoring
st.subheader("📍 타임별 수강 인원 확인")
col1, col2, col3 = st.columns(3)
df_main = get_processed_df()

with col1:
    if st.button("17:00 (고1) 인원 확인"):
        st.info(f"고1반 현재: {len(df_main[df_main['Class']=='17:00 (고1)'])}명")
        st.dataframe(df_main[df_main['Class']=='17:00 (고1)'][['Name', 'Next Due']])

with col2:
    if st.button("19:00 (고2) 인원 확인"):
        st.info(f"고2반 현재: {len(df_main[df_main['Class']=='19:00 (고2)'])}명")
        st.dataframe(df_main[df_main['Class']=='19:00 (고2)'][['Name', 'Next Due']])

with col3:
    if st.button("21:00 (고3) 인원 확인"):
        st.info(f"고3반 현재: {len(df_main[df_main['Class']=='21:00 (고3)'])}명")
        st.dataframe(df_main[df_main['Class']=='21:00 (고3)'][['Name', 'Next Due']])

st.divider()

# Row 2: Student Admin (Add/Delete)
st.subheader("👤 원생 추가 및 삭제")
add_col, del_col = st.columns(2)

with add_col:
    st.write("**➕ 신규 원생 등록**")
    new_name = st.text_input("이름 입력")
    new_class = st.selectbox("반 선택", ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"])
    if st.button("원생 추가 (30일 자동 설정)"):
        if new_name:
            new_student = {"Name": new_name, "Class": new_class, "Last Payment": datetime.now().date()}
            st.session_state.student_data = pd.concat([st.session_state.student_data, pd.DataFrame([new_student])], ignore_index=True)
            st.success(f"{new_name} 학생이 등록되었습니다. (다음 결제일: 30일 뒤)")
            st.rerun()

with del_col:
    st.write("**❌ 원생 퇴원 처리**")
    del_target = st.selectbox("삭제할 학생 선택", [""] + df_main['Name'].tolist())
    if st.button("선택한 학생 삭제"):
        if del_target:
            st.session_state.student_data = st.session_state.student_data[st.session_state.student_data['Name'] != del_target]
            st.warning(f"{del_target} 학생이 삭제되었습니다.")
            st.rerun()

st.divider()

# Row 3: Admin Actions (Finance/Extensions)
st.subheader("⚙️ 학원 관리 및 회계")
admin_col1, admin_col2, admin_col3 = st.columns(3)

with admin_col1:
    st.write("**🗓️ 휴강 및 개인사정 연장**")
    target_student = st.selectbox("연장할 학생 선택", df_main['Name'].tolist())
    days_to_add = st.number_input("연장 일수", value=1, min_value=1)
    if st.button("결제일 연장 적용"):
        idx = st.session_state.student_data.index[st.session_state.student_data['Name'] == target_student][0]
        st.session_state.student_data.at[idx, 'Last Payment'] += timedelta(days=days_to_add)
        st.success(f"{target_student} 학생 {days_to_add}일 연장 완료")
        st.rerun()

with admin_col2:
    st.write("**🔔 미납 및 결제 임박 목록**")
    alerts = df_main[df_main['Days Left'] <= 5].sort_values('Days Left')
    if not alerts.empty:
        for _, row in alerts.iterrows():
            color = "red" if row['Days Left'] < 0 else "orange"
            st.markdown(f":{color}[[{row['Class']}] {row['Name']} - {row['Days Left']}일]")
    else:
        st.write("특이사항 없음")

with admin_col3:
    st.write("**💰 월간 회계 장부**")
    total_rev = len(df_main) * FEE
    total_exp = RENT + UTILITY
    st.metric("이번 달 예상 순수익", f"{total_rev - total_exp:,.0f}원")
    st.caption(f"매출: {total_rev:,.0f} / 지출: {total_exp:,.0f}")
