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
    """Inject clean, modern CSS styles."""
    st.markdown("""
        <style>
        /* General page layout */
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2.5rem;
            max-width: 95%;
        }
        /* Metric card styling */
        .metric-card {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 16px 20px;
            border-left: 4px solid #1E88E5;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            margin-bottom: 12px;
        }
        .metric-title {
            font-size: 0.85rem;
            color: #616161;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .metric-value {
            font-size: 1.7rem;
            color: #212121;
            font-weight: 700;
            margin-top: 4px;
        }
        .metric-sub {
            font-size: 0.78rem;
            color: #757575;
            margin-top: 2px;
        }
        /* Status Badges */
        .badge-risk {
            background-color: #FFEBEE;
            color: #C62828;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
        }
        .badge-review {
            background-color: #FFF3E0;
            color: #EF6C00;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
        }
        .badge-adequate {
            background-color: #E8F5E9;
            color: #2E7D32;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
        }
        .badge-excess {
            background-color: #F3E5F5;
            color: #6A1B9A;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
        }
        .badge-info {
            background-color: #ECEFF1;
            color: #37474F;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
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


def render_metric_card(title: str, value: str, subtext: str = "", border_color: str = "#1E88E5"):
    """Render HTML KPI card."""
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: {border_color};">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            {f'<div class="metric-sub">{subtext}</div>' if subtext else ''}
        </div>
    """, unsafe_allow_html=True)
