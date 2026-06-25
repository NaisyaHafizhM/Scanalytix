# Scanalytix

> **Course:** Data Science Programming

> **Lecturer:** Bakti Siregar, M.Sc., CDS.

> **Institution:** Bandung Institute of Science and Technology (ITSB)

> **Group:** 6 

---

## Development Team

| Name                  | Student ID |
| --------------------- | ---------- |
| Dhea Putri Khasanah   | 52250009   |
| Nurul Iffah           | 52250037   |
| Fifi Muthia Pitaloka  | 52250038   |
| Clara Maisie Wanghili | 52250039   |
| Naisya Hafizh Mufidah | 52250040   |

---

## Project Description

Scanalytix is an interactive dashboard built using Streamlit that performs comprehensive and automated Exploratory Data Analysis (EDA). The dashboard enables users to analyze datasets in various formats without requiring advanced programming skills, starting from data upload, cleaning, descriptive statistics, interactive visualizations, and report export in PDF and HTML formats.

Scanalytix acts as a **data health scanner**, automatically exploring datasets and uncovering meaningful insights.

---

## System Requirements

* Python 3.9 or later
* pip (Python package manager)
* Internet connection (required for initial dependency installation)
* Minimum 4GB RAM (8GB recommended for large datasets)

---

## Installation & Running Instructions

### 1. Extract Project

Extract the project zip file into your preferred directory:

```powershell
C:\Users\YourName\Documents\Scanalytix\
```

### 2. Open Terminal / PowerShell

Navigate to the project folder:

```powershell
cd "C:\Users\YourName\Documents\Scanalytix"
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

Main packages include:

* streamlit
* pandas
* numpy
* matplotlib
* plotly
* scipy
* reportlab
* openpyxl

### 4. Run Dashboard

```powershell
streamlit run app.py
```

or

```powershell
python -m streamlit run app.py
```

### 5. Open Browser

Once the server starts, access:

```text
http://localhost:8501
```

---

## Features

### Data Upload

* Support for CSV, Excel (.xlsx/.xls), JSON, and TXT formats
* Automatic delimiter detection
* Automatic JSON parsing
* Fixed-width table parsing
* Encoding detection

### Dataset Preview & Information

* Dataset preview with searchable pagination
* Data type information
* Missing value analysis
* Quality score (0–100)

### Data Cleaning

* Remove duplicates
* Remove missing values
* Fill missing values (Mean, Median, Mode)
* Delete selected columns
* Convert data types
* Before / After comparison
* Cleaning logs

### Descriptive Statistics

* Mean
* Median
* Standard deviation
* Quartiles
* Skewness
* Kurtosis

### Interactive Visualization

#### Numerical Data

* Histogram
* Box Plot
* Violin Plot
* Density Plot
* QQ Plot

#### Categorical Data

* Bar Chart
* Pie Chart
* Pareto Chart
* Count Plot

#### Bivariate & Multivariate

* Scatter Plot
* Correlation Heatmap
* Pair Matrix
* Regression Plot
* Bubble Chart

### Insight Generator

Automatically generates insights based on:

* Data distribution
* Outliers
* Correlation
* Data readiness
* Algorithm recommendations

### Report Export

* PDF Report
* Excel Report
* Interactive reports

---

## Interface

* Dark Mode (Purple/Violet theme)

  <img width="955" height="498" alt="image" src="https://github.com/user-attachments/assets/92766415-2e74-4c9d-a3b2-2aadbc4904bf" />

* Light Mode (Sage Green theme)

  <img width="950" height="500" alt="image" src="https://github.com/user-attachments/assets/1585112e-f3e6-415f-a6c0-0ff7ace59fb5" />

* Collapsible sidebar navigation
* Interactive Plotly visualizations

---

## Notes

* Uploaded datasets are stored temporarily in session only
* Reset functionality is available
* Generated reports include embedded visualizations
* Large tables are automatically split for readability

---

*Scanalytix — Your Data Health Scanner*
