"""
backend/visualization.py
Interactive Plotly-based chart generation functions.
"""
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from scipy.stats import gaussian_kde
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Theme configuration
DARK = {
    "paper": "#1a0845",
    "plot": "#16092f",
    "font": "#f8f7ff",
    "grid": "rgba(255,255,255,0.10)",
    "accent": ["#8b5cf6", "#22d3ee", "#f59e0b", "#10b981", "#ec4899", "#f97316", "#a78bfa", "#34d399"],
    "line": "#60a5fa",
    "line2": "#f59e0b",
}
LIGHT = {
    "paper": "#ffffff",
    "plot": "#f8fffb",
    "font": "#10231a",
    "grid": "rgba(0,0,0,0.10)",
    "accent": ["#4f46e5", "#0891b2", "#f59e0b", "#16a34a", "#e11d48", "#ea580c", "#7c3aed", "#14b8a6"],
    "line": "#2563eb",
    "line2": "#d97706",
}


def _cfg(theme="dark"):
    return LIGHT if str(theme).lower().startswith("light") else DARK


def _style(fig, theme="dark", height=360, legend=True):
    cfg = _cfg(theme)
    fig.update_layout(
        height=height,
        paper_bgcolor=cfg["paper"],
        plot_bgcolor=cfg["plot"],
        font=dict(color=cfg["font"], size=13),
        margin=dict(l=50, r=25, t=60, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1) if legend else dict(),
    )
    fig.update_xaxes(showgrid=True, gridcolor=cfg["grid"], zeroline=False, tickfont=dict(color=cfg["font"]))
    fig.update_yaxes(showgrid=True, gridcolor=cfg["grid"], zeroline=False, tickfont=dict(color=cfg["font"]))
    return fig


# ── Numerical ──────────────────────────────────────────
def plot_histogram(df, col, theme="dark"):
    data = df[col].dropna()
    fig = px.histogram(
        x=data, nbins=25, title=f"Histogram — {col}",
        color_discrete_sequence=[_cfg(theme)["accent"][0]]
    )
    fig.update_traces(marker_line_color="rgba(255,255,255,0.15)", marker_line_width=1, opacity=0.9)
    fig.update_xaxes(title=col)
    fig.update_yaxes(title="Frequency")
    return _style(fig, theme, height=360)


def plot_boxplot(df, col, theme="dark"):
    data = df[col].dropna()
    fig = go.Figure()
    fig.add_trace(go.Box(y=data, name=col, boxmean=True, marker_color=_cfg(theme)["accent"][1]))
    fig.update_layout(title=f"Boxplot — {col}")
    fig.update_yaxes(title=col)
    return _style(fig, theme, height=330)


def plot_violin(df, col, theme="dark"):
    data = df[col].dropna()
    fig = go.Figure()
    fig.add_trace(go.Violin(y=data, name=col, box_visible=True, meanline_visible=True, fillcolor=_cfg(theme)["accent"][4], line_color=_cfg(theme)["accent"][4], opacity=0.7))
    fig.update_layout(title=f"Violin Plot — {col}")
    fig.update_yaxes(title=col)
    return _style(fig, theme, height=330)


def plot_density(df, col, theme="dark"):
    data = pd.to_numeric(df[col], errors="coerce").dropna()
    fig = go.Figure()
    if len(data) >= 2:
        kde = gaussian_kde(data)
        xs = np.linspace(data.min(), data.max(), 250)
        ys = kde(xs)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", fill="tozeroy", line=dict(color=_cfg(theme)["accent"][0], width=3), name="Density"))
    fig.update_layout(title=f"Density Plot — {col}")
    fig.update_xaxes(title=col)
    fig.update_yaxes(title="Density")
    return _style(fig, theme, height=330)


def plot_qq(df, col, theme="dark"):
    data = pd.to_numeric(df[col], errors="coerce").dropna()
    (osm, osr), (slope, intercept, _) = scipy_stats.probplot(data, dist="norm")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=osm, y=osr, mode="markers", marker=dict(color=_cfg(theme)["accent"][0], size=7), name="Data"))
    line_x = np.array(osm)
    line_y = slope * line_x + intercept
    fig.add_trace(go.Scatter(x=line_x, y=line_y, mode="lines", line=dict(color=_cfg(theme)["line2"], width=2.5), name="Reference"))
    fig.update_layout(title=f"QQ Plot — {col}")
    fig.update_xaxes(title="Theoretical Quantiles")
    fig.update_yaxes(title="Sample Quantiles")
    return _style(fig, theme, height=330)


