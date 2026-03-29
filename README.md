# 🐾 USDA Animal Welfare Inspection Pipeline

> Converts USDA APHIS inspection PDFs into a structured SQLite database with CLI queries and a live Streamlit dashboard for analyzing animal welfare violations.

## 🌐 Live Demo
👉 https://usda-awa-inspection-pipeline-6vcdb9pwq3ctgbyrazp7yd.streamlit.app/

---

## 📸 Screenshots

### 🏠 Dashboard
<img width="1914" height="897" alt="Screenshot 2026-03-29 091154" src="https://github.com/user-attachments/assets/20d8b224-df5b-4129-9b6b-d7d15822ff7a" />


### 🚨 Critical Violations
<img width="1919" height="907" alt="Screenshot 2026-03-29 091901" src="https://github.com/user-attachments/assets/3e972ebb-0d74-4d46-b021-bf1dd423ee0e" />


### 🔁 Repeat Violations
<img width="1919" height="903" alt="Screenshot 2026-03-29 091210" src="https://github.com/user-attachments/assets/0bda22e7-694e-4964-9b20-0c075fb8b1f2" />


### 🐾 Species Filter
<img width="1919" height="905" alt="Screenshot 2026-03-29 091228" src="https://github.com/user-attachments/assets/84cc50a9-ea1d-4334-b9d4-f049ade8f231" />


---

## 📌 Problem Statement

USDA APHIS publishes Animal Welfare Act (AWA) inspection reports as **unstructured PDFs** behind a web interface.  
These reports contain valuable compliance and violation data, but:

- ❌ Not machine-readable  
- ❌ Difficult to query  
- ❌ Hard to analyze at scale  

👉 This project solves that by converting raw PDFs into a **structured, queryable database**.

---

## 🚀 Solution Overview

This project builds a complete **data pipeline + analytics system**:

> Scraper → PDF Parser → SQLite Database → CLI + Dashboard

It enables users to:

- 🚨 Identify **critical violations**
- 🔁 Detect **repeat offenders**
- 🐾 Analyze violations by **species, facility, and time**


---

## 🌟 Key Features

- ✅ End-to-end pipeline (scraper → parser → database → dashboard)
- ✅ Processes 200+ real inspection reports
- ✅ Detects critical and repeat violations
- ✅ Species-based filtering and analysis
- ✅ CLI + interactive Streamlit dashboard
- ✅ Live deployed application

---
## 🛠 Tech Stack

- Python
- Selenium
- pdfplumber
- SQLite
- Streamlit
- Pandas

---

## 🧱 System Architecture & Product Design

This project is designed as a **complete end-to-end data product**, not just a script.

It transforms unstructured USDA inspection reports into a **usable analytics system for compliance monitoring and decision-making**.

---

### 🔹 1. Scraper (Data Acquisition Layer)

**What it does:**
- Automates USDA APHIS Public Search Tool navigation  
- Downloads inspection report PDFs  
- Handles pagination and dynamic content using Selenium  

**Purpose:**  
➡️ Collect large-scale real-world data (200+ reports) that is otherwise manually inaccessible  

---

### 🔹 2. Parser (Data Processing Layer)

**What it does:**
- Uses `pdfplumber` + regex heuristics to extract:
  - Facility name  
  - Company  
  - Location  
  - Inspection date  
  - Severity (Critical / Non-Critical / Unknown)  
  - Species affected  
  - Inspector notes  
- Splits each PDF into **multiple structured violation records**

**Purpose:**  
➡️ Convert messy, inconsistent PDFs into structured, machine-readable data  

---

### 🔹 3. Database (Storage Layer)

**What it does:**
- SQLite-based normalized schema:
  - `facilities`
  - `violations`
- Prevents duplicate entries  
- Maintains data integrity  

**Purpose:**  
➡️ Enable efficient querying and scalable storage of inspection data  

---

### 🔹 4. Query & Analytics Layer (CLI)

A command-line interface enables users to extract insights quickly:

#### 🚨 Critical Violations
```bash
python -m cli.cli --critical
```

#### 🔁 Repeat Violations

```bash
python -m cli.cli --repeat
```

#### 🐾 Species-based Analysis

```bash
python -m cli.cli --species deer
```

👉 Filters violations by animal type

---

### 🔹 5. Dashboard (User Interface Layer) 🔥

An interactive Streamlit dashboard is provided for non-technical users:

```bash
python -m streamlit run app.py
```

Features:

* 📊 Visual tabular insights
* 🔍 Filters (species, severity)
* ⚡ Real-time querying
* 🌐 Live deployed version

👉 Purpose:
Make the system accessible to analysts, researchers, and policymakers.

---

## 🎯 Product Thinking (Why this matters)

### 👤 Target Users

* Regulatory bodies (USDA / compliance teams)
* Animal welfare organizations
* Researchers & analysts

---

### 💡 Real-world Use Cases

* Identify facilities with repeated violations
* Track critical violations across regions
* Analyze violations by species
* Monitor compliance trends over time

---

### 🚀 Value Delivered

* Converts static PDFs → actionable insights
* Reduces manual effort drastically
* Enables data-driven decision making

---

## 📊 Project Output

* 📄 200+ real inspection reports processed
* 🗄️ Structured SQLite database created
* ⚡ CLI queries for instant insights
* 🌐 Live Streamlit dashboard deployed

---
## ⚙️ How to Run (Quick Start)

```bash
python main.py
python -m cli.cli --critical
python -m streamlit run app.py
```
