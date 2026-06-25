"""
backend/insight_generator.py
Automated intelligent insight generation from a DataFrame.
"""
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats


def _fmt_int(value):
    try:
        return f"{int(value):,}".replace(",", ".")
    except Exception:
        return str(value)


def _outlier_count(series):
    vals = pd.to_numeric(series, errors="coerce").dropna()
    if len(vals) < 4:
        return 0
    q1, q3 = vals.quantile(0.25), vals.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0 or pd.isna(iqr):
        return 0
    return int(((vals < q1 - 1.5 * iqr) | (vals > q3 + 1.5 * iqr)).sum())


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


def _safe_to_datetime(series):
    try:
        return pd.to_datetime(series, errors="coerce", format="mixed")
    except TypeError:
        return pd.to_datetime(series, errors="coerce")
    except Exception:
        return pd.to_datetime(series.astype(str), errors="coerce")


def _detect_time_col(df):
    hints = ("date", "tanggal", "time", "datetime", "timestamp", "year", "tahun", "month", "bulan", "period", "periode")
    for col in df.columns:
        ser = df[col]
        name = str(col).lower()
        if pd.api.types.is_datetime64_any_dtype(ser):
            return col
        if any(h in name for h in hints):
            parsed = _safe_to_datetime(ser)
            if parsed.notna().mean() >= 0.45:
                return col
        if ser.dtype == "object" or str(ser.dtype).startswith("string"):
            parsed = _safe_to_datetime(ser)
            if parsed.notna().mean() >= 0.65:
                return col
    return None


def _time_series_summary(df):
    col = _detect_time_col(df)
    if col is None:
        return ["Time Series tidak diaktifkan karena dataset tidak memiliki kolom tanggal/datetime yang valid."]
    numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != col]
    work = pd.DataFrame()
    work["date"] = _safe_to_datetime(df[col])
    if numeric_cols:
        val_col = numeric_cols[0]
        work["value"] = pd.to_numeric(df[val_col], errors="coerce")
        value_note = str(val_col)
    else:
        work["value"] = 1
        value_note = "jumlah baris/frekuensi"
    work = work.dropna()
    if work.empty:
        return [f"Kolom waktu {col} terdeteksi, tetapi tidak cukup valid untuk diringkas."]
    grouped = work.groupby(work["date"].dt.to_period("M").dt.to_timestamp())["value"].sum().reset_index()
    grouped.columns = ["periode", "value"]
    if grouped.empty:
        return ["Time Series terdeteksi, tetapi data hasil agregasi kosong."]
    delta = float(grouped["value"].iloc[-1] - grouped["value"].iloc[0]) if len(grouped) >= 2 else 0.0
    direction = "meningkat" if delta > 0 else "menurun" if delta < 0 else "stabil"
    cv = float(grouped["value"].std() / (abs(grouped["value"].mean()) + 1e-9)) if len(grouped) >= 2 else 0.0
    fluct = "tinggi" if cv >= .35 else "sedang" if cv >= .15 else "rendah"
    seasonality = "Belum cukup periode untuk mendeteksi seasonality."
    if len(grouped) >= 24:
        monthly = grouped.groupby(grouped["periode"].dt.month)["value"].mean()
        amp = (monthly.max() - monthly.min()) / (abs(monthly.mean()) + 1e-9)
        if amp >= .25:
            seasonality = f"Terdapat indikasi seasonality; bulan {int(monthly.idxmax())} cenderung paling tinggi."
        else:
            seasonality = "Seasonality tidak terlalu kuat berdasarkan pola bulanan."
    return [
        f"Time Series memakai kolom {col} dan nilai {value_note}; tren cenderung {direction} ({delta:,.2f}).",
        f"Fluktuasi Time Series tergolong {fluct} (CV {cv:.2f}). {seasonality}",
    ]