# ── Categorical ────────────────────────────────────────
def _top_counts(df, col, top_n=10):
    vc = df[col].astype(str).fillna("Missing").value_counts().head(top_n)
    return pd.DataFrame({col: vc.index, "Count": vc.values})


def plot_bar(df, col, top_n=10, theme="dark"):
    data = _top_counts(df, col, top_n)
    fig = px.bar(data, x=col, y="Count", title=f"Bar Chart — {col}", color=col, color_discrete_sequence=_cfg(theme)["accent"])
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title=col, tickangle=-25)
    return _style(fig, theme, height=340)


def plot_pie(df, col, top_n=8, theme="dark"):
    data = _top_counts(df, col, top_n)
    fig = px.pie(data, names=col, values="Count", title=f"Pie Chart — {col}", hole=0.35, color_discrete_sequence=_cfg(theme)["accent"])
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _style(fig, theme, height=360)


def plot_pareto(df, col, top_n=10, theme="dark"):
    data = _top_counts(df, col, top_n)
    data["Cumulative %"] = data["Count"].cumsum() / data["Count"].sum() * 100
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=data[col], y=data["Count"], name="Count", marker_color=_cfg(theme)["accent"][0]), secondary_y=False)
    fig.add_trace(go.Scatter(x=data[col], y=data["Cumulative %"], name="Cumulative %", mode="lines+markers", line=dict(color=_cfg(theme)["line2"], width=3)), secondary_y=True)
    fig.update_layout(title=f"Pareto Chart — {col}")
    fig.update_xaxes(title=col, tickangle=-25)
    fig.update_yaxes(title_text="Count", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative %", secondary_y=True, range=[0, 105])
    return _style(fig, theme, height=340)


# ── Bivariate / Multivariate ───────────────────────────
def plot_scatter(df, x_col, y_col, theme="dark"):
    data = df[[x_col, y_col]].dropna()
    fig = px.scatter(data, x=x_col, y=y_col, title=f"Scatter Plot — {x_col} vs {y_col}", color_discrete_sequence=[_cfg(theme)["accent"][1]], opacity=0.75)
    fig.update_traces(marker=dict(size=8))
    return _style(fig, theme, height=380)


def plot_correlation_heatmap(df, theme="dark"):
    num_df = df.select_dtypes(include="number")
    corr = num_df.corr(numeric_only=True)
    fig = px.imshow(corr, text_auto=".2f", aspect="auto", color_continuous_scale="RdYlGn", zmin=-1, zmax=1, title="Correlation Heatmap")
    return _style(fig, theme, height=max(360, 80 + 45 * len(corr)))


def plot_regression(df, x_col, y_col, theme="dark"):
    data = df[[x_col, y_col]].dropna()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data[x_col], y=data[y_col], mode="markers", name="Data", marker=dict(color=_cfg(theme)["accent"][0], size=8, opacity=0.7)))
    if len(data) >= 2:
        slope, intercept, r, p, _ = scipy_stats.linregress(data[x_col], data[y_col])
        xs = np.linspace(data[x_col].min(), data[x_col].max(), 200)
        ys = slope * xs + intercept
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", name=f"Regresi (R²={r**2:.3f})", line=dict(color=_cfg(theme)["line2"], width=3)))
    fig.update_layout(title=f"Regresi Linear — {x_col} vs {y_col}")
    fig.update_xaxes(title=x_col)
    fig.update_yaxes(title=y_col)
    return _style(fig, theme, height=380)


# ── Categorical vs Numerical ───────────────────────────
def plot_boxplot_by_cat(df, cat_col, num_col, top_n=8, theme="dark"):
    top_cats = df[cat_col].astype(str).value_counts().head(top_n).index.tolist()
    data = df[df[cat_col].astype(str).isin(top_cats)][[cat_col, num_col]].dropna().copy()
    data[cat_col] = data[cat_col].astype(str)
    fig = px.box(data, x=cat_col, y=num_col, color=cat_col, title=f"Boxplot — {num_col} by {cat_col}", color_discrete_sequence=_cfg(theme)["accent"])
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title=cat_col, tickangle=-25)
    return _style(fig, theme, height=360)


