import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 1. 앱 설정 (최우선 실행)
st.set_page_config(page_title="송수학 관리", layout="centered")

# 2. 안전한 디자인 (CSS) - 에러 유발 요소 제거
st.markdown("""
    <style>
    /* 가로 버튼 정렬: 에러 없는 안전한 방식 */
    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        font-weight: bold;
        background-color: #f8f9fa;
        border: 1px solid #d1d5db;
    }
    
    /* 화면을 가두지 않고 자연스럽게 스크롤되도록 복구 */
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
    }
    
    /* 당겨서 새로고침 방지는 유지하되 조심스럽게 적용 */
    html, body {
        overscroll-behavior-y: contain;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 초기화 (에러 방지용 체크)
if 'student_data' not in st.session_state:
    today = datetime.now().date()
    # 기본 데이터 (최소한으로 시작)
    st.session_state.student_data = pd.DataFrame([
        {"Name": "테스트1", "Class": "17:00 (고1)", "Last Payment": today},
        {"Name": "테스트2", "Class": "19:00 (고2)", "Last Payment": today}
    ])

if 'page' not in st.session_state:
    st.session_state.page = "📍현황"

# 데이터 가공 함수 (에러 방지 로직 추가)
def get_processed_df():
    df = st.session_state.student_data.copy()
    if df.empty:
        return pd.DataFrame(columns=['Name', 'Class', 'Last Payment', 'Next Due', 'D-Day'])
    df['Last Payment'] = pd.to_datetime(df['Last Payment']).dt.date
    df['Next Due'] = df['Last Payment'] + timedelta(days=30)
    df['D-Day'] = (df['Next Due'] - datetime.now().date()).apply(lambda x: x.days)
    return df

# --- 메인 화면 시작 ---
st.title("🏫 송수학 통합 관리")

# 4. 가로 메뉴 버튼 (st.columns를 표준 방식으로 사용)
m1, m2, m3 = st.columns(3)
with m1:
    if st.button("📍현황"): st.session_state.page = "📍현황"
with m2:
    if st.button("👤관리"): st.session_state.page = "👤관리"
with m3:
    if st.button("💰회계"): st.session_state.page = "💰회계"

st.divider()

current_df = get_processed_df()

# --- 5. 탭(페이지) 전환 로직 ---

# [1. 현황 페이지]
if st.session_state.page == "📍현황":
    st.subheader("타임별 인원")
    target_class = st.selectbox("반 선택", ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"])
    filtered = current_df[current_df['Class'] == target_class]
    st.write(f"현재: **{len(filtered)}명**")
    st.dataframe(filtered[['Name', 'Next Due', 'D-Day']], use_container_width=True, height=300)

# [2. 관리 페이지]
elif st.session_state.page == "👤관리":
    st.subheader("원생 관리")
    sub1, sub2 = st.tabs(["➕ 등록", "❌ 퇴원"])
    
    with sub1:
        with st.form("add_student", clear_on_submit=True):
            n_name = st.text_input("학생 이름")
            n_class = st.selectbox("반", ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"])
            if st.form_submit_button("등록 완료"):
                if n_name:
                    new_row = pd.DataFrame([{"Name": n_name, "Class": n_class, "Last Payment": datetime.now().date()}])
                    st.session_state.student_data = pd.concat([st.session_state.student_data, new_row], ignore_index=True)
                    st.rerun()
    
    with sub2:
        if not current_df.empty:
            del_target = st.selectbox("삭제할 학생", [""] + current_df['Name'].tolist())
            if st.button("영구 삭제"):
                if del_target:
                    st.session_state.student_data = st.session_state.student_data[st.session_state.student_data['Name'] != del_target]
                    st.rerun()
        else:
            st.write("삭제할 데이터가 없습니다.")

# [3. 회계 페이지]
elif st.session_state.page == "💰회계":
    st.subheader("회계 현황")
    c1, c2 = st.columns(2)
    total_rev = len(current_df) * 300000
    c1.metric("월 예상 수익", f"{total_rev - 1100000:,.0f}원")
    c2.metric("총 원생", f"{len(current_df)}명")
    
    st.divider()
    st.write("**🔔 결제 알림 (D-5)**")
    alerts = current_df[current_df['D-Day'] <= 5].sort_values('D-Day')
    if not alerts.empty:
        st.dataframe(alerts[['Name', 'D-Day']], use_container_width=True)
    else:
        st.write("임박한 결제가 없습니다.")