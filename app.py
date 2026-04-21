import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# 1. 앱 설정 및 모바일 최적화
st.set_page_config(page_title="송수학", layout="centered")

# 2. 강력한 커스텀 디자인 (CSS)
st.markdown("""
    <style>
    /* 가로형 7칸 슬림 바 디자인 */
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
        padding: 8px 1px !important;
        margin: 0 1px !important;
        font-size: 10px !important; /* 버튼이 많아져서 글자 크기 최적화 */
        font-weight: bold;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background-color: white !important;
        border-radius: 7px;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
        color: #007BFF;
    }
    div[data-testid="stRadio"] input { display: none; }
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    h1 { font-size: 1.4rem !important; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 오프라인 파일 저장 시스템 ---
DB_FILE = "students.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    else:
        return pd.DataFrame(columns=["Name", "Class", "Last Payment"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# 데이터 초기 로드
if 'student_data' not in st.session_state:
    st.session_state.student_data = load_data()

# 지출/수강료 설정 세션 유지
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

# 4. 가로 7버튼 통합 메뉴 (⚙️기타 추가)
menu = st.radio(
    "메뉴", 
    ["📍현황", "👤관리", "💰수익", "🛠️지출", "🔔알림", "🗓️연장", "⚙️기타"], 
    horizontal=True, 
    label_visibility="collapsed"
)

st.divider()
current_df = get_processed_df()

# [1. 현황]
if menu == "📍현황":
    target = st.selectbox("반", ["17:00", "19:00", "21:00"], label_visibility="collapsed")
    filtered = current_df[current_df['Class'].astype(str).str.contains(target, na=False)]
    st.write(f"현재 인원: **{len(filtered)}명**")
    st.dataframe(filtered[['Name', 'Next Due', 'D-Day']], use_container_width=True, height=350)

# [2. 관리]
elif menu == "👤관리":
    sub1, sub2 = st.tabs(["➕등록", "❌퇴원"])
    with sub1:
        with st.form("add_form", clear_on_submit=True):
            n_name = st.text_input("학생 이름")
            n_class = st.selectbox("반", ["17:00", "19:00", "21:00"])
            if st.form_submit_button("등록 완료"):
                if n_name:
                    new_row = pd.DataFrame([{"Name": n_name, "Class": n_class, "Last Payment": datetime.now().date()}])
                    st.session_state.student_data = pd.concat([st.session_state.student_data, new_row], ignore_index=True)
                    save_data(st.session_state.student_data)
                    st.success(f"✅ {n_name} 학생이 성공적으로 등록되었습니다!")
                    # 확인 문구를 보여주기 위해 잠깐 멈춤 없이 rerun 시 toast 사용 가능
                    st.toast(f"{n_name} 등록 완료!")
                else:
                    st.error("이름을 입력해주세요.")
    with sub2:
        del_target = st.selectbox("삭제 대상", [""] + current_df['Name'].tolist())
        if st.button("삭제 수행"):
            if del_target:
                st.session_state.student_data = st.session_state.student_data[st.session_state.student_data['Name'] != del_target]
                save_data(st.session_state.student_data)
                st.warning(f"🗑️ {del_target} 학생이 삭제되었습니다.")
                st.toast(f"{del_target} 삭제 완료")
                st.rerun()

# [3. 수익]
elif menu == "💰수익":
    r17 = len(current_df[current_df['Class'] == "17:00"]) * st.session_state.f17
    r19 = len(current_df[current_df['Class'] == "19:00"]) * st.session_state.f19
    r21 = len(current_df[current_df['Class'] == "21:00"]) * st.session_state.f21
    total_rev = r17 + r19 + r21
    st.metric("이번 달 매출", f"{total_rev:,.0f}원")
    st.metric("예상 순수익", f"{total_rev - (st.session_state.rent + st.session_state.other):,.0f}원")

# [4. 지출]
elif menu == "🛠️지출":
    st.write("**[수강료 및 지출 설정]**")
    st.session_state.f17 = st.number_input("고1 수강료", value=st.session_state.f17, step=10000)
    st.session_state.f19 = st.number_input("고2 수강료", value=st.session_state.f19, step=10000)
    st.session_state.f21 = st.number_input("고3 수강료", value=st.session_state.f21, step=10000)
    st.session_state.rent = st.number_input("월세", value=st.session_state.rent, step=10000)
    st.session_state.other = st.number_input("기타 공과금", value=st.session_state.other, step=5000)
    if st.button("설정 저장"):
        st.success("✅ 설정이 반영되었습니다!")

# [5. 알림]
elif menu == "🔔알림":
    st.subheader("결제 알림 (D-5)")
    alerts = current_df[current_df['D-Day'] <= 5].sort_values('D-Day')
    if not alerts.empty:
        st.dataframe(alerts[['Name', 'Class', 'D-Day']], use_container_width=True, height=350)
    else:
        st.success("깨끗합니다! 결제 예정 학생이 없습니다.")

# [6. 연장]
elif menu == "🗓️연장":
    target_s = st.selectbox("연장 학생", current_df['Name'].tolist())
    days = st.number_input("추가 일수", value=1, min_value=1)
    if st.button("기간 연장 적용"):
        idx = st.session_state.student_data.index[st.session_state.student_data['Name'] == target_s][0]
        new_date = pd.to_datetime(st.session_state.student_data.at[idx, 'Last Payment']).date() + timedelta(days=days)
        st.session_state.student_data.at[idx, 'Last Payment'] = str(new_date)
        save_data(st.session_state.student_data)
        st.success(f"🗓️ {target_s} 학생의 결제일이 {days}일 연장되었습니다!")
        st.toast("연장 완료!")

# [7. 기타] - 선용님이 요청하신 다운로드 기능!
elif menu == "⚙️기타":
    st.subheader("⚙️ 시스템 관리")
    st.write("서버가 초기화될 경우를 대비해 정기적으로 데이터를 백업하세요.")
    
    # CSV 다운로드 버튼
    csv = st.session_state.student_data.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 현재 데이터(CSV) 다운로드",
        data=csv,
        file_name=f"songmath_backup_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
    
    st.divider()
    st.info("💡 팁: 다운로드한 파일은 엑셀에서 바로 열어볼 수 있습니다.")