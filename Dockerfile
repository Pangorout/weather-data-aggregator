FROM apache/airflow:2.7.1-python3.9

RUN pip install --no-cache-dir \
    pandas \ 
    sqlalchemy \ 
    mysql-connector-python \ 
    requests \ 
    python-dotenv