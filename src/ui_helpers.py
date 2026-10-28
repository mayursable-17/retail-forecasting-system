"""
UI Helper functions and CSS styling for Streamlit Multipage Application.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional

from src.config import DEFAULT_CURRENCY, DEFAULT_CURRENCY_CODE
from src.database.connection import init_db
from src.database.repository import Repository


def load_custom_css():
    """Inject clean, modern, interactive CSS styles with dark & light theme adaptability."""
    st.markdown("""
        <style>
        /* General page layout */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2.5rem;
            max-width: 96%;
        }

        /* Modern interactive metric cards */
        .metric-card {
            background: linear-gradient(145deg, #ffffff, #f9fafb);
            border-radius: 12px;
            padding: 18px 22px;
            border: 1px solid #e5e7eb;
            border-left: 5px solid #1E88E5;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            margin-bottom: 14px;
            position: relative;
            overflow: hidden;
        }
        .metric-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 18px rgba(0, 0, 0, 0.08);
            border-color: #cbd5e1;
        }

        .metric-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 6px;
        }
        .metric-title {
            font-size: 0.82rem;
            color: #4b5563;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.6px;
        }
        .metric-icon {
            font-size: 1.15rem;
            opacity: 0.85;
        }
        .metric-value {
            font-size: 1.85rem;
            color: #111827;
            font-weight: 800;
            line-height: 1.2;
            letter-spacing: -0.5px;
        }
        .metric-sub {
            font-size: 0.80rem;
            color: #6b7280;
            margin-top: 6px;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .metric-trend-pill {
            display: inline-flex;
            align-items: center;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 0.72rem;
            font-weight: 600;
        }
        .trend-up {
            background-color: #ecfdf5;
            color: #047857;
        }
        .trend-down {
            background-color: #fef2f2;
            color: #b91c1c;
        }
        .trend-neutral {
            background-color: #f3f4f6;
            color: #4b5563;
        }

        /* Stock Alert Notification Banner */
        .stock-alert-banner {
            background: linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%);
            border: 1px solid #fecdd3;
            border-left: 5px solid #e11d48;
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 4px rgba(225, 29, 72, 0.05);
        }
        .stock-alert-title {
            font-weight: 700;
            color: #9f1239;
            font-size: 0.95rem;
            margin-bottom: 2px;
        }
        .stock-alert-desc {
            color: #be123c;
            font-size: 0.82rem;
        }

        /* Status Badges */
        .badge-risk {
            background-color: #fee2e2;
            color: #991b1b;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 0.78rem;
            font-weight: 700;
            display: inline-block;
        }
        .badge-review {
            background-color: #ffedd5;
            color: #9a3412;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 0.78rem;
            font-weight: 700;
            display: inline-block;
        }
        .badge-adequate {
            background-color: #dcfce7;
            color: #166534;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 0.78rem;
            font-weight: 700;
            display: inline-block;
        }
        .badge-excess {
            background-color: #f3e8ff;
            color: #6b21a8;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 0.78rem;
            font-weight: 700;
            display: inline-block;
        }
        .badge-info {
            background-color: #f1f5f9;
            color: #334155;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 0.78rem;
            font-weight: 700;
            display: inline-block;
        }

        /* Section Cards */
        .panel-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }

        /* Quick filter bar */
        .filter-chip-container {
            display: flex;
            gap: 8px;
            align-items: center;
            margin-bottom: 14px;
            flex-wrap: wrap;
        }
        </style>
    """, unsafe_allow_html=True)


def get_shared_repo() -> Repository:
    """Return repository instance and guarantee DB is initialized."""
    init_db()
    return Repository()


def get_active_shop(repo: Repository) -> Dict[str, Any]:
    """Retrieve shop configuration or sensible defaults."""
    shop = repo.get_shop(1)
    if not shop:
        return {
            "shop_id": 1,
            "shop_name": "Kirana & Retail Store",
            "shop_type": "Grocery & FMCG Retail",
            "currency_symbol": DEFAULT_CURRENCY,
            "currency_code": DEFAULT_CURRENCY_CODE
        }
    return shop


def render_metric_card(
    title: str,
    value: str,
    subtext: str = "",
    border_color: str = "#1E88E5",
    icon: str = "",
    trend_text: str = "",
    trend_type: str = "neutral"
):
    """Render modern, interactive KPI card with icons and trend badges."""
    trend_badge_html = ""
    if trend_text:
        trend_class = "trend-up" if trend_type == "up" else ("trend-down" if trend_type == "down" else "trend-neutral")
        trend_badge_html = f'<span class="metric-trend-pill {trend_class}">{trend_text}</span>'

    st.markdown(f"""
        <div class="metric-card" style="border-left-color: {border_color};">
            <div class="metric-header">
                <span class="metric-title">{title}</span>
                {f'<span class="metric-icon">{icon}</span>' if icon else ''}
            </div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">
                {trend_badge_html}
                <span>{subtext}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_stock_alert_banner(risk_count: int, review_count: int):
    """Render an eye-catching inventory risk notification banner."""
    total_alerts = risk_count + review_count
    if total_alerts <= 0:
        return

    st.markdown(f"""
        <div class="stock-alert-banner">
            <div>
                <div class="stock-alert-title">🚨 Action Required: {total_alerts} Product{'s' if total_alerts > 1 else ''} Need Attention</div>
                <div class="stock-alert-desc">
                    {risk_count} item(s) are at immediate stockout risk and {review_count} item(s) are below safety reorder threshold.
                </div>
            </div>
            <div>
                <span class="badge-risk">{risk_count} Critical</span>
                <span class="badge-review">{review_count} Reorder</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
