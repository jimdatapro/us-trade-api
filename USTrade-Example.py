from USTrade import USTrade 

# Get your API key from https://api.tradestatistics.io/
# and replace the placeholder below with your actual API key
API_KEY = "YOUR_API_KEY" 

#example 1: Get exports data for a specific month and year
trade_exports_in_month = USTrade(api_key=API_KEY,
                                   year="2020",
                                   month="01",
                                   country_iso_code="GB",
                                   aggregation_level_granularity="hs2",
                                   aggregation_level_transport="yes", 
                                   aggregation_level_period="year")
df_exports_test = trade_exports_in_month.get_exports_data()
if df_exports_test is not None:
    print(df_exports_test.head())
else:
    print("Failed to get data or data is empty.")

#example 2: Get imports data for all months in 2020
trade_imports_in_month = USTrade(api_key=API_KEY,
                                    year="2020",
                                    month="*",
                                    country_iso_code="FR",
                                    aggregation_level_granularity="hs2_section",
                                    aggregation_level_transport="no", 
                                    aggregation_level_period="month")
df_imports_test = trade_imports_in_month.get_imports_data() 
if df_imports_test is not None:
    print(df_imports_test.head())
else:
    print("Failed to get data or data is empty.")