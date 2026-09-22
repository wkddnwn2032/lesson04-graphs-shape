import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    page_icon="🎬",
    layout="wide",
)

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"

st.title("영화 데이터 그래프 도감 2 - 분포와 관계")
st.write("1년간 박스오피스 10위권에 든 영화 가운데 해당 기간에 개봉한 216편의 데이터를 살펴봅니다.")

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, dtype={"movieCd": str, "openDt": str})

    # 장르가 여러 개인 경우 첫 번째 장르만 사용
    if "genre" in df.columns:
        df["genre_first"] = (
            df["genre"]
            .fillna("미상")
            .astype(str)
            .str.split("|")
            .str[0]
            .str.strip()
        )
        df.loc[df["genre_first"].isin(["", "nan", "None"]), "genre_first"] = "미상"

    return df

try:
    df = load_data()
except Exception as e:
    st.error("데이터를 불러오는 중 문제가 발생했습니다.")
    st.exception(e)
    st.stop()

# ---------------------------------------------------------
# 그래프 1. 장르별 영화 편수
# ---------------------------------------------------------
st.subheader("1. 장르별 영화 편수")

genre_counts = (
    df["genre_first"]
    .value_counts()
    .rename_axis("장르")
    .reset_index(name="영화 편수")
)

fig = px.pie(
    genre_counts,
    names="장르",
    values="영화 편수",
    hole=0.55,
    title="장르별 영화 편수",
)

fig.update_traces(
    hovertemplate="<b>%{label}</b><br>편수: %{value}편<br>비율: %{percent}<extra></extra>"
)

fig.update_layout(
    legend_title_text="장르",
    margin=dict(t=60, b=20, l=20, r=20),
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("### 이 그래프로 알 수 있는 것")
st.text_input(
    "한 문장으로 작성해 보세요.",
    placeholder="예: 가장 많은 영화가 어떤 장르인지, 장르별 비중이 어떻게 다른지 알 수 있다.",
    key="graph1_observation",
)

st.caption(f"분석 대상: {len(df):,}편")
