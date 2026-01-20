# Weather Data Aggregator
An end-to-end data engineering project that extracts real-time weather data, transforms it for analytical use, and loads it into a data warehouse. The pipeline is orchestrated by Apache Airflow running in Docker and visualized using Grafana.

## Architecture
This project uses a modern containerized arhcitecture:
- Orchestrator: Apache Airflow (Dockerized) schedules and monitors the ETL workflow.
- ETL Logic: Python scripts (`extract`, `transform`, `load`) managed as Airflow tasks.
- Storage:
    - Staging: Local CSV files with timestamped versioning.
    - Warehouse: MySQL database (Containerized).
- Visualization: Grafana (Dockerized) for real-time temperature and dashboard.

## Tech Stack
- Containerization: Docker & Docker Compose
- Orchestration: Apacher Airflow
- Language: Python
- Database: MySQL (data warehouse), PostgresSQL (Airflow metadata)
- Dashboarding: Grafana

## Getting Started
1. Prerequisites
- Docker installed.
- MySQL instance running in Docker.
- API key from OpenWeatherMap.

2. Environment Setup
Create a `.env` file in the project root to store your secret keys. **Do not commit this file to GitHub!**

3. Installation & Run
- Start the entire pipeline with one command: `docker compose up -d --build`

4. Accessing the Services
- Airflow UI: http://localhost:8080
- Grafana Dashboards: http://localhost:3000

# The ETL workflow
## Phase 0: 
1. Get API access:
- Go to OpenWeatherAPI, generate an API key.

2. Environment & dependencies
- Create and active a Python virtual environment in project folder.
- Create a `requirements.txt` file and add the necessary libraries:
    - `python-dotenv`
    - `requests`
    - `pandas`
    - `SQLAlchemy`
    - `mysql-connector-python`
- Install them using `pip install -r requirements.txt`.

3. Configuration (`.env` file):
- In the `.env` file, store your secrets and configurations. **Never commit this file to Git**.

4. Install and run a MySQL server, few options like:
- **Local install**: Download and install MySQL Community Server directly onto machine.
- **Docker**: This is preference, and often the easiest way. Can pull the official MySQL image and run it in a container.

5. Create a database and user:
- Connect to MySQL server using a command-line client or a GUI tool like DBeaver or MySQL Workbench. Run the following SQL commands to create a dedicated database and a user for the application.

## Phase 1: E - Extract (`extract.py`)
- Connect to the OpenWeatherMap API and download the raw weather data for each city. Save this raw data without changing it.
- Logic:
    - Load configuration: Read the secrets from the `.env` file.
    - Prepare a place for raw data: Create a directory to store the output.
    - Loop & fetch:
        - Iterate through your list of cities.
        - For each city, construct the correct API URL. The OpenWeatherMap documentation will show you how.
        - Use the `requests` library to make a GET request to that URL.
    - Check for success: After making the request, check the HTTP status code. If it's `200 OK`, proceed. If not (e.g., `401 Unauthorized`, `404 Not Found`), should handle the error (printing a message, ...).
    - Save the raw data:
        - If the request was successful, get the content of the response, which will be a JSON text string.
        - Save this JSON string to a file.
        - **Important**: Name the file something unique and descriptive. This prevent overwriting data and makes it easy to trace back.

## Phase 2: T - Transform (`transform.py`)
- Read all the raw JSON files, clean them up, select only the necessary data, and structure it into a single, clean table format.
- Logic:
    - **Find raw files**: Get a list of all the `.json` files from the data directory.
    - **Prepare for processed data**: Create a directory to store the processed data
    - **Initialize a data list**: Create an empty Python list. This list will hold your clean data, with each item in the list representing one row (one city's weather reading).
    - **Loop & transform**:
        - Iterate through each raw JSON file.
        - Open the file and parse the JSON content into a Python dictionary.
        - **This is the core transformation work**:
            - Flatten and select: The JSON is nested. Cherry-pick the specific fields you want.
            - Example:
                - `name` -> `city`
                - `dt` -> `timestamp_utc` (it's a Unix timestamp, need to convert it).
                - `main[temp]` -> `temperature_kelvin`
                - `main[humidity]` -> `humidity_percent`
                - `wind[speed]` -> `wind_speed_ms`
                - `weather[0]['description']` -> `weather_description`
            - Enrich/Engineer features: Create new, more useful data from the existing data.
                - Convert `temperature_kelvin` into `temperature_celsius` and `temperature_fahrenheit`. The formulas are easy to find online.
                - Convert the Unix `timestamp_utc` into a human-readable datetime string.
            - Structure: Put all this cleaned data into a single, flat dictionary.
        - Append this clean dictionary to your data list.
    - **Consolidate**: Loop through all files, use `pandas` to convert your list of dictionaries into a DataFrame. This gives a nice tabular structure.
    - **Save the clean data**: Save this single DataFrame to a CSV file in data directory.

## Phase 3: L - Load (`load.py`)
- Take the clean, processed data and load it into its final destination - a database. Use MySQL or any database, personal preference.
    - **Connect to database and create the table**: Use MySQL database. Connect to the `weather_db` and run the `CREATE TABLE` statement once.
    - **Load configuration**: Read the database credentials (`DB_HOST`, `DB_USER`, etc.) from the `.env` file.
    - **Create a database connection engine**: Use SQLAlchemy's `create_engine` function. Construct a special "connection string" (also called a DSN) that tells SQLAlchemy how to find and log into the database. This engine object manages the connection pool to the database efficiently.
    - **Read processed data**: Use `pandas` to read the processed data file into a DataFrame.
    - **Load the data**: Use the powerful `.to_sql()` method from `pandas` to load the DataFrame into the MySQL database.
        - Use the `df.to_sql()` and:
            - `name`: `weather_readings` (must match your table name exactly).
            - `con`: The SQLAlchemy engine object created before.
            - `if_exists`: `'append'` (most important part).
            - `index`: `False` (prevent saving the `pandas` DataFrame index as a column in the SQL table).
        - **Crucially**, use the `if_exists='append'` argument. This tells `pandas` to add the new rows to the table if it already exists, rather than failing or overwriting it. This is what allows to build a historical dataset over time.
