# 🐾 USDA Animal Welfare Inspection Pipeline

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

- Identify **critical violations**
- Detect **repeat offenders**
- Analyze violations by **species, facility, and time**

---

## 🧱 System Architecture

### 🔹 1. Scraper (Selenium)
- Automates navigation of USDA APHIS portal
- Downloads inspection report PDFs
- Handles pagination and dynamic content

---

### 🔹 2. Parser (pdfplumber + regex)
- Extracts structured data from PDFs:
  - Facility name  
  - Location  
  - Inspection date  
  - Violation severity  
  - Species  
  - Inspector notes  
- Splits reports into **multiple violation records**

---

### 🔹 3. Database (SQLite)
Normalized schema:

- `facilities`
- `violations`

Features:
- Foreign key relationships  
- Duplicate prevention using constraints  
- Efficient querying  

---

### 🔹 4. Query System (CLI)
Users can query data directly:

```bash
python -m cli.cli --critical
python -m cli.cli --repeat
python -m cli.cli --species deer