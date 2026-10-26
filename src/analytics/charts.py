"""
Interactive Plotly Visualization Library.
Provides cleanly styled charts for dashboards, analytics, forecasting, and inventory.
"""

from typing import Optional
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


COLOR_PRIMARY = "#1E88E5"
COLOR_SECONDARY = "#00ACC1"
COLOR_ACCENT = "#FFB300"
COLOR_ALERT = "#E53935"
COLOR_SUCCESS = "#43A047"
COLOR_NEUTRAL = "#757575"

LAYOUT_TEMPLATE = "plotly_white"


def plot_revenue_trend(df_sales_daily: pd.DataFrame, currency_symbol: str = "₹") -> go.Figure:
    """Plot daily total revenue with a 7-day rolling average trendline."""
    if df_sales_daily.empty:
        fig = go.Figure()
        fig.update_layout(title="No Sales Data Available", template=LAYOUT_TEMPLATE)
        return fig

    df = df_sales_daily.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    daily = df.groupby("sale_date")["revenue"].sum().reset_index()
    daily["rolling_7"] = daily["revenue"].rolling(7, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily["sale_date"],
        y=daily["revenue"],
        name="Daily Revenue",
        marker_color="rgba(30, 136, 229, 0.4)",
        hovertemplate=f"Date: %{{x|%b %d, %Y}}<br>Revenue: {currency_symbol}%{{y:,.2f}}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=daily["sale_date"],
        y=daily["rolling_7"],
        name="7-Day Moving Avg",
        line=dict(color="#1565C0", width=2.5),
        mode="lines",
        hovertemplate=f"7D Avg: {currency_symbol}%{{y:,.2f}}<extra></extra>"
    ))

    fig.update_layout(
        template=LAYOUT_TEMPLATE,
        title="Daily Revenue Trend & 7-Day Moving Average",
        xaxis_title="Date",
        yaxis_title=f"Revenue ({currency_symbol})",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=50, b=40),
        hovermode="x unified"
    )
    return fig


def plot_category_distribution(cat_df: pd.DataFrame, currency_symbol: str = "₹") -> go.Figure:
    """Plot category revenue contribution as a donut chart."""
    if cat_df.empty:
        fig = go.Figure()
        fig.update_layout(title="No Category Data Available", template=LAYOUT_TEMPLATE)
        return fig

    fig = go.Figure(data=[go.Pie(
        labels=cat_df["category"],
        values=cat_df["revenue"],
        hole=0.45,
        textinfo="label+percent",
        hovertemplate=f"<b>%{{label}}</b><br>Revenue: {currency_symbol}%{{value:,.2f}}<br>Share: %{{percent}}<extra></extra>",
        marker=dict(colors=px.colors.qualitative.Prism)
    )])
    fig.update_layout(
        template=LAYOUT_TEMPLATE,
        title="Revenue Breakdown by Category",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig


def plot_top_products_bar(top_df: pd.DataFrame, currency_symbol: str = "₹") -> go.Figure:
    """Horizontal bar chart for top products."""
    if top_df.empty:
        fig = go.Figure()
        fig.update_layout(title="No Product Data Available", template=LAYOUT_TEMPLATE)
        return fig

    df_sorted = top_df.sort_values(by="revenue", ascending=True)
    fig = go.Figure(go.Bar(
        x=df_sorted["revenue"],
        y=df_sorted["product_name"],
        orientation="h",
        marker=dict(color="#26A69A"),
        hovertemplate=f"<b>%{{y}}</b><br>Revenue: {currency_symbol}%{{x:,.2f}}<extra></extra>"
    ))
    fig.update_layout(
        template=LAYOUT_TEMPLATE,
        title="Top Selling Products by Revenue",
        xaxis_title=f"Total Revenue ({currency_symbol})",
        yaxis_title="Product",
        margin=dict(l=120, r=20, t=40, b=40)
    )
    return fig


def plot_weekday_vs_weekend(stats_df: pd.DataFrame, currency_symbol: str = "₹") -> go.Figure:
    """Grouped bar chart comparing weekday vs weekend sales."""
    if stats_df.empty:
        fig = go.Figure()
        fig.update_layout(title="No Day Pattern Data", template=LAYOUT_TEMPLATE)
        return fig

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=stats_df["day_type"],
        y=stats_df["avg_daily_revenue"],
        name="Avg Daily Revenue",
        marker_color="#3949AB",
        text=[f"{currency_symbol}{v:,.0f}" for v in stats_df["avg_daily_revenue"]],
        textposition="auto"
    ))
    fig.update_layout(
        template=LAYOUT_TEMPLATE,
        title="Average Daily Revenue: Weekday vs Weekend",
        xaxis_title="Day Classification",
        yaxis_title=f"Avg Daily Revenue ({currency_symbol})",
        margin=dict(l=40, r=20, t=40, b=40)
    )
    return fig


