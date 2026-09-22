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


# =========================================================
# 그래프 3. 총 관객 수 분포
# =========================================================
st.subheader("3. 총 관객 수 분포")

hist_df = df.copy()
hist_df["total_audi"] = pd.to_numeric(hist_df["total_audi"], errors="coerce")
hist_df = hist_df.dropna(subset=["total_audi", "movieNm"])
hist_df = hist_df[hist_df["total_audi"] >= 0].copy()

if len(hist_df) > 0:
    max_audi = hist_df["total_audi"].max()

    # 전체 범위를 약 10개 구간으로 나누어 분포를 보기 쉽게 한다.
    bin_width = max(1_000_000, int(((max_audi / 10) + 999_999) // 1_000_000) * 1_000_000)
    bin_start = 0
    bin_end = int(((max_audi // bin_width) + 1) * bin_width)

    fig3 = px.histogram(
        hist_df,
        x="total_audi",
        nbins=max(1, int(bin_end / bin_width)),
        labels={"total_audi": "총 관객 수", "count": "영화 편수"},
    )

    fig3.update_traces(
        xbins=dict(
            start=bin_start,
            end=bin_end,
            size=bin_width,
        ),
        hovertemplate=(
            "총 관객 구간: %{x}<br>"
            "영화 편수: %{y}편"
            "<extra></extra>"
        ),
    )

    fig3.update_layout(
        title="영화별 총 관객 수 분포",
        xaxis_title="총 관객 수(명)",
        yaxis_title="영화 편수",
        xaxis=dict(
            tickformat=",",
        ),
        margin=dict(t=70, b=20, l=20, r=20),
        height=520,
    )

    st.plotly_chart(fig3, use_container_width=True)

    # 실제 히스토그램과 같은 구간으로 가장 많은 영화가 몰린 구간을 계산한다.
    hist_counts, hist_edges = pd.cut(
        hist_df["total_audi"],
        bins=list(range(bin_start, bin_end + bin_width, bin_width)),
        right=False,
        include_lowest=True,
    ).value_counts().sort_index(), None

    if len(hist_counts) > 0:
        busiest_bin = hist_counts.idxmax()
        busiest_count = int(hist_counts.max())

        # 가장 관객이 많은 영화
        top_movie = hist_df.loc[hist_df["total_audi"].idxmax()]
        top_movie_name = str(top_movie["movieNm"])
        top_movie_audi = int(top_movie["total_audi"])

        lower = int(busiest_bin.left)
        upper = int(busiest_bin.right)

        st.info(
            f"📊 가장 많은 영화가 몰려 있는 구간은 "
            f"**{lower:,}명 이상 ~ {upper:,}명 미만**으로, "
            f"**{busiest_count}편**의 영화가 이 구간에 있습니다.  \n"
            f"🏆 가장 관객이 많은 영화는 **{top_movie_name}**으로, "
            f"총 **{top_movie_audi:,}명**의 관객을 기록했습니다."
        )

    st.markdown("---")
    st.markdown("### 이 그래프로 알 수 있는 것")
    st.text_input(
        "한 문장으로 작성해 보세요.",
        placeholder="예: 영화의 총 관객 수가 특정 구간에 집중되어 있으며, 일부 영화는 매우 많은 관객을 기록한다.",
        key="graph3_observation",
    )
else:
    st.warning("총 관객 수 데이터를 확인할 수 없습니다.")