def plot_grouped_bar(df, cat_col, num_col, top_n=8, theme="dark"):
    top_cats = df[cat_col].astype(str).value_counts().head(top_n).index.tolist()
    data = df[df[cat_col].astype(str).isin(top_cats)].copy()
    grp = data.groupby(cat_col, dropna=False)[num_col].mean().reset_index().sort_values(num_col, ascending=False)
    grp[cat_col] = grp[cat_col].astype(str)
    fig = px.bar(grp, x=cat_col, y=num_col, color=cat_col, title=f"Mean {num_col} by {cat_col}", color_discrete_sequence=_cfg(theme)["accent"])
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title=cat_col, tickangle=-25)
    fig.update_yaxes(title=f"Mean {num_col}")
    return _style(fig, theme, height=360)


# ── Time Series ────────────────────────────────────────
def plot_time_series(df, date_col, val_col, window=7, theme="dark", ma_col=None, title=None, rolling_col=None, trend_col=None, forecast_df=None):
    """Interactive time-series chart with required final-exam elements.

    Includes Time Series Line Chart, Moving Average, Rolling Mean, Trend Line,
    and optional Forecast values when provided.
    """
    base_cols = [date_col, val_col]
    for extra in [ma_col, rolling_col, trend_col]:
        if extra and extra in df.columns and extra not in base_cols:
            base_cols.append(extra)
    ts = df[base_cols].dropna(subset=[date_col, val_col]).sort_values(date_col).copy()
    if ts.empty:
        fig = go.Figure()
        fig.add_annotation(text="Data time series kosong", x=0.5, y=0.5, showarrow=False)
        return _style(fig, theme, height=400)

    if ma_col is None or ma_col not in ts.columns:
        ts["__ma"] = ts[val_col].rolling(window=window, min_periods=1).mean()
        ma_col = "__ma"
    if rolling_col is None or rolling_col not in ts.columns:
        roll_window = max(2, min(window, len(ts)))
        ts["__rolling"] = ts[val_col].rolling(window=roll_window, min_periods=1).mean()
        rolling_col = "__rolling"
    if trend_col is None or trend_col not in ts.columns:
        ts["__trend"] = np.nan
        if len(ts) >= 2:
            x = np.arange(len(ts), dtype=float)
            y = pd.to_numeric(ts[val_col], errors="coerce").astype(float).values
            mask = np.isfinite(y)
            if mask.sum() >= 2:
                slope, intercept = np.polyfit(x[mask], y[mask], 1)
                ts["__trend"] = intercept + slope * x
        trend_col = "__trend"

    fig = go.Figure()
    cfg = _cfg(theme)
    fig.add_trace(go.Scatter(x=ts[date_col], y=ts[val_col], mode="lines+markers", name="Time Series Line", line=dict(color=cfg["line"], width=3), marker=dict(size=7)))
    fig.add_trace(go.Scatter(x=ts[date_col], y=ts[ma_col], mode="lines", name=f"Moving Average ({window})", line=dict(color=cfg["line2"], width=3, dash="dash")))
    if rolling_col in ts.columns:
        fig.add_trace(go.Scatter(x=ts[date_col], y=ts[rolling_col], mode="lines", name="Rolling Mean", line=dict(color=cfg["accent"][3], width=2.6, dash="dot")))
    if trend_col in ts.columns and pd.to_numeric(ts[trend_col], errors="coerce").notna().sum() >= 2:
        fig.add_trace(go.Scatter(x=ts[date_col], y=ts[trend_col], mode="lines", name="Trend Line", line=dict(color=cfg["accent"][4], width=3)))
    if forecast_df is not None:
        try:
            fdf = forecast_df[[date_col, val_col]].dropna().sort_values(date_col)
            if not fdf.empty:
                fig.add_trace(go.Scatter(x=fdf[date_col], y=fdf[val_col], mode="lines+markers", name="Forecast", line=dict(color=cfg["accent"][2], width=3, dash="longdash"), marker=dict(size=8, symbol="diamond")))
        except Exception:
            pass
    fig.update_layout(title=title or f"Time Series — {val_col}")
    fig.update_xaxes(title="Periode")
    fig.update_yaxes(title="Nilai")
    fig = _style(fig, theme, height=460)
    # Give the title, legend, and plot area extra breathing room so the Time Series page does not look cramped.
    fig.update_layout(
        margin=dict(l=60, r=35, t=92, b=62),
        legend=dict(orientation="h", yanchor="bottom", y=1.10, xanchor="right", x=1),
        title=dict(y=0.96)
    )
    return fig


