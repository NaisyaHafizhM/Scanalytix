"""
app.py — Auto EDA Insight Dashboard Data Science Programming — Kelompok 6
"""

from pathlib import Path
import base64
import mimetypes
import sys
import os
import datetime
import time
import io
import json
import re
import textwrap

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
from scipy import stats as scipy_stats

st.set_page_config(
    page_title="Auto EDA Insight",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.data_loader import load_file
from backend.descriptive_stats import numeric_stats, categorical_stats
try:
    from backend.data_cleaning import (
        snapshot, drop_duplicates, drop_missing_rows,
        fill_missing_mean, fill_missing_median, fill_missing_mode,
        fill_missing_by_method, drop_column, convert_dtype,
    )
except ModuleNotFoundError:
    from backend.preprocessing import (
        snapshot, drop_duplicates, drop_missing_rows,
        fill_missing_mean, fill_missing_median, fill_missing_mode,
        fill_missing_by_method, drop_column, convert_dtype,
    )
from backend.visualization import (
    plot_histogram, plot_boxplot, plot_density, plot_qq, plot_violin,
    plot_bar, plot_pie, plot_pareto, plot_count,
    plot_scatter, plot_correlation_heatmap, plot_regression, plot_pair_matrix, plot_bubble,
    plot_boxplot_by_cat, plot_grouped_bar, plot_violin_by_cat, plot_strip_by_cat, plot_time_series,
)
from backend.insight_generator import generate_insights

# ══════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════
DEFAULT_STATE = {
    "authenticated": False,
    "username": "",
    "user_role": "viewer",
    "df": None,
    "df_original": None,
    "history": [],
    "activity_log": [],
    "last_logged_page": "",
    "cleaning_log": [],
    "before_snap": None,
    "after_snap": None,
    "before_df": None,
    "after_df": None,
    "last_cleaning_operation": "",
    "cleaning_notice": "",
    "active_page": "🏠 Dashboard",
    "nav_radio": "🏠 Dashboard",
    "active_file": None,
    "last_upload_signature": None,
    "ui_theme": "Dark Mode",
    "_scroll_to_main": False,
    "register_mode": False,
    "users_db": {"admin": {"password": "eda2026", "role": "admin", "name": "Admin"}, "clara": {"password": "kelompok6", "role": "member", "name": "Clara"}, "naisya": {"password": "kelompok6", "role": "member", "name": "Naisya"}, "iffah": {"password": "kelompok6", "role": "member", "name": "Iffah"}, "fifi": {"password": "kelompok6", "role": "member", "name": "Fifi"}, "dhea": {"password": "kelompok6", "role": "member", "name": "Dhea Putri Khasanah"}},
}
for key, default in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ══════════════════════════════════════════════════════
#  NAVIGATION STRUCTURE — categorised sidebar
# ══════════════════════════════════════════════════════
NAV_CATEGORIES = {
    "🏠 HOME": ["🏠 Dashboard"],
    "📁 DATA MANAGEMENT": ["📤 Upload Data", "👁️ Data Preview", "📌 Dataset Info"],
    "🧹 CLEANING": ["🧹 Data Cleaning"],
    "📊 STATISTICS": ["📈 Statistik — Numerik", "📊 Statistik — Kategorik"],
    "📉 VISUALIZATION": ["📉 Visualisasi Numerik", "🎨 Visualisasi Kategorik", "🔗 Bivariate & Multivariat", "📦 Kategorik vs Numerik", "⏱️ Time Series"],
    "💡 INSIGHTS & REPORT": ["💡 Insights", "📄 Download Report"],
    "🗂️ HISTORY": ["🗂️ Riwayat Upload"],
}

ALL_PAGES = [p for pages in NAV_CATEGORIES.values() for p in pages]

# Monochrome text icons for the sidebar. These are interface symbols, not emoji,
# so they remain clean in both expanded and compact sidebar modes.
SIDEBAR_PAGE_ICONS = {
    "🏠 Dashboard": "⌂",
    "📤 Upload Data": "⇧",
    "👁️ Data Preview": "≡",
    "📌 Dataset Info": "i",
    "🧹 Data Cleaning": "⌁",
    "📈 Statistik — Numerik": "Σ",
    "📊 Statistik — Kategorik": "∷",
    "📉 Visualisasi Numerik": "▥",
    "🎨 Visualisasi Kategorik": "▦",
    "🔗 Bivariate & Multivariat": "↗",
    "📦 Kategorik vs Numerik": "≋",
    "⏱️ Time Series": "∿",
    "💡 Insights": "◇",
    "📄 Download Report": "⇩",
    "🗂️ Riwayat Upload": "↶",
}

SIDEBAR_CATEGORY_ICONS = {
    "🏠 HOME": "⌂",
    "📁 DATA MANAGEMENT": "▣",
    "🧹 CLEANING": "⌁",
    "📊 STATISTICS": "Σ",
    "📉 VISUALIZATION": "▥",
    "💡 INSIGHTS & REPORT": "◇",
    "🗂️ HISTORY": "↶",
}

COURSE_LINE = "DATA SCIENCE PROGRAMMING · Bakti Siregar, M.Sc., CDS · ITSB"
COURSE_LINE_SHORT = "DSP · Bakti Siregar, M.Sc., CDS · ITSB"

# ══════════════════════════════════════════════════════
#  COLOUR TOKENS — Excel Finance Dashboard inspired
#  Deep navy/slate + gold + teal accents
# ══════════════════════════════════════════════════════
DARK_CSS = """
    --bg:       #1a0845;
    --panel:    #1e0f3d;
    --panel-2:  #2a1258;
    --stroke:   rgba(139, 92, 246, .35);
    --text:     #f0eeff;
    --muted:    #8b78c4;
    --accent:   #7c3aed;
    --cyan:     #06b6d4;
    --gold:     #f59e0b;
    --green:    #10b981;
    --red:      #f43f5e;
    --amber:    #f97316;
    --violet:   #8b5cf6;
    --pink:     #ec4899;
    --chip-bg:  rgba(124,58,237,.12);
    --input-bg: #0f0b24;
    --input-border: rgba(139,92,246,.45);
    --shadow:   0 18px 44px rgba(0,0,0,.5);
    --clean-table-bg: rgba(31,15,68,.86);
    --clean-table-head: linear-gradient(135deg, rgba(76,29,149,.96), rgba(42,18,88,.98));
    --clean-table-cell: rgba(35,18,76,.76);
    --clean-table-border: rgba(216,180,254,.45);
    --clean-table-text: #ffffff;
    --clean-table-muted: #f7f2ff;
    --clean-chip-bg: rgba(124,58,237,.48);
    --clean-chip-text: #ffffff;
"""
LIGHT_CSS = """
    --bg:       #d7f1e5;
    --panel:    rgba(255,255,255,.80);
    --panel-2:  rgba(226,246,237,.90);
    --stroke:   rgba(22,101,52,.24);
    --text:     #082f24;
    --muted:    #315f4b;
    --accent:   #087f5b;
    --cyan:     #0e9f9a;
    --gold:     #b7791f;
    --green:    #138a51;
    --red:      #dc2626;
    --amber:    #d97706;
    --chip-bg:  rgba(8,127,91,.10);
    --input-bg: rgba(255,255,255,.86);
    --input-border: rgba(8,127,91,.32);
    --shadow:   0 20px 50px rgba(32,105,81,.20);
    --clean-table-bg: rgba(255,255,255,.84);
    --clean-table-head: linear-gradient(135deg, rgba(187,247,208,.90), rgba(191,219,254,.72));
    --clean-table-cell: rgba(255,255,255,.64);
    --clean-table-border: rgba(20,121,86,.30);
    --clean-table-text: #0b2f22;
    --clean-table-muted: #10231a;
    --clean-chip-bg: rgba(22,163,74,.24);
    --clean-chip-text: #064e3b;
"""


# ══════════════════════════════════════════════════════
#  GLOBAL CSS — separated files in frontend/static/css/
# ══════════════════════════════════════════════════════
def _read_css_file(name: str) -> str:
    path = BASE_DIR / "frontend" / "static" / "css" / name
    return path.read_text(encoding="utf-8") if path.exists() else ""

STATIC_CSS = "\n".join([
    _read_css_file("style.css"),
    _read_css_file("dashboard.css"),
    _read_css_file("cleaning.css"),
    _read_css_file("report.css"),
])

GLOBAL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600;700&display=swap');
:root {{ {DARK_CSS} }}
{STATIC_CSS}
</style>"""

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)



# ══════════════════════════════════════════════════════
#  THEME INJECTION
# ══════════════════════════════════════════════════════
def inject_theme_css():
    is_light = "Light" in st.session_state.get("ui_theme", "🌙 Dark Mode")
    vars_css = LIGHT_CSS if is_light else DARK_CSS
    if is_light:
        app_bg = "background: radial-gradient(circle at 3% 8%, rgba(22,101,52,.28), transparent 32%), radial-gradient(circle at 96% 14%, rgba(59,130,246,.20), transparent 34%), radial-gradient(circle at 76% 86%, rgba(6,182,212,.22), transparent 36%), linear-gradient(135deg, #cbeedd 0%, #f5fff8 46%, #dceaff 100%) !important;"
        app_bg_image = "radial-gradient(circle at 3% 8%, rgba(22,101,52,.28), transparent 32%), radial-gradient(circle at 96% 14%, rgba(59,130,246,.20), transparent 34%), radial-gradient(circle at 76% 86%, rgba(6,182,212,.22), transparent 36%), linear-gradient(135deg, #cbeedd 0%, #f5fff8 46%, #dceaff 100%)"
        sb_bg = "linear-gradient(180deg, #2f8f70 0%, #3aa37b 48%, #2f7d65 100%)"
        sb_var = "--sb-bg: rgba(217,243,231,.98); --app-bg-image: " + app_bg_image + ";"
    else:
        app_bg = "background: linear-gradient(135deg, #2e1065 0%, #1e0a4a 40%, #1a0533 100%) !important;"
        app_bg_image = "radial-gradient(ellipse at 0% 0%, #3b0764 0%, transparent 50%), radial-gradient(ellipse at 100% 0%, #1e1b4b 0%, transparent 50%), radial-gradient(ellipse at 50% 100%, #4c1d95 0%, transparent 55%), radial-gradient(ellipse at 100% 100%, #1a0533 0%, transparent 50%), linear-gradient(135deg, #2e1065 0%, #1e0a4a 35%, #0f0627 65%, #1a0533 100%)"
        sb_bg = "#1e0a4a"
        sb_var = "--sb-bg: #150732; --app-bg-image: " + app_bg_image + ";"
    st.markdown(f"""<style>
    :root {{ {vars_css} {sb_var} }}
    .stApp {{ {app_bg} }}
    section[data-testid="stSidebar"] {{ background: {sb_bg} !important; }}
    a.anchor-link, .anchor-link {{ display:none !important; visibility:hidden !important; }}
    .notice-success {{
        padding:13px 16px;
        border-radius:14px;
        border:1px solid {"rgba(22,163,74,.20)" if is_light else "rgba(16,185,129,.28)"};
        background:{"linear-gradient(135deg, rgba(22,163,74,.13), rgba(6,182,212,.08))" if is_light else "linear-gradient(135deg, rgba(16,185,129,.16), rgba(34,211,238,.08))"};
        color:{"#14532d" if is_light else "#d1fae5"};
        font-weight:850;
        margin:10px 0;
    }}
    .notice-info {{
        padding:13px 16px;
        border-radius:14px;
        border:1px solid {"rgba(14,159,154,.22)" if is_light else "rgba(139,92,246,.30)"};
        background:{"linear-gradient(135deg, rgba(6,182,212,.10), rgba(255,255,255,.58))" if is_light else "linear-gradient(135deg, rgba(124,58,237,.16), rgba(6,182,212,.08))"};
        color:var(--text);
        font-weight:760;
        margin:10px 0;
    }}
    .clean-title {{
        font-size:22px;
        font-weight:950;
        letter-spacing:-.2px;
        color:var(--text);
        margin:22px 0 10px;
    }}
    .soft-panel {{
        background:{"rgba(255,255,255,.70)" if is_light else "rgba(255,255,255,.035)"};
        border:1px solid var(--stroke);
        border-radius:22px;
        box-shadow:var(--shadow);
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border-radius:24px !important;
        border:1px solid {"rgba(20,121,86,.16)" if is_light else "rgba(139,92,246,.28)"} !important;
        background:{"linear-gradient(145deg, rgba(255,255,255,.78), rgba(232,249,240,.72))" if is_light else "linear-gradient(145deg, rgba(31,15,68,.90), rgba(22,11,54,.86))"} !important;
        box-shadow:{"0 18px 48px rgba(31,111,83,.13)" if is_light else "0 18px 48px rgba(0,0,0,.28)"} !important;
    }}
    .bento-card, .metric-card, .eda-card, .pf-card, .smart-card, .viz-card, .panel-card {{
        border-radius:22px !important;
        border:1px solid {"rgba(20,121,86,.16)" if is_light else "rgba(139,92,246,.28)"} !important;
        background:{"linear-gradient(145deg, rgba(255,255,255,.78), rgba(232,249,240,.72))" if is_light else "linear-gradient(145deg, rgba(38,18,82,.92), rgba(22,11,54,.88))"} !important;
        box-shadow:{"0 18px 48px rgba(31,111,83,.14)" if is_light else "0 18px 48px rgba(0,0,0,.28)"} !important;
    }}
    .metric-card {{
        min-height:118px;
        padding:20px 22px !important;
        display:flex; flex-direction:column; justify-content:space-between; gap:8px;
        position:relative; overflow:hidden;
    }}
    .metric-card:before {{
        content:""; position:absolute; width:120px; height:120px; right:-44px; top:-48px;
        border-radius:50%; background:{"rgba(18,148,107,.10)" if is_light else "rgba(124,58,237,.16)"};
    }}
    .metric-card .metric-icon {{
        width:40px; height:40px; border-radius:14px; display:flex; align-items:center; justify-content:center;
        background:{"rgba(18,148,107,.10)" if is_light else "rgba(124,58,237,.16)"}; color:var(--accent); font-weight:950;
    }}
    .metric-card .metric-label {{
        font-size:12px !important; font-weight:950 !important; letter-spacing:1.1px; color:var(--muted) !important; text-transform:uppercase;
    }}
    .metric-card .metric-value {{
        font-size:32px !important; font-weight:950 !important; color:var(--text) !important; line-height:1.05;
    }}
    .feature-card {{
        border-radius:24px; padding:22px; min-height:170px;
        border:1px solid {"rgba(20,121,86,.16)" if is_light else "rgba(139,92,246,.26)"};
        background:{"linear-gradient(145deg, rgba(255,255,255,.82), rgba(224,246,236,.72))" if is_light else "linear-gradient(145deg, rgba(39,18,85,.96), rgba(19,8,48,.94))"};
        box-shadow:{"0 20px 55px rgba(31,111,83,.14)" if is_light else "0 20px 55px rgba(0,0,0,.32)"};
    }}
    .feature-card-title {{font-size:22px;font-weight:950;color:var(--text);margin-bottom:6px;}}
    .feature-card-sub {{font-size:13px;font-weight:750;color:var(--muted);line-height:1.55;}}
    .status-card {{
        padding:18px 22px; border-radius:20px; font-size:16px; font-weight:900; line-height:1.65;
        background:{"linear-gradient(135deg, rgba(20,184,166,.12), rgba(22,163,74,.10))" if is_light else "linear-gradient(135deg, rgba(6,182,212,.16), rgba(16,185,129,.12))"};
        color:{"#14532d" if is_light else "#d1fae5"};
        border:1px solid {"rgba(18,148,107,.22)" if is_light else "rgba(16,185,129,.28)"};
        margin:16px 0;
    }}
    div[data-testid="stMetric"] {{
        border-radius:22px !important;
        padding:18px 20px !important;
        border:1px solid {"rgba(20,121,86,.16)" if is_light else "rgba(139,92,246,.28)"} !important;
        background:{"linear-gradient(145deg, rgba(255,255,255,.80), rgba(232,249,240,.72))" if is_light else "linear-gradient(145deg, rgba(38,18,82,.92), rgba(22,11,54,.88))"} !important;
        box-shadow:{"0 18px 48px rgba(31,111,83,.14)" if is_light else "0 18px 48px rgba(0,0,0,.28)"} !important;
    }}
    div[data-testid="stMetric"] label, div[data-testid="stMetric"] [data-testid="stMetricLabel"] {{
        font-size:12px !important; font-weight:950 !important; color:var(--muted) !important; letter-spacing:.5px !important;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        font-size:34px !important; font-weight:950 !important; color:var(--text) !important;
    }}
    .section-chip {{
        display:inline-flex; align-items:center; justify-content:center;
        min-width:150px; padding:10px 18px; margin:18px 0 12px;
        border-radius:999px;
        background:{"linear-gradient(135deg, rgba(22,163,74,.18), rgba(6,182,212,.12))" if is_light else "linear-gradient(135deg, rgba(124,58,237,.34), rgba(6,182,212,.12))"};
        color:{"#065f46" if is_light else "#d8b4fe"};
        border:1px solid {"rgba(20,121,86,.28)" if is_light else "rgba(167,139,250,.46)"};
        font-weight:950; letter-spacing:.6px;
        box-shadow:{"0 10px 24px rgba(31,111,83,.12)" if is_light else "0 10px 28px rgba(0,0,0,.28)"};
    }}
    .clean-table {{
        width:100% !important;
        border-collapse:separate !important;
        border-spacing:0 !important;
        table-layout:fixed !important;
        margin:0 0 10px 0 !important;
        overflow:hidden !important;
        border-radius:16px !important;
        border:1px solid {"rgba(20,121,86,.26)" if is_light else "rgba(167,139,250,.34)"} !important;
        background:{"rgba(255,255,255,.70)" if is_light else "rgba(30,16,64,.82)"} !important;
    }}
    .clean-table th {{
        padding:14px 16px !important;
        text-align:left !important;
        background:{"linear-gradient(135deg, rgba(187,247,208,.66), rgba(191,219,254,.48))" if is_light else "linear-gradient(135deg, rgba(76,29,149,.86), rgba(49,22,96,.88))"} !important;
        color:{"#065f46" if is_light else "#ffffff"} !important;
        font-size:14px !important;
        font-weight:950 !important;
        letter-spacing:.45px !important;
        text-shadow:{"none" if is_light else "0 1px 6px rgba(0,0,0,.38)"} !important;
        border-bottom:1px solid {"rgba(20,121,86,.25)" if is_light else "rgba(167,139,250,.34)"} !important;
    }}
    .clean-table td {{
        padding:15px 16px !important;
        vertical-align:middle !important;
        color:{"#0f2f22" if is_light else "#ffffff"} !important;
        font-size:14.5px !important;
        font-weight:850 !important;
        border-top:1px solid {"rgba(20,121,86,.14)" if is_light else "rgba(167,139,250,.18)"} !important;
        background:{"rgba(255,255,255,.52)" if is_light else "rgba(35,18,76,.72)"} !important;
    }}
    .clean-table.clean-row-table {{
        cursor:pointer !important;
        transition:transform .16s ease, box-shadow .16s ease, border-color .16s ease !important;
    }}
    .clean-table.clean-row-table:hover {{
        transform:translateY(-1px) !important;
        border-color:{"rgba(8,127,91,.44)" if is_light else "rgba(216,180,254,.58)"} !important;
        box-shadow:{"0 16px 34px rgba(31,111,83,.14)" if is_light else "0 16px 34px rgba(0,0,0,.28)"} !important;
    }}
    .clean-table.clean-row-table:hover td {{
        background:{"rgba(234,249,242,.92)" if is_light else "rgba(48,24,96,.86)"} !important;
    }}
    .clean-table td span[style*="var(--muted)"] {{
        color:{"#234236" if is_light else "#d8c8ff"} !important;
        font-weight:850 !important;
        opacity:1 !important;
    }}
    .op-badge {{
        display:inline-flex !important;
        border-radius:12px !important;
        padding:7px 12px !important;
        background:{"rgba(22,163,74,.14)" if is_light else "rgba(124,58,237,.24)"} !important;
        color:{"#03543f" if is_light else "#ffffff"} !important;
        border:1px solid {"rgba(20,121,86,.30)" if is_light else "rgba(216,180,254,.50)"} !important;
        font-size:13.5px !important;
        font-weight:950 !important;
    }}
    .badge {{
        display:inline-flex !important;
        border-radius:999px !important;
        padding:8px 12px !important;
        background:{"rgba(6,182,212,.12)" if is_light else "rgba(6,182,212,.14)"} !important;
        color:{"#064e3b" if is_light else "#ffffff"} !important;
        border:1px solid {"rgba(14,116,144,.20)" if is_light else "rgba(34,211,238,.28)"} !important;
        font-weight:950 !important;
        font-size:12px !important;
    }}
    .impact-high {{color:{"#b91c1c" if is_light else "#fecaca"} !important; font-weight:950 !important;}}
    .impact-medium {{color:{"#b45309" if is_light else "#fde68a"} !important; font-weight:950 !important;}}
    .impact-low {{color:{"#047857" if is_light else "#bbf7d0"} !important; font-weight:950 !important;}}
    [data-testid="stDataFrame"],
    [data-testid="stDataFrame"] > div,
    [data-testid="stDataFrameResizable"] {{
        width:100% !important;
        max-width:100% !important;
        min-width:0 !important;
    }}
    [data-testid="stDataFrame"] [role="grid"] {{
        width:100% !important;
        max-width:100% !important;
    }}
    .ts-chart-spacer {{height:72px !important;}}
    </style>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════
def fmt_int(value):
    try: return f"{int(value):,}".replace(",", ".")
    except: return str(value)

def clean_ui_label(label: str) -> str:
    """Remove leading decorative emoji/icons from labels while preserving internal page keys."""
    label = str(label)
    # Remove common leading emoji/codepoint decorations plus extra spaces
    return re.sub(r'^[^A-Za-z0-9#]+\s*', '', label).strip()

def clean_section_label(label: str) -> str:
    """Remove the category icon and format sidebar section title."""
    label = str(label)
    label = re.sub(r'^[^A-Za-z0-9]+\s*', '', label).strip()
    return label.title()

def sidebar_page_label(page: str) -> str:
    """Return a clean sidebar label with a monochrome leading icon."""
    return f"{SIDEBAR_PAGE_ICONS.get(page, '•')} {clean_ui_label(page)}"

def sidebar_category_label(category: str) -> str:
    """Return an expanded/collapsed-friendly category label."""
    return f"{SIDEBAR_CATEGORY_ICONS.get(category, '•')} {clean_section_label(category)}"

def strip_decorative_emoji(value: str) -> str:
    """Remove decorative emoji symbols from UI messages while keeping normal text."""
    value = str(value)
    value = re.sub(r'[\U00010000-\U0010ffff]', '', value)
    value = re.sub(r'[✅❌⚠️✔✖✕🔍🔎📌📊📈📉📄📤📥🧹🧠✨♻️🔁🗑️📁📦💡🎨🔗⏳🚀🏠👁️]', '', value)
    value = value.replace('  ', ' ').strip()
    return value

def file_size_label(size_bytes):
    if not size_bytes: return "-"
    units = ["B","KB","MB","GB"]; size = float(size_bytes); idx = 0
    while size >= 1024 and idx < len(units)-1: size /= 1024; idx += 1
    return f"{size:.2f} {units[idx]}"

def dataset_summary(df):
    if df is None: return {"rows":0,"cols":0,"numeric":0,"category":0,"missing":0,"duplicate":0,"date":0}
    return {
        "rows": df.shape[0], "cols": df.shape[1],
        "numeric": len(df.select_dtypes(include="number").columns),
        "category": len(df.select_dtypes(include=["object","category","bool"]).columns),
        "missing": int(df.isna().sum().sum()), "duplicate": int(df.duplicated().sum()),
        "date": len([c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]),
    }

def data_quality_score(df):
    if df is None or df.empty: return 0, "No Data"
    total = max(df.shape[0]*df.shape[1], 1)
    mp = df.isna().sum().sum()/total*100; dp = df.duplicated().sum()/max(df.shape[0],1)*100
    score = int(round(max(0, min(100, 100-mp-dp))))
    label = "Excellent" if score>=90 else "Good" if score>=75 else "Need Cleaning" if score>=55 else "Poor"
    return score, label

def metric_card(icon, label, value):
    label_clean = strip_decorative_emoji(label)
    icon_html = f'<div class="metric-icon">{strip_decorative_emoji(icon)}</div>' if str(icon).strip() else ''
    return f"""<div class="metric-card">{icon_html}<div class="metric-label">{label_clean}</div><div class="metric-value">{fmt_int(value)}</div></div>"""

def go_to(page):
    st.session_state.active_page = page; st.session_state.nav_radio = page; st.session_state._scroll_to_main = True

def log_activity(action, detail=""):
    """Keep a lightweight activity log so the final report reflects what was done in the web app."""
    try:
        if "activity_log" not in st.session_state:
            st.session_state.activity_log = []
        ts = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        entry = {"time": ts, "action": str(action), "detail": str(detail)}
        if st.session_state.activity_log and st.session_state.activity_log[-1].get("action") == entry["action"] and st.session_state.activity_log[-1].get("detail") == entry["detail"]:
            return
        st.session_state.activity_log.append(entry)
        st.session_state.activity_log = st.session_state.activity_log[-250:]
    except Exception:
        pass

def activity_log_df():
    logs = st.session_state.get("activity_log", [])
    if not logs:
        return pd.DataFrame(columns=["Time", "Action", "Detail"])
    return pd.DataFrame(logs).rename(columns={"time":"Time", "action":"Action", "detail":"Detail"})

def logout():
    for k in ["authenticated","username","user_role","df","df_original","active_page","nav_radio","before_snap","after_snap","before_df","after_df","cleaning_log","active_file","last_upload_signature","cleaning_notice"]:
        st.session_state[k] = DEFAULT_STATE.get(k, None) if k in DEFAULT_STATE else None
    st.session_state["authenticated"] = False
    st.session_state["active_page"] = "🏠 Dashboard"
    st.session_state["nav_radio"] = "🏠 Dashboard"

def scroll_to_main():
    if not st.session_state.get("_scroll_to_main", False): return
    components.html("""<script>setTimeout(()=>{const d=window.parent.document;const t=d.getElementById('main-anchor');if(t)t.scrollIntoView({behavior:'smooth'});else window.parent.scrollTo({top:0,behavior:'smooth'});},180);</script>""", height=0)
    st.session_state._scroll_to_main = False

def themed_dataframe_style(df_style):
    is_light = "Light" in st.session_state.get("ui_theme","🌙 Dark Mode")
    if is_light: bg,head,text,border = "#ffffff","#e8f5ec","#0a2218","#b7e4c7"
    else: bg,head,text,border = "#0d1526","#111e35","#e4eeff","#1e3a6b"
    return (df_style.style
        .set_table_styles([
            {"selector":"thead th","props":[("background-color",head),("color",text),("font-weight","900"),("border",f"1px solid {border}")]},
            {"selector":"tbody td","props":[("background-color",bg),("color",text),("border",f"1px solid {border}")]},
        ])
        .set_properties(**{"background-color":bg,"color":text,"border-color":border})
    )


def get_display_name(username=None):
    """Return user-facing name for sidebar/account display."""
    username = username or st.session_state.get("username", "")
    db = st.session_state.get("users_db", {})
    info = db.get(username, {}) if username else {}
    name = str(info.get("name", "")).strip()
    if name:
        return name
    return username.title() if username else "Guest"



def render_paginated_table(data, key="table", title=None, page_size_default=10, height=430):
    """Full-width dataframe viewer with search + pagination.

    Raw DataFrame rendering is intentionally used instead of Pandas Styler because
    Streamlit gives the native grid the full available width and a smoother
    horizontal scroll for datasets with many columns.
    """
    if data is None:
        st.info("Tidak ada data untuk ditampilkan.")
        return
    try:
        data = pd.DataFrame(data).copy()
    except Exception:
        st.write(data)
        return
    if data.empty:
        st.info("Dataset kosong.")
        return

    # Make every grid occupy the complete content width on preview, statistics,
    # cleaning before/after, history, and all other table pages.
    st.markdown("""
    <style>
    [data-testid="stDataFrame"],
    [data-testid="stDataFrame"] > div,
    [data-testid="stDataFrameResizable"] {
        width:100% !important;
        max-width:100% !important;
        min-width:0 !important;
    }
    [data-testid="stDataFrame"] [role="grid"] {
        width:100% !important;
        max-width:100% !important;
    }
    [data-testid="stDataFrame"] canvas {
        max-width:none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if title:
        st.markdown(f"### {title}")

    top_left, top_right = st.columns([5, 1.15])
    with top_left:
        search = st.text_input(
            "Search data",
            placeholder="Cari teks/angka di semua kolom...",
            key=f"{key}_search",
        )
    with top_right:
        page_options = [10, 25, 50, 100, 200]
        idx = page_options.index(page_size_default) if page_size_default in page_options else 0
        page_size = st.selectbox(
            "Rows/page", page_options, index=idx, key=f"{key}_page_size"
        )

    view = data
    if search:
        s_text = str(search).lower()
        try:
            mask = view.astype(str).apply(
                lambda row: row.str.lower().str.contains(s_text, na=False).any(), axis=1
            )
            view = view[mask]
        except Exception:
            pass

    total_rows = len(view)
    total_pages = max(1, int(np.ceil(total_rows / page_size)))
    page_key = f"{key}_page"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1
    st.session_state[page_key] = max(
        1, min(int(st.session_state[page_key]), total_pages)
    )
    page = st.session_state[page_key]
    start = (page - 1) * page_size
    end = min(start + page_size, total_rows)
    current_view = view.iloc[start:end].copy()

    shown_rows = max(1, len(current_view))
    dynamic_height = min(height, max(122, 36 * shown_rows + 52))

    # Native Streamlit grid: full-width and responsive. This is the same approach
    # used by the user's full-width reference project.
    st.dataframe(
        current_view,
        use_container_width=True,
        height=dynamic_height,
        hide_index=False,
    )

    p1, p2, p3, p4 = st.columns([1, 1, 3.6, 1])
    with p1:
        if st.button(
            "‹ Prev",
            key=f"{key}_prev",
            use_container_width=True,
            disabled=page <= 1,
        ):
            st.session_state[page_key] = max(1, page - 1)
            st.rerun()
    with p2:
        if st.button(
            "Next ›",
            key=f"{key}_next",
            use_container_width=True,
            disabled=page >= total_pages,
        ):
            st.session_state[page_key] = min(total_pages, page + 1)
            st.rerun()
    with p3:
        shown_start = start + 1 if total_rows else 0
        st.caption(
            f"Halaman {page} dari {total_pages} · Menampilkan {shown_start}-{end} "
            f"dari {fmt_int(total_rows)} baris hasil filter · Total asli "
            f"{fmt_int(len(data))} baris"
        )
    with p4:
        new_page = st.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            value=page,
            key=f"{key}_jump",
            label_visibility="collapsed",
        )
        if int(new_page) != page:
            st.session_state[page_key] = int(new_page)
            st.rerun()




def _safe_to_datetime(series):
    """Convert many common date formats safely without crashing on newer pandas."""
    try:
        return pd.to_datetime(series, errors="coerce", format="mixed")
    except TypeError:
        return pd.to_datetime(series, errors="coerce")
    except Exception:
        return pd.to_datetime(series.astype(str), errors="coerce")


def _is_year_like(series):
    vals = pd.to_numeric(series, errors="coerce").dropna()
    if vals.empty:
        return False
    ratio = ((vals >= 1900) & (vals <= 2100) & (vals % 1 == 0)).mean()
    unique_count = vals.nunique()
    return ratio >= 0.6 and unique_count >= 2


def detect_time_candidates(df):
    """Detect real date/time columns or year-like columns."""
    candidates = []
    if df is None or df.empty:
        return candidates

    hints = (
        "date", "tanggal", "time", "datetime", "timestamp",
        "year", "tahun", "month", "bulan", "periode", "period"
    )

    for col in df.columns:
        ser = df[col]
        col_lower = str(col).lower().strip()

        if pd.api.types.is_datetime64_any_dtype(ser):
            candidates.append((col, "datetime"))
            continue

        if ("year" in col_lower or "tahun" in col_lower) and _is_year_like(ser):
            candidates.append((col, "year"))
            continue

        if any(h in col_lower for h in hints):
            parsed = _safe_to_datetime(ser)
            parse_ratio = parsed.notna().mean() if len(parsed) else 0
            if parse_ratio >= 0.45:
                candidates.append((col, "parse"))
                continue
            if _is_year_like(ser):
                candidates.append((col, "year"))
                continue

        if ser.dtype == "object" or str(ser.dtype).startswith("string"):
            parsed = _safe_to_datetime(ser)
            parse_ratio = parsed.notna().mean() if len(parsed) else 0
            if parse_ratio >= 0.65:
                candidates.append((col, "parse"))

    seen = set()
    out = []
    for col, kind in candidates:
        if col not in seen:
            seen.add(col)
            out.append((col, kind))
    return out


def _convert_to_datetime(series, kind="parse"):
    if kind == "year":
        vals = pd.to_numeric(series, errors="coerce")
        out = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
        mask = vals.notna()
        out.loc[mask] = pd.to_datetime(vals.loc[mask].astype(int).astype(str) + "-01-01", errors="coerce")
        return out
    return _safe_to_datetime(series)



def _period_to_freq(period_label):
    return {"Harian": "D", "Mingguan": "W", "Bulanan": "M", "Tahunan": "Y"}.get(period_label, "M")


def _freq_to_offset(freq):
    try:
        return pd.tseries.frequencies.to_offset(freq)
    except Exception:
        return pd.tseries.frequencies.to_offset("M")


def _select_default_time_value(df, date_col=None):
    numeric_cols = [c for c in df.select_dtypes(include="number").columns.tolist() if str(c) != str(date_col)]
    return numeric_cols[0] if numeric_cols else "Jumlah Baris / Frekuensi"


def build_time_series_analysis(df, date_col=None, value_col=None, period_label="Bulanan", agg_label="Sum", window=7):
    """Build complete Time Series output required by the rubric."""
    if df is None or df.empty:
        return {"ok": False, "message": "Dataset kosong.", "candidates": []}

    candidates = detect_time_candidates(df)
    if not candidates:
        return {"ok": False, "message": "Dataset ini tidak memiliki kolom tanggal/datetime yang valid untuk Time Series.", "candidates": []}

    candidate_map = {str(c): kind for c, kind in candidates}
    if date_col is None or str(date_col) not in candidate_map:
        date_col = str(candidates[0][0])
    kind = candidate_map[str(date_col)]

    numeric_cols = [c for c in df.select_dtypes(include="number").columns.tolist() if str(c) != str(date_col)]
    if value_col is None or (value_col not in numeric_cols and value_col != "Jumlah Baris / Frekuensi"):
        value_col = _select_default_time_value(df, date_col)

    work = pd.DataFrame(index=df.index)
    work["Periode Asli"] = _convert_to_datetime(df[date_col], kind)
    if value_col == "Jumlah Baris / Frekuensi" or value_col not in df.columns:
        work["Nilai"] = 1.0
        value_note = "jumlah baris/frekuensi"
        agg_func = "sum"
    else:
        work["Nilai"] = pd.to_numeric(df[value_col], errors="coerce")
        value_note = str(value_col)
        agg_func = {"Sum": "sum", "Mean": "mean", "Count": "count"}.get(str(agg_label), "sum")

    work = work.dropna(subset=["Periode Asli", "Nilai"])
    if work.empty:
        return {"ok": False, "message": f"Kolom waktu {date_col} terdeteksi, tetapi nilainya tidak berhasil dikonversi menjadi tanggal.", "candidates": candidates}

    freq = _period_to_freq(period_label)
    try:
        work["Periode"] = work["Periode Asli"].dt.to_period(freq).dt.to_timestamp()
    except Exception:
        work["Periode"] = pd.to_datetime(work["Periode Asli"], errors="coerce")

    grouped = work.groupby("Periode", as_index=False).agg(Nilai=("Nilai", agg_func)).sort_values("Periode")
    grouped = grouped.dropna(subset=["Periode", "Nilai"])
    if grouped.empty:
        return {"ok": False, "message": "Data time series kosong setelah agregasi.", "candidates": candidates}

    window = int(max(2, min(int(window), max(len(grouped), 2))))
    grouped["Moving Average"] = grouped["Nilai"].rolling(window=window, min_periods=1).mean()
    grouped["Rolling Mean"] = grouped["Nilai"].rolling(window=window, min_periods=1).mean()

    trend_delta = 0.0
    slope = 0.0
    intercept = float(grouped["Nilai"].iloc[0]) if len(grouped) else 0.0
    grouped["Trend Line"] = np.nan
    if len(grouped) >= 2:
        x = np.arange(len(grouped), dtype=float)
        y = pd.to_numeric(grouped["Nilai"], errors="coerce").astype(float).values
        mask = np.isfinite(y)
        if mask.sum() >= 2:
            slope, intercept = np.polyfit(x[mask], y[mask], 1)
            grouped["Trend Line"] = intercept + slope * x
            trend_delta = float(grouped["Nilai"].iloc[-1] - grouped["Nilai"].iloc[0])

    pattern_summary = summarize_time_series_pattern(grouped, period_label, value_note, trend_delta)
    note = f"Time Series otomatis memakai kolom waktu '{date_col}' dan nilai '{value_note}' dengan agregasi {period_label.lower()}."
    return {
        "ok": True,
        "candidates": candidates,
        "date_col": str(date_col),
        "value_col": value_col,
        "value_note": value_note,
        "period_label": period_label,
        "agg_label": agg_label,
        "window": window,
        "freq": freq,
        "data": grouped,
        "trend_delta": trend_delta,
        "slope": float(slope),
        "note": note,
        "pattern_summary": pattern_summary,
    }


def summarize_time_series_pattern(grouped, period_label, value_note, trend_delta=None):
    if grouped is None or grouped.empty:
        return ["Pola time series belum dapat diringkas karena data kosong."]
    vals = pd.to_numeric(grouped["Nilai"], errors="coerce").dropna()
    if vals.empty:
        return ["Nilai time series tidak cukup valid untuk diringkas."]
    if trend_delta is None:
        trend_delta = float(vals.iloc[-1] - vals.iloc[0]) if len(vals) >= 2 else 0.0
    direction = "meningkat" if trend_delta > 0 else "menurun" if trend_delta < 0 else "stabil"
    fluct = float(vals.std() / (abs(vals.mean()) + 1e-9)) if len(vals) >= 2 else 0.0
    fluct_label = "tinggi" if fluct >= 0.35 else "sedang" if fluct >= 0.15 else "rendah"
    max_i = vals.idxmax(); min_i = vals.idxmin()
    try:
        max_period = pd.to_datetime(grouped.loc[max_i, "Periode"]).strftime("%Y-%m-%d")
        min_period = pd.to_datetime(grouped.loc[min_i, "Periode"]).strftime("%Y-%m-%d")
    except Exception:
        max_period = str(grouped.loc[max_i, "Periode"]); min_period = str(grouped.loc[min_i, "Periode"])
    seasonality = "Belum cukup periode untuk mendeteksi seasonality."
    try:
        if len(grouped) >= 24:
            tmp = grouped.copy()
            tmp["month"] = pd.to_datetime(tmp["Periode"]).dt.month
            monthly = tmp.groupby("month")["Nilai"].mean()
            if len(monthly) >= 6:
                amp = (monthly.max() - monthly.min()) / (abs(monthly.mean()) + 1e-9)
                if amp >= 0.25:
                    seasonality = f"Terdapat indikasi pola musiman; bulan {int(monthly.idxmax())} cenderung memiliki nilai rata-rata tertinggi."
                else:
                    seasonality = "Pola musiman tidak terlalu kuat berdasarkan rata-rata bulanan."
    except Exception:
        pass
    return [
        f"Tren time series untuk {value_note} cenderung {direction} dengan perubahan total {trend_delta:,.2f} dari awal ke akhir periode.",
        f"Fluktuasi data tergolong {fluct_label} (coefficient of variation {fluct:.2f}).",
        seasonality,
        f"Nilai tertinggi berada pada periode {max_period}; nilai terendah pada periode {min_period}.",
    ]


def render_universal_time_series(df):
    """Time-series page that follows the final-exam requirement."""
    st.markdown("## Time Series Analytics")
    st.caption("Auto-detection kolom tanggal/datetime untuk trend detection, moving average, rolling mean, dan visualisasi interaktif.")

    if df is None or df.empty:
        st.warning("Dataset belum tersedia atau kosong.")
        return

    time_candidates = detect_time_candidates(df)
    if not time_candidates:
        st.info("Dataset ini tidak memiliki kolom tanggal/datetime yang valid.")
        html = '<div class="panel-card" style="margin-top:14px; padding:18px;"><b>Contoh kolom waktu yang didukung:</b><br><span style="opacity:.85;">date, tanggal, timestamp, datetime, year/tahun, month/bulan, order_date, created_at</span></div>'
        st.markdown(html, unsafe_allow_html=True)
        return

    time_labels = [str(c[0]) for c in time_candidates]
    numeric_cols = [str(c) for c in df.select_dtypes(include="number").columns.tolist()]
    c1, c2, c3, c4 = st.columns([1.25, 1.25, 1, 1])
    date_sel = c1.selectbox("Kolom waktu", time_labels, key="ts_date_real_only")
    value_options = [c for c in numeric_cols if c != date_sel] + ["Jumlah Baris / Frekuensi"]
    val_sel = c2.selectbox("Nilai dianalisis", value_options, key="ts_value_real_only")
    period_label = c3.selectbox("Agregasi", ["Harian", "Mingguan", "Bulanan", "Tahunan"], index=2, key="ts_period_real_only")
    agg_label = c4.selectbox("Metode", ["Sum", "Mean", "Count"], index=0, key="ts_agg_real_only")
    window = st.slider("Moving Average / Rolling Mean", 2, 30, 7, key="ts_window_real_only")

    result = build_time_series_analysis(df, date_col=date_sel, value_col=val_sel, period_label=period_label, agg_label=agg_label, window=window)
    if not result.get("ok"):
        st.warning(result.get("message", "Time Series gagal dianalisis."))
        return

    grouped = result["data"]
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(metric_card("", "Periode", len(grouped)), unsafe_allow_html=True)
    k2.markdown(metric_card("Σ", "Total", f"{grouped['Nilai'].sum():,.2f}"), unsafe_allow_html=True)
    k3.markdown(metric_card("μ", "Rata-rata", f"{grouped['Nilai'].mean():,.2f}"), unsafe_allow_html=True)
    k4.markdown(metric_card("", "Trend", f"{result['trend_delta']:,.2f}"), unsafe_allow_html=True)

    theme_mode = "light" if "Light" in st.session_state.get("ui_theme", "Dark Mode") else "dark"
    st.markdown('<div class="ts-chart-spacer"></div>', unsafe_allow_html=True)
    st.plotly_chart(
        plot_time_series(
            grouped, "Periode", "Nilai", window=window, theme=theme_mode,
            ma_col="Moving Average", rolling_col="Rolling Mean", trend_col="Trend Line",
            title="Time Series Line Chart, Trend Line, Moving Average & Rolling Mean"
        ),
        use_container_width=True,
        config={"displayModeBar": True, "responsive": True}
    )
    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

    st.markdown('<div class="status-card">' + result["note"] + '</div>', unsafe_allow_html=True)
    pattern_html = ''.join([f'<li>{strip_decorative_emoji(x)}</li>' for x in result.get("pattern_summary", [])])
    st.markdown(f'<div class="panel-card" style="padding:18px;margin:14px 0;"><b>Ringkasan Pola Time Series</b><ul style="margin:10px 0 0 18px;line-height:1.7;">{pattern_html}</ul></div>', unsafe_allow_html=True)

    st.markdown("### Hasil Time Series")
    render_paginated_table(grouped, key="time_series_result", page_size_default=10, height=320)


# ══════════════════════════════════════════════════════
#  TEAM MEMBERS & PHOTO UTILITIES
# ══════════════════════════════════════════════════════
TEAM_MEMBERS = [
    {"nim":"52250009","name":"Dhea Putri Khasanah","aliases":["dhea","52250009"]},
    {"nim":"52250037","name":"Nurul Iffah","aliases":["iffah","52250037"]},
    {"nim":"52250038","name":"Fifi Muthia Pitaloka","aliases":["fifi","52250038"]},
    {"nim":"52250039","name":"Clara Maisie Wanghili","aliases":["clara","52250039"]},
    {"nim":"52250040","name":"Naisya Hafizh Mufidah","aliases":["naisya","52250040"]},
]

def _image_data_uri(path):
    try:
        mime = mimetypes.guess_type(str(path))[0] or "image/png"
        return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"
    except: return None

def _find_member_photo(member):
    dirs = [BASE_DIR/"frontend"/"static"/"assets"/"images"]
    exts = [".png",".jpg",".jpeg"]
    aliases = list(dict.fromkeys([*member.get("aliases",[]), member["nim"]]))
    for folder in dirs:
        if not folder.exists(): continue
        for alias in aliases:
            for ext in exts:
                p = folder/f"{alias}{ext}"
                if p.exists(): return p
        for f in folder.iterdir():
            if f.suffix.lower() in exts:
                stem = f.stem.lower()
                if any(a.lower() in stem for a in aliases): return f
    return None

def _get_avatar_path(member):
    img_dir = BASE_DIR/"frontend"/"static"/"assets"/"images"
    for name in [f"avatar_{member['nim']}.png", f"avatar_{member['aliases'][0]}.png"] if member.get("aliases") else [f"avatar_{member['nim']}.png"]:
        p = img_dir/name
        if p.exists(): return str(p)
    p = _find_member_photo(member)
    return str(p) if p else None

def _member_avatar_html(member, size=80, border_color="var(--cyan)"):
    path = _get_avatar_path(member)
    initials = "".join(p[0] for p in member["name"].split()[:2]).upper()
    if path:
        uri = _image_data_uri(Path(path))
        if uri:
            return f'<img src="{uri}" alt="{member["name"]}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;object-position:center top;border:3px solid {border_color};box-shadow:0 0 16px rgba(34,211,238,.35);display:block;margin:0 auto;">'
    return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--cyan));color:#fff;font-size:{size//4}px;font-weight:900;display:flex;align-items:center;justify-content:center;margin:0 auto;border:3px solid {border_color};">{initials}</div>'

def render_team_grid(card_class="", size=80):
    cards = []
    for m in TEAM_MEMBERS:
        avatar = _member_avatar_html(m, size)
        cards.append(f"""
        <div class="team-card-auth {card_class}">
            {avatar}
            <div class="team-name-auth">{m['name']}</div>
            <div class="team-nim-auth">{m['nim']}</div>
        </div>""")
    st.markdown(f'<div class="team-grid-auth">{"".join(cards)}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
#  AUTH PAGES — Sign In + Sign Up
# ══════════════════════════════════════════════════════
def auth_page():
    inject_theme_css()
    mode = st.session_state.get("register_mode", False)

    st.markdown("""
    <style>
    [data-testid="stHeader"],[data-testid="stToolbar"],
    [data-testid="stDecoration"],footer { display:none!important; }
    html, body, .stApp, [data-testid="stAppViewContainer"], .main {
        height:100vh!important;
        max-height:100vh!important;
        overflow:hidden!important;
    }
    .block-container {
        padding:.55rem 1rem!important;
        max-width:940px!important;
        margin:0 auto!important;
        min-height:100vh!important;
        display:flex!important;
        flex-direction:column!important;
        justify-content:center!important;
    }
    div[data-testid="InputInstructions"],
    div[data-testid="stTextInput"] small,
    [data-testid="stTextInput"] [data-testid="InputInstructions"] {
        display:none!important;
        visibility:hidden!important;
        height:0!important;
        margin:0!important;
        padding:0!important;
    }

    /* ── Uniform 4-side input border ── */
    [data-testid="stTextInput"]>div,
    [data-testid="stTextInput"]>div>div,
    div[data-baseweb="base-input"],
    div[data-baseweb="input"] {
        background:transparent!important; border:none!important;
        box-shadow:none!important; outline:none!important;
    }
    [data-testid="stTextInput"] input {
        background:rgba(255,255,255,.07)!important;
        border-top:   1.5px solid rgba(255,255,255,.2)!important;
        border-right: 1.5px solid rgba(255,255,255,.2)!important;
        border-bottom:1.5px solid rgba(255,255,255,.2)!important;
        border-left:  1.5px solid rgba(255,255,255,.2)!important;
        border-radius:12px!important;
        padding:12px 16px!important; font-size:14px!important;
        color:#f0eeff!important; width:100%!important;
        outline:none!important; box-shadow:none!important;
    }
    [data-testid="stTextInput"] input:focus {
        border-top:   1.5px solid #7c3aed!important;
        border-right: 1.5px solid #7c3aed!important;
        border-bottom:1.5px solid #7c3aed!important;
        border-left:  1.5px solid #7c3aed!important;
        box-shadow:0 0 0 3px rgba(124,58,237,.18)!important;
        outline:none!important;
    }
    [data-testid="stTextInput"] input::placeholder { color:rgba(255,255,255,.3)!important; }
    input[type="password"]::-ms-reveal,
    input[type="password"]::-ms-clear { display:none!important; width:0!important; height:0!important; }
    input[type="password"]::-webkit-credentials-auto-fill-button,
    input[type="password"]::-webkit-contacts-auto-fill-button { visibility:hidden!important; display:none!important; pointer-events:none!important; }
    [data-testid="stWidgetLabel"] { display:none!important; }

    div[data-testid="stFormSubmitButton"]>button {
        background:linear-gradient(135deg,#7c3aed,#4c1d95)!important;
        border:none!important; border-radius:12px!important;
        color:#fff!important; font-size:15px!important;
        font-weight:900!important; min-height:48px!important;
        box-shadow:0 8px 24px rgba(124,58,237,.4)!important;
        letter-spacing:1px!important; text-transform:uppercase!important;
        transition: all .25s ease!important;
    }
    div[data-testid="stFormSubmitButton"]>button:hover {
        box-shadow:0 12px 32px rgba(124,58,237,.6)!important;
        transform:translateY(-1px)!important;
    }
    .f-label { font-size:11px; font-weight:800; color:rgba(196,181,253,.7);
               letter-spacing:.8px; text-transform:uppercase;
               margin:10px 0 5px; display:block; }

    /* ── Native st.container(border=True) styling — used for BOTH panels ── */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius:24px!important;
        transition: all .45s cubic-bezier(.4,0,.2,1)!important;
        animation: fadeSlide .45s ease;
    }
    @keyframes fadeSlide {
        from { opacity:0; transform: translateX(12px); }
        to   { opacity:1; transform: translateX(0); }
    }
    /* Purple "switch" panel container */
    .switch-box div[data-testid="stVerticalBlockBorderWrapper"] {
        background:linear-gradient(160deg,#7c3aed 0%,#4c1d95 60%,#2e1065 100%)!important;
        border:none!important;
        box-shadow:0 20px 60px rgba(124,58,237,.3)!important;
    }
    .switch-box div[data-testid="stVerticalBlock"] { gap:0.4rem!important; }
    /* Form panel container */
    .form-box div[data-testid="stVerticalBlockBorderWrapper"] {
        background:#15092f!important;
        border:1px solid rgba(139,92,246,.25)!important;
        box-shadow:0 20px 60px rgba(0,0,0,.4)!important;
    }

    /* Switch button styling */
    .switch-box div[data-testid="stButton"]>button {
        border-radius:999px!important; font-weight:900!important;
        font-size:12.5px!important; min-height:42px!important;
        border:1.5px solid rgba(255,255,255,.6)!important;
        background:rgba(255,255,255,.1)!important; color:#fff!important;
        letter-spacing:1.5px!important; text-transform:uppercase!important;
        transition: all .2s ease!important;
    }
    .switch-box div[data-testid="stButton"]>button:hover {
        background:rgba(255,255,255,.25)!important;
        transform:translateY(-1px)!important;
    }

    /* Team strip inside switch panel */
    .team-strip-row {
        display:grid; grid-template-columns:repeat(5,1fr);
        gap:6px; margin-top:8px;
    }
    .tm-s { text-align:center; }
    .tm-s-name { font-size:9px; font-weight:900; color:#fff; margin-top:5px; line-height:1.2; }
    .tm-s-nim  { font-size:7.5px; font-family:'JetBrains Mono',monospace; color:rgba(255,255,255,.7); margin-top:1px; }
    </style>
    """, unsafe_allow_html=True)

    # ── Mode-dependent text & order ──
    if not mode:
        purple_title, purple_text = "Hello, Friend!", "Belum punya akun? Daftar sekarang untuk mengakses semua fitur Auto EDA Insight Dashboard."
        purple_btn = "Register"
        form_title = "Login"
        form_first = True
    else:
        purple_title, purple_text = "Welcome Back!", "Sudah punya akun? Masuk untuk melanjutkan eksplorasi data kamu di Auto EDA Insight."
        purple_btn = "Login"
        form_title = "Create Account"
        form_first = False

    # ── Logo header ──
    st.markdown(
        '<div style="text-align:center;padding:0 0 10px;">'
        '<div style="font-size:22px;filter:drop-shadow(0 0 16px rgba(139,92,246,.9));margin-bottom:6px;">◈</div>'
        '<div style="font-size:24px;font-weight:950;color:#fff;letter-spacing:-1px;'
        'text-shadow:0 0 30px rgba(139,92,246,.7);">Auto EDA Insight</div>'
        '<div style="font-family:JetBrains Mono,monospace;font-size:9.5px;color:#f59e0b;'
        'letter-spacing:3px;text-transform:uppercase;margin-top:4px;">DATA SCIENCE PROGRAMMING · Kelompok 6 · ITSB</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # ── TEAM photos HTML (used inside switch panel) ──
    team_cards = []
    for m in TEAM_MEMBERS:
        av = _member_avatar_html(m, size=38, border_color="rgba(255,255,255,.6)")
        team_cards.append(
            '<div class="tm-s">' + av +
            '<div class="tm-s-name">' + m["name"].split()[0] + '</div>' +
            '<div class="tm-s-nim">'  + m["nim"] + '</div></div>'
        )
    team_html = '<div class="team-strip-row">' + "".join(team_cards) + '</div>'

    # ── TWO-COLUMN LAYOUT — order swaps based on mode ──
    col_a, col_b = st.columns([1, 1], gap="medium")
    form_col   = col_a if form_first else col_b
    purple_col = col_b if form_first else col_a

    # ── PURPLE SWITCH PANEL ──
    with purple_col:
        st.markdown('<div class="switch-box">', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(
                f'<div style="text-align:center;color:#fff;padding:8px 4px;">'
                f'<div style="font-size:21px;font-weight:950;margin-bottom:6px;letter-spacing:-.5px;">{purple_title}</div>'
                f'<div style="font-size:11.5px;opacity:.85;line-height:1.45;margin-bottom:10px;">{purple_text}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            _, bcenter, _ = st.columns([1,1.6,1])
            with bcenter:
                if st.button(purple_btn, key="toggle_mode", use_container_width=True):
                    st.session_state.register_mode = not mode
                    st.rerun()
            st.markdown(team_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── FORM PANEL ──
    with form_col:
        st.markdown('<div class="form-box">', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(
                f'<div style="font-size:20px;font-weight:950;margin-bottom:8px;color:#fff;text-align:center;">{form_title}</div>',
                unsafe_allow_html=True
            )

            if not mode:
                with st.form("login_form", clear_on_submit=False):
                    st.markdown('<span class="f-label">Username</span>', unsafe_allow_html=True)
                    username = st.text_input("_u", placeholder="Username kamu",
                                             label_visibility="collapsed", key="login_user")
                    st.markdown('<span class="f-label">Password</span>', unsafe_allow_html=True)
                    password = st.text_input("_p", placeholder="Password kamu",
                                             type="password", label_visibility="collapsed", key="login_pass")
                    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                    submitted = st.form_submit_button("Sign In", use_container_width=True)
                if submitted:
                    db = st.session_state.users_db
                    username = username.strip().lower()
                    if username in db and db[username]["password"] == password:
                        st.session_state.authenticated = True
                        st.session_state.username    = username
                        st.session_state.user_role   = db[username].get("role","member")
                        st.session_state.active_page = "🏠 Dashboard"
                        st.session_state.nav_radio   = "🏠 Dashboard"
                        st.session_state.login_success_msg = f"Login berhasil, Selamat datang {get_display_name(username)}!"
                        st.rerun()
                    else:
                        st.error("Username atau password salah.")
            else:
                with st.form("register_form", clear_on_submit=True):
                    st.markdown('<span class="f-label">Username</span>', unsafe_allow_html=True)
                    new_user  = st.text_input("_ru", placeholder="Pilih username unik",  label_visibility="collapsed")
                    st.markdown('<span class="f-label">Nama Lengkap</span>', unsafe_allow_html=True)
                    new_name  = st.text_input("_rn", placeholder="Nama lengkap kamu",    label_visibility="collapsed")
                    st.markdown('<span class="f-label">Password</span>', unsafe_allow_html=True)
                    new_pass  = st.text_input("_rp", placeholder="Min. 6 karakter",      type="password", label_visibility="collapsed")
                    st.markdown('<span class="f-label">Ulangi Password</span>', unsafe_allow_html=True)
                    new_pass2 = st.text_input("_rp2", placeholder="Konfirmasi password", type="password", label_visibility="collapsed")
                    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                    reg_submit = st.form_submit_button("Sign Up", use_container_width=True)
                if reg_submit:
                    new_user = new_user.strip().lower()
                    new_name = new_name.strip() or new_user.title()
                    if not new_user or not new_pass:   st.error("Username & password wajib diisi.")
                    elif len(new_pass) < 6:            st.error("Password minimal 6 karakter.")
                    elif new_pass != new_pass2:        st.error("Konfirmasi password tidak cocok.")
                    elif new_user in st.session_state.users_db: st.error("Username sudah dipakai.")
                    else:
                        st.session_state.users_db[new_user] = {"password":new_pass,"role":"member","name":new_name}
                        st.success("Akun berhasil dibuat! Silakan Masuk.")
                        st.session_state.register_mode = False; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    components.html("""
    <script>
    (function(){
      const doc = window.parent.document;
      function visible(el){
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
      }
      function hardenAuthFields(){
        doc.querySelectorAll('form').forEach(form => {
          form.setAttribute('autocomplete', 'off');
          form.setAttribute('data-form-type', 'other');
        });
        const inputs = Array.from(doc.querySelectorAll('input')).filter(visible);
        const user = inputs.find(x => (x.getAttribute('placeholder') || '') === 'Username kamu');
        const pass = inputs.find(x => (x.getAttribute('placeholder') || '') === 'Password kamu');
        const passwordInputs = inputs.filter(x => (x.getAttribute('type') || '').toLowerCase() === 'password');
        if(user){
          user.setAttribute('autocomplete','off');
          user.setAttribute('autocapitalize','none');
          user.setAttribute('spellcheck','false');
          user.setAttribute('data-lpignore','true');
          user.setAttribute('data-1p-ignore','true');
          user.setAttribute('data-form-type','other');
        }
        passwordInputs.forEach(field => {
          field.setAttribute('autocomplete','off');
          field.setAttribute('data-lpignore','true');
          field.setAttribute('data-1p-ignore','true');
          field.setAttribute('data-form-type','other');
          field.setAttribute('passwordrules','');
          field.setAttribute('spellcheck','false');
        });
        return {user, pass};
      }
      function setupLoginEnter(){
        const {user, pass} = hardenAuthFields();
        if(user && pass && !user.dataset.enterFocusFixed){
          user.dataset.enterFocusFixed = '1';
          user.addEventListener('keydown', function(e){
            if(e.key === 'Enter'){
              e.preventDefault();
              e.stopPropagation();
              pass.focus();
            }
          }, true);
        }
        if(pass && !pass.dataset.enterSubmitFixed){
          pass.dataset.enterSubmitFixed = '1';
          pass.addEventListener('keydown', function(e){
            if(e.key === 'Enter'){
              const buttons = Array.from(doc.querySelectorAll('button'));
              const btn = buttons.find(b => (b.innerText || '').trim().toLowerCase() === 'sign in');
              if(btn){
                e.preventDefault();
                e.stopPropagation();
                btn.click();
              }
            }
          }, true);
        }
      }
      setupLoginEnter();
      setTimeout(setupLoginEnter, 250);
      setTimeout(setupLoginEnter, 700);
      setTimeout(setupLoginEnter, 1400);
    })();
    </script>
    """, height=0)



def inject_compact_sidebar_rail():
    """Keep a functional icon rail visible when Streamlit's sidebar is collapsed.

    Each compact category icon exposes the same child pages as the expanded
    sidebar, so navigation remains complete without reopening the sidebar.
    """
    is_light = "Light" in st.session_state.get("ui_theme", "Dark Mode")
    active_page = st.session_state.get("active_page", "🏠 Dashboard")

    category_targets = [
        ("Dashboard", "🏠 HOME", '<svg viewBox="0 0 24 24"><path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z"/></svg>'),
        ("Data Management", "📁 DATA MANAGEMENT", '<svg viewBox="0 0 24 24"><path d="M3 7.5h7l2 2h9v9.5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 7.5V6a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v1.5"/></svg>'),
        ("Cleaning", "🧹 CLEANING", '<svg viewBox="0 0 24 24"><path d="m14 4 6 6"/><path d="m12.5 5.5 6 6"/><path d="M4 20c3.2-.2 5.7-1.2 7.5-3l4-4-4.5-4.5-4 4C5.2 14.3 4.2 16.8 4 20Z"/></svg>'),
        ("Statistics", "📊 STATISTICS", '<svg viewBox="0 0 24 24"><path d="M5 20V10h4v10M10 20V4h4v16M15 20v-7h4v7"/><path d="M3 20h18"/></svg>'),
        ("Visualization", "📉 VISUALIZATION", '<svg viewBox="0 0 24 24"><path d="M4 18 9 12l4 3 7-9"/><path d="M15 6h5v5"/><path d="M4 4v16h16"/></svg>'),
        ("Insights & Report", "💡 INSIGHTS & REPORT", '<svg viewBox="0 0 24 24"><path d="M9 18h6M10 22h4"/><path d="M8.2 14.5A7 7 0 1 1 15.8 14.5C14.8 15.4 14 16.3 14 18h-4c0-1.7-.8-2.6-1.8-3.5Z"/></svg>'),
        ("History", "🗂️ HISTORY", '<svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/></svg>'),
    ]

    def clean_page_label(page: str) -> str:
        return clean_ui_label(page)

    rail_items = []
    for label, category_key, icon in category_targets:
        pages = NAV_CATEGORIES.get(category_key, [])
        children = [
            {
                "label": clean_page_label(page),
                "target": clean_page_label(page),
                "icon": SIDEBAR_PAGE_ICONS.get(page, "•"),
                "active": page == active_page,
            }
            for page in pages
        ]
        rail_items.append(
            {
                "label": label,
                "target": children[0]["target"] if children else label,
                "group": label,
                "icon": icon,
                "active": active_page in pages,
                "children": children,
            }
        )

    script_path = BASE_DIR / "frontend" / "static" / "js" / "script.js"
    if not script_path.exists():
        return
    script = script_path.read_text(encoding="utf-8")
    config = {
        "theme": "light" if is_light else "dark",
        "activePage": clean_page_label(active_page),
        "items": rail_items,
    }
    components.html(
        "<script>window.PF_RAIL_CONFIG=" + json.dumps(config, ensure_ascii=False) + ";</script><script>" + script + "</script>",
        height=0,
    )


# ══════════════════════════════════════════════════════
#  SIDEBAR — Categorised navigation
# ══════════════════════════════════════════════════════
def render_sidebar():
    inject_theme_css()
    is_light = "Light" in st.session_state.get("ui_theme","🌙 Dark Mode")

    with st.sidebar:
        st.markdown(f"""
        <style>
        section[data-testid="stSidebar"] {{
            background: {"linear-gradient(180deg, rgba(217,243,231,.98) 0%, rgba(226,246,237,.98) 45%, rgba(224,235,255,.97) 100%)" if is_light else "#150732"} !important;
            border-right: 1px solid {"rgba(18,148,107,.20)" if is_light else "rgba(139,92,246,.25)"} !important;
            transition: width .25s ease, min-width .25s ease, max-width .25s ease, transform .25s ease !important;
        }}
        [data-testid="stAppViewContainer"] .main .block-container {{
            max-width: 100% !important;
            padding-left: 1.2rem !important;
            padding-right: 1.2rem !important;
        }}
        section[data-testid="stSidebar"] > div:first-child {{ padding: 16px 14px !important; }}
        [data-testid="stSidebarCollapseButton"] {{ visibility:visible !important; }}

        .sb-brand {{
            display:flex; align-items:center; gap:10px;
            padding: 4px 4px 16px;
            border-bottom: 1px solid {"rgba(22,163,74,.12)" if is_light else "rgba(139,92,246,.18)"};
            margin-bottom: 12px;
        }}
        .sb-logo-box {{
            width:38px; height:38px; border-radius:11px; flex-shrink:0;
            background: {"linear-gradient(135deg,#16a34a,#14532d)" if is_light else "linear-gradient(135deg,#7c3aed,#4c1d95)"};
            display:flex; align-items:center; justify-content:center;
            font-size:18px; color:#fff; box-shadow:{"0 8px 20px rgba(18,148,107,.26)" if is_light else "0 4px 14px rgba(124,58,237,.4)"};
        }}
        .sb-brand-title {{ font-size:14px; font-weight:950; color:{"#0a2218" if is_light else "#fff"}; line-height:1.2; }}
        .sb-brand-sub {{ font-size:9px; font-family:'JetBrains Mono',monospace; color:{"#16a34a" if is_light else "#7c3aed"};
                         letter-spacing:2px; text-transform:uppercase; font-weight:800; }}
        .sb-user-name {{ margin-top:5px; display:inline-flex; gap:5px; align-items:center;
                         padding:4px 9px; border-radius:999px; font-size:10.5px; font-weight:900;
                         color:{"#14532d" if is_light else "#e9d5ff"};
                         background:{"rgba(22,163,74,.10)" if is_light else "rgba(124,58,237,.18)"}; }}

        section[data-testid="stSidebar"] [data-testid="stButton"] > button {{
            width:100% !important; text-align:left !important; justify-content:flex-start !important;
            border-radius:10px !important; border:none !important;
            background:transparent !important; box-shadow:none !important;
            color:{"#2d5a3d" if is_light else "rgba(224,217,255,.85)"} !important;
            font-size:13px !important; font-weight:700 !important;
            padding:9px 12px !important; min-height:38px !important;
            margin:1px 0 !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stButton"] > button:hover {{
            background:{"rgba(22,163,74,.07)" if is_light else "rgba(124,58,237,.15)"} !important;
            color:{"#0a2218" if is_light else "#fff"} !important; transform:none !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] {{
            background:{"linear-gradient(135deg,#16a34a,#14532d)" if is_light else "linear-gradient(135deg,#7c3aed,#4c1d95)"} !important;
            color:#fff !important; font-weight:900 !important;
            box-shadow:{"0 3px 10px rgba(22,163,74,.35)" if is_light else "0 3px 10px rgba(124,58,237,.35)"} !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"]:hover {{
            background:{"linear-gradient(135deg,#22c55e,#15803d)" if is_light else "linear-gradient(135deg,#8b4ff5,#5b21b6)"} !important; color:#fff !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="secondary"] {{
            border:1px solid {"rgba(22,163,74,.25)" if is_light else "rgba(139,92,246,.25)"} !important;
        }}

        .sb-group-header {{
            display:flex; align-items:center; gap:10px;
            padding:10px 12px; border-radius:10px; cursor:pointer;
            font-size:13px; font-weight:900; color:{"#0a2218" if is_light else "#fff"};
            margin-top:4px;
        }}
        .sb-group-header.open {{
            background:{"#e8f5ec" if is_light else "rgba(124,58,237,.12)"};
        }}
        .sb-group-icon {{
            width:30px; height:30px; border-radius:9px; flex-shrink:0;
            display:flex; align-items:center; justify-content:center; font-size:15px;
            background:{"#d1fae5" if is_light else "rgba(124,58,237,.18)"};
        }}
        .sb-group-chevron {{ margin-left:auto; font-size:11px; color:{"#6aad84" if is_light else "rgba(196,181,253,.5)"}; }}

        .sb-subitem-wrap {{
            margin-left:18px; border-left:1.5px solid {"#b7e4c7" if is_light else "rgba(139,92,246,.2)"};
            padding-left:10px; margin-bottom:4px;
        }}
        section[data-testid="stSidebar"] .sb-subitem-wrap [data-testid="stButton"] > button {{
            font-size:12.5px !important; font-weight:600 !important; padding:7px 10px !important; min-height:32px !important;
        }}

        section[data-testid="stSidebar"] [data-testid="stExpander"] {{
            border:none !important; background:transparent !important; box-shadow:none !important;
            margin-bottom:2px !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stExpander"] summary {{
            padding:10px 12px !important; border-radius:10px !important;
            font-size:13px !important; font-weight:900 !important;
            color:{"#0a2218" if is_light else "#fff"} !important;
            background:transparent !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {{
            background:{"#e8f5ec" if is_light else "rgba(124,58,237,.1)"} !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stExpander"] details[open] summary {{
            background:{"#e8f5ec" if is_light else "rgba(124,58,237,.12)"} !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stExpander"] > div > div {{
            border:none !important; padding:2px 0 4px 14px !important;
        }}

        .sb-divider {{ height:1px; background:{"rgba(22,163,74,.12)" if is_light else "rgba(139,92,246,.18)"}; margin:10px 4px; }}
        section[data-testid="stSidebar"] [data-testid="stToggle"] {{ margin:0 0 2px 0 !important; }}
        section[data-testid="stSidebar"] [data-testid="stToggle"] label {{ min-height:32px !important; }}
        section[data-testid="stSidebar"] [data-testid="stToggle"] div[role="switch"] {{ transform:scale(.88); transform-origin:left center; }}

        section[data-testid="stSidebar"] .sb-brand-title,
        section[data-testid="stSidebar"] .sb-brand-sub,
        section[data-testid="stSidebar"] .sb-user-name,
        section[data-testid="stSidebar"] [data-testid="stExpander"] summary {{
            color: {"#f7fff9" if is_light else "inherit"} !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stButton"] > button {{
            border: 1px solid {"rgba(255,255,255,.30)" if is_light else "rgba(139,92,246,.20)"} !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] {{
            background: {"rgba(255,255,255,.92)" if is_light else "linear-gradient(135deg,#7c3aed,#4c1d95)"} !important;
            color: {"#0b4f3a" if is_light else "#fff"} !important;
            box-shadow: {"0 12px 30px rgba(10,70,45,.22)" if is_light else "0 12px 30px rgba(124,58,237,.32)"} !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="secondary"] {{
            color: {"#eefcf4" if is_light else "rgba(224,217,255,.85)"} !important;
        }}

        .sb-dataset-card {{
            margin-top:8px; padding:12px 14px; border-radius:14px;
            background:{"#e8f5ec" if is_light else "rgba(124,58,237,.1)"};
            border:1px solid {"rgba(22,163,74,.15)" if is_light else "rgba(139,92,246,.22)"};
        }}
        .sb-dataset-label {{ font-size:9px; font-weight:900; letter-spacing:1.5px; text-transform:uppercase;
                              color:{"#16a34a" if is_light else "#7c3aed"}; margin-bottom:4px; }}
        .sb-dataset-name {{ font-size:12px; font-weight:900; color:{"#0a2218" if is_light else "#fff"};
                            word-break:break-word; line-height:1.3; }}
        .sb-dataset-meta {{ font-size:11px; color:{"#4a6b56" if is_light else "rgba(196,181,253,.6)"}; margin-top:4px; }}

        /* Compact mode is rendered by frontend/static/js/script.js only.
           The native Streamlit sidebar remains fully off-canvas when closed,
           preventing duplicated rails and allowing the dashboard to expand. */
        </style>
        """, unsafe_allow_html=True)

        if st.session_state.active_page not in ALL_PAGES:
            st.session_state.active_page = "🏠 Dashboard"
        active = st.session_state.active_page

        # ── TOP THEME SWITCH ──
        dark_now = not is_light
        top_cols = st.columns([1.2, 1.0], gap="small")
        with top_cols[0]:
            new_dark = st.toggle("Dark Mode", value=dark_now, key="theme_toggle_switch", label_visibility="collapsed")
        wanted_theme = "Dark Mode" if new_dark else "Light Mode"
        if wanted_theme != st.session_state.get("ui_theme"):
            st.session_state.ui_theme = wanted_theme
            st.rerun()
        st.markdown(
            '<div class="sb-theme-label" style="margin-top:-26px;margin-left:54px;font-size:10px;font-weight:950;'
            'letter-spacing:1.3px;text-transform:uppercase;color:var(--muted);line-height:1;">'
            + ("Dark Mode" if dark_now else "Light Mode") + '</div>'
            '<div style="height:14px"></div>',
            unsafe_allow_html=True
        )

        # ── BRAND + ACCOUNT ──
        display_name = get_display_name()
        st.markdown(
            '<div class="sb-brand">'
            '<div class="sb-logo-box">◈</div>'
            '<div><div class="sb-brand-title">Auto EDA Insight</div>'
            '<div class="sb-brand-sub">KELOMPOK 6</div>'
            '<div class="sb-user-name">' + display_name + '</div></div>'
            '</div>',
            unsafe_allow_html=True
        )

        # ── HOME — standalone top-level item ──
        for page in NAV_CATEGORIES.get("🏠 HOME", []):
            is_active = (page == active)
            if st.button(sidebar_page_label(page), key=f"nav_{page}", use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state.active_page = page
                st.session_state._scroll_to_main = True
                st.rerun()

        # ── GROUPED NAVIGATION via collapsible expanders ──
        for cat_name, pages in NAV_CATEGORIES.items():
            if cat_name == "🏠 HOME":
                continue
            clean_label = sidebar_category_label(cat_name)
            group_has_active = active in pages
            with st.expander(clean_label, expanded=group_has_active):
                for page in pages:
                    is_active = (page == active)
                    if st.button(sidebar_page_label(page), key=f"nav_{page}", use_container_width=True,
                                 type="primary" if is_active else "secondary"):
                        st.session_state.active_page = page
                        st.session_state._scroll_to_main = True
                        st.rerun()

        # ── DATASET STATUS ──
        df = st.session_state.df
        if df is not None:
            s = dataset_summary(df)
            score, qlabel = data_quality_score(df)
            fname = st.session_state.active_file.get("name","-") if st.session_state.active_file else "-"
            badge_clr = "#10b981" if score>=75 else "#f43f5e" if score<55 else "#f97316"
            st.markdown(
                '<div class="sb-dataset-card">'
                '<div class="sb-dataset-label">Active Dataset</div>'
                '<div class="sb-dataset-name">' + fname + '</div>'
                '<div class="sb-dataset-meta">' + fmt_int(s["rows"]) + ' baris · ' + str(s["cols"]) + ' kolom</div>'
                '<div style="margin-top:6px;display:inline-block;padding:3px 10px;border-radius:999px;'
                'font-size:10px;font-weight:900;background:' + badge_clr + '22;color:' + badge_clr + ';">'
                + qlabel + ' · ' + str(score) + '/100</div>'
                '</div>',
                unsafe_allow_html=True
            )

        st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

        # ── LOGOUT ──
        if st.button("Logout", key="sb_logout", use_container_width=True, on_click=logout):
            st.rerun()

    # The custom rail lives in the parent app so it remains visible after Streamlit
    # moves the native sidebar off-canvas.
    inject_compact_sidebar_rail()

# ══════════════════════════════════════════════════════
#  DATA CLEANING — Multi-choice table UI
# ══════════════════════════════════════════════════════
CLEANING_OPS = [
    {
        "id": "drop_dup",
        "name": "Hapus Baris Duplikat",
        "icon": "🔁",
        "category": "Deduplication",
        "description": "Menghapus baris yang identik secara keseluruhan. Cocok bila ada data entry ganda.",
        "impact": "High",
        "when": "Ada duplikat terdeteksi",
        "fn_key": "drop_duplicates",
        "needs_col": False,
        "needs_dtype": False,
    },
    {
        "id": "drop_missing",
        "name": "Hapus Baris Missing Values",
        "icon": "🗑️",
        "category": "Missing Value",
        "description": "Menghapus semua baris yang memiliki minimal satu nilai kosong (NaN). Pilih ini ATAU 'Isi Missing Value', tidak bisa keduanya.",
        "impact": "High",
        "when": "Missing value tidak bisa diisi / sudah banyak",
        "fn_key": "drop_missing_rows",
        "needs_col": False,
        "needs_dtype": False,
    },
    {
        "id": "fill_missing",
        "name": "Isi Missing Value",
        "icon": "✚",
        "category": "Missing Value",
        "description": "Mengisi semua nilai kosong di dataset sesuai metode yang kamu pilih (Mean/Median/Modus) — wajib pilih salah satu metode dulu. Pilih ini ATAU 'Hapus Baris Missing Values', tidak bisa keduanya.",
        "impact": "Medium",
        "when": "Ingin mengisi missing value tanpa menghapus baris/kolom",
        "fn_key": "fill_missing_value",
        "needs_col": False,
        "needs_dtype": False,
        "needs_method": True,
    },
    {
        "id": "drop_col",
        "name": "Hapus Kolom",
        "icon": "❌",
        "category": "Column Management",
        "description": "Menghapus kolom yang tidak relevan dari dataset.",
        "impact": "High",
        "when": "Kolom tidak diperlukan / terlalu banyak missing",
        "fn_key": "drop_column",
        "needs_col": True,
        "needs_dtype": False,
    },
    {
        "id": "convert_dtype",
        "name": "Ubah Tipe Data Kolom",
        "icon": "🔄",
        "category": "Type Conversion",
        "description": "Mengkonversi tipe data sebuah kolom ke tipe yang lebih sesuai.",
        "impact": "Medium",
        "when": "Tipe data terdeteksi salah saat import",
        "fn_key": "convert_dtype",
        "needs_col": True,
        "needs_dtype": True,
    },
]

FN_MAP = {
    "drop_duplicates": drop_duplicates,
    "drop_missing_rows": drop_missing_rows,
}

def render_cleaning_page(df):
    s = dataset_summary(df)
    st.markdown("## Data Cleaning")
    st.markdown(f"""
    <div class="eda-card eda-card-sm" style="margin-bottom:16px;">
        <div style="display:flex; gap:24px; flex-wrap:wrap; font-size:15px; font-weight:700;">
            <span>Dataset: <b>{s['rows']} baris × {s['cols']} kolom</b></span>
            <span style="color:var(--amber);">Missing: <b>{fmt_int(s['missing'])}</b></span>
            <span style="color:var(--red);">Duplikat: <b>{fmt_int(s['duplicate'])}</b></span>
        </div>
    </div>""", unsafe_allow_html=True)
    _tab_key = "cleaning_active_tab"
    if _tab_key not in st.session_state:
        st.session_state[_tab_key] = 0
    _tab_labels = ["Pilih & Jalankan Operasi", "Log & Before/After", "Reset"]
    _tab_btn_cols = st.columns(len(_tab_labels))
    for _ti, _tlabel in enumerate(_tab_labels):
        with _tab_btn_cols[_ti]:
            if st.button(_tlabel, key=f"cleaning_tabbtn_{_ti}", use_container_width=True,
                         type="primary" if st.session_state[_tab_key] == _ti else "secondary"):
                st.session_state[_tab_key] = _ti
                st.rerun()
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    _active_tab = st.session_state[_tab_key]

    if _active_tab == 0:
        st.markdown("### Pilih Operasi Cleaning")
        st.markdown('<div class="callout" style="margin-bottom:16px;">Centang satu atau beberapa operasi di bawah, atur parameter jika diperlukan, lalu klik <b>Jalankan Operasi Terpilih</b>.</div>', unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════
        # Select All
        # ══════════════════════════════════════════════════════
        _sa_key = "cleaning_select_all_state"
        if _sa_key not in st.session_state:
            st.session_state[_sa_key] = False
        _sa_cols = st.columns([1, 5], gap="small")
        with _sa_cols[0]:
            _new_sa = st.checkbox(
                "Select All",
                value=st.session_state[_sa_key],
                key="cleaning_select_all_cb",
                help="Centang untuk memilih SEMUA operasi cleaning sekaligus. Hilangkan centang untuk membatalkan semua pilihan.",
            )
        with _sa_cols[1]:
            if st.session_state[_sa_key]:
                st.markdown(
                    f'<div class="notice-success" style="margin:0;padding:9px 14px;">'
                    f'<b>{len(CLEANING_OPS)} operasi</b> dipilih (Select All aktif). '
                    f'Klik "Jalankan Operasi Terpilih" untuk melanjutkan.</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div class="notice-info" style="margin:0;padding:9px 14px;">'
                    'Pilih operasi secara individual atau aktifkan <b>Select All</b> untuk memilih semuanya.</div>',
                    unsafe_allow_html=True
                )
        if _new_sa != st.session_state[_sa_key]:
            st.session_state[_sa_key] = _new_sa
            for _op in CLEANING_OPS:
                st.session_state[f"op_{_op['id']}"] = _new_sa
            st.rerun()
        # ══════════════════════════════════════════════════════
        # [/TAMBAHAN]
        # ══════════════════════════════════════════════════════

        cats = {}
        for op in CLEANING_OPS:
            cats.setdefault(op["category"], []).append(op)

        with st.form("cleaning_ops_form", clear_on_submit=False):
            selected_ops = []
            col_extras = {}  # op_id → (col, dtype)

            for cat_name, ops in cats.items():
                st.markdown(f'<div class="section-chip">{cat_name}</div>', unsafe_allow_html=True)
                st.markdown("""
                <table class="clean-table">
                  <thead><tr>
                    <th style="width:40px;"></th>
                    <th>Operasi</th><th>Kategori</th><th>Dampak</th><th>Kapan digunakan?</th>
                  </tr></thead>
                </table>""", unsafe_allow_html=True)

                for op in ops:
                    impact_cls = "impact-high" if op["impact"]=="High" else "impact-medium" if op["impact"]=="Medium" else "impact-low"
                    col_cb, col_info = st.columns([0.42, 5.58])
                    with col_cb:
                        checked = st.checkbox("", key=f"op_{op['id']}", label_visibility="collapsed")
                    with col_info:
                        st.markdown(f"""
                        <table class="clean-table clean-row-table" style="margin-top:0;">
                          <tbody><tr>
                            <td style="width:40px;"></td>
                            <td><span class="op-badge">{op['name']}</span><br>
                                <span style="font-size:12px; color:var(--muted);">{op['description']}</span></td>
                            <td><span class="badge">{op['category']}</span></td>
                            <td class="{impact_cls}">{op['impact']}</td>
                            <td style="font-size:13px; color:var(--muted);">{op['when']}</td>
                          </tr></tbody>
                        </table>""", unsafe_allow_html=True)

                    if op["needs_col"] or op["needs_dtype"] or op.get("needs_method"):
                        with st.expander(f"Parameter untuk: {op['name']}", expanded=False):
                            extra_col = None; extra_dtype = None; extra_method = None
                            if op["needs_col"]:
                                col_options = ["— Pilih kolom —"] + list(df.columns)
                                extra_col_raw = st.selectbox(
                                    f"Pilih kolom ({op['name']})",
                                    col_options,
                                    index=0,
                                    key=f"col_{op['id']}",
                                )
                                extra_col = extra_col_raw if extra_col_raw != "— Pilih kolom —" else None
                            if op.get("needs_method"):
                                method_options = ["— Pilih metode —", "Mean", "Median", "Modus"]
                                extra_method_raw = st.selectbox(
                                    "Isi missing value dengan metode apa?",
                                    method_options,
                                    index=0,
                                    key=f"method_{op['id']}",
                                    help="Mean & Median diterapkan ke kolom numerik. Modus diterapkan ke semua kolom (numerik & kategorik) karena cocok untuk semua tipe data.",
                                )
                                extra_method = extra_method_raw if extra_method_raw != "— Pilih metode —" else None
                            if op["needs_dtype"]:
                                extra_dtype = st.selectbox("Target tipe data", ["float64","int64","str","datetime64[ns]"], key=f"dtype_{op['id']}")
                            col_extras[op["id"]] = (extra_col, extra_dtype, extra_method)
                    if checked:
                        selected_ops.append(op)
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            if selected_ops:
                st.markdown(f'<div class="callout"><b>{len(selected_ops)} operasi dipilih:</b> {", ".join([o["name"] for o in selected_ops])}</div>', unsafe_allow_html=True)
            run_clicked = st.form_submit_button("Jalankan Operasi Terpilih", type="primary", use_container_width=True)

        components.html("""
        <script>
        (function(){
          const doc = window.parent.document;
          function visible(el){
            const r = el.getBoundingClientRect();
            return r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < window.innerHeight;
          }
          function bindCleaningRows(){
            const tables = Array.from(doc.querySelectorAll('table.clean-row-table'));
            tables.forEach(function(tbl){
              if(tbl.dataset.cleanRowClickable === '1') return;
              tbl.dataset.cleanRowClickable = '1';
              tbl.setAttribute('title','Klik area box ini untuk memilih operasi');
              tbl.addEventListener('click', function(ev){
                if(ev.target.closest('input,button,select,textarea,label,a')) return;
                const rect = tbl.getBoundingClientRect();
                const mid = rect.top + rect.height/2;
                const boxes = Array.from(doc.querySelectorAll('input[type="checkbox"]')).filter(visible);
                let best = null;
                boxes.forEach(function(cb){
                  const r = cb.getBoundingClientRect();
                  const d = Math.abs((r.top + r.height/2) - mid);
                  if(!best || d < best.d) best = {cb: cb, d: d};
                });
                if(best && best.d < Math.max(150, rect.height/2 + 45)){
                  best.cb.click();
                }
              }, true);
            });
          }
          bindCleaningRows();
          setTimeout(bindCleaningRows, 400);
          setTimeout(bindCleaningRows, 1000);
        })();
        </script>
        """, height=0)

        status_box = st.empty()
        if st.session_state.get("cleaning_notice") and not run_clicked:
            status_box.markdown('<div class="status-card">' + st.session_state.cleaning_notice + '</div>', unsafe_allow_html=True)

        if run_clicked:
            if not selected_ops:
                st.toast("⚠️ Pilih minimal 1 operasi cleaning terlebih dahulu.", icon="⚠️")
                st.warning("Pilih minimal 1 operasi terlebih dahulu.")
            else:
                selected_ids = {o["id"] for o in selected_ops}
                if "drop_missing" in selected_ids and "fill_missing" in selected_ids:
                    conflict_msg = ("Untuk Missing Value, pilih salah satu saja: "
                                     "'Hapus Baris Missing Values' ATAU 'Isi Missing Value' — "
                                     "tidak bisa keduanya dicentang bersamaan karena saling bertentangan.")
                    st.toast(f"⚠️ {conflict_msg}", icon="⚠️")
                    st.warning(conflict_msg)
                    selected_ops = [o for o in selected_ops if o["id"] not in ("drop_missing", "fill_missing")]

            if not selected_ops:
                pass
            else:
                current_df = st.session_state.df.copy()
                all_msgs = []
                skipped_msgs = []
                st.session_state.cleaning_notice = ""
                progress = st.progress(0, text="Menyiapkan proses cleaning...")
                with st.spinner("Cleaning sedang diproses..."):
                    for i, op in enumerate(selected_ops, start=1):
                        status_box.markdown(f'<div class="notice-info">Menjalankan operasi {i}/{len(selected_ops)}: {op["name"]}</div>', unsafe_allow_html=True)
                        before_df_snap = current_df.copy()
                        extras = col_extras.get(op["id"], (None, None, None))
                        extra_col, extra_dtype, extra_method = extras
                        try:
                            time.sleep(0.08)
                            if op["fn_key"] in FN_MAP:
                                new_df, bef, aft, msg = FN_MAP[op["fn_key"]](current_df)
                            elif op["fn_key"] == "drop_column":
                                if not extra_col:
                                    skip_msg = f"Operasi '{op['name']}' dilewati — pilih dulu kolom yang ingin dihapus di bagian Parameter."
                                    st.toast(f"⚠️ {skip_msg}", icon="⚠️")
                                    skipped_msgs.append(skip_msg)
                                    continue
                                new_df, bef, aft, msg = drop_column(current_df, extra_col)
                            elif op["fn_key"] == "convert_dtype":
                                if not extra_col:
                                    skip_msg = f"Operasi '{op['name']}' dilewati — pilih dulu kolom yang ingin diubah tipe datanya di bagian Parameter."
                                    st.toast(f"⚠️ {skip_msg}", icon="⚠️")
                                    skipped_msgs.append(skip_msg)
                                    continue
                                if not extra_dtype:
                                    skip_msg = f"Operasi '{op['name']}' dilewati — pilih dulu target tipe data di bagian Parameter."
                                    st.toast(f"⚠️ {skip_msg}", icon="⚠️")
                                    skipped_msgs.append(skip_msg)
                                    continue
                                new_df, bef, aft, msg = convert_dtype(current_df, extra_col, extra_dtype)
                            elif op["fn_key"] == "fill_missing_value":
                                if not extra_method:
                                    skip_msg = f"Operasi '{op['name']}' dilewati — pilih dulu metode pengisian (Mean / Median / Modus) di bagian Parameter."
                                    st.toast(f"⚠️ {skip_msg}", icon="⚠️")
                                    skipped_msgs.append(skip_msg)
                                    continue
                                new_df, bef, aft, msg = fill_missing_by_method(current_df, extra_method)
                            else:
                                st.warning(f"Operasi '{op['name']}' membutuhkan parameter tambahan."); continue
                            current_df = new_df
                            st.session_state.before_snap = bef
                            st.session_state.after_snap = aft
                            st.session_state.before_df = before_df_snap
                            st.session_state.after_df = current_df.copy()
                            st.session_state.last_cleaning_operation = op["name"]
                            ts = datetime.datetime.now().strftime("%H:%M:%S")
                            st.session_state.cleaning_log.append(f"[{ts}] {msg}")
                            all_msgs.append(msg)
                            progress.progress(i / len(selected_ops), text=f"Selesai {i}/{len(selected_ops)} operasi")
                        except Exception as e:
                            err_msg = f"Error pada '{op['name']}': {e}"
                            st.toast(f"❌ {err_msg}", icon="❌")
                            st.error(err_msg)
                st.session_state.df = current_df
                if all_msgs:
                    st.session_state.cleaning_notice = "Proses cleaning selesai: " + " | ".join(all_msgs)
                    log_activity("Data Cleaning", " | ".join(all_msgs))
                    if skipped_msgs:
                        # ada operasi yang berhasil TAPI juga ada yang dilewati karena belum spesifik —
                        # jangan auto-pindah tab, biar user lihat dulu notif mana yang perlu dilengkapi
                        st.toast(f"⚠️ {len(all_msgs)} operasi berhasil, {len(skipped_msgs)} dilewati — lengkapi parameter yang kurang.", icon="⚠️")
                        st.warning("Beberapa operasi dilewati karena parameter belum spesifik:\n\n" + "\n\n".join(f"• {m}" for m in skipped_msgs))
                        st.success("Operasi yang berhasil dijalankan: " + " | ".join(all_msgs))
                    else:
                        st.toast(f"✅ Cleaning selesai! {len(all_msgs)} operasi berhasil dijalankan.", icon="✅")
                        # semua operasi terpilih spesifik & berhasil → baru auto-pindah ke tab Before/After
                        st.session_state[_tab_key] = 1
                        st.rerun()
                elif skipped_msgs:
                    st.toast("⚠️ Tidak ada operasi yang berhasil dijalankan — lengkapi parameter yang dilewati lalu coba lagi.", icon="⚠️")
                    st.warning("Operasi belum spesifik, dilewati semua:\n\n" + "\n\n".join(f"• {m}" for m in skipped_msgs))

    elif _active_tab == 1:
        if st.session_state.before_snap and st.session_state.after_snap:
            b, a = st.session_state.before_snap, st.session_state.after_snap
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Baris Before", fmt_int(b["shape"][0]))
            c2.metric("Baris After", fmt_int(a["shape"][0]), delta=fmt_int(a["shape"][0]-b["shape"][0]))
            c3.metric("Missing Before", fmt_int(b["missing_total"]))
            c4.metric("Missing After", fmt_int(a["missing_total"]), delta=fmt_int(a["missing_total"]-b["missing_total"]))
            if st.session_state.before_df is not None and st.session_state.after_df is not None:
                st.markdown('<div class="clean-title">Before Cleaning</div>', unsafe_allow_html=True)
                render_paginated_table(st.session_state.before_df, key="clean_before", page_size_default=10, height=360)
                st.markdown('<div class="clean-title">After Cleaning</div>', unsafe_allow_html=True)
                render_paginated_table(st.session_state.after_df, key="clean_after", page_size_default=10, height=360)
        else:
            st.info("Jalankan operasi cleaning untuk melihat perbandingan before/after.")

        if st.session_state.cleaning_log:
            st.markdown("### Log Operasi")
            for log_entry in reversed(st.session_state.cleaning_log):
                st.markdown(f'<div class="log-chip">• {log_entry}</div>', unsafe_allow_html=True)

    elif _active_tab == 2:
        if st.session_state.df_original is not None:
            if st.button("Reset ke Data Original", use_container_width=True):
                st.session_state.df = st.session_state.df_original.copy()
                st.session_state.cleaning_log = []
                st.session_state.before_snap = None; st.session_state.after_snap = None
                st.session_state.before_df = None; st.session_state.after_df = None
                st.session_state.last_cleaning_operation = ""
                st.session_state.cleaning_notice = ""
                # reset select-all state juga
                st.session_state["cleaning_select_all_state"] = False
                for _op in CLEANING_OPS:
                    st.session_state[f"op_{_op['id']}"] = False
                st.toast("✅ Data berhasil direset ke kondisi awal.", icon="✅")
                st.success("Data berhasil direset ke kondisi awal."); st.rerun()
        else:
            st.info("Tidak ada data original untuk direset.")


# ══════════════════════════════════════════════════════
#  INSIGHTS BUILDER
# ══════════════════════════════════════════════════════

def _normality_label(series):
    vals = pd.to_numeric(series, errors="coerce").dropna()
    if len(vals) < 8:
        return "Data belum cukup", np.nan
    try:
        sample = vals.sample(min(len(vals), 5000), random_state=42) if len(vals) > 5000 else vals
        stat, pval = scipy_stats.shapiro(sample)
        return ("Normal" if pval >= 0.05 else "Tidak normal"), float(pval)
    except Exception:
        try:
            stat, pval = scipy_stats.normaltest(vals) if len(vals) >= 20 else (np.nan, np.nan)
            return ("Normal" if pval >= 0.05 else "Tidak normal"), float(pval)
        except Exception:
            return "Tidak dapat diuji", np.nan


def _outlier_count(series):
    vals = pd.to_numeric(series, errors="coerce").dropna()
    if len(vals) < 4:
        return 0
    q1, q3 = vals.quantile(0.25), vals.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0 or pd.isna(iqr):
        return 0
    return int(((vals < q1 - 1.5 * iqr) | (vals > q3 + 1.5 * iqr)).sum())


def build_initial_intelligent_insights(df):
    """Generate full intelligent insights required by the final-exam PDF."""
    if df is None or df.empty:
        return ["Upload dataset untuk melihat initial intelligent insights."]
    insights = []
    rows, cols = df.shape
    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    missing_total = int(df.isna().sum().sum())
    dup_total = int(df.duplicated().sum())
    total_cells = max(rows * cols, 1)

    insights.append(f"Dataset memiliki {fmt_int(rows)} baris dan {fmt_int(cols)} kolom ({len(num_cols)} numerik, {len(cat_cols)} kategorik).")

    if num_cols:
        means = df[num_cols].apply(pd.to_numeric, errors="coerce").mean(numeric_only=True).dropna()
        if not means.empty:
            top_mean = means.idxmax()
            insights.append(f"Variabel dengan rata-rata tertinggi adalah {top_mean} ({means.loc[top_mean]:,.2f}).")

    miss_by_col = df.isna().sum().sort_values(ascending=False)
    if missing_total:
        top_missing = miss_by_col[miss_by_col > 0].head(3)
        detail = ", ".join([f"{i} ({fmt_int(v)})" for i, v in top_missing.items()])
        insights.append(f"Variabel dengan missing value terbanyak: {detail}. Total missing {fmt_int(missing_total)} sel ({missing_total / total_cells * 100:.1f}%).")
    else:
        insights.append("Tidak ditemukan missing value; dataset siap untuk analisis lanjutan.")

    if num_cols:
        outlier_counts = {col: _outlier_count(df[col]) for col in num_cols}
        if outlier_counts:
            top_out = max(outlier_counts, key=outlier_counts.get)
            insights.append(f"Variabel dengan jumlah outlier tertinggi adalah {top_out} ({fmt_int(outlier_counts[top_out])} data).")

        stds = df[num_cols].apply(pd.to_numeric, errors="coerce").std(numeric_only=True).dropna()
        if not stds.empty:
            top_std = stds.idxmax()
            insights.append(f"Variabel dengan standar deviasi terbesar adalah {top_std} ({stds.loc[top_std]:,.4f}).")

        if len(num_cols) >= 2:
            corr = df[num_cols].apply(pd.to_numeric, errors="coerce").corr(numeric_only=True).abs().copy()
            upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
            stacked = upper.stack().dropna().sort_values(ascending=False)
            if not stacked.empty:
                (a, b), val = stacked.index[0], stacked.iloc[0]
                insights.append(f"Korelasi terkuat antar variabel numerik: {a} dengan {b} (r = {val:.3f}).")

        normal_labels = []
        nonnormal_labels = []
        for col in num_cols[:12]:
            label, pval = _normality_label(df[col])
            if label == "Normal":
                normal_labels.append(col)
            elif label == "Tidak normal":
                nonnormal_labels.append(col)
        if normal_labels or nonnormal_labels:
            insights.append(
                "Distribusi normal: " + (", ".join(normal_labels[:4]) if normal_labels else "tidak ada yang kuat") +
                "; distribusi tidak normal: " + (", ".join(nonnormal_labels[:4]) if nonnormal_labels else "tidak ada yang kuat") + "."
            )
    else:
        insights.append("Dataset belum memiliki kolom numerik untuk rata-rata, outlier, standar deviasi, korelasi, dan normality test.")

    if dup_total:
        insights.append(f"Terdapat {fmt_int(dup_total)} baris duplikat. Disarankan menjalankan Data Cleaning sebelum analisis final.")
    else:
        insights.append("Tidak ada baris duplikat terdeteksi.")

    if cat_cols:
        top_cat = cat_cols[0]
        mode = df[top_cat].mode(dropna=True)
        if not mode.empty:
            insights.append(f"Kategori dominan pada {top_cat}: {mode.iloc[0]}.")

    ts_result = build_time_series_analysis(df, period_label="Bulanan", agg_label="Sum", window=7)
    if ts_result.get("ok"):
        insights.extend(ts_result.get("pattern_summary", []))
    else:
        insights.append("Time Series tidak diaktifkan karena dataset tidak memiliki kolom tanggal/datetime yang valid.")

    return insights[:14]


# ══════════════════════════════════════════════════════
#  REPORT GENERATOR — complete dashboard/web activity export
# ══════════════════════════════════════════════════════
def _safe_html(value):
    value = str(value)
    return (value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                 .replace('"', '&quot;').replace("'", '&#39;'))


def _safe_df(data):
    try:
        if data is None:
            return pd.DataFrame()
        return pd.DataFrame(data).copy()
    except Exception:
        return pd.DataFrame()


def _table_html(title, df, max_rows=40, description=""):
    df = _safe_df(df)
    if df.empty:
        return f"<section class='report-section'><h2>{_safe_html(title)}</h2><p class='muted'>Tidak ada data untuk bagian ini.</p></section>"
    show = df.head(max_rows).copy()
    try:
        html = '<div class="report-table-wrap">' + show.to_html(index=False, classes="report-table", border=0, escape=False) + '</div>'
    except Exception:
        html = '<div class="report-table-wrap">' + show.astype(str).to_html(index=False, classes="report-table", border=0, escape=True) + '</div>'
    extra = f"<p class='muted'>{_safe_html(description)}</p>" if description else ""
    note = "" if len(df) <= max_rows else f"<p class='muted'>Menampilkan {max_rows} baris pertama dari {fmt_int(len(df))} baris.</p>"
    return f"<section class='report-section'><h2>{_safe_html(title)}</h2>{extra}{html}{note}</section>"


def build_dataset_info_df(df):
    if df is None or df.empty:
        return pd.DataFrame()
    rows = []
    for col in df.columns:
        ser = df[col]
        non_null = int(ser.notna().sum())
        null_count = int(ser.isna().sum())
        sample = ser.dropna().iloc[0] if non_null else ""
        rows.append({
            "Column": col,
            "Data Type": str(ser.dtype),
            "Non-Null": non_null,
            "Null": null_count,
            "Null %": round(null_count / max(len(df), 1) * 100, 2),
            "Unique": int(ser.nunique(dropna=True)),
            "Sample": str(sample)[:120],
        })
    return pd.DataFrame(rows)


def build_missing_summary_df(df):
    if df is None or df.empty:
        return pd.DataFrame()
    miss = df.isna().sum().reset_index()
    miss.columns = ["Column", "Missing Count"]
    miss["Missing %"] = (miss["Missing Count"] / max(len(df), 1) * 100).round(2)
    miss = miss.sort_values(["Missing Count", "Column"], ascending=[False, True])
    return miss


def build_upload_history_df():
    rows = []
    for h in st.session_state.get("history", []):
        rows.append({
            "Time": h.get("time", ""),
            "File": h.get("name", ""),
            "Rows": h.get("rows", ""),
            "Columns": h.get("cols", ""),
        })
    return pd.DataFrame(rows)


def build_before_after_summary_df():
    b = st.session_state.get("before_snap")
    a = st.session_state.get("after_snap")
    if not b or not a:
        return pd.DataFrame()
    return pd.DataFrame([
        {"Metric": "Jumlah Baris", "Before": b.get("shape", [0, 0])[0], "After": a.get("shape", [0, 0])[0], "Change": a.get("shape", [0, 0])[0] - b.get("shape", [0, 0])[0]},
        {"Metric": "Jumlah Kolom", "Before": b.get("shape", [0, 0])[1], "After": a.get("shape", [0, 0])[1], "Change": a.get("shape", [0, 0])[1] - b.get("shape", [0, 0])[1]},
        {"Metric": "Missing Values", "Before": b.get("missing_total", 0), "After": a.get("missing_total", 0), "Change": a.get("missing_total", 0) - b.get("missing_total", 0)},
        {"Metric": "Duplikat", "Before": b.get("duplicates", 0), "After": a.get("duplicates", 0), "Change": a.get("duplicates", 0) - b.get("duplicates", 0)},
    ])



def compute_time_series_report(df):
    result = build_time_series_analysis(df, period_label="Bulanan", agg_label="Sum", window=7)
    if not result.get("ok"):
        return None, result.get("message", "Time series tidak tersedia."), None
    grouped = result["data"].copy()
    note = result.get("note", "") + " " + " ".join(result.get("pattern_summary", []))
    return grouped, note, (result.get("date_col"), result.get("value_note"))


def _fig_to_html(fig, title=""):
    try:
        plot_html = fig.to_html(
            full_html=False,
            include_plotlyjs="cdn",
            config={
                "displayModeBar": False,
                "responsive": True,
                "scrollZoom": False,
            },
        )
        return "<div class='chart-title'>" + _safe_html(title) + "</div>" + plot_html
    except Exception as e:
        return f"<div class='chart-error'>Chart gagal dibuat: {_safe_html(e)}</div>"


def _report_insight_html(text):
    """Convert a short markdown-like chart insight into safe HTML."""
    safe = _safe_html(str(text or "")).replace("\n", "<br>")
    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
    return safe


def _chart_report_block(fig, title, insight):
    return (
        "<div class='report-chart-block'>"
        + _fig_to_html(fig, title)
        + "<div class='report-insight chart-conclusion'>"
        + "<span class='conclusion-label'>Insight</span>"
        + _report_insight_html(insight)
        + "</div></div>"
    )



# ══════════════════════════════════════════════════════
# [TAMBAHAN] Auto-insight per section visualisasi di report
# Fungsi ini dipanggil di dalam build_visual_report_sections()
# untuk menghasilkan insight singkat yang ditampilkan di atas
# setiap chart section pada HTML report.
# ══════════════════════════════════════════════════════
def _section_insight(df, section_key):
    """Generate a short auto insight string for each visualization section in the HTML report."""
    try:
        num_cols = df.select_dtypes(include="number").columns.tolist() if df is not None else []
        cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist() if df is not None else []

        if section_key == "numerical" and num_cols:
            col = num_cols[0]
            vals = pd.to_numeric(df[col], errors="coerce").dropna()
            if vals.empty:
                return ""
            skew = float(vals.skew())
            out_count = _outlier_count(df[col])
            norm_label, pval = _normality_label(df[col])
            skew_desc = (
                "kanan / positif (ekor kanan panjang)" if skew > 0.5
                else "kiri / negatif (ekor kiri panjang)" if skew < -0.5
                else "relatif simetris"
            )
            pval_str = f" (p={pval:.4f})" if pval == pval else ""
            return (
                f"<b>Insight Numerical:</b> Kolom utama <b>{col}</b> — "
                f"rata-rata <b>{vals.mean():,.2f}</b>, median <b>{vals.median():,.2f}</b>, "
                f"standar deviasi <b>{vals.std():,.2f}</b>. "
                f"Distribusi cenderung <b>{skew_desc}</b> (skewness={skew:.2f}). "
                f"Uji normalitas: <b>{norm_label}</b>{pval_str}. "
                f"Terdeteksi <b>{out_count:,}</b> outlier (metode IQR)."
            )

        elif section_key == "categorical" and cat_cols:
            col = cat_cols[0]
            vc = df[col].astype(str).value_counts()
            if vc.empty:
                return ""
            top_val = vc.index[0]
            top_cnt = int(vc.iloc[0])
            total = int(vc.sum())
            pct = top_cnt / max(total, 1) * 100
            unique_n = int(df[col].nunique(dropna=True))
            cv = vc.std() / max(vc.mean(), 1e-9)
            merata = "Distribusi antar kategori cukup merata." if cv < 0.5 else "Distribusi tidak merata — satu atau beberapa kategori mendominasi."
            return (
                f"<b>Insight Categorical:</b> Kolom <b>{col}</b> memiliki <b>{unique_n}</b> kategori unik. "
                f"Kategori terbanyak: <b>'{top_val}'</b> dengan <b>{top_cnt:,}</b> kemunculan "
                f"({pct:.1f}% dari total). {merata}"
            )

        elif section_key == "bivariate" and len(num_cols) >= 2:
            x, y = num_cols[0], num_cols[1]
            xy = df[[x, y]].apply(pd.to_numeric, errors="coerce").dropna()
            if len(xy) < 3:
                return ""
            corr = float(xy[x].corr(xy[y]))
            abs_corr = abs(corr)
            corr_label = (
                "sangat kuat" if abs_corr >= 0.8
                else "kuat" if abs_corr >= 0.6
                else "sedang" if abs_corr >= 0.4
                else "lemah" if abs_corr >= 0.2
                else "sangat lemah"
            )
            direction = "positif" if corr > 0 else "negatif"
            # cari pasangan korelasi tertinggi di seluruh numerik
            all_corr = df[num_cols].apply(pd.to_numeric, errors="coerce").corr(numeric_only=True).abs()
            upper = all_corr.where(np.triu(np.ones(all_corr.shape), k=1).astype(bool))
            stacked = upper.stack().dropna().sort_values(ascending=False)
            max_pair_txt = ""
            if not stacked.empty:
                (a, b_col), val = stacked.index[0], stacked.iloc[0]
                max_pair_txt = f" Pasangan korelasi tertinggi di dataset: <b>{a}</b> vs <b>{b_col}</b> (r={val:.3f})."
            return (
                f"<b>Insight Bivariate:</b> Korelasi <b>{x}</b> ↔ <b>{y}</b>: "
                f"<b>r={corr:.3f}</b> — hubungan <b>{corr_label} {direction}</b>.{max_pair_txt}"
            )

        elif section_key == "cat_num" and cat_cols and num_cols:
            cat, num = cat_cols[0], num_cols[0]
            top_cats = df[cat].astype(str).value_counts().head(8).index.tolist()
            data = df[df[cat].astype(str).isin(top_cats)][[cat, num]].copy()
            data[num] = pd.to_numeric(data[num], errors="coerce")
            data = data.dropna(subset=[cat, num])
            if data.empty:
                return ""
            group_means = data.groupby(cat)[num].mean().sort_values(ascending=False)
            top_g = group_means.index[0]
            top_v = float(group_means.iloc[0])
            low_g = group_means.index[-1]
            low_v = float(group_means.iloc[-1])
            selisih = top_v - low_v
            return (
                f"<b>Insight Kategorik vs Numerik:</b> Rata-rata <b>{num}</b> tertinggi "
                f"di kategori <b>'{top_g}'</b> ({top_v:,.2f}), terendah di "
                f"<b>'{low_g}'</b> ({low_v:,.2f}). "
                f"Selisih antar kategori: <b>{selisih:,.2f}</b>."
            )

        elif section_key == "timeseries":
            ts_result = build_time_series_analysis(df, period_label="Bulanan", agg_label="Sum", window=7)
            if not ts_result.get("ok"):
                return ""
            parts = ts_result.get("pattern_summary", [])
            return "<b>Insight Time Series:</b> " + " ".join(parts[:3]) if parts else ""

    except Exception:
        pass
    return ""
# ══════════════════════════════════════════════════════
# [/TAMBAHAN]
# ══════════════════════════════════════════════════════



def build_visual_report_sections(df, theme_mode="dark"):
    """Build HTML-report visualizations with one insight below every chart."""
    sections = []
    if df is None or df.empty:
        return sections

    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    if num_cols:
        col = num_cols[0]
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        chart_specs = [
            ("Histogram", lambda: plot_histogram(df, col, theme=theme_mode), insight_histogram(vals, col)),
            ("Box Plot", lambda: plot_boxplot(df, col, theme=theme_mode), insight_boxplot(vals, col)),
            ("Density Plot", lambda: plot_density(df, col, theme=theme_mode), insight_density(vals, col)),
            ("QQ Plot", lambda: plot_qq(df, col, theme=theme_mode), insight_qq(vals, col)),
            ("Violin Plot", lambda: plot_violin(df, col, theme=theme_mode), insight_violin(vals, col)),
        ]
        html_parts = []
        for title, fn, insight in chart_specs:
            try:
                html_parts.append(_chart_report_block(fn(), f"{title} — {col}", insight))
            except Exception as e:
                html_parts.append(
                    f"<div class='report-chart-block'><div class='chart-error'>{_safe_html(title)} gagal: {_safe_html(e)}</div></div>"
                )
        sections.append((
            "Numerical Visualization",
            f"Kolom numerik utama: {col}. Setiap visualisasi memiliki insight dan kesimpulan tersendiri.",
            "".join(html_parts),
        ))

    if cat_cols:
        col = cat_cols[0]
        vc = df[col].astype(str).fillna("Missing").value_counts().head(12)
        chart_specs = [
            ("Bar Chart", lambda: plot_bar(df, col, theme=theme_mode), insight_bar_count(vc, col)),
            ("Count Plot", lambda: plot_count(df, col, theme=theme_mode), insight_bar_count(vc, col)),
            ("Pie Chart", lambda: plot_pie(df, col, theme=theme_mode), insight_pie(vc, col)),
            ("Pareto Chart", lambda: plot_pareto(df, col, theme=theme_mode), insight_pareto(vc, col)),
        ]
        html_parts = []
        for title, fn, insight in chart_specs:
            try:
                html_parts.append(_chart_report_block(fn(), f"{title} — {col}", insight))
            except Exception as e:
                html_parts.append(
                    f"<div class='report-chart-block'><div class='chart-error'>{_safe_html(title)} gagal: {_safe_html(e)}</div></div>"
                )
        sections.append((
            "Categorical Visualization",
            f"Kolom kategorik utama: {col}. Setiap chart dilengkapi interpretasi otomatis.",
            "".join(html_parts),
        ))

    if len(num_cols) >= 2:
        x, y = num_cols[0], num_cols[1]
        size_col = num_cols[2] if len(num_cols) >= 3 else None
        color_col = cat_cols[0] if cat_cols else None
        chart_specs = [
            ("Correlation Heatmap", lambda: plot_correlation_heatmap(df, theme=theme_mode), insight_corr_heatmap(df, num_cols)),
            ("Pair Plot", lambda: plot_pair_matrix(df, cols=num_cols[:5], theme=theme_mode), insight_pair_plot(df, num_cols[:5])),
            ("Scatter Plot", lambda: plot_scatter(df, x, y, theme=theme_mode), insight_scatter(df, x, y)),
            ("Regression Plot", lambda: plot_regression(df, x, y, theme=theme_mode), insight_regression(df, x, y)),
            ("Bubble Chart", lambda: plot_bubble(df, x, y, size_col=size_col, color_col=color_col, theme=theme_mode), insight_bubble(df, x, y, size_col)),
        ]
        html_parts = []
        for title, fn, insight in chart_specs:
            try:
                html_parts.append(_chart_report_block(fn(), f"{title} — {x} vs {y}", insight))
            except Exception as e:
                html_parts.append(
                    f"<div class='report-chart-block'><div class='chart-error'>{_safe_html(title)} gagal: {_safe_html(e)}</div></div>"
                )
        sections.append((
            "Bivariate & Multivariate Analysis",
            f"Hubungan utama dianalisis menggunakan {x} dan {y}; heatmap dan pair plot memakai beberapa kolom numerik.",
            "".join(html_parts),
        ))

    if cat_cols and num_cols:
        cat, num = cat_cols[0], num_cols[0]
        common_insight = insight_cat_num(df, cat, num)
        chart_specs = [
            ("Boxplot by Category", lambda: plot_boxplot_by_cat(df, cat, num, theme=theme_mode)),
            ("Violin Plot by Category", lambda: plot_violin_by_cat(df, cat, num, theme=theme_mode)),
            ("Grouped Bar Chart", lambda: plot_grouped_bar(df, cat, num, theme=theme_mode)),
            ("Strip Plot", lambda: plot_strip_by_cat(df, cat, num, theme=theme_mode)),
        ]
        html_parts = []
        for title, fn in chart_specs:
            try:
                chart_insight = f"{common_insight} Visualisasi {title} memperlihatkan perbandingan {num} pada setiap kelompok {cat}."
                html_parts.append(_chart_report_block(fn(), f"{title} — {num} by {cat}", chart_insight))
            except Exception as e:
                html_parts.append(
                    f"<div class='report-chart-block'><div class='chart-error'>{_safe_html(title)} gagal: {_safe_html(e)}</div></div>"
                )
        sections.append((
            "Categorical vs Numerical Analysis",
            f"Perbandingan nilai {num} berdasarkan kategori {cat}.",
            "".join(html_parts),
        ))

    ts_result = build_time_series_analysis(
        df, period_label="Bulanan", agg_label="Sum", window=7
    )
    if ts_result.get("ok"):
        ts_actual = ts_result["data"]
        ts_note = ts_result.get("note", "") + " " + " ".join(
            ts_result.get("pattern_summary", [])
        )
        try:
            fig = plot_time_series(
                ts_actual,
                "Periode",
                "Nilai",
                window=7,
                theme=theme_mode,
                ma_col="Moving Average",
                rolling_col="Rolling Mean",
                trend_col="Trend Line",
                title="Time Series Auto-Detection, Trend Line, Moving Average & Rolling Mean",
            )
            ts_insight = " ".join(ts_result.get("pattern_summary", [])) or ts_note
            ts_html = _chart_report_block(
                fig, "Time Series Auto-Detection", ts_insight
            )
            ts_html += ts_actual.head(60).to_html(
                index=False, classes="report-table", border=0
            )
        except Exception as e:
            ts_html = (
                f"<div class='chart-error'>Time series chart gagal: {_safe_html(e)}</div>"
                + ts_actual.head(50).to_html(index=False, classes="report-table", border=0)
            )
        sections.append(("Time Series Analytics", ts_note, ts_html))
    else:
        ts_note = ts_result.get(
            "message", "Dataset ini tidak memiliki kolom time series yang valid."
        )
        sections.append((
            "Time Series Analytics",
            ts_note,
            "<p class='muted'>Time series tidak dibuat karena dataset tidak memiliki kolom waktu yang valid.</p>",
        ))
    return sections



def list_visual_report_sections(df):
    """Lightweight visual index for Excel/PDF export cache."""
    sections = []
    if df is None or df.empty:
        return sections
    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    if num_cols:
        sections.append(("Numerical Visualization", "Histogram, Box Plot, Density Plot, QQ Plot, dan Violin Plot.", ""))
    if cat_cols:
        sections.append(("Categorical Visualization", "Bar Chart, Count Plot, Pie Chart, dan Pareto Chart.", ""))
    if len(num_cols) >= 2:
        sections.append(("Bivariate & Multivariate Analysis", "Scatter Plot, Correlation Heatmap, Pair Plot, Regression Plot, dan Bubble Chart.", ""))
    if cat_cols and num_cols:
        sections.append(("Categorical vs Numerical Analysis", "Boxplot by Category, Violin Plot by Category, Grouped Bar Chart, dan Strip Plot.", ""))
    try:
        ts_df, ts_note, _ = compute_time_series_report(df)
        if ts_df is not None and not ts_df.empty:
            sections.append(("Time Series Analytics", ts_note or "Time Series Line Chart, Moving Average, Rolling Mean, dan Trend Line.", ""))
        else:
            sections.append(("Time Series Analytics", "Dataset tidak memiliki kolom tanggal/datetime valid.", ""))
    except Exception:
        sections.append(("Time Series Analytics", "Dataset tidak memiliki kolom tanggal/datetime valid.", ""))
    return sections


def build_complete_report_bundle(df, theme_mode="light", include_visual_sections=True):
    s = dataset_summary(df)
    score, qlabel = data_quality_score(df)
    insights = [strip_decorative_emoji(i) for i in build_initial_intelligent_insights(df)]
    cleaning_log = st.session_state.get("cleaning_log", [])
    meta = st.session_state.get("active_file") or {}
    activity = activity_log_df()
    upload_hist = build_upload_history_df()
    dataset_info = build_dataset_info_df(df)
    missing_summary = build_missing_summary_df(df)
    before_after = build_before_after_summary_df()
    ts_df, ts_note, ts_meta = compute_time_series_report(df)
    try:
        ns = numeric_stats(df)
    except Exception:
        ns = pd.DataFrame()
    try:
        cs = categorical_stats(df)
    except Exception:
        cs = pd.DataFrame()
    visual_sections = build_visual_report_sections(df, theme_mode) if include_visual_sections else list_visual_report_sections(df)
    return {
        "summary": s,
        "quality_score": score,
        "quality_label": qlabel,
        "insights": insights,
        "cleaning_log": cleaning_log,
        "meta": meta,
        "activity": activity,
        "upload_history": upload_hist,
        "dataset_info": dataset_info,
        "missing_summary": missing_summary,
        "before_after": before_after,
        "time_series": ts_df if ts_df is not None else pd.DataFrame(),
        "time_series_note": ts_note,
        "numeric_stats": ns,
        "categorical_stats": cs,
        "visual_sections": visual_sections,
    }


def generate_html_report(df, insights=None, cleaning_log=None, meta=None, theme_mode="light"):
    bundle = build_complete_report_bundle(df, theme_mode=theme_mode)
    s = bundle["summary"]
    meta = bundle["meta"]
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    insight_cards = "".join([f"<div class='insight-card'><b>{i+1:02d}</b><span>{_safe_html(txt)}</span></div>" for i, txt in enumerate(bundle["insights"])])
    log_df = pd.DataFrame({"Cleaning Log": bundle["cleaning_log"]}) if bundle["cleaning_log"] else pd.DataFrame()
    visual_html = "".join([
        f"<section class='report-section'><h2>{_safe_html(title)}</h2><p class='muted'>{_safe_html(desc)}</p><div class='chart-grid'>{html}</div></section>"
        for title, desc, html in bundle["visual_sections"]
    ])
    return f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Auto EDA Insight — Complete Report</title>
<style>
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:Inter, Arial, sans-serif; background:{'#f0f7f4' if theme_mode == 'light' else '#16082f'}; color:{'#10231a' if theme_mode == 'light' else '#f8f7ff'}; }}
.report-wrap {{ max-width:1180px; margin:0 auto; padding:28px; }}
.hero {{ border-radius:28px; padding:28px; background:{'linear-gradient(135deg,#d8f7e6,#ffffff,#dceaff)' if theme_mode == 'light' else 'linear-gradient(135deg,#2e1065,#1e0a4a,#16082f)'}; border:1px solid {'#bde8d1' if theme_mode == 'light' else 'rgba(139,92,246,.38)'}; box-shadow:0 18px 52px {'rgba(31,111,83,.14)' if theme_mode == 'light' else 'rgba(0,0,0,.38)'}; }}
.hero h1 {{ margin:0; font-size:34px; color:{'#10231a' if theme_mode == 'light' else '#ffffff'}; }} .hero p,.muted {{ color:{'#527266' if theme_mode == 'light' else '#b8a6e8'}; line-height:1.65; }}
.kpi-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-top:20px; }}
.kpi {{ border-radius:20px; padding:18px; background:{'rgba(255,255,255,.74)' if theme_mode == 'light' else 'rgba(255,255,255,.055)'}; border:1px solid {'#ccebd9' if theme_mode == 'light' else 'rgba(139,92,246,.28)'}; }}
.kpi .lbl {{ font-size:11px; font-weight:900; letter-spacing:1.1px; text-transform:uppercase; color:{'#5b756a' if theme_mode == 'light' else '#a998d7'}; }} .kpi .val {{ font-size:28px; font-weight:950; margin-top:8px; color:{'#10231a' if theme_mode == 'light' else '#ffffff'}; }}
.report-section {{ margin-top:22px; border-radius:24px; padding:22px; background:{'rgba(255,255,255,.86)' if theme_mode == 'light' else 'rgba(24,10,55,.90)'}; border:1px solid {'#ccebd9' if theme_mode == 'light' else 'rgba(139,92,246,.28)'}; box-shadow:0 12px 36px {'rgba(31,111,83,.10)' if theme_mode == 'light' else 'rgba(0,0,0,.32)'}; overflow:hidden; }}
.report-section h2 {{ margin:0 0 10px; font-size:24px; color:{'#10231a' if theme_mode == 'light' else '#ffffff'}; }}
.report-table-wrap {{ width:100%; overflow-x:auto; border-radius:14px; }}
.report-table {{ border-collapse:collapse; width:100%; min-width:max-content; font-size:13px; margin-top:10px; }} .report-table th {{ background:{'#dff6eb' if theme_mode == 'light' else '#2d1760'}; color:{'#0f5132' if theme_mode == 'light' else '#ffffff'}; text-align:left; font-weight:900; }} .report-table td,.report-table th {{ border:1px solid {'#ccebd9' if theme_mode == 'light' else 'rgba(139,92,246,.24)'}; padding:8px 10px; vertical-align:top; color:{'#10231a' if theme_mode == 'light' else '#f3edff'}; }}
.insight-grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:12px; }} .insight-card {{ border-radius:18px; padding:14px; background:{'#f4fbf7' if theme_mode == 'light' else '#21104a'}; border:1px solid {'#d2eddf' if theme_mode == 'light' else 'rgba(139,92,246,.30)'}; display:flex; gap:10px; line-height:1.6; }} .insight-card b {{ color:{'#12946b' if theme_mode == 'light' else '#22d3ee'}; }}
.report-insight {{ border-radius:14px; padding:13px 16px; margin:10px 0 16px;
    background:{'rgba(22,163,74,.09)' if theme_mode == 'light' else 'rgba(124,58,237,.14)'};
    border-left:4px solid {'#16a34a' if theme_mode == 'light' else '#7c3aed'};
    border-top:1px solid {'rgba(20,121,86,.18)' if theme_mode == 'light' else 'rgba(139,92,246,.28)'};
    border-right:1px solid {'rgba(20,121,86,.18)' if theme_mode == 'light' else 'rgba(139,92,246,.28)'};
    border-bottom:1px solid {'rgba(20,121,86,.18)' if theme_mode == 'light' else 'rgba(139,92,246,.28)'};
    color:{'#0b3d22' if theme_mode == 'light' else '#e9e0ff'};
    font-size:13.5px; font-weight:760; line-height:1.7; }}
.chart-title {{ font-weight:950; font-size:18px; margin:18px 0 8px; color:{'#17382a' if theme_mode == 'light' else '#ffffff'}; }} .chart-error {{ padding:12px; border-radius:14px; background:{'#fee2e2' if theme_mode == 'light' else '#451a2c'}; color:{'#991b1b' if theme_mode == 'light' else '#fecdd3'}; margin:10px 0; }}
.chart-grid {{ display:grid; grid-template-columns:1fr; gap:18px; }}
.report-chart-block {{ margin:16px 0 24px; padding:18px; border-radius:22px; background:{'rgba(245,252,248,.95)' if theme_mode == 'light' else 'rgba(255,255,255,.035)'}; border:1px solid {'#ccebd9' if theme_mode == 'light' else 'rgba(139,92,246,.24)'}; overflow:hidden; }}
.report-chart-block .plotly-graph-div {{ min-height:430px; }}
.chart-conclusion {{ margin-top:14px !important; margin-bottom:0 !important; }}
.conclusion-label {{ display:inline-block; margin-right:8px; padding:3px 9px; border-radius:999px; font-size:10px; letter-spacing:.8px; text-transform:uppercase; font-weight:950; background:{'rgba(14,159,154,.14)' if theme_mode == 'light' else 'rgba(34,211,238,.16)'}; color:{'#0f766e' if theme_mode == 'light' else '#67e8f9'}; }}
.footer {{ margin-top:26px; color:{'#527266' if theme_mode == 'light' else '#b8a6e8'}; font-size:12px; }}
@media(max-width:900px){{ .kpi-grid,.insight-grid{{grid-template-columns:1fr 1fr}} }} @media(max-width:640px){{ .kpi-grid,.insight-grid{{grid-template-columns:1fr}} .report-wrap{{padding:14px}} }}
</style></head><body><div class="report-wrap">
<div class="hero"><h1>Auto EDA Insight — Complete Report</h1><p><b>{COURSE_LINE}</b></p><p>Laporan ini merangkum seluruh aktivitas dan modul yang tersedia di dashboard: upload, preview, dataset info, cleaning, statistik, visualisasi, time series, insight, history, serta export.</p>
<div class="kpi-grid">
<div class="kpi"><div class="lbl">Dataset</div><div class="val">{_safe_html(meta.get('name','-'))}</div></div>
<div class="kpi"><div class="lbl">Rows</div><div class="val">{fmt_int(s['rows'])}</div></div>
<div class="kpi"><div class="lbl">Columns</div><div class="val">{fmt_int(s['cols'])}</div></div>
<div class="kpi"><div class="lbl">Quality</div><div class="val">{bundle['quality_score']}/100</div></div>
</div></div>
{_table_html('Activity Log / Aktivitas Web', bundle['activity'], 120, 'Halaman dan proses yang dijalankan selama sesi dashboard.')}
{_table_html('Riwayat Upload Dataset', bundle['upload_history'], 60)}
{_table_html('Dataset Overview / Preview', df.head(40), 40, 'Preview dataset aktif yang sedang dianalisis.')}
{_table_html('Dataset Information', bundle['dataset_info'], 120)}
{_table_html('Missing Value Summary', bundle['missing_summary'], 120)}
{_table_html('Cleaning Before / After Summary', bundle['before_after'], 40)}
{_table_html('Cleaning Log', log_df, 120)}
{_table_html('Before Cleaning Data', st.session_state.get('before_df'), 40)}
{_table_html('After Cleaning Data', st.session_state.get('after_df'), 40)}
{_table_html('Descriptive Statistics — Numeric', bundle['numeric_stats'], 120)}
{_table_html('Descriptive Statistics — Categorical', bundle['categorical_stats'], 120)}
{visual_html}
{_table_html('Time Series Result Table', bundle['time_series'], 120, bundle['time_series_note'])}
<section class='report-section'><h2>Initial Intelligent Insight Interpretation</h2><div class='insight-grid'>{insight_cards}</div></section>
<div class="footer">Generated at {now} · Auto EDA Insight · {COURSE_LINE}</div>
</div></body></html>"""


def generate_pdf_report(df, theme_mode="light"):
    """Generate PDF in makalah format — reportlab, portrait A4, clickable TOC,
    Word-style tables, ALL dashboard charts embedded, cover + kata pengantar + daftar isi."""
    bundle = build_complete_report_bundle(df, theme_mode=theme_mode, include_visual_sections=False)
    buf = io.BytesIO()

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable, Image as RLImage, BaseDocTemplate,
        Frame, PageTemplate, KeepTogether, NextPageTemplate)
    from reportlab.platypus.tableofcontents import TableOfContents
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

    PW, PH = A4
    LM, RM, TM, BM = 2.5*cm, 2.0*cm, 2.5*cm, 2.5*cm
    CW = PW - LM - RM

    ACCENT   = rl_colors.HexColor("#1a1a7e")
    MUTED_C  = rl_colors.HexColor("#4a5568")
    HDR_BG   = rl_colors.HexColor("#1a1a7e")
    ROW_ALT  = rl_colors.HexColor("#f4f6fb")
    EDGE_C   = rl_colors.HexColor("#c0cce8")
    INFO_BG  = rl_colors.HexColor("#eef2ff")
    WHITE    = rl_colors.white
    BLACK    = rl_colors.HexColor("#10231a")

    palette = ["#4f46e5","#0891b2","#f59e0b","#16a34a","#e11d48","#ea580c","#7c3aed","#14b8a6"]

    normal_st = ParagraphStyle("NRL", fontName="Helvetica",
        fontSize=10.5, leading=16, textColor=BLACK, spaceAfter=8, alignment=TA_JUSTIFY)
    bold_lbl  = ParagraphStyle("BL", fontName="Helvetica-Bold",
        fontSize=10, textColor=BLACK, spaceAfter=4, spaceBefore=10)
    caption_st = ParagraphStyle("Cap", fontName="Helvetica-Oblique",
        fontSize=8.5, textColor=MUTED_C, spaceAfter=6, alignment=TA_CENTER)

    # ── Heading factory (auto-registers in TOC) ──
    def _h(text, level=0, key=None):
        anchor = (key or text).replace(" ","_").replace("/","_").replace(".","_")
        if level == 0:
            st = ParagraphStyle(f"H0_{anchor}", fontName="Helvetica-Bold",
                fontSize=13, spaceBefore=22, spaceAfter=6, textColor=ACCENT, keepWithNext=1)
        else:
            st = ParagraphStyle(f"H1_{anchor}", fontName="Helvetica",
                fontSize=11, spaceBefore=12, spaceAfter=4, textColor=ACCENT,
                leftIndent=14, keepWithNext=1)
        p = Paragraph(f'<a name="{anchor}"/>' + text, st)
        p._is_heading = True
        p._heading_key   = anchor
        p._heading_level = level
        p._heading_text  = text
        return p

    def _safe_df(d):
        try:
            if d is None: return pd.DataFrame()
            return pd.DataFrame(d) if not isinstance(d, pd.DataFrame) else d
        except Exception:
            return pd.DataFrame()

    # ── Smart Word/Excel-style table: auto column widths, PORTRAIT ONLY ──
    # Wide tables are split into column chunks so they always fit portrait A4.
    def _tbl(df_in, max_rows=None, force_landscape=False):
        d = _safe_df(df_in)
        if max_rows is not None:
            d = d.head(max_rows)
        if d.empty:
            return [Paragraph("Tidak ada data untuk bagian ini.", normal_st)]
        d = d.copy().astype(str)

        # Max columns that comfortably fit portrait A4 at fs=7.5
        MAX_COLS = 8
        n = len(d.columns)

        def _make_chunk(chunk_df):
            """Render a single chunk as a Word-style table, portrait A4."""
            nc = len(chunk_df.columns)
            max_lens = [max(len(str(c)), max((len(str(v)) for v in chunk_df[col]), default=1))
                        for c, col in zip(chunk_df.columns, chunk_df.columns)]
            total_len = sum(max_lens) or 1
            col_widths = [max(1.0*cm, CW * (ml / total_len)) for ml in max_lens]
            chars_per = [max(6, int(w / (0.175*cm))) for w in col_widths]
            dc = chunk_df.copy()
            for i, c in enumerate(dc.columns):
                dc[c] = dc[c].str.slice(0, chars_per[i])
            fs = 7.5
            hdr = [Paragraph(f"<b>{str(c)}</b>",
                    ParagraphStyle(f"TH_{c}", fontName="Helvetica-Bold", fontSize=fs,
                        textColor=WHITE, alignment=TA_LEFT, leading=fs+2))
                   for c in dc.columns]
            rows = [[Paragraph(str(v),
                      ParagraphStyle(f"TD_{i}_{j}", fontName="Helvetica", fontSize=fs,
                          textColor=BLACK, alignment=TA_LEFT, leading=fs+2))
                     for j, v in enumerate(row)] for i, row in enumerate(dc.values)]
            all_rows = [hdr] + rows
            t = Table(all_rows, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
            cmds = [
                ("BACKGROUND",    (0,0),(-1,0),   HDR_BG),
                ("LINEBELOW",     (0,0),(-1,0),   1.0, ACCENT),
                ("GRID",          (0,0),(-1,-1),  0.35, EDGE_C),
                ("VALIGN",        (0,0),(-1,-1),  "MIDDLE"),
                ("TOPPADDING",    (0,0),(-1,-1),  3),
                ("BOTTOMPADDING", (0,0),(-1,-1),  3),
                ("LEFTPADDING",   (0,0),(-1,-1),  4),
                ("RIGHTPADDING",  (0,0),(-1,-1),  4),
            ]
            for i in range(1, len(all_rows)):
                if i % 2 == 0:
                    cmds.append(("BACKGROUND",(0,i),(-1,i), ROW_ALT))
            t.setStyle(TableStyle(cmds))
            return t

        if n <= MAX_COLS:
            return [_make_chunk(d)]

        # Split into column chunks
        elems = []
        col_list = list(d.columns)
        chunks = [col_list[i:i+MAX_COLS] for i in range(0, n, MAX_COLS)]
        for ci, chunk_cols in enumerate(chunks):
            if ci > 0:
                elems.append(Paragraph(
                    f"<i>Lanjutan tabel (kolom {chunk_cols[0]} s/d {chunk_cols[-1]})</i>",
                    ParagraphStyle("ChunkLbl", fontName="Helvetica-Oblique",
                        fontSize=8, textColor=MUTED_C, spaceBefore=8, spaceAfter=4)))
            elems.append(_make_chunk(d[chunk_cols]))
        return elems

    # ── Matplotlib chart → PNG → RLImage ──
    def _chart(draw_fn, w_cm=13, h_cm=7, caption=""):
        try:
            fig, ax = plt.subplots(figsize=(w_cm/2.54, h_cm/2.54))
            fig.patch.set_facecolor("white")
            ax.set_facecolor("#f8fafc")
            ax.tick_params(colors="#4a5568", labelsize=8)
            for sp in ax.spines.values(): sp.set_color("#c0cce8")
            ax.grid(True, color="#d4dce8", alpha=0.5, linewidth=0.5)
            draw_fn(ax)
            ibuf = io.BytesIO()
            fig.tight_layout(pad=0.8)
            fig.savefig(ibuf, format="png", dpi=130, bbox_inches="tight", facecolor="white")
            plt.close(fig)
            ibuf.seek(0)
            elems = [RLImage(ibuf, width=w_cm*cm, height=h_cm*cm)]
            if caption:
                elems.append(Paragraph(caption, caption_st))
            return KeepTogether(elems) if caption else elems[0]
        except Exception as exc:
            plt.close("all")
            return Paragraph(f"[Chart tidak dapat dibuat: {exc}]", caption_st)

    def _chart2(draw_fn, w_cm=13, h_cm=7, caption=""):
        """Chart with 2 subplots side by side."""
        try:
            fig, axes = plt.subplots(1, 2, figsize=(w_cm/2.54, h_cm/2.54))
            fig.patch.set_facecolor("white")
            for ax in axes:
                ax.set_facecolor("#f8fafc")
                ax.tick_params(colors="#4a5568", labelsize=8)
                for sp in ax.spines.values(): sp.set_color("#c0cce8")
                ax.grid(True, color="#d4dce8", alpha=0.5, linewidth=0.5)
            draw_fn(axes)
            ibuf = io.BytesIO()
            fig.tight_layout(pad=0.8)
            fig.savefig(ibuf, format="png", dpi=130, bbox_inches="tight", facecolor="white")
            plt.close(fig)
            ibuf.seek(0)
            elems = [RLImage(ibuf, width=w_cm*cm, height=h_cm*cm)]
            if caption:
                elems.append(Paragraph(caption, caption_st))
            return KeepTogether(elems) if caption else elems[0]
        except Exception as exc:
            plt.close("all")
            return Paragraph(f"[Chart tidak dapat dibuat: {exc}]", caption_st)

    # ── ReportDoc ──
    class ReportDoc(BaseDocTemplate):
        def __init__(self, buf_):
            BaseDocTemplate.__init__(self, buf_, pagesize=A4,
                leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM)
            frame_main   = Frame(LM, BM, CW, PH-TM-BM, id="main")
            frame_cover  = Frame(LM, BM, CW, PH-TM-BM, id="cover")
            tmpl_main    = PageTemplate(id="main",  frames=frame_main,  onPage=self._footer_portrait)
            tmpl_cover   = PageTemplate(id="cover", frames=frame_cover)
            self.addPageTemplates([tmpl_cover, tmpl_main])

        def _footer_portrait(self, c, doc):
            c.saveState()
            c.setStrokeColor(EDGE_C); c.setLineWidth(0.5)
            c.line(LM, 1.8*cm, PW-RM, 1.8*cm)
            c.setFont("Helvetica", 7); c.setFillColor(MUTED_C)
            c.drawString(LM, 1.5*cm,
                "Auto EDA Insight  \u00b7  Kelompok 6  \u00b7  Bakti Siregar, M.Sc., CDS.  \u00b7  ITSB")
            c.drawRightString(PW-RM, 1.5*cm, f"Halaman {doc.page}")
            c.restoreState()

        def afterFlowable(self, flowable):
            if getattr(flowable, "_is_heading", False):
                self.notify("TOCEntry", (
                    flowable._heading_level, flowable._heading_text,
                    self.page, flowable._heading_key))

    # ──────────────────────────────────────────────
    # PREPARE DATA
    # ──────────────────────────────────────────────
    dataset_name = bundle["meta"].get("name", "-")
    s = bundle["summary"]
    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include=["object","category","bool"]).columns.tolist()

    # ──────────────────────────────────────────────
    # BUILD STORY
    # ──────────────────────────────────────────────
    story = []

    # ── COVER ──
    story.append(NextPageTemplate("cover"))
    logo_path = str(BASE_DIR / "frontend" / "static" / "assets" / "images" / "itsb.png")
    cover_elems = [Spacer(1, 1.6*cm)]
    try:
        cover_elems.append(RLImage(logo_path, width=3.5*cm, height=3.5*cm, hAlign="CENTER"))
    except Exception:
        pass
    cover_elems += [
        Spacer(1, 0.4*cm),
        Paragraph("INSTITUT TEKNOLOGI SAINS BANDUNG",
            ParagraphStyle("CI", fontName="Helvetica-Bold", fontSize=13,
                alignment=TA_CENTER, textColor=ACCENT, spaceAfter=4)),
        Paragraph("Program Studi Sistem Informasi",
            ParagraphStyle("CP", fontName="Helvetica", fontSize=10,
                alignment=TA_CENTER, textColor=MUTED_C, spaceAfter=6)),
        HRFlowable(width="55%", thickness=1.2, color=ACCENT, hAlign="CENTER", spaceAfter=18),
        Paragraph("LAPORAN ANALISIS DATA",
            ParagraphStyle("CS", fontName="Helvetica-Oblique", fontSize=11,
                alignment=TA_CENTER, textColor=MUTED_C, spaceAfter=8)),
        Paragraph("AUTO EDA INSIGHT DASHBOARD",
            ParagraphStyle("CT", fontName="Helvetica-Bold", fontSize=20,
                alignment=TA_CENTER, textColor=ACCENT, spaceAfter=8)),
        Paragraph(f"Dataset: {dataset_name}",
            ParagraphStyle("CD", fontName="Helvetica", fontSize=11,
                alignment=TA_CENTER, textColor=BLACK, spaceAfter=20)),
    ]
    info_tbl = Table([
        ["Mata Kuliah",    "Data Science Programming (SD-1306)"],
        ["Dosen Pengampu", "Bakti Siregar, M.Sc., CDS."],
        ["Kelompok",       "Kelompok 6  \u2014  Sistem Informasi"],
    ], colWidths=[4.5*cm, 9.5*cm], hAlign="CENTER")
    info_tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),INFO_BG), ("BOX",(0,0),(-1,-1),0.8,ACCENT),
        ("INNERGRID",(0,0),(-1,-1),0.3,EDGE_C), ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ("FONTNAME",(1,0),(1,-1),"Helvetica"), ("FONTSIZE",(0,0),(-1,-1),10),
        ("TEXTCOLOR",(0,0),(-1,-1),BLACK),
        ("TOPPADDING",(0,0),(-1,-1),7), ("BOTTOMPADDING",(0,0),(-1,-1),7),
        ("LEFTPADDING",(0,0),(-1,-1),10), ("RIGHTPADDING",(0,0),(-1,-1),10),
    ]))
    cover_elems.append(info_tbl)
    cover_elems.append(Spacer(1, 18))
    cover_elems.append(Paragraph("Disusun Oleh:",
        ParagraphStyle("DL", fontName="Helvetica-Oblique", fontSize=10.5,
            alignment=TA_CENTER, textColor=MUTED_C, spaceAfter=8)))
    mem_tbl = Table([[m["name"], m["nim"]] for m in TEAM_MEMBERS],
                    colWidths=[8*cm, 4*cm], hAlign="CENTER")
    mem_tbl.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1),"Helvetica"), ("FONTSIZE",(0,0),(-1,-1),10.5),
        ("TEXTCOLOR",(0,0),(-1,-1),BLACK),
        ("TOPPADDING",(0,0),(-1,-1),4), ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("ALIGN",(0,0),(0,-1),"RIGHT"), ("ALIGN",(1,0),(1,-1),"LEFT"),
    ]))
    cover_elems += [
        mem_tbl, Spacer(1, 24),
        HRFlowable(width="75%", thickness=1.2, color=ACCENT, hAlign="CENTER", spaceAfter=8),
        Paragraph("BEKASI", ParagraphStyle("CK", fontName="Helvetica-Bold", fontSize=11,
            alignment=TA_CENTER, textColor=ACCENT, spaceAfter=4)),
        Paragraph(datetime.datetime.now().strftime("%Y"),
            ParagraphStyle("CY", fontName="Helvetica", fontSize=11,
                alignment=TA_CENTER, textColor=MUTED_C)),
    ]
    story.extend(cover_elems)
    story.append(NextPageTemplate("main"))
    story.append(PageBreak())

    # ── KATA PENGANTAR ──
    story.append(_h("KATA PENGANTAR", 0, "kata_pengantar"))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=14))
    for para in [
        "Puji syukur kami panjatkan ke hadirat Tuhan Yang Maha Esa atas rahmat dan "
        "karunia-Nya sehingga laporan analisis data ini dapat diselesaikan dengan baik.",
        f'Laporan ini merupakan hasil pengembangan Dashboard Auto EDA Insight sebagai proyek akhir '
        f'(UAS) mata kuliah Data Science Programming (SD-1306) di Institut Teknologi Sains Bandung (ITSB), '
        f'di bawah bimbingan Bapak Bakti Siregar, M.Sc., CDS. Dataset yang dianalisis adalah "{dataset_name}".',
        "Dashboard ini dirancang untuk melakukan Exploratory Data Analysis (EDA) secara otomatis, "
        "mencakup upload data, data cleaning, statistik deskriptif, visualisasi interaktif, "
        "analisis time series, dan ekspor laporan dalam berbagai format.",
        "Kami menyadari bahwa laporan ini masih jauh dari sempurna. Oleh karena itu, kami sangat "
        "mengharapkan kritik dan saran yang membangun demi perbaikan di masa mendatang.",
        "Akhir kata, kami ucapkan terima kasih kepada Bapak Bakti Siregar, M.Sc., CDS. selaku "
        "dosen pengampu yang telah membimbing kami sepanjang perkuliahan ini.",
    ]:
        story.append(Paragraph(para, normal_st)); story.append(Spacer(1, 6))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Bekasi, {datetime.datetime.now().strftime('%d %B %Y')}",
        ParagraphStyle("RR", fontName="Helvetica", fontSize=10.5, alignment=TA_RIGHT, textColor=MUTED_C)))
    story.append(Paragraph("<b>Tim Pengembang \u2014 Kelompok 6</b>",
        ParagraphStyle("RRB", fontName="Helvetica-Bold", fontSize=10.5, alignment=TA_RIGHT, textColor=BLACK)))
    story.append(PageBreak())

    # ── DAFTAR ISI ──
    story.append(Paragraph("DAFTAR ISI",
        ParagraphStyle("TocTitle", fontName="Helvetica-Bold", fontSize=14,
            alignment=TA_CENTER, textColor=ACCENT, spaceAfter=16)))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=14))
    toc = TableOfContents()
    toc.dotsMinLevel = 0
    toc.levelStyles = [
        ParagraphStyle("TOC0", fontName="Helvetica-Bold", fontSize=11, leading=20, leftIndent=0, textColor=BLACK),
        ParagraphStyle("TOC1", fontName="Helvetica", fontSize=10, leading=18, leftIndent=22, textColor=MUTED_C),
    ]
    story.append(toc)
    story.append(PageBreak())

    # ── BAB I: PENDAHULUAN ──
    story.append(_h("BAB I  Pendahuluan", 0, "bab1"))
    story.append(HRFlowable(width="100%", thickness=0.5, color=EDGE_C, spaceAfter=8))
    story.append(_h("1.1  Latar Belakang", 1, "bab1_1"))
    story.append(Paragraph(
        "Dalam era digital saat ini, analisis data menjadi kebutuhan fundamental di berbagai bidang. "
        "Dashboard Auto EDA Insight dikembangkan untuk membantu proses Exploratory Data Analysis (EDA) "
        "secara otomatis dan interaktif, sehingga pengguna dapat memperoleh insight dari data "
        "tanpa memerlukan keahlian pemrograman mendalam.", normal_st))
    story.append(_h("1.2  Tujuan", 1, "bab1_2"))
    story.append(Paragraph(
        "Laporan ini bertujuan mendokumentasikan hasil analisis data secara menyeluruh, meliputi "
        "ringkasan statistik, hasil data cleaning, visualisasi lengkap, dan insight otomatis.", normal_st))
    story.append(_h("1.3  Ringkasan Dataset", 1, "bab1_3"))
    story.extend(_tbl(pd.DataFrame([
        ["Nama Dataset",    dataset_name],
        ["Jumlah Baris",    str(s["rows"])],
        ["Jumlah Kolom",    str(s["cols"])],
        ["Kolom Numerik",   str(s["numeric"])],
        ["Kolom Kategorik", str(s["category"])],
        ["Missing Values",  str(s["missing"])],
        ["Data Duplikat",   str(s["duplicate"])],
        ["Quality Score",   f'{bundle["quality_score"]}/100 ({bundle["quality_label"]})'],
    ], columns=["Keterangan", "Nilai"])))
    story.append(PageBreak())

    # ── BAB II: PEMBAHASAN ──
    story.append(_h("BAB II  Pembahasan", 0, "bab2"))
    story.append(HRFlowable(width="100%", thickness=0.5, color=EDGE_C, spaceAfter=8))

    story.append(_h("2.1  Aktivitas Web", 1, "bab2_1"))
    story.extend(_tbl(bundle["activity"], max_rows=30))
    story.append(Spacer(1, 10))
    story.append(_h("2.2  Riwayat Upload Dataset", 1, "bab2_2"))
    story.extend(_tbl(bundle["upload_history"], max_rows=20))
    story.append(PageBreak())

    story.append(_h("2.3  Dataset Preview", 1, "bab2_3"))
    story.append(Paragraph(
        "Berikut adalah tampilan awal dataset yang diupload (25 baris pertama):", normal_st))
    story.extend(_tbl(df, max_rows=len(df)))
    story.append(PageBreak())

    story.append(_h("2.4  Informasi Dataset", 1, "bab2_4"))
    story.extend(_tbl(bundle["dataset_info"], max_rows=35))
    story.append(Spacer(1, 10))
    story.append(_h("2.5  Missing Value Summary", 1, "bab2_5"))
    story.extend(_tbl(bundle["missing_summary"], max_rows=35))
    story.append(PageBreak())

    story.append(_h("2.6  Data Cleaning", 1, "bab2_6"))
    story.append(Paragraph("Perbandingan data sebelum dan sesudah proses cleaning:", normal_st))
    story.extend(_tbl(bundle["before_after"], max_rows=20))
    story.append(Spacer(1, 10))
    story.append(_h("2.6.1  Log Cleaning", 1, "bab2_6_1"))
    log_df = pd.DataFrame({"Cleaning Log": bundle["cleaning_log"]}) \
             if bundle["cleaning_log"] else pd.DataFrame({"Cleaning Log": ["Belum ada operasi cleaning."]})
    story.extend(_tbl(log_df, max_rows=35))
    story.append(PageBreak())

    story.append(_h("2.7  Statistik Deskriptif", 1, "bab2_7"))
    ns = _safe_df(bundle["numeric_stats"])
    cs = _safe_df(bundle["categorical_stats"])
    if not ns.empty:
        story.append(Paragraph("<b>Statistik Numerik</b>", bold_lbl))
        story.extend(_tbl(ns, max_rows=35))
        story.append(Spacer(1, 12))
    if not cs.empty:
        story.append(Paragraph("<b>Statistik Kategorik</b>", bold_lbl))
        story.extend(_tbl(cs, max_rows=35))
    story.append(PageBreak())

    # ── 2.8 VISUALISASI NUMERIK ──
    story.append(_h("2.8  Visualisasi Numerik", 1, "bab2_8"))
    story.append(Paragraph(
        "Bagian ini memuat seluruh visualisasi untuk setiap kolom numerik: "
        "Histogram, Box Plot, Violin Plot, Density Plot, dan QQ Plot.", normal_st))

    for col in num_cols:
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        if vals.empty: continue
        story.append(Paragraph(f"<b>Kolom: {col}</b>",
            ParagraphStyle(f"ColH_{col}", fontName="Helvetica-Bold", fontSize=10,
                textColor=ACCENT, spaceBefore=14, spaceAfter=6)))

        # Row 1: Histogram + Box Plot
        def _hist_box(axes, col=col, vals=vals):
            axes[0].hist(vals, bins=20, color=palette[0], alpha=0.82, edgecolor="white")
            axes[0].set_title(f"Histogram: {col}", fontsize=9, color="#1a1a7e")
            axes[0].set_xlabel(col, fontsize=8); axes[0].set_ylabel("Frekuensi", fontsize=8)
            axes[1].boxplot(vals.tolist(), vert=True, patch_artist=True,
                boxprops=dict(facecolor=palette[1], alpha=0.7),
                medianprops=dict(color="white", linewidth=2))
            axes[1].set_title(f"Box Plot: {col}", fontsize=9, color="#1a1a7e")
            axes[1].set_ylabel(col, fontsize=8)
        story.append(_chart2(_hist_box, w_cm=CW/cm, h_cm=6,
            caption=f"Histogram dan Box Plot — {col}"))

        # Row 2: Violin + Density
        def _vio_den(axes, col=col, vals=vals):
            axes[0].violinplot(vals.tolist(), positions=[0], showmedians=True,
                               showextrema=True)
            axes[0].set_title(f"Violin Plot: {col}", fontsize=9, color="#1a1a7e")
            axes[0].set_xticks([]); axes[0].set_ylabel(col, fontsize=8)
            try:
                from scipy.stats import gaussian_kde
                import numpy as np
                kde = gaussian_kde(vals)
                x_range = np.linspace(vals.min(), vals.max(), 200)
                axes[1].plot(x_range, kde(x_range), color=palette[2], linewidth=2)
                axes[1].fill_between(x_range, kde(x_range), alpha=0.25, color=palette[2])
            except Exception:
                axes[1].hist(vals, bins=20, density=True, color=palette[2], alpha=0.6)
            axes[1].set_title(f"Density Plot: {col}", fontsize=9, color="#1a1a7e")
            axes[1].set_xlabel(col, fontsize=8); axes[1].set_ylabel("Density", fontsize=8)
        story.append(_chart2(_vio_den, w_cm=CW/cm, h_cm=6,
            caption=f"Violin Plot dan Density Plot — {col}"))

        # QQ Plot
        def _qq(ax, col=col, vals=vals):
            try:
                import scipy.stats as stats
                import numpy as np
                qq = stats.probplot(vals, dist="norm")
                ax.scatter(qq[0][0], qq[0][1], color=palette[3], alpha=0.7, s=18)
                ax.plot(qq[0][0], qq[1][0]*qq[0][0]+qq[1][1], color="red", linewidth=1.5)
                ax.set_title(f"QQ Plot: {col}", fontsize=9, color="#1a1a7e")
                ax.set_xlabel("Theoretical Quantiles", fontsize=8)
                ax.set_ylabel("Sample Quantiles", fontsize=8)
            except Exception as e:
                ax.text(0.5, 0.5, f"QQ Plot error: {e}", transform=ax.transAxes,
                        ha="center", fontsize=8)
        story.append(_chart(_qq, w_cm=CW/cm*0.6, h_cm=5.5,
            caption=f"QQ Plot — {col}"))
        story.append(Spacer(1, 8))
    story.append(PageBreak())

    # ── 2.9 VISUALISASI KATEGORIK ──
    story.append(_h("2.9  Visualisasi Kategorik", 1, "bab2_9"))
    story.append(Paragraph(
        "Bagian ini memuat visualisasi untuk kolom kategorik: "
        "Bar Chart, Pie Chart, Pareto Chart, dan Count Plot.", normal_st))

    for col in cat_cols:
        vc = df[col].value_counts().head(12)
        if vc.empty: continue
        story.append(Paragraph(f"<b>Kolom: {col}</b>",
            ParagraphStyle(f"CatH_{col}", fontName="Helvetica-Bold", fontSize=10,
                textColor=ACCENT, spaceBefore=14, spaceAfter=6)))

        def _bar_pie(axes, col=col, vc=vc):
            # Bar chart
            axes[0].bar(range(len(vc)), vc.values, color=palette[1], alpha=0.85, edgecolor="white")
            axes[0].set_xticks(range(len(vc)))
            axes[0].set_xticklabels([str(v)[:12] for v in vc.index], rotation=35, ha="right", fontsize=7)
            axes[0].set_title(f"Bar Chart: {col}", fontsize=9, color="#1a1a7e")
            axes[0].set_ylabel("Count", fontsize=8)
            # Pie chart
            clrs = [palette[i % len(palette)] for i in range(len(vc))]
            axes[1].pie(vc.values, labels=[str(v)[:10] for v in vc.index],
                        colors=clrs, autopct="%1.1f%%", pctdistance=0.8,
                        textprops={"fontsize": 7})
            axes[1].set_title(f"Pie Chart: {col}", fontsize=9, color="#1a1a7e")
        story.append(_chart2(_bar_pie, w_cm=CW/cm, h_cm=6,
            caption=f"Bar Chart dan Pie Chart — {col}"))

        def _pareto(ax, col=col, vc=vc):
            cumsum = vc.values.cumsum() / vc.values.sum() * 100
            ax.bar(range(len(vc)), vc.values, color=palette[0], alpha=0.8, edgecolor="white")
            ax2 = ax.twinx()
            ax2.plot(range(len(vc)), cumsum, color="red", marker="o", linewidth=2, markersize=4)
            ax2.axhline(y=80, color="gray", linestyle="--", linewidth=1)
            ax2.set_ylabel("Kumulatif (%)", fontsize=8); ax2.set_ylim(0, 110)
            ax.set_xticks(range(len(vc)))
            ax.set_xticklabels([str(v)[:12] for v in vc.index], rotation=35, ha="right", fontsize=7)
            ax.set_title(f"Pareto Chart: {col}", fontsize=9, color="#1a1a7e")
            ax.set_ylabel("Frequency", fontsize=8)
        story.append(_chart(_pareto, w_cm=CW/cm*0.75, h_cm=6,
            caption=f"Pareto Chart — {col}"))
        story.append(Spacer(1, 8))
    story.append(PageBreak())

    # ── 2.10 ANALISIS BIVARIATE & MULTIVARIATE ──
    story.append(_h("2.10  Analisis Bivariate & Multivariate", 1, "bab2_10"))
    story.append(Paragraph(
        "Bagian ini mencakup Scatter Plot, Correlation Heatmap, Regression Plot, "
        "Pair Plot (Pair Matrix), dan Bubble Chart untuk analisis hubungan antar variabel.", normal_st))

    if len(num_cols) >= 2:
        # Scatter & Regression for each pair (up to 3 pairs)
        pairs = [(num_cols[i], num_cols[i+1]) for i in range(min(len(num_cols)-1, 3))]
        for x_col, y_col in pairs:
            xv = pd.to_numeric(df[x_col], errors="coerce")
            yv = pd.to_numeric(df[y_col], errors="coerce")
            mask = xv.notna() & yv.notna()
            xv, yv = xv[mask], yv[mask]
            if len(xv) < 3: continue

            def _scat_reg(axes, xv=xv, yv=yv, x_col=x_col, y_col=y_col):
                axes[0].scatter(xv, yv, color=palette[0], alpha=0.6, s=18)
                axes[0].set_title(f"Scatter: {x_col} vs {y_col}", fontsize=9, color="#1a1a7e")
                axes[0].set_xlabel(x_col, fontsize=8); axes[0].set_ylabel(y_col, fontsize=8)
                try:
                    import numpy as np
                    m, b = np.polyfit(xv, yv, 1)
                    xl = np.linspace(xv.min(), xv.max(), 100)
                    axes[1].scatter(xv, yv, color=palette[1], alpha=0.6, s=18)
                    axes[1].plot(xl, m*xl+b, color="red", linewidth=2)
                except Exception:
                    pass
                axes[1].set_title(f"Regression: {x_col} vs {y_col}", fontsize=9, color="#1a1a7e")
                axes[1].set_xlabel(x_col, fontsize=8); axes[1].set_ylabel(y_col, fontsize=8)
            story.append(_chart2(_scat_reg, w_cm=CW/cm, h_cm=6,
                caption=f"Scatter Plot dan Regression — {x_col} vs {y_col}"))
            story.append(Spacer(1, 6))

        # Correlation Heatmap
        corr = df[num_cols].corr()
        def _heat(ax, corr=corr, nc=num_cols):
            import numpy as np
            im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            ax.set_xticks(range(len(nc))); ax.set_yticks(range(len(nc)))
            ax.set_xticklabels([c[:10] for c in nc], rotation=45, ha="right", fontsize=7)
            ax.set_yticklabels([c[:10] for c in nc], fontsize=7)
            for i in range(len(nc)):
                for j in range(len(nc)):
                    ax.text(j, i, f"{corr.values[i,j]:.2f}", ha="center", va="center",
                            fontsize=6.5, color="white" if abs(corr.values[i,j]) > 0.5 else "black")
            ax.set_title("Correlation Heatmap", fontsize=9, color="#1a1a7e")
        story.append(_chart(_heat, w_cm=CW/cm, h_cm=min(10, max(6, len(num_cols)*1.2)),
            caption="Correlation Heatmap — Hubungan Antar Variabel Numerik"))
        story.append(Spacer(1, 6))

        # Pair Matrix (up to 4 cols)
        pair_cols = num_cols[:4]
        n_pair = len(pair_cols)
        def _pair(ax, pair_cols=pair_cols, n=n_pair):
            import numpy as np
            fig_pair, axes_pair = plt.subplots(n, n, figsize=(n*2.5, n*2.5))
            fig_pair.patch.set_facecolor("white")
            if n == 1: axes_pair = [[axes_pair]]
            for i in range(n):
                for j in range(n):
                    a = axes_pair[i][j] if n > 1 else axes_pair[0][0]
                    a.set_facecolor("#f8fafc")
                    xi = pd.to_numeric(df[pair_cols[i]], errors="coerce").dropna()
                    xj = pd.to_numeric(df[pair_cols[j]], errors="coerce").dropna()
                    if i == j:
                        a.hist(xi, bins=15, color=palette[i%len(palette)], alpha=0.75)
                    else:
                        common = df[[pair_cols[i],pair_cols[j]]].dropna()
                        a.scatter(common[pair_cols[j]], common[pair_cols[i]],
                                  color=palette[(i+j)%len(palette)], alpha=0.5, s=8)
                    if i == n-1: a.set_xlabel(pair_cols[j][:8], fontsize=7)
                    if j == 0:   a.set_ylabel(pair_cols[i][:8], fontsize=7)
                    a.tick_params(labelsize=6)
            fig_pair.suptitle("Pair Matrix", fontsize=10, color="#1a1a7e")
            fig_pair.tight_layout(pad=0.5)
            ibuf2 = io.BytesIO()
            fig_pair.savefig(ibuf2, format="png", dpi=110, bbox_inches="tight", facecolor="white")
            plt.close(fig_pair)
            ibuf2.seek(0)
            ax.imshow(plt.imread(ibuf2)); ax.axis("off")
        sz = min(12, max(7, n_pair * 2.8))
        story.append(_chart(_pair, w_cm=sz, h_cm=sz, caption="Pair Matrix — Kombinasi Variabel Numerik"))
        story.append(Spacer(1, 6))

        # Bubble Chart (if 3+ num cols)
        if len(num_cols) >= 3:
            xc, yc, sc = num_cols[0], num_cols[1], num_cols[2]
            def _bubble(ax, xc=xc, yc=yc, sc=sc):
                sub = df[[xc,yc,sc]].dropna().apply(pd.to_numeric, errors="coerce").dropna()
                if sub.empty: ax.text(0.5,0.5,"No data",transform=ax.transAxes,ha="center"); return
                sizes = ((sub[sc] - sub[sc].min()) / (sub[sc].max() - sub[sc].min() + 1e-9) * 300 + 20)
                clr_col = cat_cols[0] if cat_cols else None
                if clr_col:
                    cats = df.loc[sub.index, clr_col].astype("category")
                    for i, cat in enumerate(cats.cat.categories):
                        mask = cats == cat
                        ax.scatter(sub.loc[mask, xc], sub.loc[mask, yc],
                                   s=sizes[mask], color=palette[i%len(palette)], alpha=0.6, label=str(cat)[:12])
                    ax.legend(fontsize=7, loc="best")
                else:
                    ax.scatter(sub[xc], sub[yc], s=sizes, color=palette[0], alpha=0.6)
                ax.set_xlabel(xc, fontsize=8); ax.set_ylabel(yc, fontsize=8)
                ax.set_title(f"Bubble Chart: {xc} vs {yc} (size={sc})", fontsize=9, color="#1a1a7e")
            story.append(_chart(_bubble, w_cm=CW/cm, h_cm=7,
                caption=f"Bubble Chart — {xc} vs {yc}, ukuran bubble = {sc}"))
    else:
        story.append(Paragraph("Dataset tidak memiliki cukup kolom numerik untuk analisis bivariate.", normal_st))
    story.append(PageBreak())

    # ── 2.11 ANALISIS KATEGORIK vs NUMERIK ──
    story.append(_h("2.11  Analisis Kategorik vs Numerik", 1, "bab2_11"))
    story.append(Paragraph(
        "Bagian ini mencakup Box Plot by Category, Violin Plot by Category, "
        "Grouped Bar Chart, dan Strip Plot untuk setiap kombinasi kolom kategorik dan numerik.", normal_st))

    if cat_cols and num_cols:
        cat_col = cat_cols[0]
        for num_col in num_cols[:3]:
            sub = df[[cat_col, num_col]].dropna()
            cats = sub[cat_col].value_counts().head(8).index.tolist()
            sub = sub[sub[cat_col].isin(cats)]
            groups = [sub[sub[cat_col]==c][num_col].dropna().tolist() for c in cats]
            if not any(groups): continue
            story.append(Paragraph(f"<b>{cat_col} vs {num_col}</b>",
                ParagraphStyle(f"CVN_{cat_col}_{num_col}", fontName="Helvetica-Bold",
                    fontSize=10, textColor=ACCENT, spaceBefore=12, spaceAfter=6)))

            def _box_vio(axes, cats=cats, groups=groups, cat_col=cat_col, num_col=num_col):
                bp = axes[0].boxplot(groups, patch_artist=True, labels=[str(c)[:10] for c in cats])
                for i, patch in enumerate(bp["boxes"]):
                    patch.set_facecolor(palette[i % len(palette)]); patch.set_alpha(0.75)
                axes[0].set_title(f"Box Plot by {cat_col}", fontsize=9, color="#1a1a7e")
                axes[0].set_ylabel(num_col, fontsize=8)
                axes[0].tick_params(axis="x", rotation=30, labelsize=7)
                axes[1].violinplot(groups, positions=range(len(cats)), showmedians=True)
                axes[1].set_xticks(range(len(cats)))
                axes[1].set_xticklabels([str(c)[:10] for c in cats], rotation=30, fontsize=7)
                axes[1].set_title(f"Violin by {cat_col}", fontsize=9, color="#1a1a7e")
                axes[1].set_ylabel(num_col, fontsize=8)
            story.append(_chart2(_box_vio, w_cm=CW/cm, h_cm=6,
                caption=f"Box Plot dan Violin Plot by {cat_col} — {num_col}"))

            def _gbar_strip(axes, cats=cats, groups=groups, sub=sub, cat_col=cat_col, num_col=num_col):
                means = [pd.Series(g).mean() for g in groups]
                axes[0].bar(range(len(cats)), means,
                            color=[palette[i%len(palette)] for i in range(len(cats))],
                            alpha=0.85, edgecolor="white")
                axes[0].set_xticks(range(len(cats)))
                axes[0].set_xticklabels([str(c)[:10] for c in cats], rotation=30, ha="right", fontsize=7)
                axes[0].set_title(f"Grouped Bar: Mean {num_col}", fontsize=9, color="#1a1a7e")
                axes[0].set_ylabel(f"Mean {num_col}", fontsize=8)
                import numpy as np
                for i, g in enumerate(groups):
                    jitter = np.random.normal(i, 0.08, len(g))
                    axes[1].scatter(jitter, g, color=palette[i%len(palette)], alpha=0.5, s=12)
                axes[1].set_xticks(range(len(cats)))
                axes[1].set_xticklabels([str(c)[:10] for c in cats], rotation=30, ha="right", fontsize=7)
                axes[1].set_title(f"Strip Plot by {cat_col}", fontsize=9, color="#1a1a7e")
                axes[1].set_ylabel(num_col, fontsize=8)
            story.append(_chart2(_gbar_strip, w_cm=CW/cm, h_cm=6,
                caption=f"Grouped Bar Chart dan Strip Plot — {cat_col} vs {num_col}"))
            story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("Dataset tidak memiliki kombinasi kolom kategorik dan numerik.", normal_st))
    story.append(PageBreak())

    # ── 2.12 TIME SERIES ──
    story.append(_h("2.12  Analisis Time Series", 1, "bab2_12"))
    story.append(Paragraph(
        "Bagian ini mencakup Time Series Line Chart, Moving Average, Rolling Mean, dan Trend Line.", normal_st))
    ts_df = _safe_df(bundle.get("time_series"))
    ts_note = bundle.get("time_series_note", "")
    if not ts_df.empty:
        story.extend(_tbl(ts_df, max_rows=36))
        story.append(Spacer(1, 10))
        # detect date and value columns
        date_col_ts = next((c for c in ts_df.columns if "date" in c.lower() or "period" in c.lower() or "waktu" in c.lower()), None)
        val_col_ts  = next((c for c in ts_df.columns if ts_df[c].dtype in ["float64","int64"]), None)
        if date_col_ts and val_col_ts:
            ts_plot = ts_df.copy()
            ts_plot[date_col_ts] = pd.to_datetime(ts_plot[date_col_ts], errors="coerce")
            ts_plot[val_col_ts]  = pd.to_numeric(ts_plot[val_col_ts], errors="coerce")
            ts_plot = ts_plot.dropna(subset=[date_col_ts, val_col_ts]).sort_values(date_col_ts)
            if len(ts_plot) >= 3:
                import numpy as np
                ts_plot["MA"] = ts_plot[val_col_ts].rolling(3, min_periods=1).mean()
                trend_x = np.arange(len(ts_plot))
                trend_m, trend_b = np.polyfit(trend_x, ts_plot[val_col_ts], 1)
                def _ts_line(ax, ts_plot=ts_plot, val_col_ts=val_col_ts, trend_m=trend_m, trend_b=trend_b):
                    ax.plot(range(len(ts_plot)), ts_plot[val_col_ts], marker="o", linewidth=2,
                            color=palette[0], markersize=4, label="Aktual/Forecast")
                    ax.plot(range(len(ts_plot)), ts_plot["MA"], linewidth=2,
                            color=palette[1], linestyle="--", label="Moving Average")
                    ax.plot(range(len(ts_plot)), trend_m * np.arange(len(ts_plot)) + trend_b,
                            color="red", linewidth=1.5, linestyle=":", label="Trend Line")
                    ax.set_xticks(range(len(ts_plot)))
                    ax.set_xticklabels([str(d)[:7] for d in ts_plot[date_col_ts]], rotation=35, ha="right", fontsize=7)
                    ax.set_title(f"Time Series: {val_col_ts}", fontsize=9, color="#1a1a7e")
                    ax.set_ylabel(val_col_ts, fontsize=8)
                    ax.legend(fontsize=8)
                story.append(_chart(_ts_line, w_cm=CW/cm, h_cm=7,
                    caption=f"Time Series Line Chart + Moving Average + Trend — {val_col_ts}"))
    else:
        story.append(Paragraph(ts_note or "Dataset tidak memiliki kolom tanggal/datetime valid.", normal_st))
    story.append(PageBreak())

    # ── BAB III: PENUTUP ──
    story.append(_h("BAB III  Penutup", 0, "bab3"))
    story.append(HRFlowable(width="100%", thickness=0.5, color=EDGE_C, spaceAfter=8))
    story.append(_h("3.1  Kesimpulan", 1, "bab3_1"))
    insights = bundle.get("insights") or []
    if insights:
        for ins in insights[:8]:
            story.append(Paragraph(f"\u2022  {ins}",
                ParagraphStyle("Bul", fontName="Helvetica", fontSize=10,
                    leading=15, textColor=BLACK, leftIndent=14, spaceAfter=6)))
    else:
        story.append(Paragraph("Analisis data telah berhasil dilakukan menggunakan Auto EDA Insight Dashboard.", normal_st))
    story.append(_h("3.2  Saran", 1, "bab3_2"))
    story.append(Paragraph(
        "Berdasarkan hasil analisis, disarankan untuk melakukan validasi lebih lanjut terhadap data "
        "yang memiliki missing value tinggi, serta mempertimbangkan penambahan fitur analisis lanjutan "
        "seperti pemodelan prediktif dan clustering.", normal_st))
    story.append(PageBreak())

    # ── Build ──
    doc = ReportDoc(buf)
    doc.multiBuild(story)
    buf.seek(0)
    return buf.getvalue()



