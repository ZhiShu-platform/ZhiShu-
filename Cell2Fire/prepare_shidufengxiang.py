import pandas as pd
import numpy as np
import os

# --- Configuration ---
hourly_data_file = 'shidufengxiang.csv'
output_file = 'dailyshifufengxiang.csv' # Output file for the calculated daily averages

# Define the path to where your hourly data file is located
# Assuming it's in the same directory as this script, or specify full path
# Example: data_dir = '/data/Tiaozhanbei/Cell2Fire/Cell2Fire-main/'
data_dir = '/data/Tiaozhanbei/Cell2Fire/Cell2Fire-main/Input_Landscape'

hourly_data_path = os.path.join(data_dir, hourly_data_file)
output_path = os.path.join(data_dir, output_file)

print(f"Loading hourly data from: {hourly_data_path}")

# --- 1. Load Hourly Data ---
try:
    # The hourly data might be very large, use low_memory=False
    df_hourly = pd.read_csv(hourly_data_path, low_memory=False)
except FileNotFoundError as e:
    print(f"Error: Input file '{hourly_data_file}' not found. Please ensure it's in the '{data_dir}' directory.")
    print(e)
    exit()
except pd.errors.EmptyDataError:
    print("Error: The hourly CSV file is empty.")
    exit()
except Exception as e:
    print(f"An unexpected error occurred while reading the hourly CSV file: {e}")
    exit()

print("Hourly data loaded successfully.")

# --- 2. Preprocess Data and Filter by Date Range ---

print("Converting 'DATE' column and filtering for January 1st to January 25th...")

# Convert 'DATE' to datetime objects
df_hourly['DATE'] = pd.to_datetime(df_hourly['DATE'], errors='coerce')

# Drop rows where DATE could not be parsed
df_hourly.dropna(subset=['DATE'], inplace=True)

# Filter for January 1st to January 25th
start_date = pd.to_datetime('2025-01-01').date() # Assuming year is 2025 based on previous context
end_date = pd.to_datetime('2025-01-25').date()

df_hourly['Day'] = df_hourly['DATE'].dt.date
df_filtered = df_hourly[(df_hourly['Day'] >= start_date) & (df_hourly['Day'] <= end_date)].copy()

if df_filtered.empty:
    print(f"No data found for the period from {start_date} to {end_date}.")
    print("Please check your hourly data file and the specified date range.")
    exit()

# Convert relevant columns to numeric, coercing errors will turn non-numeric into NaN
df_filtered['HourlyRelativeHumidity'] = pd.to_numeric(df_filtered['HourlyRelativeHumidity'], errors='coerce')
df_filtered['HourlyWindDirection'] = pd.to_numeric(df_filtered['HourlyWindDirection'], errors='coerce')

# Drop rows where essential columns are NaN
df_filtered.dropna(subset=['HourlyRelativeHumidity', 'HourlyWindDirection'], inplace=True)

if df_filtered.empty:
    print(f"No valid numerical data for Relative Humidity or Wind Direction found after filtering for {start_date} to {end_date}.")
    exit()

print(f"Filtered data for {start_date} to {end_date}. Proceeding with calculations.")

# --- 3. Calculate Daily Average Relative Humidity ---
print("Calculating daily average Relative Humidity...")
daily_rh = df_filtered.groupby('Day')['HourlyRelativeHumidity'].mean().reset_index()
daily_rh.rename(columns={'HourlyRelativeHumidity': 'Daily_RelativeHumidity_Avg'}, inplace=True)

# --- 4. Calculate Daily Average Wind Direction (Vector Method) ---
print("Calculating daily average Wind Direction (using vector method)...")

# Convert degrees to radians for calculation
df_filtered['WD_rad_sin'] = np.sin(np.deg2rad(df_filtered['HourlyWindDirection']))
df_filtered['WD_rad_cos'] = np.cos(np.deg2rad(df_filtered['HourlyWindDirection']))

daily_wd_components = df_filtered.groupby('Day')[['WD_rad_sin', 'WD_rad_cos']].mean().reset_index()

# Calculate the mean angle from averaged sine and cosine components
daily_wd_components['Daily_WindDirection_Avg'] = np.degrees(np.arctan2(daily_wd_components['WD_rad_sin'], daily_wd_components['WD_rad_cos']))
# Normalize angles to be between 0 and 360 degrees
daily_wd_components['Daily_WindDirection_Avg'] = (daily_wd_components['Daily_WindDirection_Avg'] + 360) % 360

# Select only the 'Day' and 'Daily_WindDirection_Avg' columns
daily_wd = daily_wd_components[['Day', 'Daily_WindDirection_Avg']]

print("Daily averages for RH and WD calculated.")

# --- 5. Combine and Save Results ---
df_results = pd.merge(daily_rh, daily_wd, on='Day', how='left')

# Format 'Day' column to string for cleaner CSV output
df_results['Day'] = df_results['Day'].astype(str)
df_results.rename(columns={'Day': 'Date'}, inplace=True) # Rename 'Day' to 'Date' for clarity

print("\nCalculated Daily Averages Preview:")
print(df_results.head())

df_results.to_csv(output_path, index=False)
print(f"\nDaily average RH and WD for Jan 1st - Jan 25th saved to: {output_path}")
print("\n--- Script Complete ---")