# ── Additional visualizations for final requirement ───────────────
def plot_count(df, col, top_n=12, theme="dark"):
    data = _top_counts(df, col, top_n)
    fig = px.bar(
        data, y=col, x="Count", orientation="h",
        title=f"Count Plot — {col}", color=col,
        color_discrete_sequence=_cfg(theme)["accent"]
    )
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title="Count")
    fig.update_yaxes(title=col, autorange="reversed")
    return _style(fig, theme, height=360)


def plot_pair_matrix(df, cols=None, theme="dark"):
    num_df = df.select_dtypes(include="number").copy()
    if cols is None:
        cols = num_df.columns.tolist()[:5]
    cols = [c for c in cols if c in num_df.columns][:5]
    if len(cols) < 2:
        fig = go.Figure()
        fig.add_annotation(text="Minimal 2 kolom numerik dibutuhkan untuk Pair Plot", x=0.5, y=0.5, showarrow=False)
        return _style(fig, theme, height=360)
    data = num_df[cols].dropna()
    if len(data) > 700:
        data = data.sample(700, random_state=42)
    fig = px.scatter_matrix(data, dimensions=cols, title="Pair Plot — Numeric Relationships", color_discrete_sequence=[_cfg(theme)["accent"][0]])
    fig.update_traces(diagonal_visible=False, marker=dict(size=4, opacity=.65))
    return _style(fig, theme, height=max(430, 95 * len(cols)), legend=False)


def plot_bubble(df, x_col, y_col, size_col=None, color_col=None, theme="dark"):
    cols = [x_col, y_col]
    if size_col and size_col not in cols:
        cols.append(size_col)
    if color_col and color_col not in cols and color_col in df.columns:
        cols.append(color_col)
    data = df[cols].copy()
    data[x_col] = pd.to_numeric(data[x_col], errors="coerce")
    data[y_col] = pd.to_numeric(data[y_col], errors="coerce")
    if size_col:
        data[size_col] = pd.to_numeric(data[size_col], errors="coerce")
    data = data.dropna(subset=[x_col, y_col])
    if len(data) > 1500:
        data = data.sample(1500, random_state=42)
    kwargs = dict(x=x_col, y=y_col, title=f"Bubble Chart — {x_col} vs {y_col}", color_discrete_sequence=_cfg(theme)["accent"])
    if size_col:
        kwargs["size"] = size_col
    if color_col and color_col in data.columns:
        kwargs["color"] = color_col
    fig = px.scatter(data, **kwargs)
    fig.update_traces(marker=dict(opacity=.68, sizemode="area", line=dict(width=.5, color="rgba(255,255,255,.25)")))
    return _style(fig, theme, height=380)


def plot_violin_by_cat(df, cat_col, num_col, top_n=8, theme="dark"):
    top_cats = df[cat_col].astype(str).value_counts().head(top_n).index.tolist()
    data = df[df[cat_col].astype(str).isin(top_cats)][[cat_col, num_col]].copy()
    data[num_col] = pd.to_numeric(data[num_col], errors="coerce")
    data = data.dropna(subset=[cat_col, num_col])
    data[cat_col] = data[cat_col].astype(str)
    fig = px.violin(data, x=cat_col, y=num_col, color=cat_col, box=True, points="outliers", title=f"Violin Plot — {num_col} by {cat_col}", color_discrete_sequence=_cfg(theme)["accent"])
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title=cat_col, tickangle=-25)
    fig.update_yaxes(title=num_col)
    return _style(fig, theme, height=370)


def plot_strip_by_cat(df, cat_col, num_col, top_n=8, theme="dark"):
    top_cats = df[cat_col].astype(str).value_counts().head(top_n).index.tolist()
    data = df[df[cat_col].astype(str).isin(top_cats)][[cat_col, num_col]].copy()
    data[num_col] = pd.to_numeric(data[num_col], errors="coerce")
    data = data.dropna(subset=[cat_col, num_col])
    if len(data) > 1600:
        data = data.sample(1600, random_state=42)
    data[cat_col] = data[cat_col].astype(str)
    fig = px.strip(data, x=cat_col, y=num_col, color=cat_col, title=f"Strip Plot — {num_col} by {cat_col}", color_discrete_sequence=_cfg(theme)["accent"])
    fig.update_traces(jitter=.38, marker=dict(size=7, opacity=.68))
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title=cat_col, tickangle=-25)
    fig.update_yaxes(title=num_col)
    return _style(fig, theme, height=370)