def generate_excel_report(df, theme_mode="light"):
    bundle = build_complete_report_bundle(df, theme_mode=theme_mode, include_visual_sections=False)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        def write_sheet(name, data):
            data = _safe_df(data)
            if data.empty:
                data = pd.DataFrame({"Info": ["Tidak ada data"]})
            data.to_excel(writer, sheet_name=name[:31], index=False)
        write_sheet("Overview", pd.DataFrame([{
            "Generated At": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Dataset": bundle["meta"].get("name", "-"),
            "Rows": bundle["summary"]["rows"],
            "Columns": bundle["summary"]["cols"],
            "Numeric": bundle["summary"]["numeric"],
            "Category": bundle["summary"]["category"],
            "Missing": bundle["summary"]["missing"],
            "Duplicate": bundle["summary"]["duplicate"],
            "Quality Score": bundle["quality_score"],
            "Quality Label": bundle["quality_label"],
        }]))
        write_sheet("Activity Log", bundle["activity"])
        write_sheet("Upload History", bundle["upload_history"])
        write_sheet("Dataset", df.head(10000))
        write_sheet("Dataset Info", bundle["dataset_info"])
        write_sheet("Missing Summary", bundle["missing_summary"])
        write_sheet("Numeric Stats", bundle["numeric_stats"])
        write_sheet("Categorical Stats", bundle["categorical_stats"])
        write_sheet("Before After", bundle["before_after"])
        write_sheet("Before Cleaning", st.session_state.get("before_df"))
        write_sheet("After Cleaning", st.session_state.get("after_df"))
        write_sheet("Cleaning Log", pd.DataFrame({"Cleaning Log": bundle["cleaning_log"]}))
        write_sheet("Time Series", bundle["time_series"])
        write_sheet("Insights", pd.DataFrame({"Insight": bundle["insights"]}))
        write_sheet("Visualization Index", pd.DataFrame({"Section": [v[0] for v in bundle["visual_sections"]], "Included": [v[1] for v in bundle["visual_sections"]]}))
    buf.seek(0)
    return buf.getvalue()