def plot_forecast_vs_history(
    history_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    val_dates: list = None,
    val_preds: list = None,
    product_name: str = "Product"
) -> go.Figure:
    """
    Plot historical sales, validation out-of-sample predictions,
    and future forecast with uncertainty envelope.
    """
    fig = go.Figure()

    # 1. Historical Actuals (last 60 days max for clarity)
    if not history_df.empty:
        hist_recent = history_df.tail(60).copy()
        hist_recent["sale_date"] = pd.to_datetime(hist_recent["sale_date"])
        fig.add_trace(go.Scatter(
            x=hist_recent["sale_date"],
            y=hist_recent["quantity_sold"],
            name="Actual Demand (History)",
            mode="lines+markers",
            line=dict(color="#37474F", width=2),
            marker=dict(size=4)
        ))

    # 2. Validation predictions if provided
    if val_dates and val_preds and len(val_dates) == len(val_preds):
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(val_dates),
            y=val_preds,
            name="Validation Holdout Preds",
            mode="lines",
            line=dict(color="#FB8C00", width=2, dash="dash")
        ))

    # 3. Future Forecast with Confidence Envelope
    if not forecast_df.empty:
        f_dates = pd.to_datetime(forecast_df["forecast_date"])
        f_pred = forecast_df["predicted_demand"]
        f_lower = forecast_df["lower_bound"]
        f_upper = forecast_df["upper_bound"]

        # Upper bound
        fig.add_trace(go.Scatter(
            x=f_dates,
            y=f_upper,
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip"
        ))
        # Lower bound with fill
        fig.add_trace(go.Scatter(
            x=f_dates,
            y=f_lower,
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(30, 136, 229, 0.15)",
            name="90% Prediction Interval",
            hoverinfo="skip"
        ))
        # Forecast Mean
        fig.add_trace(go.Scatter(
            x=f_dates,
            y=f_pred,
            name="Future Forecast",
            mode="lines+markers",
            line=dict(color="#1E88E5", width=2.5),
            marker=dict(size=5, symbol="diamond")
        ))

    fig.update_layout(
        template=LAYOUT_TEMPLATE,
        title=f"Demand History & Future Forecast: {product_name}",
        xaxis_title="Date",
        yaxis_title="Units Demanded",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=50, b=40),
        hovermode="x unified"
    )
    return fig


def plot_inventory_risk_pie(recommendations_df: pd.DataFrame) -> go.Figure:
    """Display distribution of inventory risk categories."""
    if recommendations_df.empty or "risk_status" not in recommendations_df.columns:
        fig = go.Figure()
        fig.update_layout(title="No Recommendations Generated", template=LAYOUT_TEMPLATE)
        return fig

    status_counts = recommendations_df["risk_status"].value_counts().reset_index()
    status_counts.columns = ["risk_status", "count"]

    color_map = {
        "Stock Risk": "#E53935",
        "Reorder Review": "#FB8C00",
        "Adequate Stock": "#43A047",
        "Potential Excess Stock": "#8E24AA",
        "Insufficient Inventory Information": "#757575"
    }
    colors = [color_map.get(s, "#757575") for s in status_counts["risk_status"]]

    fig = go.Figure(go.Pie(
        labels=status_counts["risk_status"],
        values=status_counts["count"],
        hole=0.4,
        marker=dict(colors=colors),
        textinfo="label+value"
    ))
    fig.update_layout(
        template=LAYOUT_TEMPLATE,
        title="Inventory Recommendation Statuses",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig
