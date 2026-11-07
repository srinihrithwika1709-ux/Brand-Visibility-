import os
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# =====================================================
# BRANDPULSE — BRAND VISIBILITY INTELLIGENCE DASHBOARD
# =====================================================

st.set_page_config(
    page_title="BrandPulse | Brand Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Aesthetic theme ----------
NAVY = "#18243A"
TEAL = "#12B8A6"
PURPLE = "#8067E8"
CORAL = "#F28C76"
BLUE = "#4E8DF5"
MUTED = "#68758A"

st.markdown("""
<style>
    .stApp {
        background: #F4F7FB;
    }

    [data-testid="stHeader"] {
        background: rgba(244,247,251,0.92);
    }

    [data-testid="stSidebar"] {
        background: #18243A;
    }

    [data-testid="stSidebar"] * {
        color: #F2F5FA;
    }

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        color: #18243A;
        background: white;
    }

    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
        max-width: 1500px;
    }

    .hero {
        background: linear-gradient(120deg, #18243A 0%,
                    #263B5B 65%, #246E78 100%);
        padding: 30px 32px;
        border-radius: 20px;
        margin-bottom: 24px;
        color: white;
    }

    .hero h1 {
        color: white;
        font-size: 2.15rem;
        margin: 0 0 8px 0;
        font-weight: 750;
    }

    .hero p {
        color: #D4DFEE;
        margin: 0;
        font-size: 1rem;
    }

    .section-title {
        color: #18243A;
        font-size: 1.35rem;
        font-weight: 750;
        margin: 12px 0 4px 0;
    }

    .section-subtitle {
        color: #68758A;
        font-size: 0.91rem;
        margin-bottom: 16px;
    }

    [data-testid="stMetric"] {
        background: white;
        padding: 19px 20px;
        border: 1px solid #E6EBF2;
        border-radius: 16px;
        box-shadow: 0 4px 16px rgba(24,36,58,0.045);
    }

    [data-testid="stMetricLabel"] {
        color: #68758A;
    }

    [data-testid="stMetricValue"] {
        color: #18243A;
        font-weight: 750;
    }

    div[data-testid="stTabs"] button {
        font-weight: 650;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #E6EBF2;
        border-radius: 12px;
        overflow: hidden;
    }

    .insight {
        background: white;
        border-left: 4px solid #12B8A6;
        padding: 16px 18px;
        border-radius: 10px;
        color: #26354B;
        margin: 8px 0 16px 0;
        border-top: 1px solid #E6EBF2;
        border-right: 1px solid #E6EBF2;
        border-bottom: 1px solid #E6EBF2;
    }

    .footer {
        color: #68758A;
        text-align: center;
        padding: 22px 0 4px 0;
        font-size: 0.83rem;
    }

    .stButton button {
        border-radius: 9px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ---------- Load configuration ----------
PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / "notebooks" / ".env", override=True)

HOST = os.getenv("MYSQL_HOST", "localhost")
PORT = int(os.getenv("MYSQL_PORT", "3306"))
USER = os.getenv("MYSQL_USER", "root")
PASSWORD = os.getenv("MYSQL_PASSWORD")
DATABASE = os.getenv("MYSQL_DATABASE", "brand_visibility")


@st.cache_resource
def get_engine():
    if not PASSWORD:
        raise ValueError(
            "MYSQL_PASSWORD is missing from notebooks/.env"
        )

    url = (
        f"mysql+pymysql://{quote_plus(USER)}:"
        f"{quote_plus(PASSWORD)}@{HOST}:{PORT}/{DATABASE}"
    )
    return create_engine(url, pool_pre_ping=True)


@st.cache_data(ttl=60)
def load_data():
    with get_engine().connect() as connection:
        return pd.read_sql(
            text("SELECT * FROM products"),
            connection
        )


# ---------- Helpers ----------
def section(title, subtitle):
    st.markdown(
        f'<div class="section-title">{title}</div>'
        f'<div class="section-subtitle">{subtitle}</div>',
        unsafe_allow_html=True
    )


def make_chart(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Arial, sans-serif",
            color=NAVY,
            size=12
        ),
        title_font=dict(size=17, color=NAVY),
        margin=dict(l=15, r=15, t=55, b=15),
        legend_title_text="",
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(
        gridcolor="#E9EEF5",
        zeroline=False
    )
    return fig


def money(value):
    if pd.isna(value):
        return "N/A"
    return f"{value:,.2f}"


# ---------- Main application ----------
st.markdown("""
<div class="hero">
    <h1>BrandPulse 📊</h1>
    <p>Brand Visibility Intelligence · Understand the market.
    Compare competitors. Discover opportunities.</p>
</div>
""", unsafe_allow_html=True)

try:
    df = load_data()

    if df.empty:
        st.warning("Your products table has no records yet.")
        st.stop()

    # Standardize text and numeric columns
    for col in ["brand", "platform", "title", "keyword"]:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()

    for col in [
        "price", "rating", "reviews",
        "position", "visibility_score"
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col], errors="coerce"
            )

    # ---------- Sidebar ----------
    st.sidebar.markdown("## 🎛️ Explore your data")
    st.sidebar.caption("Adjust the filters to refine every chart.")

    filtered = df.copy()

    if "brand" in filtered.columns:
        brand_values = sorted(
            filtered["brand"].dropna().unique().tolist()
        )
        selected_brands = st.sidebar.multiselect(
            "Brands",
            brand_values,
            default=brand_values,
            placeholder="Choose brands"
        )
        filtered = filtered[
            filtered["brand"].isin(selected_brands)
        ]

    if "platform" in filtered.columns:
        platform_values = sorted(
            filtered["platform"].dropna().unique().tolist()
        )
        selected_platforms = st.sidebar.multiselect(
            "Platforms",
            platform_values,
            default=platform_values,
            placeholder="Choose platforms"
        )
        filtered = filtered[
            filtered["platform"].isin(selected_platforms)
        ]

    if "price" in filtered.columns:
        prices = filtered["price"].dropna()

        if not prices.empty and prices.min() < prices.max():
            lower, upper = st.sidebar.slider(
                "Product price range",
                min_value=float(prices.min()),
                max_value=float(prices.max()),
                value=(float(prices.min()), float(prices.max()))
            )
            filtered = filtered[
                filtered["price"].between(lower, upper)
                | filtered["price"].isna()
            ]

    if st.sidebar.button("Reset cached data", use_container_width=True):
        load_data.clear()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption("BrandPulse · Market intelligence")

    if filtered.empty:
        st.warning("No products match these filters. Adjust your selections.")
        st.stop()

    # ---------- KPI cards ----------
    section(
        "Your market at a glance",
        "A quick summary of the products currently selected."
    )

    k1, k2, k3, k4 = st.columns(4)

    k1.metric(
        "📦 Products",
        f"{len(filtered):,}",
        help="Number of product records after filtering."
    )

    brand_count = (
        filtered["brand"].nunique()
        if "brand" in filtered.columns else 0
    )
    k2.metric("🏷️ Brands", f"{brand_count:,}")

    avg_price = (
        filtered["price"].mean()
        if "price" in filtered.columns else float("nan")
    )
    k3.metric("💰 Average price", money(avg_price))

    avg_rating = (
        filtered["rating"].mean()
        if "rating" in filtered.columns else float("nan")
    )
    k4.metric(
        "⭐ Average rating",
        f"{avg_rating:.2f} / 5"
        if pd.notna(avg_rating) else "N/A"
    )

    # ---------- Navigation tabs ----------
    overview, brands_tab, pricing, visibility, explorer = st.tabs([
        "🏠 Overview",
        "🏷️ Brand Insights",
        "💰 Pricing",
        "🔎 Visibility",
        "🛍️ Product Explorer"
    ])

    # ---------- Overview ----------
    with overview:
        section(
            "Market snapshot",
            "See where products are listed and how their prices are distributed."
        )

        left, right = st.columns(2)

        with left:
            if "platform" in filtered.columns:
                counts = (
                    filtered["platform"].fillna("Unknown")
                    .value_counts()
                    .rename_axis("Platform")
                    .reset_index(name="Products")
                )

                fig = px.pie(
                    counts,
                    names="Platform",
                    values="Products",
                    hole=0.62,
                    title="Product mix by platform",
                    color_discrete_sequence=[
                        TEAL, PURPLE, BLUE, CORAL, "#E5B94F"
                    ]
                )
                fig.update_traces(
                    textposition="inside",
                    textinfo="percent+label"
                )
                st.plotly_chart(
                    make_chart(fig),
                    use_container_width=True
                )

        with right:
            if "price" in filtered.columns:
                price_data = filtered.dropna(subset=["price"])

                fig = px.histogram(
                    price_data,
                    x="price",
                    nbins=25,
                    title="How product prices are distributed",
                    color_discrete_sequence=[TEAL]
                )
                fig.update_traces(
                    marker_line_color="white",
                    marker_line_width=1
                )
                st.plotly_chart(
                    make_chart(fig),
                    use_container_width=True
                )

        if "platform" in filtered.columns:
            platform_table = (
                filtered.groupby("platform", dropna=False)
                .size()
                .reset_index(name="Product count")
                .sort_values("Product count", ascending=False)
            )

            if not platform_table.empty:
                top_platform = platform_table.iloc[0]
                st.markdown(
                    f'<div class="insight"><b>💡 Market insight</b><br>'
                    f'{top_platform["platform"]} has the most records '
                    f'in the current selection '
                    f'({int(top_platform["Product count"]):,}). '
                    f'This measures dataset coverage, not total market share.'
                    f'</div>',
                    unsafe_allow_html=True
                )

    # ---------- Brand insights ----------
    with brands_tab:
        section(
            "Know your competitors",
            "Compare product coverage, average prices, and ratings by brand."
        )

        if "brand" in filtered.columns:
            aggregations = {"brand": "size"}

            brand_table = filtered.groupby(
                "brand", dropna=False
            ).agg(
                Product_Count=("brand", "size"),
                **({
                    "Average_Price": ("price", "mean")
                } if "price" in filtered.columns else {}),
                **({
                    "Average_Rating": ("rating", "mean")
                } if "rating" in filtered.columns else {})
            ).reset_index()

            brand_table = brand_table.sort_values(
                "Product_Count", ascending=False
            )

            left, right = st.columns([1.4, 1])

            with left:
                fig = px.bar(
                    brand_table.head(15).sort_values("Product_Count"),
                    x="Product_Count",
                    y="brand",
                    orientation="h",
                    title="Brands with the most product records",
                    color="Product_Count",
                    color_continuous_scale=["#BCEFE8", TEAL]
                )
                fig.update_layout(coloraxis_showscale=False)
                st.plotly_chart(
                    make_chart(fig),
                    use_container_width=True
                )

            with right:
                if "Average_Rating" in brand_table.columns:
                    rating_table = brand_table.dropna(
                        subset=["Average_Rating"]
                    ).sort_values("Average_Rating", ascending=False)

                    fig = px.bar(
                        rating_table.head(10).sort_values(
                            "Average_Rating"
                        ),
                        x="Average_Rating",
                        y="brand",
                        orientation="h",
                        title="Highest average product ratings",
                        color="Average_Rating",
                        color_continuous_scale=["#D9D0FF", PURPLE]
                    )
                    fig.update_layout(
                        coloraxis_showscale=False,
                        xaxis_range=[0, 5]
                    )
                    st.plotly_chart(
                        make_chart(fig),
                        use_container_width=True
                    )

            display_table = brand_table.rename(columns={
                "brand": "Brand",
                "Product_Count": "Product count",
                "Average_Price": "Average price",
                "Average_Rating": "Average rating"
            })
            st.dataframe(
                display_table,
                use_container_width=True,
                hide_index=True
            )

    # ---------- Pricing ----------
    with pricing:
        section(
            "Pricing intelligence",
            "Understand price variation and identify products across price levels."
        )

        if "price" in filtered.columns:
            valid_prices = filtered.dropna(subset=["price"])

            if not valid_prices.empty:
                left, right = st.columns(2)

                with left:
                    fig = px.box(
                        valid_prices,
                        x="platform" if "platform" in valid_prices.columns
                        else None,
                        y="price",
                        title="Price spread by platform",
                        color="platform" if "platform" in valid_prices.columns
                        else None,
                        color_discrete_sequence=[
                            TEAL, PURPLE, BLUE, CORAL
                        ]
                    )
                    st.plotly_chart(
                        make_chart(fig),
                        use_container_width=True
                    )

                with right:
                    if "brand" in valid_prices.columns:
                        averages = (
                            valid_prices.groupby("brand", as_index=False)
                            ["price"].mean()
                            .sort_values("price", ascending=False)
                            .head(12)
                        )

                        fig = px.bar(
                            averages.sort_values("price"),
                            x="price",
                            y="brand",
                            orientation="h",
                            title="Average price by brand",
                            color="price",
                            color_continuous_scale=["#C9E8FF", BLUE]
                        )
                        fig.update_layout(coloraxis_showscale=False)
                        st.plotly_chart(
                            make_chart(fig),
                            use_container_width=True
                        )

                st.caption(
                    "Prices are analyzed as stored in the dataset. "
                    "Check installment-priced API records before interpreting "
                    "them as full product prices."
                )
            else:
                st.info("No valid prices are available for this selection.")

    # ---------- Visibility ----------
    with visibility:
        section(
            "Search visibility",
            "Explore recorded search positions and calculated visibility scores."
        )

        has_position = "position" in filtered.columns
        has_score = "visibility_score" in filtered.columns

        if has_position:
            ranked = filtered.dropna(subset=["position"])

            if not ranked.empty:
                left, right = st.columns(2)

                with left:
                    if "brand" in ranked.columns:
                        position_table = (
                            ranked.groupby("brand", as_index=False)
                            ["position"].mean()
                            .sort_values("position")
                            .head(15)
                        )

                        fig = px.bar(
                            position_table.sort_values(
                                "position", ascending=False
                            ),
                            x="position",
                            y="brand",
                            orientation="h",
                            title="Best average search positions",
                            color="position",
                            color_continuous_scale=["#B8EFE7", TEAL]
                        )
                        fig.update_layout(coloraxis_showscale=False)
                        st.plotly_chart(
                            make_chart(fig),
                            use_container_width=True
                        )

                with right:
                    if has_score and "brand" in ranked.columns:
                        scores = ranked.dropna(
                            subset=["visibility_score"]
                        ).groupby("brand", as_index=False)[
                            "visibility_score"
                        ].mean().sort_values(
                            "visibility_score", ascending=False
                        ).head(15)

                        if not scores.empty:
                            fig = px.bar(
                                scores.sort_values("visibility_score"),
                                x="visibility_score",
                                y="brand",
                                orientation="h",
                                title="Average visibility score",
                                color="visibility_score",
                                color_continuous_scale=["#D9D0FF", PURPLE]
                            )
                            fig.update_layout(coloraxis_showscale=False)
                            st.plotly_chart(
                                make_chart(fig),
                                use_container_width=True
                            )

                st.info(
                    "A smaller search-position number indicates a better "
                    "ranking. Scores are based on the available collected data; "
                    "they do not represent all search results on the internet."
                )
            else:
                st.warning(
                    "No search positions are available for the selected products."
                )
        else:
            st.info("The position column is not available in this table.")

    # ---------- Product explorer ----------
    with explorer:
        section(
            "Explore individual products",
            "Search product names and inspect the underlying records."
        )

        search = st.text_input(
            "🔍 Search products",
            placeholder="Enter a product, brand, or keyword..."
        )

        results = filtered.copy()

        search_cols = [
            col for col in ["title", "keyword", "brand", "platform"]
            if col in results.columns
        ]

        if search and search_cols:
            mask = pd.Series(False, index=results.index)
            for col in search_cols:
                mask |= results[col].astype(str).str.contains(
                    search, case=False, na=False, regex=False
                )
            results = results[mask]

        st.write(f"**{len(results):,}** matching records")

        preferred = [
            "brand", "title", "keyword", "price", "rating",
            "reviews", "platform", "position", "visibility_score",
            "product_link"
        ]
        visible_cols = [c for c in preferred if c in results.columns]
        visible_cols += [
            c for c in results.columns if c not in visible_cols
        ]

        st.dataframe(
            results[visible_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "product_link": st.column_config.LinkColumn(
                    "Product link"
                ),
                "price": st.column_config.NumberColumn(
                    "Price", format="%.2f"
                ),
                "rating": st.column_config.NumberColumn(
                    "Rating", format="%.2f ⭐"
                ),
                "visibility_score": st.column_config.NumberColumn(
                    "Visibility score", format="%.1f"
                )
            }
        )

        csv = results.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download filtered products (CSV)",
            data=csv,
            file_name="brandpulse_filtered_products.csv",
            mime="text/csv"
        )

    st.markdown(
        '<div class="footer">BrandPulse · Brand Visibility Intelligence '
        'Dashboard · Data-driven decisions, made clearer.</div>',
        unsafe_allow_html=True
    )

except Exception as error:
    st.error("The dashboard could not load the product data.")
    st.exception(error)
    st.info(
        "Check that MySQL is running, the brand_visibility database "
        "and products table exist, and notebooks/.env contains the "
        "correct connection settings."
    )