def _df_report_signature(df):
    try:
        h = int(pd.util.hash_pandas_object(df, index=True).sum())
    except Exception:
        h = hash(str(df.shape) + "|" + "|".join(map(str, df.columns.tolist())))
    return f"{df.shape[0]}x{df.shape[1]}_{h}_{'|'.join(map(str, df.columns.tolist()))[:200]}"


def _report_cache_key(df, theme_mode):
    active = st.session_state.get("active_file") or {}
    return "|".join([
        _df_report_signature(df),
        str(theme_mode),
        str(active.get("name", "-")),
        str(len(st.session_state.get("cleaning_log", []))),
        str(len(st.session_state.get("history", []))),
        str(len(st.session_state.get("activity_log", []))),
    ])


def _get_cached_report_payload(df, theme_mode):
    cache_key = _report_cache_key(df, theme_mode)
    cache = st.session_state.get("report_payload_cache", {})
    if cache.get("key") == cache_key:
        return cache.get("payload"), True

    html_report = generate_html_report(df, theme_mode=theme_mode)
    csv_data = df.to_csv(index=False).encode("utf-8")
    try:
        excel_bytes = generate_excel_report(df, theme_mode=theme_mode)
        excel_error = None
    except Exception as e:
        excel_bytes = None
        excel_error = str(e)
    try:
        pdf_bytes = generate_pdf_report(df, theme_mode=theme_mode)
        pdf_error = None
    except Exception as e:
        pdf_bytes = None
        pdf_error = str(e)

    payload = {
        "html": html_report.encode("utf-8"),
        "csv": csv_data,
        "excel": excel_bytes,
        "excel_error": excel_error,
        "pdf": pdf_bytes,
        "pdf_error": pdf_error,
        "timestamp": datetime.datetime.now().strftime('%Y%m%d_%H%M%S'),
    }
    st.session_state.report_payload_cache = {"key": cache_key, "payload": payload}
    return payload, False


