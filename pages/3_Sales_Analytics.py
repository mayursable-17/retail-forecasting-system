"""
Page 3: Comprehensive Sales Analytics & Retail Insights
Deep interactive exploration of sales trends, product contributions, and pricing patterns.
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.ui_helpers import load_custom_css, get_shared_repo, get_active_shop
from src.analytics.kpis import compute_category_breakdown, compute_weekday_weekend_stats
from src.analytics.charts import plot_revenue_trend, plot_category_distribution, plot_weekday_vs_weekend

st.set_page_config(page_title="Sales Analytics - Retail System", page_icon="📈", layout="wide")
load_custom_css()
repo = get_shared_repo()
shop = get_active_shop(repo)

st.title("📈 Retail Sales Analytics")
st.markdown("Analyze historical consumer demand, product revenue contributions, and operational cycles.")

sales_df = repo.get_daily_sales_df(shop_id=shop["shop_id"])

if sales_df.empty:
    st.warning("⚠️ No sales data found in the system. Please upload data or load the demo dataset.")
    st.page_link("pages/1_Upload_Data.py", label="➡️ Go to Upload Data", icon="📤")
    st.stop()
else:
    cur = shop["currency_symbol"]

    # Global Filters
    with st.sidebar:
        st.markdown("### 🔍 Filters")
        dt_series = pd.to_datetime(sales_df["sale_date"])
        min_date = dt_series.min().date()
        max_date = dt_series.max().date()
        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        all_categories = sorted(sales_df["category"].unique())
        sel_categories = st.multiselect("Category", options=all_categories, default=all_categories)

        all_prods = sorted(sales_df["product_name"].unique())
        sel_prods = st.multiselect("Filter Specific Products (Optional)", options=all_prods, default=[])

    # Apply filters
    df = sales_df.copy()
    if isinstance(date_range, tuple) and len(date_range) == 2:
        s_dt, e_dt = date_range
        df = df[(df["sale_date"].dt.date >= s_dt) & (df["sale_date"].dt.date <= e_dt)]
    if sel_categories:
        df = df[df["category"].isin(sel_categories)]
    if sel_prods:
        df = df[df["product_name"].isin(sel_prods)]

    if df.empty:
        st.warning("No sales records match the selected filter criteria.")
    else:
        # Monthly & Daily Aggregate Trends
        tab_trends, tab_products, tab_cycles = st.tabs(["📊 Revenue & Volume Trends", "📦 Product & Category Share", "🗓️ Temporal & Day Patterns"])

        with tab_trends:
            st.subheader("Daily Sales Performance")
            metric_choice = st.radio("Display Metric", ["Revenue", "Units Sold"], horizontal=True)

            if metric_choice == "Revenue":
                st.plotly_chart(plot_revenue_trend(df, currency_symbol=cur), use_container_width=True)
            else:
                daily_units = df.groupby(df["sale_date"].dt.date)["quantity_sold"].sum().reset_index()
                daily_units["rolling_7"] = daily_units["quantity_sold"].rolling(7, min_periods=1).mean()

                fig_units = go.Figure()
                fig_units.add_trace(go.Bar(
                    x=daily_units["sale_date"],
                    y=daily_units["quantity_sold"],
                    name="Daily Units",
                    marker_color="rgba(67, 160, 71, 0.4)",
                    hovertemplate="Date: %{x}<br>Units: %{y:,.1f}<extra></extra>"
                ))
                fig_units.add_trace(go.Scatter(
                    x=daily_units["sale_date"],
                    y=daily_units["rolling_7"],
                    name="7-Day Moving Avg",
                    line=dict(color="#2E7D32", width=2.5)
                ))
                fig_units.update_layout(
                    template="plotly_white",
                    title="Daily Units Sold & 7-Day Moving Average",
                    xaxis_title="Date",
                    yaxis_title="Units Sold",
                    hovermode="x unified"
                )
                st.plotly_chart(fig_units, use_container_width=True)

            # Monthly Summary
            df["year_month"] = df["sale_date"].dt.to_period("M").astype(str)
            monthly_agg = df.groupby("year_month").agg(
                total_rev=("revenue", "sum"),
                total_units=("quantity_sold", "sum"),
                active_days=("sale_date", lambda d: d.dt.date.nunique())
            ).reset_index()
            monthly_agg["avg_daily_rev"] = (monthly_agg["total_rev"] / monthly_agg["active_days"]).round(2)

            st.subheader("Monthly Performance Summary")
            disp_m = monthly_agg.copy()
            disp_m["total_rev"] = disp_m["total_rev"].apply(lambda v: f"{cur}{v:,.2f}")
            disp_m["total_units"] = disp_m["total_units"].apply(lambda v: f"{v:,.1f}")
            disp_m["avg_daily_rev"] = disp_m["avg_daily_rev"].apply(lambda v: f"{cur}{v:,.2f}")
            disp_m.columns = ["Month", f"Total Revenue ({cur})", "Total Units", "Active Days", "Avg Daily Revenue"]
            st.dataframe(disp_m, hide_index=True, use_container_width=True)


        with tab_products:
            st.subheader("Category Breakdown & Revenue Contribution")
            cat_df = compute_category_breakdown(df)
            c1, c2 = st.columns([1, 1])
            with c1:
                st.plotly_chart(plot_category_distribution(cat_df, currency_symbol=cur), use_container_width=True)
            with c2:
                disp_cat = cat_df.copy()
                disp_cat["revenue"] = disp_cat["revenue"].apply(lambda v: f"{cur}{v:,.2f}")
                disp_cat["quantity_sold"] = disp_cat["quantity_sold"].apply(lambda v: f"{v:,.1f}")
                disp_cat["revenue_share_pct"] = disp_cat["revenue_share_pct"].apply(lambda v: f"{v:.2f}%")
                disp_cat.columns = ["Category", "Units Sold", "Total Revenue", "Revenue Share (%)"]
                st.dataframe(disp_cat, hide_index=True, use_container_width=True)

            st.markdown("---")
            st.subheader("Cumulative Revenue Contribution (Pareto Analysis)")
            prod_agg = df.groupby(["product_id", "product_name", "category"]).agg(
                revenue=("revenue", "sum"),
                units=("quantity_sold", "sum")
            ).reset_index().sort_values(by="revenue", ascending=False).reset_index(drop=True)

            prod_agg["cum_revenue"] = prod_agg["revenue"].cumsum()
            tot_rev = prod_agg["revenue"].sum()
            prod_agg["cum_share_pct"] = (prod_agg["cum_revenue"] / tot_rev * 100).round(2)

            fig_pareto = go.Figure()
            fig_pareto.add_trace(go.Bar(
                x=prod_agg["product_name"],
                y=prod_agg["revenue"],
                name="Product Revenue",
                marker_color="#1E88E5",
                yaxis="y1"
            ))
            fig_pareto.add_trace(go.Scatter(
                x=prod_agg["product_name"],
                y=prod_agg["cum_share_pct"],
                name="Cumulative % Share",
                line=dict(color="#D81B60", width=2.5),
                mode="lines+markers",
                yaxis="y2"
            ))
            fig_pareto.update_layout(
                template="plotly_white",
                title="Product Revenue Contribution & Cumulative Pareto Curve",
                xaxis_title="Product",
                yaxis=dict(title=f"Revenue ({cur})"),
                yaxis2=dict(title="Cumulative Share (%)", overlaying="y", side="right", range=[0, 105]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=40, r=40, t=50, b=100)
            )
            st.plotly_chart(fig_pareto, use_container_width=True)


        with tab_cycles:
            st.subheader("Day-of-Week Demand Patterns")
            w_stats = compute_weekday_weekend_stats(df)
            st.plotly_chart(plot_weekday_vs_weekend(w_stats, currency_symbol=cur), use_container_width=True)

            # Detailed Day of week breakdown (Monday - Sunday)
            df["dow_num"] = df["sale_date"].dt.dayofweek
            df["dow_name"] = df["sale_date"].dt.day_name()
            dow_df = df.groupby(["dow_num", "dow_name"]).agg(
                total_rev=("revenue", "sum"),
                total_units=("quantity_sold", "sum"),
                day_count=("sale_date", lambda d: d.dt.date.nunique())
            ).reset_index().sort_values(by="dow_num")
            dow_df["avg_rev"] = (dow_df["total_rev"] / dow_df["day_count"]).round(2)
            dow_df["avg_units"] = (dow_df["total_units"] / dow_df["day_count"]).round(1)

            fig_dow = go.Figure(go.Bar(
                x=dow_df["dow_name"],
                y=dow_df["avg_rev"],
                marker_color="#5E35B1",
                text=[f"{cur}{v:,.0f}" for v in dow_df["avg_rev"]],
                textposition="auto"
            ))
            fig_dow.update_layout(
                template="plotly_white",
                title="Average Daily Revenue by Day of Week",
                xaxis_title="Day of Week",
                yaxis_title=f"Average Revenue ({cur})"
            )
            st.plotly_chart(fig_dow, use_container_width=True)
