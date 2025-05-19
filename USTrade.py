import pandas as pd
import requests
# from datetime import datetime # Not strictly used in the class itself

# Initialize df_country_code_name to None
df_country_code_name = None
df_hs2_ref = None
df_hs2_section = None

try:
    df_country_code_name = pd.read_csv("data/country.csv")
    df_hs2_ref = pd.read_csv("data/hs2_reference.csv", dtype={'HS2': str})
    # hs2_section.csv needs: HS2_Code (2-digit string), Section, Section_Title
    df_hs2_section = pd.read_csv("data/hs2_section.csv", dtype={'HS2_Code': str})
except FileNotFoundError:
    print("Please ensure country.csv, hs2_reference.csv, and hs2_section.csv are in the correct directory.")
except Exception as e:
    print(f"An unexpected error occurred while reading CSV files: {e}")

class USTrade:
    # Removed trade_type from __init__
    def __init__(self, api_key=None, country_iso_code=None, year=None, month=None,
                 aggregation_level_period="month", aggregation_level_granularity="hs2", aggregation_level_transport="yes"):
        self.api_key = api_key
        self.country_iso_code = country_iso_code
        self.year = year
        self.month = month
        self.aggregation_level_period = aggregation_level_period
        self.aggregation_level_granularity = aggregation_level_granularity
        
        if aggregation_level_transport == "all":
            self.aggregation_level_transport = "yes"
        else:
            self.aggregation_level_transport = aggregation_level_transport

    def get_ctry_code(self):
        if df_country_code_name is None:
            return None
        if self.country_iso_code:
            match = df_country_code_name.loc[df_country_code_name['ISO Code'].astype(str).str.upper() == self.country_iso_code.upper(), 'Code']
            if not match.empty:
                country_code = match.values[0]
                return str(country_code)
            else:
               print(f"Warning: Country ISO code '{self.country_iso_code}' not found in country.csv.")
               return None
        return None

    # params() now accepts trade_type as an argument
    def _params(self, trade_type_for_params): 
        if self.api_key is None:
            raise ValueError("API key is required to access the U.S. Census Bureau API.")

        params_dict = {
            "key": self.api_key,
            "COMM_LVL": "HS2"
        }

        get_list_fields = []
        transport_fields_api = ["AIR_VAL_MO", "VES_VAL_MO", "CNT_VAL_MO"]

        # Uses the passed trade_type_for_params
        if trade_type_for_params == "exports":
            base_fields = ["CTY_NAME", "E_COMMODITY", "ALL_VAL_MO"]
            get_list_fields.extend(base_fields)
            get_list_fields.extend(transport_fields_api)
        elif trade_type_for_params == "imports":
            base_fields = ["CTY_NAME", "I_COMMODITY", "GEN_VAL_MO"]
            get_list_fields.extend(base_fields)
            get_list_fields.extend(transport_fields_api)
        else:
            raise ValueError("Internal error: Invalid trade_type provided to _params method.")

        params_dict["get"] = ",".join(list(set(get_list_fields)))

        if self.country_iso_code is not None:
            country_code = self.get_ctry_code()
            if country_code:
                params_dict["CTY_CODE"] = country_code

        if self.year is not None:
            params_dict["YEAR"] = str(self.year)

        if self.month is not None:
            if str(self.month) == "*":
                params_dict["MONTH"] = "*"
            else:
                try:
                    month_num = int(self.month)
                    if 1 <= month_num <= 12:
                        params_dict["MONTH"] = f"{month_num:02d}"
                    else:
                        print(f"Warning: Invalid month number '{self.month}'. Sending as is.")
                        params_dict["MONTH"] = str(self.month)
                except ValueError:
                    print(f"Warning: Invalid month format '{self.month}'. Sending as is.")
                    params_dict["MONTH"] = str(self.month)
        return params_dict

    def _process_data(self, df_raw, commodity_col_api, main_value_col_api):
        if df_raw is None or df_raw.empty:
            return df_raw

        df_processed = df_raw.copy()
        
        transport_value_cols = ["AIR_VAL_MO", "VES_VAL_MO", "CNT_VAL_MO"]
        all_potential_value_cols = [main_value_col_api] + transport_value_cols

        for col in all_potential_value_cols:
            if col in df_processed.columns:
                df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce').fillna(0)
            else: 
                df_processed[col] = 0

        if self.aggregation_level_granularity == "hs2":
            if df_hs2_ref is not None and 'HS2' in df_hs2_ref.columns and 'HS2_Name' in df_hs2_ref.columns:
                df_processed = df_processed.merge(
                    df_hs2_ref[['HS2', 'HS2_Name']], 
                    left_on=commodity_col_api, 
                    right_on="HS2",
                    how="left"
                )
                df_processed = df_processed.drop(columns=[commodity_col_api], errors='ignore')
            else:
                print(f"Warning: df_hs2_ref not loaded or essential columns missing. Original '{commodity_col_api}' will be kept.")
        
        elif self.aggregation_level_granularity == "hs2_section":
            if df_hs2_section is not None and 'HS2_Code' in df_hs2_section.columns and \
               'Section' in df_hs2_section.columns and 'Section_Title' in df_hs2_section.columns:
                df_processed = df_processed.merge(
                    df_hs2_section[['HS2_Code', 'Section', 'Section_Title']], 
                    left_on=commodity_col_api, 
                    right_on="HS2_Code",
                    how="left"
                )
                df_processed = df_processed.drop(columns=[commodity_col_api, 'HS2_Code'], errors='ignore')
            else:
                print(f"Warning: df_hs2_section not loaded or essential columns missing. Original '{commodity_col_api}' will be kept.")

        current_value_cols_to_sum = [main_value_col_api]
        if self.aggregation_level_transport == "yes":
            for tc in transport_value_cols:
                if tc in df_processed.columns:
                     current_value_cols_to_sum.append(tc)
        elif self.aggregation_level_transport == "no":
            cols_to_drop_transport = [col for col in transport_value_cols if col in df_processed.columns]
            if cols_to_drop_transport:
                df_processed = df_processed.drop(columns=cols_to_drop_transport)
        
        if self.aggregation_level_period == "year":
            if "MONTH" in df_processed.columns and "YEAR" in df_processed.columns:
                cols_to_exclude_from_grouping = all_potential_value_cols + ['MONTH']
                grouping_cols = [col for col in df_processed.columns if col not in cols_to_exclude_from_grouping]
                grouping_cols = [gc for gc in grouping_cols if gc in df_processed.columns]

                if not grouping_cols:
                    print("Warning: No valid grouping columns found for year aggregation.")
                else:
                    agg_dict = {val_col: 'sum' for val_col in current_value_cols_to_sum if val_col in df_processed.columns}
                    if agg_dict:
                         df_processed = df_processed.groupby(grouping_cols, as_index=False).agg(agg_dict)
                    else:
                        print("Warning: No value columns to sum for year aggregation. Dropping MONTH and removing duplicates.")
                        df_processed = df_processed.drop(columns=['MONTH'], errors='ignore').drop_duplicates(subset=grouping_cols)
            else:
                print("Warning: 'MONTH' or 'YEAR' column not found for yearly aggregation.")
        
        return df_processed

    def _fetch_and_create_dataframe(self, url, params_for_fetch, trade_type_str_log): # Renamed params to params_for_fetch
        try:
            response = requests.get(url, params=params_for_fetch) # Use params_for_fetch
            if response.status_code == 200:
                if not response.content:
                    print(f"Warning: Received status 200 but no content for {trade_type_str_log}.")
                    return pd.DataFrame()
                try:
                    raw_data = response.json()
                except requests.exceptions.JSONDecodeError:
                    print(f"Error: Failed to decode JSON for {trade_type_str_log}. Response text: {response.text[:200]}...")
                    return None
                
                if not raw_data or len(raw_data) < 2:
                    return pd.DataFrame(columns=raw_data[0] if raw_data and raw_data[0] else [])
                
                api_headers = raw_data[0]
                df_raw = pd.DataFrame(raw_data[1:], columns=api_headers)

                if df_raw.columns.has_duplicates:
                    df_raw = df_raw.loc[:, ~df_raw.columns.duplicated(keep='first')]
                
                return df_raw

            elif response.status_code == 204:
                return pd.DataFrame()
            else:
                print(f"Error fetching {trade_type_str_log} data: {response.status_code}")
                print(f"Response content: {response.text}")
                return None
        except requests.RequestException as e:
            print(f"An error occurred while fetching {trade_type_str_log} data: {e}")
            return None

    def get_exports_data(self):
        export_url = "https://api.census.gov/data/timeseries/intltrade/exports/hs"
        current_params = self._params("exports") # Pass "exports" to _params
        df_exports_raw = self._fetch_and_create_dataframe(export_url, current_params, "exports")
        
        if df_exports_raw is None or df_exports_raw.empty:
            return df_exports_raw 

        return self._process_data(df_exports_raw, "E_COMMODITY", "ALL_VAL_MO")

    def get_imports_data(self):
        import_url = "https://api.census.gov/data/timeseries/intltrade/imports/hs"
        current_params = self._params("imports") # Pass "imports" to _params
        df_imports_raw = self._fetch_and_create_dataframe(import_url, current_params, "imports")

        if df_imports_raw is None or df_imports_raw.empty:
            return df_imports_raw 

        return self._process_data(df_imports_raw, "I_COMMODITY", "GEN_VAL_MO")

