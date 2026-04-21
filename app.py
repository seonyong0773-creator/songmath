import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os # 파일이 있는지 확인하기 위한 도구

# 1. 앱 설정 및 모바일 최적화
st.set_page_config(page_title="송수학", layout="centered")

# 2. 디자인 최적화 (가로 6버튼 메뉴)
st.markdown("""
    <style>
    div[data-testid="stRadio"] > div {
        flex-direction: row !important;
        background-color: #f0f2f6;
        border-radius: 10px; padding: 3px; border: 1px solid #d1d5db;
        display: flex; justify-content: space-between;
    }
    div[data-testid="stRadio"] label {
        flex: 1; text-align: center; padding: 8px 2px !important;
        margin: 0 1px !important; font-size: 11px !important; font-weight: bold;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background-color: white !important; border-radius: 7px;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.1); color: #007BFF;
    }
    div[data-testid="stRadio"] input { display: none; }
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    h1 { font-size: 1.5rem !important; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 오프라인 파일 저장 시스템 (핵심!) ---
DB_FILE = "students.csv"

def load_data():
    # 파일이 있으면 읽어오고, 없으면 빈 데이터를 만듭니다.
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    else:
        return pd.DataFrame(columns=["Name", "Class", "Last Payment"])

def save_data(df):
    # 데이터를 CSV 파일로 저장합니다. (비밀 장부에 적기)
    df.to_csv(DB_FILE, index=False)

# 데이터 초기 로드
if 'student_data' not in st.session_state:
    st.session_state.student_data = load_data()

# 지출/수강료 설정 (이것도 세션에 저장)
settings = {'rent': 800000, 'other': 300000, 'f17': 300000, 'f19': 350000, 'f21': 400000}
for k, v in settings.items():
    if k not in st.session_state: st.session_state[k] = v

def get_processed_df():
    df = st.session_state.student_data.copy()
    if df.empty: return pd.DataFrame(columns=['Name', 'Class', 'Last Payment', 'Next Due', 'D-Day'])
    df['Last Payment'] = pd.to_datetime(df['Last Payment']).dt.date
    df['Next Due'] = df['Last Payment'] + timedelta(days=30)
    df['D-Day'] = (df['Next Due'] - datetime.now().date()).apply(lambda x: x.days)
    return df

# --- 메인 인터페이스 ---
st.title("🏫 송수학 통합 관리")

menu = st.radio("메뉴", ["📍현황", "👤관리", "💰수익", "⚙️설정", "🔔알림", "🗓️연장"], horizontal=True, label_visibility="collapsed")
st.divider()
current_df = get_processed_df()

# [1. 현황]
if menu == "📍현황":
    target = st.selectbox("반 선택", ["17:00", "19:00", "21:00"], label_visibility="collapsed")
    filtered = current_df[current_df['Class'].astype(str).str.contains(target, na=False)]
    st.write(f"인원: **{len(filtered)}명**")
    st.dataframe(filtered[['Name', 'Next Due', 'D-Day']], use_container_width=True, height=350)

# [2. 관리]
elif menu == "👤관리":
    sub1, sub2 = st.tabs(["➕등록", "❌퇴원"])
    with sub1:
        with st.form("add", clear_on_submit=True):
            n_name = st.text_input("이름")
            n_class = st.selectbox("반", ["17:00", "19:00", "21:00"])
            if st.form_submit_button("등록"):
                if n_name:
                    new_row = pd.DataFrame([{"Name": n_name, "Class": n_class, "Last Payment": datetime.now().date()}])
                    st.session_state.student_data = pd.concat([st.session_state.student_data, new_row], ignore_index=True)
                    save_data(st.session_state.student_data) # 파일에 저장!
                    st.success(f"{n_name} 등록 완료")
                    st.rerun()
    with sub2:
        del_target = st.selectbox("삭제", [""] + current_df['Name'].tolist())
        if st.button("삭제 수행"):
            st.session_state.student_data = st.session_state.student_data[st.session_state.student_data['Name'] != del_target]
            save_data(st.session_state.student_data) # 파일에 반영!
            st.rerun()

# [3. 수익]
elif menu == "💰수익":
    r17 = len(current_df[current_df['Class'] == "17:00"]) * st.session_state.f17
    r19 = len(current_df[current_df['Class'] == "19:00"]) * st.session_state.f19
    r21 = len(current_df[current_df['Class'] == "21:00"]) * st.session_state.f21
    total_rev = r17 + r19 + r21
    st.metric("총 매출", f"{total_rev:,.0f}원")
    st.metric("순수익", f"{total_rev - (st.session_state.rent + st.session_state.other):,.0f}원")

# [4. 설정]
elif menu == "⚙️설정":
    st.write("**[단가 설정]**")
    st.session_state.f17 = st.number_input("고1 (원)", value=st.session_state.f17)
    st.session_state.f19 = st.number_input("고2 (원)", value=st.session_state.f19)
    st.session_state.f21 = st.number_input("고3 (원)", value=st.session_state.f21)
    st.write("**[지출 설정]**")
    st.session_state.rent = st.number_input("월세 (원)", value=st.session_state.rent)
    st.session_state.other = st.number_input("기타 (원)", value=st.session_state.other)

# [5. 알림]
elif menu == "🔔알림":
    alerts = current_df[current_df['D-Day'] <= 5].sort_values('D-Day')
    st.dataframe(alerts[['Name', 'Class', 'D-Day']], use_container_width=True, height=400)

# [6. 연장]
elif menu == "🗓️연장":
    target_s = st.selectbox("학생 선택", current_df['Name'].tolist())
    days = st.number_input("연장 일수", value=1, min_value=1)
    if st.button("적용"):
        idx = st.session_state.student_data.index[st.session_state.student_data['Name'] == target_s][0]
        # 날짜 데이터 형식 맞춰서 연장
        new_date = pd.to_datetime(st.session_state.student_data.at[idx, 'Last Payment']).date() + timedelta(days=days)
        st.session_state.student_data.at[idx, 'Last Payment'] = str(new_date)
        save_data(st.session_state.student_data) # 파일에 저장!
        st.rerun()