def _download_button_no_rerun(label, data, file_name, mime):
    """Download without triggering a full rerun/loading screen after clicking."""
    try:
        return st.download_button(
            label,
            data,
            file_name=file_name,
            mime=mime,
            use_container_width=True,
            on_click="ignore",
        )
    except TypeError:
        return st.download_button(
            label,
            data,
            file_name=file_name,
            mime=mime,
            use_container_width=True,
        )


def _get_cached_report_format_payload(df, theme_mode, fmt):
    """Generate only the selected report format and cache it.
    This keeps opening the Report page fast; download buttons never rebuild everything."""
    base_key = _report_cache_key(df, theme_mode)
    key = f"{base_key}::{fmt}"
    cache = st.session_state.get("report_format_cache", {})
    if key in cache:
        return cache[key], True

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    if fmt == "html":
        payload = {
            "data": generate_html_report(df, theme_mode=theme_mode).encode("utf-8"),
            "filename": f"eda_complete_report_{ts}.html",
            "mime": "text/html",
        }
    elif fmt == "csv":
        payload = {
            "data": df.to_csv(index=False).encode("utf-8"),
            "filename": f"dataset_cleaned_{ts}.csv",
            "mime": "text/csv",
        }
    elif fmt == "excel":
        payload = {
            "data": generate_excel_report(df, theme_mode=theme_mode),
            "filename": f"eda_complete_report_{ts}.xlsx",
            "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
    elif fmt == "pdf":
        payload = {
            "data": generate_pdf_report(df, theme_mode=theme_mode),
            "filename": f"eda_complete_report_{ts}.pdf",
            "mime": "application/pdf",
        }
    else:
        raise ValueError("Format report tidak dikenal.")

    cache[key] = payload
    st.session_state.report_format_cache = cache
    return payload, False


def render_report_page(df):
    if df is None:
        st.warning("Belum ada data. Upload file terlebih dahulu.")
        return

    log_activity("Buka Halaman", "Download Report")
    s = dataset_summary(df)
    score, qlabel = data_quality_score(df)
    is_light = "Light" in st.session_state.get("ui_theme", "Dark Mode")
    theme_mode = "light" if is_light else "dark"

    report_css = f"""
    <style>
    .report-summary {{
        border-radius:24px; padding:20px 22px;
        border:1px solid {("rgba(20,121,86,.18)" if is_light else "rgba(139,92,246,.28)")};
        background:{("linear-gradient(135deg, rgba(255,255,255,.76), rgba(223,245,234,.78), rgba(235,241,255,.72))" if is_light else "linear-gradient(135deg, rgba(42,18,88,.92), rgba(30,15,61,.92))")};
        box-shadow:var(--shadow); margin-bottom:22px;
    }}
    .report-summary-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; }}
    .report-stat {{ border-radius:18px; padding:16px 18px; background:{("rgba(255,255,255,.62)" if is_light else "rgba(255,255,255,.055)")}; border:1px solid {("rgba(20,121,86,.16)" if is_light else "rgba(139,92,246,.24)")}; }}
    .report-stat .lbl {{ font-size:11px; font-weight:900; text-transform:uppercase; letter-spacing:1.2px; color:var(--muted); }}
    .report-stat .val {{ margin-top:6px; font-size:28px; font-weight:950; color:var(--text); line-height:1; }}
    .download-card {{ border-radius:24px; padding:22px 22px 20px; min-height:235px; display:flex; flex-direction:column; justify-content:space-between; border:1px solid rgba(255,255,255,.22); box-shadow:0 18px 42px rgba(0,0,0,.16); position:relative; overflow:hidden; }}
    .download-card::after {{ content:""; position:absolute; width:130px; height:130px; border-radius:999px; right:-45px; top:-45px; background:rgba(255,255,255,.25); }}
    .download-card .tiny {{ font-size:11px; font-weight:950; text-transform:uppercase; letter-spacing:1.4px; opacity:.78; margin-bottom:8px; }}
    .download-card h3 {{ margin:0 0 14px 0; font-size:24px !important; font-weight:950 !important; color:#12221a !important; line-height:1.12; }}
    .download-card p {{ margin:0; font-size:14px; font-weight:760; color:rgba(18,34,26,.82); line-height:1.62; }}
    .download-card.dark h3, .download-card.dark p, .download-card.dark .tiny {{ color:white !important; }} .download-card.dark p {{ opacity:.90; }}
    div[data-testid="stDownloadButton"] button {{ margin-top:8px !important; border-radius:15px !important; min-height:44px !important; font-weight:900 !important; border:1px solid var(--stroke) !important; background:var(--panel) !important; color:var(--text) !important; box-shadow:none !important; }}
    .report-loading-panel {{ border-radius:26px; padding:34px 34px; background:{("linear-gradient(135deg,rgba(255,255,255,.72),rgba(219,244,232,.70))" if is_light else "linear-gradient(135deg,rgba(42,18,88,.94),rgba(22,8,53,.94))")}; border:1px solid {("rgba(20,121,86,.22)" if is_light else "rgba(139,92,246,.34)")}; box-shadow:var(--shadow); margin:8px 0 22px; }}
    .report-loading-row {{ display:flex;align-items:center;gap:18px; }}
    .report-loader-circle {{ width:34px;height:34px;border-radius:999px;border:4px solid {("#dbeafe" if is_light else "rgba(255,255,255,.20)")};border-top-color:{("#16a34a" if is_light else "#7c3aed")};animation:spinreport .85s linear infinite; }}
    @keyframes spinreport {{ to {{ transform:rotate(360deg); }} }}
    .report-preview {{ margin:32px 0 34px; padding:22px 24px; border-radius:24px; background:{("linear-gradient(135deg,rgba(255,255,255,.80),rgba(223,245,234,.72))" if is_light else "linear-gradient(135deg,rgba(38,18,81,.92),rgba(21,9,49,.92))")}; border:1px solid {("rgba(20,121,86,.18)" if is_light else "rgba(139,92,246,.28)")}; }}
    .report-preview h4 {{ margin:0 0 8px; color:var(--text); font-weight:950; }}
    .report-preview p, .report-preview li {{ color:var(--text); opacity:.90; font-weight:650; line-height:1.65; }}
    .preview-frame-wrap {{ border-radius:22px; overflow:hidden; border:1px solid var(--stroke); box-shadow:0 16px 40px rgba(0,0,0,.14); margin-top:28px; }}
    div[data-testid="stElementContainer"]:has(.report-preview) + div[data-testid="stElementContainer"] {{ margin-top:28px !important; border-radius:22px !important; overflow:hidden !important; border:1px solid var(--stroke) !important; box-shadow:0 16px 40px rgba(0,0,0,.14) !important; }}
    div[data-testid="stElementContainer"]:has(.report-preview) + div[data-testid="stElementContainer"] iframe {{ border-radius:22px !important; }}
    div[data-testid="stElementContainer"]:has(.report-preview) {{ margin-bottom:6px !important; }}
    @media(max-width:1000px) {{ .report-summary-grid {{ grid-template-columns:repeat(2,1fr); }} }}
    </style>
    """
    st.markdown(report_css, unsafe_allow_html=True)

    st.markdown("## Download Report")
    st.markdown(f"""
    <div class="report-summary"><div class="report-summary-grid">
        <div class="report-stat"><div class="lbl">Total Rows</div><div class="val">{fmt_int(s['rows'])}</div></div>
        <div class="report-stat"><div class="lbl">Columns</div><div class="val">{fmt_int(s['cols'])}</div></div>
        <div class="report-stat"><div class="lbl">Quality Score</div><div class="val">{score}/100</div></div>
        <div class="report-stat"><div class="lbl">Cleaning Ops</div><div class="val">{len(st.session_state.get('cleaning_log', []))}</div></div>
    </div></div>
    """, unsafe_allow_html=True)

    cache_key = _report_cache_key(df, theme_mode)
    has_cache = st.session_state.get("report_payload_cache", {}).get("key") == cache_key
    if not has_cache:
        box = st.empty()
        with box.container():
            st.markdown(f"""
            <div class="report-loading-panel">
              <div class="report-loading-row"><div class="report-loader-circle"></div>
              <div><div style="font-size:20px;font-weight:950;color:var(--text);">Menyusun report lengkap...</div>
              <div style="font-size:13px;font-weight:780;color:var(--muted);margin-top:4px;">Menyiapkan file HTML, CSV, Excel, dan PDF.</div></div></div>
            </div>
            """, unsafe_allow_html=True)
            prog = st.progress(0, text="Loading report 0%")
            for pct, label in [(18, "Mengumpulkan activity log..."), (36, "Menyusun tabel dan insight..."), (58, "Membuat visualisasi report..."), (78, "Menyiapkan file download...")]:
                prog.progress(pct, text=f"Loading report {pct}% · {label}")
                time.sleep(0.08)
            payload, _ = _get_cached_report_payload(df, theme_mode)
            prog.progress(100, text="Loading report 100% · Report siap")
            time.sleep(0.15)
        box.empty()
    else:
        payload, _ = _get_cached_report_payload(df, theme_mode)

    st.markdown("### Pilih Format Download")
    dark_class = "dark" if not is_light else ""
    card_colors = {
        "html": "linear-gradient(135deg,#dff7ff,#d8fbe9)",
        "csv": "linear-gradient(135deg,#e9ddff,#dff7ff)",
        "excel": "linear-gradient(135deg,#dcfce7,#fef3c7)",
        "pdf": "linear-gradient(135deg,#ffe4ef,#e9ddff)",
    }
    if not is_light:
        card_colors = {
            "html": "linear-gradient(135deg,#2563eb,#0891b2)",
            "csv": "linear-gradient(135deg,#7c3aed,#2563eb)",
            "excel": "linear-gradient(135deg,#16a34a,#0f766e)",
            "pdf": "linear-gradient(135deg,#db2777,#7c3aed)",
        }
    format_meta = {
        "html": ("Web Report", "HTML Report", "Report lengkap semua modul web: overview, preview, info, cleaning, statistik, visualisasi dengan insight singkat, time series, insight, history, dan activity log."),
        "csv": ("Clean Dataset", "Dataset CSV", "Export dataset aktif setelah proses cleaning dalam format CSV."),
        "excel": ("Workbook", "Excel Report", "Workbook lengkap dengan banyak sheet: activity, upload, dataset, info, statistik, cleaning, time series, insight."),
        "pdf": ("Document Report", "PDF Report", "Laporan formal final dalam PDF landscape yang memuat ringkasan, tabel, visualisasi, insight, dan identitas dosen pengampu."),
    }
    cards = st.columns(4, gap="medium")
    payload_map = {
        "html": (payload.get("html"), f"eda_complete_report_{payload.get('timestamp','report')}.html", "text/html", "Download HTML"),
        "csv": (payload.get("csv"), f"dataset_cleaned_{payload.get('timestamp','report')}.csv", "text/csv", "Download CSV"),
        "excel": (payload.get("excel"), f"eda_complete_report_{payload.get('timestamp','report')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "Download Excel"),
        "pdf": (payload.get("pdf"), f"eda_complete_report_{payload.get('timestamp','report')}.pdf", "application/pdf", "Download PDF"),
    }
    for fmt, col in zip(["html", "csv", "excel", "pdf"], cards):
        tiny, title, desc = format_meta[fmt]
        with col:
            st.markdown(f'<div class="download-card {dark_class}" style="background:{card_colors[fmt]};"><div><div class="tiny">{tiny}</div><h3>{title}</h3><p>{desc}</p></div></div>', unsafe_allow_html=True)
            data, fname, mime, btn_label = payload_map[fmt]
            err = payload.get(f"{fmt}_error")
            if data:
                _download_button_no_rerun(btn_label, data, fname, mime)
            else:
                st.caption(f"Belum bisa membuat {title}: {err or 'tidak ada data'}")

    st.markdown("### Preview Sebelum Download")
    preview = st.selectbox("Pilih preview format", ["HTML Report", "PDF Report", "Excel Report", "Dataset CSV"], label_visibility="collapsed")
    st.markdown('<div class="report-preview-select-spacer" style="height:18px"></div>', unsafe_allow_html=True)
    if preview == "HTML Report":
        st.markdown('<div class="report-preview"><h4>Preview HTML Report</h4><p>Preview di bawah menampilkan bentuk web report lengkap.</p></div>', unsafe_allow_html=True)
        try:
            html_data = payload.get("html", b"").decode("utf-8", errors="ignore")
            components.html(html_data, height=620, scrolling=True)
        except Exception as e:
            st.caption(f"Preview HTML belum bisa ditampilkan: {e}")
    elif preview == "PDF Report":
        st.markdown("""
        <div class="report-preview"><h4>Preview PDF Report</h4>
        <p>PDF Report dibuat sebagai laporan formal landscape yang konsisten. Isi PDF meliputi overview, activity log, upload history, dataset preview, dataset information, cleaning before/after, statistik numerik/kategorik, seluruh bagian visualisasi statis dengan insight singkat, time series, dan intelligent insight.</p>
        <ul><li>Cocok untuk lampiran tugas dan presentasi.</li><li>Visualisasi dibuat statis supaya PDF ringan dibuka.</li><li>Identitas dosen pengampu dicantumkan di laporan.</li></ul></div>
        """, unsafe_allow_html=True)
    elif preview == "Excel Report":
        st.markdown("""
        <div class="report-preview"><h4>Preview Excel Report</h4>
        <p>Excel Report berisi beberapa sheet terstruktur: Overview, Activity Log, Upload History, Dataset, Dataset Info, Missing Summary, Numeric Stats, Categorical Stats, Before/After, Cleaning Log, Time Series, Insights, dan Visualization Index.</p></div>
        """, unsafe_allow_html=True)
        st.dataframe(activity_log_df().head(20), use_container_width=True, height=260)
    else:
        st.markdown("""
        <div class="report-preview"><h4>Preview Dataset CSV</h4>
        <p>CSV berisi dataset aktif yang sedang dipakai di dashboard, termasuk hasil setelah proses data cleaning bila operasi cleaning sudah dijalankan.</p></div>
        """, unsafe_allow_html=True)
        st.dataframe(df.head(25), use_container_width=True, height=360)


# ══════════════════════════════════════════════════════
#  HOME DASHBOARD
# ══════════════════════════════════════════════════════
def plot_dtype_donut(df):
    counts = df.dtypes.astype(str).value_counts()
    is_light = "Light" in st.session_state.get("ui_theme","🌙 Dark Mode")
    bg = "#f8f5ff" if is_light else "#1a0a3e"
    text_color = "#1e0a4a" if is_light else "#f0eeff"
    fig, ax = plt.subplots(figsize=(4, 3), facecolor=bg)
    ax.set_facecolor(bg)
    colors = ["#7c3aed","#06b6d4","#f59e0b","#10b981","#f43f5e","#a78bfa"]
    wedges, texts, autotexts = ax.pie(
        counts.values, labels=counts.index.astype(str), autopct="%1.0f%%",
        startangle=90, pctdistance=0.72,
        wedgeprops={"width":0.48,"edgecolor":bg,"linewidth":2},
        colors=colors[:len(counts)])
    for t in texts: t.set_color(text_color); t.set_fontsize(8); t.set_fontweight("bold")
    for t in autotexts: t.set_color("white"); t.set_fontsize(7); t.set_fontweight("bold")
    plt.tight_layout(pad=0.5)
    return fig


def _summary_paragraph(df, s):
    """Short natural-language summary of the dataset."""
    lines = []
    lines.append(f"Dataset memiliki **{s['rows']:,} baris** dan **{s['cols']} kolom** "
                 f"({s['numeric']} numerik, {s['category']} kategorik).")
    if s["missing"]:
        pct = s["missing"] / max(s["rows"]*s["cols"],1) * 100
        lines.append(f"Terdapat **{s['missing']:,} nilai kosong** ({pct:.1f}%) — cleaning disarankan.")
    else:
        lines.append("Tidak ada nilai kosong — dataset bersih.")
    if s["duplicate"]:
        lines.append(f"Ditemukan **{s['duplicate']} baris duplikat**.")
    return " ".join(lines)


def render_home_dashboard():
    df = st.session_state.df
    meta = st.session_state.active_file or {}
    s = dataset_summary(df)
    score, qlabel = data_quality_score(df)
    insights = build_initial_intelligent_insights(df)
    is_light = "Light" in st.session_state.get("ui_theme", "Dark Mode")
    theme_mode = "light" if is_light else "dark"

    num_cols = df.select_dtypes(include="number").columns.tolist() if df is not None else []
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist() if df is not None else []

    if "dash_num_col" not in st.session_state or st.session_state.dash_num_col not in num_cols:
        st.session_state.dash_num_col = num_cols[0] if num_cols else None
    if "dash_cat_col" not in st.session_state or st.session_state.dash_cat_col not in cat_cols:
        st.session_state.dash_cat_col = cat_cols[0] if cat_cols else None

    sel_num = st.session_state.dash_num_col
    sel_cat = st.session_state.dash_cat_col

    if is_light:
        bg_main = "radial-gradient(circle at 2% 8%, rgba(23,121,83,.25), transparent 30%), radial-gradient(circle at 90% 10%, rgba(91,141,239,.20), transparent 34%), linear-gradient(135deg,#cbeedd 0%,#f8fff9 48%,#dceaff 100%)"
        text_main = "#10281f"
        text_mute = "#526f63"
        card_bg = "rgba(255,255,255,.78)"
        card_bdr = "rgba(20,121,86,.16)"
        panel_bg = "linear-gradient(145deg, rgba(255,255,255,.82), rgba(232,249,240,.74))"
        accent = "#16a34a"
        accent2 = "#06b6d4"
        nav_active = "linear-gradient(135deg,#16a34a,#0f766e)"
        kpi_colors = ["#16a34a", "#06b6d4", "#f59e0b", "#10b981", "#ec4899"]
        donut_bg = "rgba(255,255,255,.0)"
    else:
        bg_main = "linear-gradient(135deg,#2e1065 0%,#1e0a4a 45%,#150732 100%)"
        text_main = "#f3efff"
        text_mute = "#a9a0d0"
        card_bg = "rgba(31,15,68,.90)"
        card_bdr = "rgba(139,92,246,.28)"
        panel_bg = "linear-gradient(145deg, rgba(39,18,85,.94), rgba(19,8,48,.92))"
        accent = "#7c3aed"
        accent2 = "#22d3ee"
        nav_active = "linear-gradient(135deg,#7c3aed,#4c1d95)"
        kpi_colors = ["#7c3aed", "#22d3ee", "#f59e0b", "#10b981", "#ec4899"]
        donut_bg = "rgba(255,255,255,.0)"

    st.markdown(f"""
    <style>
    .stApp {{ background:{bg_main} !important; }}
    .block-container {{ padding-top:.6rem !important; padding-left:.8rem !important; padding-right:.8rem !important; max-width:100% !important; }}
    .pf-brand {{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:12px;}}
    .pf-brand-left {{display:flex;align-items:center;gap:12px;}}
    .pf-logo {{width:44px;height:44px;border-radius:16px;background:{nav_active};display:flex;align-items:center;justify-content:center;color:#fff;font-weight:950;box-shadow:0 14px 32px rgba(0,0,0,{'.16' if is_light else '.36'});}}
    .pf-title-main {{font-size:22px;font-weight:950;color:{text_main};letter-spacing:-.4px;}}
    .pf-sub-main {{font-family:JetBrains Mono,monospace;font-size:12px;font-weight:950;letter-spacing:2.2px;color:{'#0f5132' if is_light else '#d8c8ff'};text-transform:uppercase;text-shadow:{'none' if is_light else '0 0 14px rgba(139,92,246,.35)'};}}
    .pf-stat-strip {{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin:10px 0 18px;}}
    .pf-stat-mini {{
        border-radius:20px;
        padding:16px 20px;
        min-height:86px;
        background:linear-gradient(135deg, var(--stat-main) 0%, var(--stat-soft) 100%);
        border:1px solid var(--stat-border);
        box-shadow:0 12px 30px rgba(0,0,0,{'.07' if is_light else '.24'});
        display:flex;
        flex-direction:column;
        justify-content:center;
        position:relative;
        overflow:hidden;
    }}
    .pf-stat-mini:after {{
        content:"";
        position:absolute;
        width:92px;
        height:92px;
        right:-32px;
        top:-38px;
        border-radius:999px;
        background:rgba(255,255,255,{'.38' if is_light else '.07'});
        pointer-events:none;
    }}
    .pf-stat-label {{font-size:12px;font-weight:950;color:{'#ffffff' if not is_light else '#062e22'};position:relative;z-index:1;text-shadow:{'0 1px 8px rgba(0,0,0,.30)' if not is_light else '0 1px 8px rgba(255,255,255,.35)'};}}
    .pf-stat-value {{font-size:23px;font-weight:950;color:{'#ffffff' if not is_light else '#062e22'};line-height:1.1;position:relative;z-index:1;margin-top:6px;text-shadow:{'0 1px 10px rgba(0,0,0,.25)' if not is_light else '0 1px 8px rgba(255,255,255,.32)'};}}
    .pf-nav-row [data-testid="stButton"]>button {{border-radius:999px!important;min-height:40px!important;font-size:12px!important;font-weight:950!important;text-transform:uppercase!important;letter-spacing:.6px!important;background:{card_bg}!important;color:{text_main}!important;border:1px solid {card_bdr}!important;box-shadow:none!important;}}
    .pf-nav-row [data-testid="stButton"]>button[kind="primary"] {{background:{nav_active}!important;color:#fff!important;border:none!important;box-shadow:0 10px 24px rgba(0,0,0,{'.12' if is_light else '.32'})!important;}}
    .pf-panel-title {{font-size:22px;font-weight:950;color:{text_main};margin-bottom:3px;letter-spacing:-.2px;}}
    .pf-panel-sub {{font-size:13px;font-weight:760;color:{text_mute};margin-bottom:12px;}}
    .pf-pill {{display:inline-flex;align-items:center;border-radius:999px;padding:6px 12px;font-size:12px;font-weight:900;background:{'rgba(22,163,74,.11)' if is_light else 'rgba(124,58,237,.20)'};color:{text_main};border:1px solid {card_bdr};}}
    .pf-kpi-grid {{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin:16px 0;}}
    .pf-kpi-card {{border-radius:22px;padding:18px 20px;min-height:116px;background:{panel_bg};border:1px solid {card_bdr};box-shadow:0 16px 42px rgba(0,0,0,{'.08' if is_light else '.25'});position:relative;overflow:hidden;}}
    .pf-kpi-card:after {{content:"";position:absolute;right:-38px;top:-46px;width:120px;height:120px;border-radius:999px;background:rgba(255,255,255,{'.42' if is_light else '.06'});}}
    .pf-kpi-val {{font-size:30px;font-weight:950;line-height:1;color:{text_main};margin-top:18px;}}
    .pf-kpi-lbl {{font-size:11px;font-weight:950;letter-spacing:1.15px;color:{text_mute};text-transform:uppercase;}}
    .pf-row {{display:flex;align-items:center;justify-content:space-between;padding:11px 0;border-bottom:1px solid {card_bdr};gap:12px;}}
    .pf-row:last-child {{border-bottom:none;}}
    .pf-row span {{font-size:13px;font-weight:850;color:{text_mute};}}
    .pf-row b {{font-size:14px;font-weight:950;color:{text_main};}}
    .pf-col-icon {{display:none !important;}}
    .pf-summary {{border-radius:16px;padding:14px 16px;border:1px solid {card_bdr};background:{'rgba(255,255,255,.52)' if is_light else 'rgba(255,255,255,.045)'};font-weight:780;line-height:1.7;color:{text_main};}}
    .pf-ins-row {{display:flex;gap:10px;align-items:flex-start;padding:8px 0;color:{text_main};font-weight:760;}}
    .pf-ins-dot {{width:8px;height:8px;border-radius:99px;flex-shrink:0;margin-top:8px;background:{accent};}}
    @media(max-width:1100px){{.pf-stat-strip,.pf-kpi-grid{{grid-template-columns:repeat(2,minmax(0,1fr));}}}}
    </style>
    """, unsafe_allow_html=True)

    team_av = "".join([_member_avatar_html(m, size=34, border_color=(accent if is_light else "#7c3aed")) for m in TEAM_MEMBERS])
    st.markdown(
        f'<div class="pf-brand"><div class="pf-brand-left"><div class="pf-logo">◇</div><div>'
        f'<div class="pf-title-main">Auto EDA Insight</div><div class="pf-sub-main">{COURSE_LINE}</div>'
        f'</div></div><div style="display:flex;gap:7px;align-items:center;">' + team_av + '</div></div>',
        unsafe_allow_html=True,
    )

    miss_pct_total = (s["missing"] / max(s["rows"] * s["cols"], 1) * 100) if df is not None else 0
    stat_items = [
        ("Total Rows", fmt_int(s["rows"]), kpi_colors[0]),
        ("Columns", str(s["cols"]), kpi_colors[1]),
        ("Missing Rate", f"{miss_pct_total:.1f}%", kpi_colors[2]),
        ("Quality Score", f"{score}/100", kpi_colors[3]),
    ]
    stat_html = "".join([
        f'<div class="pf-stat-mini" style="--stat-main:{c};--stat-soft:{c}33;--stat-border:{c}22;"><div class="pf-stat-label">{lbl}</div><div class="pf-stat-value">{val}</div></div>'
        for lbl, val, c in stat_items
    ])
    st.markdown('<div class="pf-stat-strip">' + stat_html + '</div>', unsafe_allow_html=True)

    nav_pages = [
        ("🏠 Dashboard", "Dashboard"), ("🧹 Data Cleaning", "Cleaning"),
        ("📈 Statistik — Numerik", "Num Stats"), ("📊 Statistik — Kategorik", "Cat Stats"),
        ("📉 Visualisasi Numerik", "Num Viz"), ("🔗 Bivariate & Multivariat", "Bivariate"),
        ("💡 Insights", "Insights"), ("📄 Download Report", "Report"),
    ]
    st.markdown('<div class="pf-nav-row">', unsafe_allow_html=True)
    nav_cols = st.columns(len(nav_pages), gap="small")
    for col, (dest, label) in zip(nav_cols, nav_pages):
        if col.button(label, key=f"topnav_{dest}", use_container_width=True, type="primary" if st.session_state.active_page == dest else "secondary"):
            st.session_state.active_page = dest
            st.session_state._scroll_to_main = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # Main overview keeps the previous dashboard layout, but panels are native containers so text and box stay unified.
    r1a, r1b = st.columns([3.2, 1.05], gap="medium")
    with r1a:
        with st.container(border=True):
            miss_pct = (s["missing"] / max(s["rows"] * s["cols"], 1) * 100) if df is not None else 0
            st.markdown(
                '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;margin-bottom:8px;">'
                '<div><div class="pf-panel-title">Visual Overview Dataset</div><div class="pf-panel-sub">Histogram dan tipe data dalam satu panel agar dashboard terlihat menyatu.</div></div>'
                '<div style="display:flex;gap:8px;flex-wrap:wrap;">'
                f'<span class="pf-pill">Valid {100-miss_pct:.0f}%</span><span class="pf-pill">Missing {miss_pct:.0f}%</span>'
                '</div></div>',
                unsafe_allow_html=True,
            )
            c_hist, c_dtype = st.columns([1.65, 1.0], gap="medium")
            with c_hist:
                if df is not None and sel_num:
                    try:
                        fig_hist = plot_histogram(df, sel_num, theme=theme_mode)
                        fig_hist.update_layout(height=310, margin=dict(l=30, r=10, t=38, b=34), title=f"Distribusi — {sel_num}")
                        st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": True, "responsive": True})
                    except Exception as e:
                        st.caption(f"Chart error: {e}")
                else:
                    st.markdown('<div class="notice-info">Upload data dan pilih kolom numerik untuk melihat histogram.</div>', unsafe_allow_html=True)
            with c_dtype:
                if df is not None:
                    try:
                        dtype_counts = df.dtypes.astype(str).value_counts().reset_index()
                        dtype_counts.columns = ["Tipe Data", "Jumlah"]
                        colors = (["#16a34a", "#06b6d4", "#f59e0b", "#7c3aed", "#ec4899"] if is_light else ["#7c3aed", "#22d3ee", "#f59e0b", "#10b981", "#ec4899"])
                        fig_dtype = px.pie(dtype_counts, names="Tipe Data", values="Jumlah", hole=.52, title="Tipe Data", color_discrete_sequence=colors)
                        fig_dtype.update_traces(textposition="inside", textinfo="percent+label")
                        fig_dtype.update_layout(height=310, margin=dict(l=5, r=5, t=38, b=5), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=text_main, size=12), legend=dict(orientation="h", y=-.06, x=0))
                        st.plotly_chart(fig_dtype, use_container_width=True, config={"displayModeBar": True, "responsive": True})
                    except Exception as e:
                        st.caption(f"Chart error: {e}")
                else:
                    st.markdown('<div class="notice-info">Upload data untuk melihat komposisi tipe data.</div>', unsafe_allow_html=True)
    with r1b:
        st.markdown(
            f'<div style="border-radius:28px;padding:24px;background:{nav_active};color:#fff;box-shadow:0 20px 46px rgba(0,0,0,{.12 if is_light else .35});min-height:365px;display:flex;flex-direction:column;justify-content:space-between;">'
            '<div><div style="font-size:12px;font-weight:950;letter-spacing:1.6px;text-transform:uppercase;opacity:.82;">Quality Score</div>'
            f'<div style="font-size:46px;font-weight:950;line-height:1.05;margin-top:12px;">{score}<span style="font-size:18px;">/100</span></div>'
            f'<div style="font-size:13px;font-weight:850;margin-top:4px;opacity:.88;">{qlabel}</div></div>'
            f'<div><div style="height:7px;border-radius:999px;background:rgba(255,255,255,.25);overflow:hidden;margin:16px 0;"><div style="height:100%;width:{score}%;background:white;border-radius:999px;"></div></div>'
            f'<div style="font-size:12px;font-weight:850;line-height:1.9;opacity:.9;">{fmt_int(s["rows"])} baris · {s["cols"]} kolom<br>{fmt_int(s["missing"])} missing · {fmt_int(s["duplicate"])} duplikat<br>{meta.get("name", "Belum ada dataset")[:28]}</div></div></div>',
            unsafe_allow_html=True,
        )

    kpi_data = [("Rows", fmt_int(s["rows"])), ("Columns", fmt_int(s["cols"])), ("Numerik", str(s["numeric"])), ("Kategorik", str(s["category"])), ("Missing", fmt_int(s["missing"]))]
    kpi_html = "".join([f'<div class="pf-kpi-card" style="border-left:4px solid {kpi_colors[i%len(kpi_colors)]};"><div class="pf-kpi-val" style="color:{kpi_colors[i%len(kpi_colors)]};">{val}</div><div class="pf-kpi-lbl">{lbl}</div></div>' for i, (lbl, val) in enumerate(kpi_data)])
    st.markdown('<div class="pf-kpi-grid">' + kpi_html + '</div>', unsafe_allow_html=True)

    r2a, r2b, r2c = st.columns([1.25, 1.65, 1.45], gap="medium")
    with r2a:
        with st.container(border=True):
            st.markdown(f'<div class="pf-panel-title">{sel_num or "Kolom numerik"}</div><div class="pf-panel-sub">Statistik ringkas</div>', unsafe_allow_html=True)
            if df is not None and sel_num:
                vals = pd.to_numeric(df[sel_num], errors="coerce").dropna()
                if len(vals):
                    rows = [("Mean", f"{vals.mean():.2f}", kpi_colors[0]), ("Median", f"{vals.median():.2f}", kpi_colors[1]), ("Std", f"{vals.std():.2f}", kpi_colors[2]), ("Min", f"{vals.min():.2f}", kpi_colors[3]), ("Max", f"{vals.max():.2f}", kpi_colors[4])]
                    st.markdown("".join([f'<div class="pf-row"><span>{k}</span><b style="color:{c};">{v}</b></div>' for k, v, c in rows]), unsafe_allow_html=True)
                else:
                    st.markdown('<div class="notice-info">Kolom numerik tidak memiliki nilai valid.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="notice-info">Pilih kolom numerik.</div>', unsafe_allow_html=True)
    with r2b:
        with st.container(border=True):
            st.markdown(f'<div class="pf-panel-title">Top Nilai — {sel_cat or "Kolom kategori"}</div><div class="pf-panel-sub">6 kategori terbanyak</div>', unsafe_allow_html=True)
            if df is not None and sel_cat:
                vc = df[sel_cat].astype(str).value_counts().head(6).reset_index()
                vc.columns = [sel_cat, "count"]
                fig_top = px.bar(vc, x="count", y=sel_cat, orientation="h", color=sel_cat, color_discrete_sequence=["#7c3aed", "#8b5cf6", "#a78bfa", "#06b6d4", "#67e8f9", "#c4b5fd"], text="count")
                fig_top.update_layout(height=300, margin=dict(l=8, r=8, t=8, b=26), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=text_mute, size=11), showlegend=False, xaxis_title=None, yaxis_title=None)
                fig_top.update_yaxes(autorange="reversed")
                fig_top.update_layout(margin=dict(l=70, r=18, t=18, b=48))
                st.plotly_chart(fig_top, use_container_width=True, config={"displayModeBar": False, "responsive": True})
            else:
                st.markdown('<div class="notice-info">Pilih kolom kategorik.</div>', unsafe_allow_html=True)
    with r2c:
        with st.container(border=True):
            st.markdown('<div class="pf-panel-title">Ringkasan Kolom</div><div class="pf-panel-sub">Statistik per kolom numerik</div>', unsafe_allow_html=True)
            if df is not None and num_cols:
                rows_html = ""
                for i, colname in enumerate(num_cols[:6]):
                    vals = pd.to_numeric(df[colname], errors="coerce").dropna()
                    meanv = f"{vals.mean():,.1f}" if len(vals) else "—"
                    clr = kpi_colors[i % len(kpi_colors)]
                    rows_html += f'<div class="pf-row" style="border-left:4px solid {clr}; padding-left:12px;"><div style="display:flex;align-items:center;gap:10px;"><b>{colname[:18]}</b></div><b>{meanv}</b></div>'
                st.markdown(rows_html, unsafe_allow_html=True)
            else:
                st.markdown('<div class="notice-info">Upload data untuk melihat ringkasan kolom.</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    r3a, r3b = st.columns([1.0, 1.65], gap="medium")
    with r3a:
        with st.container(border=True):
            st.markdown('<div class="pf-panel-title">Kontrol Visualisasi</div><div class="pf-panel-sub">Pilih kolom, chart dashboard akan ikut berubah</div>', unsafe_allow_html=True)
            if num_cols:
                new_num = st.selectbox("Kolom Numerik (chart utama)", num_cols, index=num_cols.index(sel_num) if sel_num in num_cols else 0, key="dash_num_sel")
                if new_num != st.session_state.dash_num_col:
                    st.session_state.dash_num_col = new_num
                    st.rerun()
            if cat_cols:
                new_cat = st.selectbox("Kolom Kategorik", cat_cols, index=cat_cols.index(sel_cat) if sel_cat in cat_cols else 0, key="dash_cat_sel")
                if new_cat != st.session_state.dash_cat_col:
                    st.session_state.dash_cat_col = new_cat
                    st.rerun()
    with r3b:
        with st.container(border=True):
            summary_txt = _summary_paragraph(df, s) if df is not None else "Upload dataset untuk melihat ringkasan."
            st.markdown('<div class="pf-panel-title">Ringkasan & Insights</div><div class="pf-panel-sub">Rangkuman otomatis dataset kamu</div>', unsafe_allow_html=True)
            st.markdown('<div class="pf-summary">' + strip_decorative_emoji(summary_txt).replace("**", "") + '</div>', unsafe_allow_html=True)
            dot_colors = ["#7c3aed", "#06b6d4", "#10b981", "#f97316", "#ec4899", "#f59e0b"]
            rows = "".join([f'<div class="pf-ins-row"><div class="pf-ins-dot" style="background:{dot_colors[i%len(dot_colors)]};"></div><div>{strip_decorative_emoji(ins).replace("**", "")}</div></div>' for i, ins in enumerate(insights[:4])])
            st.markdown(rows, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
#  FILE PROCESSING
# ══════════════════════════════════════════════════════
def process_uploaded_file(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    sig = f"{uploaded_file.name}:{len(file_bytes)}"
    if st.session_state.last_upload_signature == sig and st.session_state.df is not None:
        return st.session_state.df, None, None
    raw_dir = BASE_DIR/"data"/"raw"; raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir/uploaded_file.name).write_bytes(file_bytes)
    # Use a fresh BytesIO so seek/read always works regardless of Streamlit state
    file_like = io.BytesIO(file_bytes)
    file_like.name = uploaded_file.name
    df_new, text_content, err = load_file(file_like)
    if err: return None, text_content, err
    ext = uploaded_file.name.split(".")[-1].upper()
    st.session_state.active_file = {"name":uploaded_file.name,"format":ext,"size_bytes":len(file_bytes),"saved_path":str(Path("data")/"raw"/uploaded_file.name),"uploaded_at":datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}
    st.session_state.last_upload_signature = sig
    if df_new is not None:
        st.session_state.df = df_new; st.session_state.df_original = df_new.copy()
        st.session_state.cleaning_log = []
        st.session_state.cleaning_notice = ""
        st.session_state.before_snap = st.session_state.after_snap = st.session_state.before_df = st.session_state.after_df = None
        st.session_state.history.append({"name":uploaded_file.name,"rows":df_new.shape[0],"cols":df_new.shape[1],"time":datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),"df":df_new.copy(),"meta":st.session_state.active_file.copy()})
        log_activity("Upload Dataset", f"{uploaded_file.name} ({df_new.shape[0]} baris × {df_new.shape[1]} kolom)")
    return df_new, text_content, None


# ══════════════════════════════════════════════════════
#  INSIGHT HELPERS — short, data-driven takeaways per chart type
# ══════════════════════════════════════════════════════
def _fmt_num(x):
    try:
        return f"{x:,.2f}"
    except Exception:
        return str(x)
 
def insight_histogram(series, col):
    if series.empty: return "Tidak ada data valid untuk dianalisis."
    skew = series.skew() if len(series) > 2 else 0
    if abs(skew) < 0.5:
        shape = "relatif simetris (mendekati distribusi normal)"
    elif skew > 0:
        shape = "menjulur ke kanan (right-skewed), banyak nilai rendah dengan beberapa outlier tinggi"
    else:
        shape = "menjulur ke kiri (left-skewed), banyak nilai tinggi dengan beberapa outlier rendah"
    return f"Distribusi **{col}** {shape} (skewness={skew:.2f}). Rata-rata {_fmt_num(series.mean())}, median {_fmt_num(series.median())}."
 
def insight_boxplot(series, col):
    if series.empty: return "Tidak ada data valid untuk dianalisis."
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n_out = ((series < low) | (series > high)).sum()
    if n_out > 0:
        return f"Terdeteksi **{n_out}** potensi outlier ({n_out/len(series)*100:.1f}% dari data) pada **{col}**, di luar rentang IQR [{_fmt_num(low)}, {_fmt_num(high)}]."
    return f"Tidak ditemukan outlier signifikan pada **{col}** berdasarkan metode IQR."
 
def insight_violin(series, col):
    if series.empty: return "Tidak ada data valid untuk dianalisis."
    mean, median = series.mean(), series.median()
    skew = series.skew() if len(series) > 2 else 0
    spread = "lebar" if series.std() > series.mean() * 0.5 else "cukup sempit"
    shape = "simetris" if abs(skew) < 0.5 else ("condong kanan (right-skewed)" if skew > 0 else "condong kiri (left-skewed)")
    return f"Sebaran nilai **{col}** tergolong {spread} (std dev {_fmt_num(series.std())}). Mean ({_fmt_num(mean)}) dan median ({_fmt_num(median)}) mengindikasikan bentuk distribusi {shape} (skewness={skew:.2f})."
 
def insight_density(series, col):
    if series.empty or series.nunique() <= 1: return "Data tidak cukup variatif untuk disimpulkan."
    skew = series.skew() if len(series) > 2 else 0
    return f"Kurva densitas **{col}** menunjukkan satu puncak utama (unimodal) dengan kemiringan (skewness) {skew:.2f}, {'mendekati simetris' if abs(skew) < 0.5 else ('condong kanan' if skew > 0 else 'condong kiri')}."
 
def insight_qq(series, col):
    if len(series) < 3: return "Data tidak cukup untuk QQ plot."
    skew = series.skew()
    if abs(skew) < 0.5:
        return f"Titik-titik pada QQ plot **{col}** mendekati garis diagonal, mengindikasikan distribusi mendekati normal."
    return f"Titik-titik pada QQ plot **{col}** menyimpang dari garis diagonal di bagian ekor, mengindikasikan distribusi tidak normal (skewness={skew:.2f})."
 
def insight_bar_count(vc, col):
    if vc.empty: return "Tidak ada data valid untuk dianalisis."
    total = vc.sum()
    top_val, top_count = vc.index[0], vc.iloc[0]
    top_pct = top_count / total * 100
    dominance = "sangat dominan" if top_pct > 60 else "cukup dominan" if top_pct > 35 else "tidak terlalu dominan"
    return f"Kategori **'{top_val}'** {dominance} pada **{col}** dengan {top_pct:.1f}% dari total data ({fmt_int(int(top_count))} baris)."
 
def insight_pie(vc, col):
    if vc.empty: return "Tidak ada data valid untuk dianalisis."
    total = vc.sum()
    top_pct = vc.iloc[0] / total * 100
    n_cat = len(vc)
    return f"Dari **{n_cat}** kategori teratas pada **{col}**, kategori **'{vc.index[0]}'** menguasai {top_pct:.1f}% pangsa data."
 
def insight_pareto(vc, col):
    if vc.empty: return "Tidak ada data valid untuk dianalisis."
    cum_pct = (vc.cumsum() / vc.sum() * 100)
    n_80 = int((cum_pct <= 80).sum()) + 1
    n_80 = min(n_80, len(vc))
    return f"Sekitar **{n_80}** dari {len(vc)} kategori teratas pada **{col}** sudah menyumbang ±80% dari total data (prinsip Pareto 80/20)."
 
def insight_corr_heatmap(df, num_cols):
    try:
        corr = df[num_cols].corr(numeric_only=True)
        pairs = corr.abs().where(~np.eye(len(corr), dtype=bool)).stack()
        if pairs.empty: return "Tidak cukup variabel numerik untuk menghitung korelasi."
        top_pair = pairs.idxmax()
        top_val = corr.loc[top_pair[0], top_pair[1]]
        direction = "positif" if top_val > 0 else "negatif"
        return f"Korelasi terkuat antar variabel numerik: **{top_pair[0]}** & **{top_pair[1]}** (r={top_val:.2f}, {direction})."
    except Exception:
        return "Korelasi belum dapat dihitung dari kolom numerik yang tersedia."
 
def insight_scatter(df, x_col, y_col):
    try:
        xy = df[[x_col, y_col]].apply(pd.to_numeric, errors="coerce").dropna()
        if len(xy) < 2: return "Data tidak cukup untuk menghitung hubungan."
        r = xy[x_col].corr(xy[y_col])
        strength = "kuat" if abs(r) > 0.7 else "moderat" if abs(r) > 0.3 else "lemah"
        direction = "positif" if r > 0 else "negatif"
        return f"Hubungan antara **{x_col}** dan **{y_col}** tergolong {strength} dan {direction} (r={r:.2f})."
    except Exception:
        return "Hubungan antar variabel belum dapat disimpulkan."
 
def insight_pair_plot(df, cols):
    return insight_corr_heatmap(df, cols)
 
def insight_regression(df, x_col, y_col):
    try:
        xy = df[[x_col, y_col]].apply(pd.to_numeric, errors="coerce").dropna()
        if len(xy) < 2: return "Data tidak cukup untuk regresi linear."
        slope, intercept, r, p, _ = scipy_stats.linregress(xy[x_col], xy[y_col])
        r2 = r * r
        fit = "sangat baik" if r2 > 0.7 else "cukup baik" if r2 > 0.3 else "kurang baik"
        return f"Model regresi linear **{y_col}** terhadap **{x_col}** memiliki R²={r2:.3f} (kecocokan {fit}). Setiap kenaikan 1 unit {x_col}, {y_col} berubah sekitar {slope:.3f}."
    except Exception:
        return "Model regresi belum dapat dihitung dari data yang tersedia."
 
def insight_bubble(df, x_col, y_col, size_col):
    base = insight_scatter(df, x_col, y_col)
    if size_col:
        return f"{base} Ukuran bubble merepresentasikan besaran **{size_col}**."
    return base
 
def insight_cat_num(df, cat_col, num_col):
    try:
        agg = df.groupby(cat_col)[num_col].mean().sort_values(ascending=False)
        if agg.empty: return "Data tidak cukup untuk dibandingkan antar kategori."
        top_cat, top_mean = agg.index[0], agg.iloc[0]
        low_cat, low_mean = agg.index[-1], agg.iloc[-1]
        gap = ((top_mean - low_mean) / abs(low_mean) * 100) if low_mean != 0 else 0
        return f"Rata-rata **{num_col}** tertinggi pada kategori **'{top_cat}'** ({_fmt_num(top_mean)}), terendah pada **'{low_cat}'** ({_fmt_num(low_mean)}) — selisih sekitar {gap:.0f}%."
    except Exception:
        return "Perbandingan antar kategori belum dapat disimpulkan."
 
 
# ══════════════════════════════════════════════════════
#  MAIN DASHBOARD ROUTER
# ══════════════════════════════════════════════════════
def show_loading(label="Memuat..."):
    st.markdown(f'<div class="eda-card"><div style="font-weight:800;">{label}</div><div class="prog-track"><div class="prog-fill" style="width:100%;"></div></div></div>', unsafe_allow_html=True)
 
def main_dashboard():
    render_sidebar()
    menu = st.session_state.active_page

    # Keep the successful-login notification only on Dashboard. It remains visible
    # until the user closes it or navigates to another page.
    if menu != "🏠 Dashboard":
        st.session_state.pop("login_success_msg", None)
    login_msg = st.session_state.get("login_success_msg") if menu == "🏠 Dashboard" else None
    if login_msg:
        is_light_toast = "Light" in st.session_state.get("ui_theme", "Dark Mode")
        toast_bg = "linear-gradient(135deg,#dff8ec,#dcecff)" if is_light_toast else "linear-gradient(135deg,#178b77,#6d28d9)"
        toast_text = "#083b2d" if is_light_toast else "#ffffff"
        toast_border = "rgba(20,121,86,.28)" if is_light_toast else "rgba(255,255,255,.22)"
        st.markdown(f"""
        <style>
        #login-toast-dismiss {{ position:fixed; opacity:0; pointer-events:none; }}
        #login-toast-dismiss:checked + .login-floating-toast {{ display:none !important; }}
        .login-floating-toast {{
            position:fixed; top:78px; right:22px; z-index:999999;
            width:min(330px,calc(100vw - 42px)); padding:14px 44px 14px 17px;
            border-radius:16px; background:{toast_bg}; color:{toast_text};
            border:1px solid {toast_border}; box-shadow:0 16px 40px rgba(0,0,0,.24);
            font-size:13.5px; font-weight:900; line-height:1.45; letter-spacing:-.05px;
            animation:toastIn .32s ease-out both;
        }}
        .login-toast-close {{
            position:absolute; top:8px; right:9px; width:28px; height:28px; border-radius:9px;
            display:flex; align-items:center; justify-content:center; cursor:pointer;
            color:{toast_text}; font-family:Arial,sans-serif; font-size:22px; font-weight:500; line-height:1;
            background:rgba(255,255,255,.12); transition:background .18s ease, transform .18s ease;
        }}
        .login-toast-close:hover {{ background:rgba(255,255,255,.24); transform:scale(1.04); }}
        @keyframes toastIn {{ from {{ transform:translateY(-10px); opacity:0; }} to {{ transform:translateY(0); opacity:1; }} }}
        @media(max-width:720px) {{ .login-floating-toast {{ top:68px; right:12px; }} }}
        </style>
        <input type="checkbox" id="login-toast-dismiss" aria-label="Tutup notifikasi login">
        <div class="login-floating-toast">
            <label for="login-toast-dismiss" class="login-toast-close" title="Tutup">×</label>
            {_safe_html(login_msg)}
        </div>
        """, unsafe_allow_html=True)
    if st.session_state.get("last_logged_page") != menu:
        log_activity("Buka Halaman", clean_ui_label(menu))
        st.session_state.last_logged_page = menu
    with st.container():
        st.markdown('<div id="main-anchor"></div>', unsafe_allow_html=True)
        scroll_to_main()
        df = st.session_state.df
 
        if menu == "🏠 Dashboard":
            render_home_dashboard()
 
        elif menu == "📤 Upload Data":
            st.markdown("## Upload Data")
            st.caption("Upload dataset CSV, Excel, JSON, atau TXT.")
            uploaded = st.file_uploader("Drag & drop file di sini", type=["csv","xlsx","xls","json","txt"], label_visibility="collapsed")
            if uploaded:
                progress_box = st.empty()
                progress = st.progress(0, text=f"Uploading {uploaded.name} ...")
                try:
                    for pct, label in [(20, "Menerima file..."), (45, "Membaca struktur dataset..."), (70, "Mendeteksi tipe data...")]:
                        progress.progress(pct, text=f"{label}")
                        time.sleep(0.08)
                    with progress_box.container():
                        show_loading(f"Memproses dataset: {uploaded.name}")
                    df_new, text_c, err = process_uploaded_file(uploaded)
                    progress.progress(100, text="Dataset berhasil diproses.")
                    time.sleep(0.08)
                finally:
                    progress.empty()
                    progress_box.empty()
 
                if err: st.error(f"{err}")
                elif df_new is not None:
                    st.markdown(f'<div class="notice-success"><b>{uploaded.name}</b> — {df_new.shape[0]} baris × {df_new.shape[1]} kolom berhasil diupload.</div>', unsafe_allow_html=True)
                    render_paginated_table(df_new, key="upload_preview", page_size_default=10, height=380)
                    st.button("Lihat Dashboard", use_container_width=True, on_click=go_to, args=("🏠 Dashboard",))
                elif text_c:
                    st.markdown('<div class="notice-success">File teks berhasil dimuat.</div>', unsafe_allow_html=True)
                    st.text_area("Isi File", text_c, height=300)
            else:
                st.markdown('<div class="notice-info">Pilih file untuk memulai analisis.</div>', unsafe_allow_html=True)
 
        elif menu == "👁️ Data Preview":
            if df is None: st.warning("Upload file terlebih dahulu.")
            else:
                st.markdown("## Data Preview")
                render_paginated_table(df, key="data_preview", page_size_default=25, height=520)
 
        elif menu == "📌 Dataset Info":
            if df is None: st.warning("Upload file terlebih dahulu.")
            else:
                st.markdown("## Dataset Information")
                s = dataset_summary(df)
                cols = st.columns(6, gap="medium")
                for cw, item in zip(cols, [("","Rows",s["rows"]),("","Columns",s["cols"]),("","Numeric",s["numeric"]),("","Category",s["category"]),("","Missing",s["missing"]),("","Duplicate",s["duplicate"])]):
                    with cw: st.markdown(metric_card(*item), unsafe_allow_html=True)
                st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
                dtype_df = pd.DataFrame({"Column":df.columns,"Data Type":df.dtypes.astype(str).values,"Non-Null":df.notnull().sum().values,"Null":df.isnull().sum().values,"Null %":(df.isnull().sum()/len(df)*100).round(2).astype(str).values+"%","Sample":[str(df[c].dropna().iloc[0]) if df[c].dropna().shape[0]>0 else "—" for c in df.columns]})
                render_paginated_table(dtype_df, key="dataset_info", page_size_default=25, height=480)
 
        elif menu == "🧹 Data Cleaning":
            if df is None: st.warning("Upload file terlebih dahulu.")
            else: render_cleaning_page(df)
 
        elif menu == "📈 Statistik — Numerik":
            if df is None: st.warning("Upload file terlebih dahulu.")
            else:
                st.markdown("## Statistik Deskriptif — Numerik")
                stats = numeric_stats(df)
                if stats.empty: st.info("Tidak ada kolom numerik.")
                else: render_paginated_table(stats, key="numeric_stats", page_size_default=50, height=620)
 
        elif menu == "📊 Statistik — Kategorik":
            if df is None: st.warning("Upload file terlebih dahulu.")
            else:
                st.markdown("## Statistik Deskriptif — Kategorik")
                stats = categorical_stats(df)
                if stats.empty: st.info("Tidak ada kolom kategorik.")
                else: render_paginated_table(stats, key="categorical_stats", page_size_default=50, height=620)
 
        elif menu == "📉 Visualisasi Numerik":
            if df is None: st.warning("Upload file terlebih dahulu.")
            else:
                num_cols = df.select_dtypes(include="number").columns.tolist()
                if not num_cols: st.info("Tidak ada kolom numerik.")
                else:
                    theme_mode = "light" if "Light" in st.session_state.get("ui_theme", "🌙 Dark Mode") else "dark"
                    st.markdown("## Visualisasi Numerik")
                    st.markdown('<div class="viz-card"><b>Pilih kolom numerik untuk eksplorasi visual interaktif yang lebih rapi dan mudah dibaca.</b></div>', unsafe_allow_html=True)
                    col_sel = st.selectbox("Pilih Kolom Numerik", num_cols)
                    series = df[col_sel].dropna()
                    m1,m2,m3,m4 = st.columns(4, gap="medium")
                    m1.markdown(metric_card("Σ","Non-null",len(series)), unsafe_allow_html=True)
                    m2.markdown(metric_card("μ","Mean",f"{series.mean():.2f}" if len(series) else 0), unsafe_allow_html=True)
                    m3.markdown(metric_card("M","Median",f"{series.median():.2f}" if len(series) else 0), unsafe_allow_html=True)
                    m4.markdown(metric_card("","Missing",int(df[col_sel].isna().sum())), unsafe_allow_html=True)
                    chart_tabs = st.tabs(["Histogram","Boxplot","Violin","Density","QQ Plot"])
                    with chart_tabs[0]:
                        st.plotly_chart(plot_histogram(df, col_sel, theme=theme_mode), use_container_width=True)
                        st.info(insight_histogram(series, col_sel))
                    with chart_tabs[1]:
                        st.plotly_chart(plot_boxplot(df, col_sel, theme=theme_mode), use_container_width=True)
                        st.info(insight_boxplot(series, col_sel))
                    with chart_tabs[2]:
                        st.plotly_chart(plot_violin(df, col_sel, theme=theme_mode), use_container_width=True)
                        st.info(insight_violin(series, col_sel))
                    with chart_tabs[3]:
                        st.plotly_chart(plot_density(df, col_sel, theme=theme_mode), use_container_width=True)
                        st.info(insight_density(series, col_sel))
                    with chart_tabs[4]:
                        st.plotly_chart(plot_qq(df, col_sel, theme=theme_mode), use_container_width=True)
                        st.info(insight_qq(series, col_sel))
 
        elif menu == "🎨 Visualisasi Kategorik":
            if df is None: st.warning("Upload file terlebih dahulu.")
            else:
                cat_cols = df.select_dtypes(include=["object","category","bool"]).columns.tolist()
                if not cat_cols: st.info("Tidak ada kolom kategorik.")
                else:
                    theme_mode = "light" if "Light" in st.session_state.get("ui_theme", "🌙 Dark Mode") else "dark"
                    st.markdown("## Visualisasi Kategorik")
                    col_sel = st.selectbox("Pilih Kolom Kategorik", cat_cols)
                    m1,m2,m3 = st.columns(3)
                    m1.markdown(metric_card("","Unique",df[col_sel].nunique()), unsafe_allow_html=True)
                    m2.markdown(metric_card("","Top Value",str(df[col_sel].mode().iloc[0])[:18] if not df[col_sel].mode().empty else "-"), unsafe_allow_html=True)
                    m3.markdown(metric_card("","Missing",int(df[col_sel].isna().sum())), unsafe_allow_html=True)
                    vc_full = df[col_sel].astype(str).fillna("Missing").value_counts()
                    chart_tabs = st.tabs(["Bar Chart", "Count Plot", "Pie Chart", "Pareto Chart"])
                    with chart_tabs[0]:
                        st.plotly_chart(plot_bar(df, col_sel, theme=theme_mode), use_container_width=True)
                        st.info(insight_bar_count(vc_full, col_sel))
                    with chart_tabs[1]:
                        st.plotly_chart(plot_count(df, col_sel, theme=theme_mode), use_container_width=True)
                        st.info(insight_bar_count(vc_full, col_sel))
                    with chart_tabs[2]:
                        st.plotly_chart(plot_pie(df, col_sel, theme=theme_mode), use_container_width=True)
                        st.info(insight_pie(vc_full.head(10), col_sel))
                    with chart_tabs[3]:
                        st.plotly_chart(plot_pareto(df, col_sel, theme=theme_mode), use_container_width=True)
                        st.info(insight_pareto(vc_full, col_sel))
 
        elif menu == "🔗 Bivariate & Multivariat":
            if df is None: st.warning("Upload file terlebih dahulu.")
            else:
                num_cols = df.select_dtypes(include="number").columns.tolist()
                if len(num_cols) < 2: st.info("Minimal 2 kolom numerik dibutuhkan.")
                else:
                    theme_mode = "light" if "Light" in st.session_state.get("ui_theme", "🌙 Dark Mode") else "dark"
                    st.markdown("## Bivariate & Multivariat")
                    chart_tabs = st.tabs(["Heatmap Korelasi", "Scatter Plot", "Pair Plot", "Regresi Linear", "Bubble Chart"])
                    with chart_tabs[0]:
                        st.plotly_chart(plot_correlation_heatmap(df, theme=theme_mode), use_container_width=True)
                        st.info(insight_corr_heatmap(df, num_cols))
                    with chart_tabs[1]:
                        c1,c2 = st.columns(2)
                        x_col = c1.selectbox("Kolom X", num_cols, key="scatter_x")
                        y_col = c2.selectbox("Kolom Y", num_cols, index=min(1,len(num_cols)-1), key="scatter_y")
                        st.plotly_chart(plot_scatter(df, x_col, y_col, theme=theme_mode), use_container_width=True)
                        st.info(insight_scatter(df, x_col, y_col))
                    with chart_tabs[2]:
                        st.caption("Pair plot otomatis memakai maksimal 5 kolom numerik pertama agar dashboard tetap ringan.")
                        st.plotly_chart(plot_pair_matrix(df, cols=num_cols[:5], theme=theme_mode), use_container_width=True)
                        st.info(insight_pair_plot(df, num_cols[:5]))
                    with chart_tabs[3]:
                        c1,c2 = st.columns(2)
                        x_col = c1.selectbox("X (Independen)", num_cols, key="reg_x")
                        y_col = c2.selectbox("Y (Dependen)", num_cols, index=min(1,len(num_cols)-1), key="reg_y")
                        st.plotly_chart(plot_regression(df, x_col, y_col, theme=theme_mode), use_container_width=True)
                        st.info(insight_regression(df, x_col, y_col))
                    with chart_tabs[4]:
                        c1,c2,c3 = st.columns(3)
                        x_col = c1.selectbox("Kolom X", num_cols, key="bubble_x")
                        y_col = c2.selectbox("Kolom Y", num_cols, index=min(1,len(num_cols)-1), key="bubble_y")
                        size_col = c3.selectbox("Ukuran Bubble", ["Tidak ada"] + num_cols, index=0, key="bubble_size")
                        size_col = None if size_col == "Tidak ada" else size_col
                        cat_cols_b = df.select_dtypes(include=["object","category","bool"]).columns.tolist()
                        color_col = cat_cols_b[0] if cat_cols_b else None
                        st.plotly_chart(plot_bubble(df, x_col, y_col, size_col=size_col, color_col=color_col, theme=theme_mode), use_container_width=True)
                        st.info(insight_bubble(df, x_col, y_col, size_col))
 
        elif menu == "📦 Kategorik vs Numerik":
            if df is None: st.warning("Upload file terlebih dahulu.")
            else:
                cat_cols = df.select_dtypes(include=["object","category","bool"]).columns.tolist()
                num_cols = df.select_dtypes(include="number").columns.tolist()
                if not cat_cols or not num_cols: st.info("Dibutuhkan minimal 1 kolom kategorik dan 1 numerik.")
                else:
                    theme_mode = "light" if "Light" in st.session_state.get("ui_theme", "🌙 Dark Mode") else "dark"
                    st.markdown("## Kategorik vs Numerik")
                    c1,c2 = st.columns(2)
                    cat_sel = c1.selectbox("Kolom Kategorik", cat_cols)
                    num_sel = c2.selectbox("Kolom Numerik", num_cols)
                    chart_tabs = st.tabs(["Boxplot by Category", "Violin Plot by Category", "Grouped Bar Chart", "Strip Plot"])
                    with chart_tabs[0]:
                        st.plotly_chart(plot_boxplot_by_cat(df, cat_sel, num_sel, theme=theme_mode), use_container_width=True)
                        st.info(insight_cat_num(df, cat_sel, num_sel))
                    with chart_tabs[1]:
                        st.plotly_chart(plot_violin_by_cat(df, cat_sel, num_sel, theme=theme_mode), use_container_width=True)
                        st.info(insight_cat_num(df, cat_sel, num_sel))
                    with chart_tabs[2]:
                        st.plotly_chart(plot_grouped_bar(df, cat_sel, num_sel, theme=theme_mode), use_container_width=True)
                        st.info(insight_cat_num(df, cat_sel, num_sel))
                    with chart_tabs[3]:
                        st.plotly_chart(plot_strip_by_cat(df, cat_sel, num_sel, theme=theme_mode), use_container_width=True)
                        st.info(insight_cat_num(df, cat_sel, num_sel))


        elif menu == "⏱️ Time Series":
            if df is None: st.warning("Upload file terlebih dahulu.")
            else:
                render_universal_time_series(df)

        elif menu == "💡 Insights":
            if df is None: st.warning("Upload file terlebih dahulu.")
            else:
                st.markdown("## Initial Intelligent Insight Generation")
                st.caption("Insight otomatis dibuat dari struktur dataset, kualitas data, missing value, duplikasi, outlier, dan korelasi.")

                initial_insights = build_initial_intelligent_insights(df)
                with st.spinner("Menyusun insight otomatis..."):
                    insights = generate_insights(df)

                s = dataset_summary(df)
                score, qlabel = data_quality_score(df)
                is_light = "Light" in st.session_state.get("ui_theme", "🌙 Dark Mode")
                panel_bg = "#ffffff" if is_light else "#1a1640"
                soft_bg = "#f0faf4" if is_light else "#24104e"
                border = "rgba(22,163,74,.18)" if is_light else "rgba(139,92,246,.28)"
                text_color = "#0a2218" if is_light else "#f4f1ff"
                muted = "#4a6b56" if is_light else "#aaa1d6"

                st.markdown(f"""
                <style>
                .insight-hero {{
                    background: linear-gradient(135deg, {"#dcfce7,#ffffff" if is_light else "#28145f,#180934"});
                    border:1px solid {border};
                    border-radius:22px;
                    padding:20px 22px;
                    box-shadow:0 12px 34px rgba(0,0,0,{".08" if is_light else ".35"});
                    margin-bottom:16px;
                }}
                .insight-grid {{
                    display:grid;
                    grid-template-columns: repeat(4, minmax(0,1fr));
                    gap:12px;
                    margin-top:14px;
                }}
                .insight-mini {{
                    background:{soft_bg};
                    border:1px solid {border};
                    border-radius:16px;
                    padding:14px 15px;
                }}
                .insight-mini .lbl {{
                    color:{muted};
                    font-size:11px;
                    font-weight:900;
                    text-transform:uppercase;
                    letter-spacing:1px;
                }}
                .insight-mini .val {{
                    color:{text_color};
                    font-size:24px;
                    font-weight:950;
                    margin-top:4px;
                }}
                .insight-list {{
                    display:grid;
                    grid-template-columns: repeat(2, minmax(0,1fr));
                    gap:12px;
                    margin-top:10px;
                }}
                .smart-card {{
                    background:{panel_bg};
                    border:1px solid {border};
                    border-radius:18px;
                    padding:15px 16px;
                    min-height:92px;
                    box-shadow:0 8px 22px rgba(0,0,0,{".05" if is_light else ".22"});
                }}
                .smart-card .tag {{
                    display:inline-flex;
                    padding:4px 9px;
                    border-radius:999px;
                    font-size:10px;
                    font-weight:900;
                    letter-spacing:.8px;
                    text-transform:uppercase;
                    margin-bottom:8px;
                }}
                .smart-card .txt {{
                    color:{text_color};
                    font-size:14px;
                    font-weight:750;
                    line-height:1.55;
                }}
                @media(max-width: 1000px) {{
                    .insight-grid {{ grid-template-columns: repeat(2, minmax(0,1fr)); }}
                    .insight-list {{ grid-template-columns: 1fr; }}
                }}
                </style>
                <div class="insight-hero">
                    <div style="display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;">
                        <div>
                            <div style="font-size:22px;font-weight:950;color:{text_color};">Smart Dataset Interpretation</div>
                            </div>
                        </div>
                        <div style="font-size:13px;font-weight:900;color:{text_color};background:{soft_bg};border:1px solid {border};border-radius:999px;padding:8px 13px;">
                            Quality: {score}/100 · {qlabel}
                        </div>
                    </div>
                    <div class="insight-grid">
                        <div class="insight-mini"><div class="lbl">Rows</div><div class="val">{fmt_int(s["rows"])}</div></div>
                        <div class="insight-mini"><div class="lbl">Columns</div><div class="val">{fmt_int(s["cols"])}</div></div>
                        <div class="insight-mini"><div class="lbl">Missing</div><div class="val">{fmt_int(s["missing"])}</div></div>
                        <div class="insight-mini"><div class="lbl">Duplicate</div><div class="val">{fmt_int(s["duplicate"])}</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                color_pool = [
                    ("Overview", "#7c3aed"), ("Quality", "#06b6d4"),
                    ("Cleaning", "#10b981"), ("Pattern", "#f59e0b"),
                    ("Correlation", "#ec4899"), ("Recommendation", "#f97316")
                ]
                cards_html = '<div class="insight-list">'
                all_insights = list(initial_insights[:4]) + list(insights[:6])
                for i, ins in enumerate(all_insights, 1):
                    tag, color = color_pool[(i-1) % len(color_pool)]
                    clean_ins = strip_decorative_emoji(str(ins).replace("**", "").replace("`", ""))
                    cards_html += (
                        f'<div class="smart-card">'
                        f'<div class="tag" style="background:{color}22;color:{color};">{i:02d} · {tag}</div>'
                        f'<div class="txt">{clean_ins}</div>'
                        f'</div>'
                    )
                cards_html += '</div>'
                st.markdown(cards_html, unsafe_allow_html=True)

                st.markdown("### Rekomendasi Lanjutan")
                recs = []
                if s["missing"] > 0:
                    recs.append("Lakukan data cleaning pada missing value sebelum analisis lanjutan.")
                if s["duplicate"] > 0:
                    recs.append("Hapus atau validasi baris duplikat agar hasil statistik tidak bias.")
                if s["numeric"] >= 2:
                    recs.append("Gunakan Bivariate & Multivariat untuk membaca korelasi antar variabel numerik.")
                if s["category"] > 0:
                    recs.append("Gunakan Visualisasi Kategorik untuk melihat kategori yang paling dominan.")
                if not recs:
                    recs.append("Dataset sudah cukup bersih dan siap untuk visualisasi serta pelaporan.")

                for rec in recs:
                    st.markdown(f'<div class="smart-card" style="min-height:unset;margin-bottom:8px;"><div class="txt">{rec}</div></div>', unsafe_allow_html=True)

        elif menu == "📄 Download Report":
            render_report_page(df)

        elif menu == "🗂️ Riwayat Upload":
            st.markdown("## Riwayat Upload")
            history = st.session_state.history
            if not history: st.info("Belum ada file yang pernah diupload di sesi ini.")
            else:
                for i, h in enumerate(reversed(history), 1):
                    with st.expander(f"{h['name']} · {h['time']} · {h['rows']} baris × {h['cols']} kolom"):
                        render_paginated_table(h["df"], key=f"history_{i}", page_size_default=10, height=360)
                        if st.button(f"Muat ulang", key=f"reload_{i}"):
                            st.session_state.df = h["df"].copy()
                            st.session_state.df_original = h["df"].copy()
                            st.session_state.active_file = h.get("meta",{"name":h["name"]})
                            st.session_state.cleaning_log = []
                            st.success(f"Dataset '{h['name']}' dimuat ulang."); st.rerun()


# ══════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════
inject_theme_css()
if not st.session_state.authenticated:
    auth_page()
else:
    main_dashboard()
