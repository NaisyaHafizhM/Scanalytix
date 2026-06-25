
# Auto EDA Insight Dashboard

> **Mata Kuliah:** Data Science Programming 
> **Dosen Pengampu:** Bakti Siregar, M.Sc., CDS.
> **Institusi:** Institut Teknologi Sains Bandung (ITSB)
> **Kelompok:** 6 — Program Studi Sistem Informasi

---

## Tim Pengembang

| Nama | NIM |
|------|-----|
| Dhea Putri Khasanah | 52250009 |
| Nurul Iffah | 52250037 |
| Fifi Muthia Pitaloka | 52250038 |
| Clara Maisie Wanghili | 52250039 |
| Naisya Hafizh Mufidah | 52250040 |

---

## Deskripsi Proyek

Auto EDA Insight adalah dashboard interaktif berbasis **Streamlit** yang dirancang untuk melakukan **Exploratory Data Analysis (EDA) secara otomatis dan menyeluruh**. Dashboard ini memungkinkan pengguna untuk menganalisis dataset dalam berbagai format tanpa memerlukan keahlian pemrograman mendalam, mulai dari upload data, cleaning, statistik deskriptif, visualisasi interaktif, hingga ekspor laporan dalam format PDF dan HTML.

---

## Persyaratan Sistem

- Python **3.9** atau lebih baru
- pip (Python package manager)
- Koneksi internet (untuk install dependencies pertama kali)
- RAM minimal 4GB (disarankan 8GB untuk dataset besar)

---

## Cara Instalasi & Menjalankan

### 1. Extract Project
Extract file zip ke folder yang diinginkan, misalnya:
C:\Users\NamaKamu\Documents\Auto_EDA_Insight\

### 2. Buka Terminal / PowerShell
Masuk ke folder project:
```powershell
cd "C:\Users\NamaKamu\Documents\Auto_EDA_Insight"
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```
> Pastikan semua package terinstall tanpa error sebelum lanjut. Package utama yang diinstall: 
- `streamlit`, 
- `pandas`,
- `numpy`,
- `matplotlib`,
- `plotly`,
- `scipy`,
- `reportlab`,
- `openpyxl`.

### 4. Jalankan Dashboard
```powershell
streamlit run app.py *atau*
python -m streamlit run app.py
```

### 5. Buka di Browser
Setelah server berjalan, buka browser dan akses:
http://localhost:8501

---

## Akun Login

| Username | Password | Role |
|----------|----------|------|
| `admin` | `eda2026` | Admin |
| `dhea` | `kelompok6` | Member |
| `naisya` | `kelompok6` | Member |
| `iffah` | `kelompok6` | Member |
| `fifi` | `kelompok6` | Member |
| `clara` | `kelompok6` | Member |

> jika belum mempunyai akun, silahkan register terlebih dahulu.

---

## Struktur Folder
Auto_EDA_Insight/

│

├── app.py                        # File utama aplikasi Streamlit

├── requirements.txt              # Daftar dependencies Python

├── README.md                     # Dokumentasi proyek

│

├── backend/                      # Modul logika backend

│   ├── data_loader.py            # Loader untuk CSV, Excel, JSON, TXT

│   ├── preprocessing.py          # Fungsi data cleaning

│   ├── data_cleaning.py          # Wrapper modul cleaning

│   ├── visualization.py          # Fungsi visualisasi

│   ├── statistical_analysis.py   # Statistik deskriptif

│   ├── categorical_analysis.py   # Analisis kategorik

│   ├── time_series_analysis.py   # Analisis time series

│   └── export_report.py          # Ekspor laporan

│

├── frontend/                     # Aset tampilan

│   └── static/

│   └── assets/

│   └── images/

│   └── itsb.png      # Logo ITSB (digunakan di PDF report)

│

├── data/                         # Folder data

│   ├── raw/                      # Dataset mentah (belum diproses)

│   ├── processed/                # Dataset hasil processing

│   └── sample_dataset/           # Contoh dataset untuk testing

│

├── outputs/                      # Hasil ekspor (PDF, Excel)

├── models/                       # Model machine learning (jika ada)

├── docs/                         # Dokumentasi tambahan

└── tests/                        # Unit test

---

##  Fitur Lengkap

###  Upload Data
- Format yang didukung: **CSV, Excel (.xlsx/.xls), JSON, TXT**
- Deteksi delimiter otomatis untuk file TXT (spasi, koma, titik koma, tab, pipe)
- Parsing JSON otomatis — mendukung JSON flat, nested, list-of-dicts, wrapped (misal `{"meta": {...}, "data": [...]}`)
- Parsing fixed-width text table (format pretty-printed dengan garis pemisah `---`)
- Deteksi encoding otomatis (UTF-8, Latin-1, dll)