def generate_insights(df: pd.DataFrame) -> list[str]:
    insights: list[str] = []
    if df is None or df.empty:
        return ["Dataset belum tersedia. Silakan upload dataset terlebih dahulu."]

    total_rows, total_cols = df.shape
    num_df = df.select_dtypes(include=[np.number])
    cat_df = df.select_dtypes(include=["object", "category", "bool"])
    missing_total = int(df.isna().sum().sum())
    duplicate_total = int(df.duplicated().sum())
    total_cells = max(total_rows * total_cols, 1)

    insights.append(f"Dataset memiliki {_fmt_int(total_rows)} baris dan {_fmt_int(total_cols)} kolom ({num_df.shape[1]} numerik, {cat_df.shape[1]} kategorik).")

    if not num_df.empty:
        means = num_df.mean(numeric_only=True).dropna()
        if not means.empty:
            top_mean_col = means.idxmax()
            insights.append(f"Variabel dengan rata-rata tertinggi adalah {top_mean_col} ({means.loc[top_mean_col]:,.2f}).")

    if missing_total > 0:
        missing_pct = missing_total / total_cells * 100
        top_missing = df.isna().sum().sort_values(ascending=False)
        top_missing = top_missing[top_missing > 0].head(3)
        detail = ", ".join([f"{col} ({_fmt_int(val)})" for col, val in top_missing.items()])
        insights.append(f"Variabel dengan missing value terbanyak: {detail}. Total missing {_fmt_int(missing_total)} ({missing_pct:.2f}% dari total sel).")
    else:
        insights.append("Tidak ditemukan missing value pada dataset.")

    if not num_df.empty:
        outlier_counts = {col: _outlier_count(num_df[col]) for col in num_df.columns}
        if outlier_counts:
            top_out = max(outlier_counts, key=outlier_counts.get)
            insights.append(f"Variabel dengan outlier terbanyak adalah {top_out} sebanyak {_fmt_int(outlier_counts[top_out])} data.")

        stds = num_df.std(numeric_only=True).dropna()
        if not stds.empty:
            top_std_col = stds.idxmax()
            insights.append(f"Variabel dengan standar deviasi terbesar adalah {top_std_col} ({stds.loc[top_std_col]:,.4f}).")

        if num_df.shape[1] >= 2:
            corr = num_df.corr(numeric_only=True).abs().copy(deep=True)
            for col in corr.columns:
                corr.loc[col, col] = np.nan
            stacked = corr.stack().dropna()
            if not stacked.empty:
                idx = stacked.idxmax()
                insights.append(f"Korelasi terkuat antara {idx[0]} dan {idx[1]} (r = {stacked.loc[idx]:.3f}).")

        normal, nonnormal = [], []
        for col in num_df.columns[:12]:
            lab, _ = _normality_label(num_df[col])
            if lab == "Normal":
                normal.append(col)
            elif lab == "Tidak normal":
                nonnormal.append(col)
        if normal or nonnormal:
            insights.append("Distribusi normal: " + (", ".join(normal[:4]) if normal else "tidak ada yang kuat") + "; tidak normal: " + (", ".join(nonnormal[:4]) if nonnormal else "tidak ada yang kuat") + ".")
    else:
        insights.append("Dataset belum memiliki kolom numerik untuk statistik lanjutan.")

    if duplicate_total > 0:
        insights.append(f"Ditemukan {_fmt_int(duplicate_total)} baris duplikat. Disarankan menjalankan fitur Data Cleaning.")
    else:
        insights.append("Tidak ditemukan baris duplikat.")

    if not cat_df.empty:
        for col in cat_df.columns[:2]:
            vc = df[col].value_counts(dropna=True)
            if not vc.empty:
                top_val = vc.index[0]
                top_pct = vc.iloc[0] / max(len(df), 1) * 100
                insights.append(f"Kategori dominan pada {col} adalah {top_val} ({top_pct:.1f}% dari baris data).")

    insights.extend(_time_series_summary(df))
    return insights[:14]
