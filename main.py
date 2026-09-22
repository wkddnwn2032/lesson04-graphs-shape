import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    page_icon="🎬",
    layout="wide",
)

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"

st.title("영화 데이터 그래프 도감 2 - 분포와 관계")
st.write(
    "1년간 박스오피스 10위권에 든 영화 가운데 해당 기간에 개봉한 216편의 데이터를 살펴봅니다."
)


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, dtype={"movieCd": str, "openDt": str})

    # 데이터에 장르 구분자가 |와 /가 섞여 있는 경우가 있어 정리한다.
    # 단, '멜로/로맨스'는 하나의 장르명이므로 그대로 둔다.
    def first_genre(value):
        if pd.isna(value):
            return "미상"

        value = str(value).strip()

        # 먼저 |를 기준으로 첫 번째 장르를 선택
        first = value.split("|")[0].strip()

        # 일부 데이터는 여러 장르를 /로 기록하고 있다.
        # '멜로/로맨스' 자체는 하나의 장르명이므로 예외 처리한다.
        if "/" in first and first != "멜로/로맨스":
            first = first.split("/")[0].strip()

        return first if first else "미상"

    df["genre_first"] = df["genre"].apply(first_genre)
    return df


try:
    df = load_data()
except Exception as e:
    st.error("데이터를 불러오는 중 문제가 발생했습니다.")
    st.exception(e)
    st.stop()


# =========================================================
# 그래프 1. 장르별 영화 편수
# =========================================================
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
    hole=0.58,
)

# 작은 조각까지 퍼센트 숫자를 모두 표시하면 그래프가 너무 복잡해지므로
# 그래프 안에는 숫자를 표시하지 않고, 마우스를 올렸을 때 자세히 보여준다.
fig.update_traces(
    textinfo="none",
    hovertemplate=(
        "<b>%{label}</b><br>"
        "영화 편수: %{value}편<br>"
        "비율: %{percent}<extra></extra>"
    ),
)

fig.update_layout(
    title="장르별 영화 편수",
    legend_title_text="장르",
    margin=dict(t=70, b=20, l=20, r=20),
    height=560,
    annotations=[
        dict(
            text=f"<b>{len(df)}편</b>",
            x=0.5,
            y=0.5,
            font=dict(size=24),
            showarrow=False,
        )
    ],
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("### 이 그래프로 알 수 있는 것")
st.text_input(
    "한 문장으로 작성해 보세요.",
    placeholder="예: 어떤 장르의 영화가 가장 많고, 각 장르가 전체에서 어느 정도의 비중을 차지하는지 알 수 있다.",
    key="graph1_observation",
)

st.caption(f"분석 대상: {len(df):,}편")


# =========================================================
# 그래프 2. 장르별 영화 총 관객 트리맵
# =========================================================
st.subheader("2. 장르별 영화 총 관객 트리맵")

# 총 관객 수를 숫자로 변환하고, 영화명/장르가 없는 행은 제외한다.
treemap_df = df.copy()
treemap_df["total_audi"] = pd.to_numeric(
    treemap_df["total_audi"], errors="coerce"
)
treemap_df = treemap_df.dropna(
    subset=["genre_first", "movieNm", "total_audi"]
)
treemap_df = treemap_df[treemap_df["total_audi"] >= 0]

fig2 = px.treemap(
    treemap_df,
    path=["genre_first", "movieNm"],
    values="total_audi",
)

# 영화 칸에 마우스를 올렸을 때 영화명과 총 관객이 보이도록 설정
fig2.update_traces(
    hovertemplate=(
        "<b>%{label}</b><br>"
        "총 관객: %{value:,.0f}명"
        "<extra></extra>"
    ),
    root_color="lightgray",
)

fig2.update_layout(
    title="장르 안에 들어 있는 영화별 총 관객",
    margin=dict(t=70, b=20, l=20, r=20),
    height=700,
)

st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
st.markdown("### 이 그래프로 알 수 있는 것")
st.text_input(
    "한 문장으로 작성해 보세요.",
    placeholder="예: 어떤 장르에 관객 수가 많은 영화가 많이 포함되어 있는지 알 수 있다.",
    key="graph2_observation",
)