### Dataset Preview & Info
- Preview seluruh baris dataset dalam tabel paginasi yang bisa dicari
- Informasi lengkap: tipe data, jumlah nilai unik, missing value per kolom
- Missing value summary dengan persentase
- Quality Score otomatis (0–100)

###  Data Cleaning
- **Hapus duplikat** — menghapus baris yang identik
- **Hapus baris missing value** — menghapus semua baris dengan NaN
- **Isi missing value** — pilih metode: Mean, Median, atau Modus (wajib dipilih dulu sebelum dijalankan)
- **Hapus kolom** — pilih kolom spesifik yang ingin dihapus
- **Ubah tipe data** — konversi tipe data kolom (int, float, str, datetime)
- Validasi: operasi "Hapus" dan "Isi" missing value tidak bisa dijalankan bersamaan
- Tampilan **Before / After** otomatis setelah cleaning selesai
- Log cleaning tersimpan per sesi

###  Statistik Deskriptif
- **Numerik:** mean, median, std, min, max, Q1, Q3, skewness, kurtosis
- **Kategorik:** jumlah nilai unik, modus, frekuensi tertinggi, persentase

###  Visualisasi (Interaktif — Plotly)
#### Numerik
- Histogram
- Box Plot
- Violin Plot
- Density Plot (KDE)
- QQ Plot

#### Kategorik
- Bar Chart
- Pie Chart
- Pareto Chart
- Count Plot

#### Bivariate & Multivariate
- Scatter Plot
- Correlation Heatmap
- Pair Plot / Pair Matrix
- Regression Plot
- Bubble Chart

#### Kategorik vs Numerik
- Box Plot by Category
- Violin Plot by Category
- Grouped Bar Chart
- Strip Plot

#### Time Series
- Time Series Line Chart
- Moving Average
- Rolling Mean
- Trend Line

###  Insight Generator
- Insight otomatis berbasis data: distribusi, outlier, korelasi, kesiapan modeling, rekomendasi algoritma

### Export Laporan

#### PDF Report (Makalah Akademik)
- Format **portrait A4**, gaya makalah akademik Indonesia
- **Halaman cover** dengan logo ITSB, nama institusi, dosen pengampu, kelompok, dan seluruh anggota
- **Kata Pengantar**
- **Daftar Isi interaktif** — bisa diklik untuk loncat ke BAB yang dituju
- **BAB I** Pendahuluan (latar belakang, tujuan, ringkasan dataset)
- **BAB II** Pembahasan (aktivitas web, riwayat upload, dataset preview FULL, info dataset, missing value, data cleaning, log, statistik, visualisasi lengkap, time series)
- **BAB III** Penutup (kesimpulan dari insight + saran)
- Footer setiap halaman: identitas kelompok + nomor halaman
- Tabel wide (>8 kolom) otomatis dipecah jadi beberapa chunk portrait
- Seluruh visualisasi dari dashboard di-embed sebagai gambar

#### Excel Report
- Setiap bagian analisis di sheet terpisah

---

##  Tampilan

- **Dark Mode** — tema ungu/violet neon
- **Light Mode** — tema sage green terang
- Sidebar collapsible dengan navigasi per halaman
- Semua visualisasi menggunakan Plotly (interaktif)

---

##  Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `No module named 'reportlab'` | Jalankan `pip install -r requirements.txt` |
| `No module named 'streamlit'` | Jalankan `pip install streamlit` |
| Port 8501 sudah dipakai | Jalankan `streamlit run app.py --server.port 8502` |
| PDF tidak bisa dibuat | Pastikan `reportlab>=4.0.0` terinstall |
| File TXT tidak terbaca | Pastikan file punya header kolom dan format konsisten |
| JSON nested tidak terbaca | Didukung hingga 3 level nested — pastikan ada list-of-dicts di dalamnya |
| Dashboard lambat | Gunakan dataset ≤ 100.000 baris untuk performa optimal |

---

## Catatan

- Semua data yang diupload **hanya tersimpan sementara di session** — tidak disimpan permanen di server
- Reset data bisa dilakukan kapan saja melalui tombol **Reset** di halaman Data Cleaning
- File PDF yang digenerate sudah termasuk semua visualisasi dalam format gambar statis
- Untuk dataset dengan banyak kolom (>8), tabel di PDF otomatis dipecah per 8 kolom agar tetap terbaca di portrait A4

---

*Auto EDA Insight Dashboard — Proyek Akhir Semester 2 UAS Data Science Programming · ITSB · 2026*
=======
# Scanalytix
Your data health scanner, automatically exploring datasets and uncovering meaningful insights.
>>>>>>> 5f140292cd915171f672d850c26b818ec1b37413
