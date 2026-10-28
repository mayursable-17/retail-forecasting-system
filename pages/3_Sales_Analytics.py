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
        # Top summary metrics strip
        f_rev = float(df["revenue"].sum())
        f_units = float(df["quantity_sold"].sum())
        f_days = int(df["sale_date"].dt.date.nunique())
        f_asp = (f_rev / f_units) if f_units > 0 else 0.0

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Filtered Revenue", f"{cur}{f_rev:,.2f}", help="Total revenue inside the active filter window")
        with m2:
            st.metric("Units Sold", f"{f_units:,.1f}", f"Avg {(f_units/max(1, f_days)):.1f}/day")
        with m3:
            st.metric("Avg Selling Price (ASP)", f"{cur}{f_asp:,.2f}")
        with m4:
            top_cat = df.groupby("category")["revenue"].sum().idxmax() if not df.empty else "N/A"
            st.metric("Lead Category", top_cat)

        st.markdown("<br>", unsafe_allow_html=True)

        # Monthly & Daily Aggregate Trends
        tab_trends, tab_products, tab_cycles = st.tabs(["📊 Revenue & Volume Trends", "📦 Product & Category Share (ABC Analysis)", "🗓️ Temporal & Heatmap Patterns"])

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
            st.subheader("Cumulative Revenue Contribution & ABC Inventory Classification")
            prod_agg = df.groupby(["product_id", "product_name", "category"]).agg(
                revenue=("revenue", "sum"),
                units=("quantity_sold", "sum")
            ).reset_index().sort_values(by="revenue", ascending=False).reset_index(drop=True)

            tot_rev = max(1.0, float(prod_agg["revenue"].sum()))
            prod_agg["cum_revenue"] = prod_agg["revenue"].cumsum()
            prod_agg["cum_share_pct"] = (prod_agg["cum_revenue"] / tot_rev * 100).round(2)

            def get_abc_class(row):
                if row["cum_share_pct"] <= 80.0 or row.name == 0:
                    return "Class A (Top 80%)"
                elif row["cum_share_pct"] <= 95.0:
                    return "Class B (Next 15%)"
                else:
                    return "Class C (Bottom 5%)"

            prod_agg["abc_class"] = prod_agg.apply(get_abc_class, axis=1)

            # ABC Metric pills
            abc_counts = prod_agg["abc_class"].value_counts().to_dict()
            a_col, b_col, c_col = st.columns(3)
            with a_col:
                st.metric("Class A Products (Core)", f"{abc_counts.get('Class A (Top 80%)', 0)} Items", "Drives 80% of sales")
            with b_col:
                st.metric("Class B Products (Regular)", f"{abc_counts.get('Class B (Next 15%)', 0)} Items", "Drives 15% of sales")
            with c_col:
                st.metric("Class C Products (Tail)", f"{abc_counts.get('Class C (Bottom 5%)', 0)} Items", "Drives bottom 5% of sales")

            fig_pareto = go.Figure()
            color_map = {
                "Class A (Top 80%)": "#1E88E5",
                "Class B (Next 15%)": "#FB8C00",
                "Class C (Bottom 5%)": "#78909C"
            }
            bar_colors = [color_map.get(c, "#1E88E5") for c in prod_agg["abc_class"]]

            fig_pareto.add_trace(go.Bar(
                x=prod_agg["product_name"],
                y=prod_agg["revenue"],
                name="Product Revenue",
                marker_color=bar_colors,
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
                title="Product Revenue Pareto Curve & ABC Segments",
                xaxis_title="Product",
                yaxis=dict(title=f"Revenue ({cur})"),
                yaxis2=dict(title="Cumulative Share (%)", overlaying="y", side="right", range=[0, 105]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=40, r=40, t=50, b=100)
            )
            st.plotly_chart(fig_pareto, use_container_width=True)

            # Formatted ABC Table
            disp_abc = prod_agg.copy()
            disp_abc["revenue"] = disp_abc["revenue"].apply(lambda v: f"{cur}{v:,.2f}")
            disp_abc["units"] = disp_abc["units"].apply(lambda v: f"{v:,.1f}")
            disp_abc["cum_share_pct"] = disp_abc["cum_share_pct"].apply(lambda v: f"{v:.1f}%")
            disp_abc.columns = ["Product ID", "Product Name", "Category", "Revenue", "Units Sold", "Cumulative Revenue", "Cumulative Share", "ABC Segment"]
            st.dataframe(disp_abc[["Product ID", "Product Name", "Category", "ABC Segment", "Units Sold", "Revenue", "Cumulative Share"]], hide_index=True, use_container_width=True)


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

            c_dow1, c_dow2 = st.columns([1, 1])
            with c_dow1:
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

            with c_dow2:
                # Category × Day-of-Week Heatmap
                heat_pivot = df.pivot_table(index="category", columns="dow_name", values="revenue", aggfunc="mean").fillna(0)
                # Reorder columns Monday through Sunday if available
                day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                avail_days = [d for d in day_order if d in heat_pivot.columns]
                heat_pivot = heat_pivot[avail_days]

                fig_heat = go.Figure(data=go.Heatmap(
                    z=heat_pivot.values,
                    x=heat_pivot.columns,
                    y=heat_pivot.index,
                    colorscale="Blues",
                    hovertemplate="Category: %{y}<br>Day: %{x}<br>Avg Revenue: " + cur + "%{z:,.2f}<extra></extra>"
                ))
                fig_heat.update_layout(
                    template="plotly_white",
                    title="Category Demand Heatmap Across Days of Week",
                    xaxis_title="Day of Week",
                    yaxis_title="Category"
                )
                st.plotly_chart(fig_heat, use_container_width=True)
