import os
import pandas as pd
import glob
from sqlalchemy import create_engine
from dotenv import load_dotenv

def run():
    print("Starting load process...")

    load_dotenv()

    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    db_port = os.getenv("DB_PORT")

    # Input validation
    if not all([db_host, db_user, db_password, db_name, db_port]):
        print(f"Error: Database credentials not found in .env file.")
        raise Exception("Missing Database Credentials")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    processed_dir = os.path.join(project_root, 'data', 'processed')
    search_pattern = os.path.join(processed_dir, "processed_weather_*.csv") 
    
    # Get a list of all matching files
    print(f"Searching for files at: {search_pattern}")
    list_of_files = glob.glob(search_pattern)
    
    if not list_of_files:
        print(f"Error: No processed files found matching '{search_pattern}'.")
        print(f"Please run (or rerun) transform script.")
        # Raise error so Airflow marks task as failed
        raise FileNotFoundError("No processed CSV files found.")

    # Find the latest file based on creation time
    processed_file_path = max(list_of_files, key=os.path.getctime)
    print(f"Found latest data file: {processed_file_path}")
    
    # Create database connection
    try:
        connection_string = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        engine = create_engine(connection_string)

        with engine.connect() as connection:
            print(f"Successfully connected to MySQL database.")

    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise e # Fail the task if DB connection fails
    
    # Load data into database
    try:
        df = pd.read_csv(processed_file_path)

        if df.empty:
            print("Processed data file is empty. No data to load.")
            return
        
        table_name = "weather_readings"

        df.to_sql(table_name, con=engine, if_exists='append', index=False)

        print("-" * 50)
        print(f"Successfully loaded {len(df)} records into the {table_name}.")

    except FileNotFoundError:
        print(f"Error: The file {processed_file_path} was not found.")
        raise
    except Exception as e:
        print(f"An error occurred during the data loading process: {e}")
        raise e

if __name__ == "__main__":
    run()