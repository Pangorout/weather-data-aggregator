import os
import json
import pandas as pd
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
raw_dir = os.path.join(project_root, 'data', 'raw')
processed_dir = os.path.join(project_root, 'data', 'processed')

def kelvin_to_celsius(kelvin):
    return kelvin - 273.15

def celsius_to_fahrenheit(celsius):
    return celsius * (9 / 5) + 32

def run():
    print("Starting transformation process...")

    os.makedirs(processed_dir, exist_ok=True)
    if not os.path.exists(raw_dir):
        print(f"Error: Raw data directory not found at '{raw_dir}'.")
        print("Please rerun the extraction script first.")
        return
    
    # Find all files in the directory that end with .json
    json_files = [f for f in os.listdir(raw_dir) if f.endswith('.json')]

    if not json_files:
        print("No raw JSON files found to process.")
        return
    
    # List to hold all the processed data (one dict per file/row)
    all_weather_data = []

    # Loop through files and transforms data
    for file_name in json_files:
        file_path = os.path.join(raw_dir, file_name)

        try:
            with open(file_path, 'r') as f:
                raw_data = json.load(f)

            # Core logic to cherry-pick, clean and create data
            # Extract relevant fields
            city = raw_data.get('name')
            # 'dt' field is a Unix timestamp (seconds since epoch)
            unix_timestamp = raw_data.get('dt')
            # Navigate nested dictionary to get temperature, humidity, etc.
            temp_kelvin = raw_data.get('main', {}).get('temp')
            humidity = raw_data.get('main', {}).get('humidity')
            wind_speed = raw_data.get('wind', {}).get('speed')
            # The 'weather' key holds a list of dicts; take the description from the first one.
            description = raw_data.get('weather', [{}])[0].get('description')

            # Handle potential missing data
            if not all([city, unix_timestamp, temp_kelvin, humidity, wind_speed, description]):
                print(f"Skipping file {file_name} due to missing essential data.")
                continue

            # Enrich the data (create new, more useful fields)
            timestamp_utc = datetime.utcfromtimestamp(unix_timestamp)
            temp_c = kelvin_to_celsius(temp_kelvin)
            temp_f = celsius_to_fahrenheit(temp_c)

            # Structure the clean data into a flat dict
            clean_row = {
                'city': city,
                'timestamp_utc': timestamp_utc.strftime('%Y-%m-%d %H:%M:%S'),
                'temperature_celsius': round(temp_c, 2),
                'temperature_fahrenheit': round(temp_f, 2),
                'humidity_percent': humidity,
                'wind_speed_ms': wind_speed,
                'weather_description': description
            }

            all_weather_data.append(clean_row)
            print(f"Successfully processed {file_name}")

        except json.JSONDecodeError:
            print(f"Error decoding JSON from file: {file_name}")
        except Exception as e:
            print(f"An unexpected error occurred processing {file_name}: {e}")

    # Consolidate and save
    if not all_weather_data:
        print(f"No data was processed. Exiting.")
        return
    
    # Convert the list of dicts to Pandas DF
    df = pd.DataFrame(all_weather_data)


    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name =  f"processed_weather_data_{timestamp}.csv"
    output_path = os.path.join(processed_dir, file_name)

    df.to_csv(output_path, index=False)
    
    print("-" * 50)
    print(f"Transformation completed. Processed {len(df)} records.")
    print(f"Cleaned data saved to: {output_path}")
    print("Preview data:")
    print(df.head())

if __name__ == '__main__':
    run()