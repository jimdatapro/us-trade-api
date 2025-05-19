# US Trade API – Python Wrapper for U.S. Census Bureau Trade Data

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`us-trade-api` is a lightweight Python wrapper designed to simplify access to the [U.S. Census Bureau International Trade Data API](https://www.census.gov/foreign-trade/reference/apis/index.html). It helps users construct queries, manage API keys, and convert responses into structured `pandas` DataFrames for analysis.

> 🔑 **Note**: You need a (free) API key from the [U.S. Census Bureau](https://api.census.gov/data/key_signup.html) to use this package.

---

## 🚀 Features

- Easy setup with API key and query parameters
- Supports import/export data fetching (user defines actual API logic)
- Built-in mapping from ISO country codes to Census Bureau country codes
- Processes data into clean, analysis-ready `pandas` DataFrames
- Enriches data with Harmonized System (HS2) commodity codes and descriptions
- Aggregation support by month/year and commodity granularity (HS2 or HS sections)
- Optional inclusion of transportation mode breakdowns:
  - `AIR_VAL_MO` – Air cargo
  - `VES_VAL_MO` – Non-container vessels
  - `CNT_VAL_MO` – Container vessels
- Includes reference CSV files for HS codes and country codes
- Trade values are expressed in USD for both imports and exports

---

## 📦 Installation

Install the latest version from PyPI:

```bash
pip install us-trade-api
