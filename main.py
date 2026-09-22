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
hist_df = hist_df.dropna(subset=["total_audi", "movieNm"]).copy()
hist_df = hist_df[hist_df["total_audi"] >= 0].copy()

if not hist_df.empty:
    max_audi = int(hist_df["total_audi"].max())

    # 최대 관객 수를 기준으로 1천만 명 단위의 구간을 만든다.
    # 너무 많은 구간이 생기지 않도록 최소 100만 명 단위를 사용한다.
    raw_width = max_audi / 10 if max_audi > 0 else 1_000_000
    unit = 1_000_000
    bin_width = max(unit, int((raw_width + unit - 1) // unit) * unit)
    bin_end = max(bin_width, ((max_audi // bin_width) + 1) * bin_width)

    # 그래프에 사용할 구간을 직접 만들어서 Plotly histogram의 자동 구간 문제를 피한다.
    edges = list(range(0, bin_end + bin_width, bin_width))
    hist_df["관객 구간"] = pd.cut(
        hist_df["total_audi"],
        bins=edges,
        right=False,
        include_lowest=True,
    )

    distribution = (
        hist_df["관객 구간"]
        .value_counts(sort=False)
        .reset_index()
    )
    distribution.columns = ["관객 구간", "영화 편수"]
    distribution["구간"] = distribution["관객 구간"].apply(
        lambda x: f"{int(x.left):,}~{int(x.right):,}"
    )

    fig3 = px.bar(
        distribution,
        x="구간",
        y="영화 편수",
        labels={"구간": "총 관객 수 구간", "영화 편수": "영화 편수"},
        text="영화 편수",
    )

    fig3.update_traces(
        hovertemplate=(
            "총 관객 구간: %{x}명<br>"
            "영화 편수: %{y}편"
            "<extra></extra>"
        ),
        textposition="outside",
    )

    fig3.update_layout(
        title="영화별 총 관객 수 분포",
        xaxis_title="총 관객 수 구간(명)",
        yaxis_title="영화 편수",
        margin=dict(t=70, b=80, l=20, r=20),
        height=560,
    )

    st.plotly_chart(fig3, use_container_width=True)

    # 가장 많은 영화가 몰려 있는 구간
    busiest_index = distribution["영화 편수"].idxmax()
    busiest_row = distribution.loc[busiest_index]
    busiest_count = int(busiest_row["영화 편수"])
    busiest_label = str(busiest_row["구간"])

    # 가장 관객이 많은 영화
    top_movie = hist_df.loc[hist_df["total_audi"].idxmax()]
    top_movie_name = str(top_movie["movieNm"])
    top_movie_audi = int(top_movie["total_audi"])

    st.info(
        f"📊 가장 많은 영화가 몰려 있는 구간은 "
        f"**{busiest_label}명**으로, **{busiest_count}편**의 영화가 이 구간에 있습니다.  \n"
        f"🏆 가장 관객이 많은 영화는 **{top_movie_name}**으로, "
        f"총 **{top_movie_audi:,}명**의 관객을 기록했습니다."
    )

    st.markdown("---")
    st.markdown("### 이 그래프로 알 수 있는 것")
    st.text_input(
        "한 문장으로 작성해 보세요.",
        placeholder="예: 영화의 총 관객 수가 어느 구간에 가장 많이 몰려 있는지 알 수 있다.",
        key="graph3_observation",
    )
else:
    st.warning("총 관객 수 데이터를 확인할 수 없습니다.")


# =========================================================
# 그래프 4. 개봉일 스크린 수와 총 관객의 관계
# =========================================================
st.subheader("4. 개봉일 스크린 수와 총 관객의 관계")

scatter_df = df.copy()
scatter_df["first_scrn"] = pd.to_numeric(
    scatter_df["first_scrn"], errors="coerce"
)
scatter_df["total_audi"] = pd.to_numeric(
    scatter_df["total_audi"], errors="coerce"
)
scatter_df = scatter_df.dropna(
    subset=["first_scrn", "total_audi", "movieNm", "genre_first"]
).copy()
scatter_df = scatter_df[
    (scatter_df["first_scrn"] >= 0) & (scatter_df["total_audi"] >= 0)
].copy()

if not scatter_df.empty:
    fig4 = px.scatter(
        scatter_df,
        x="first_scrn",
        y="total_audi",
        color="genre_first",
        hover_name="movieNm",
        labels={
            "first_scrn": "개봉일 스크린 수",
            "total_audi": "총 관객 수",
            "genre_first": "장르",
        },
        title="개봉일 스크린 수와 총 관객 수의 관계",
    )

    fig4.update_traces(
        marker=dict(size=9, opacity=0.75),
        hovertemplate=(
            "영화명: %{hovertext}<br>"
            "개봉일 스크린 수: %{x:,.0f}개<br>"
            "총 관객 수: %{y:,.0f}명"
            "<extra></extra>"
        ),
    )

    fig4.update_layout(
        xaxis_title="개봉일 스크린 수(개)",
        yaxis_title="총 관객 수(명)",
        legend_title_text="장르",
        margin=dict(t=70, b=60, l=20, r=20),
        height=650,
    )

    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")
    st.markdown("### 이 그래프로 알 수 있는 것")
    st.text_input(
        "한 문장으로 작성해 보세요.",
        placeholder="예: 개봉일 스크린 수가 많을수록 총 관객 수가 많은 경향이 있는지 확인할 수 있다.",
        key="graph4_observation",
    )
else:
    st.warning("스크린 수와 총 관객 수 데이터를 확인할 수 없습니다.")


# =========================================================
# 그래프 5. 장르별 총 관객 수 상자 그림
# =========================================================
st.subheader("5. 장르별 총 관객 수 분포")

box_df = df.copy()
box_df["total_audi"] = pd.to_numeric(
    box_df["total_audi"], errors="coerce"
)
box_df = box_df.dropna(
    subset=["genre_first", "total_audi", "movieNm"]
).copy()
box_df = box_df[box_df["total_audi"] >= 0].copy()

# 영화가 10편 이상인 장르만 선택한다.
genre_counts = box_df["genre_first"].value_counts()
selected_genres = genre_counts[genre_counts >= 10].index.tolist()
box_df = box_df[box_df["genre_first"].isin(selected_genres)].copy()

if not box_df.empty:
    fig5 = px.box(
        box_df,
        x="genre_first",
        y="total_audi",
        points="outliers",
        custom_data=["movieNm"],
        labels={
            "genre_first": "장르",
            "total_audi": "총 관객 수",
        },
        title="영화가 10편 이상인 장르의 총 관객 수 분포",
    )

    fig5.update_traces(
        marker=dict(size=8),
        hovertemplate=(
            "영화명: %{customdata[0]}<br>"
            "총 관객 수: %{y:,.0f}명"
            "<extra></extra>"
        ),
    )

    fig5.update_layout(
        xaxis_title="장르",
        yaxis_title="총 관객 수(명)",
        margin=dict(t=70, b=70, l=20, r=20),
        height=650,
    )

    st.plotly_chart(fig5, use_container_width=True)

    st.markdown("---")
    st.markdown("### 이 그래프로 알 수 있는 것")
    st.text_input(
        "한 문장으로 작성해 보세요.",
        placeholder="예: 장르별 총 관객 수의 중앙값과 분포의 차이를 비교할 수 있다.",
        key="graph5_observation",
    )
else:
    st.warning("영화가 10편 이상인 장르의 데이터를 확인할 수 없습니다.")
