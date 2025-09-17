from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook
 
def extract():
    data = {"id":[1,2,3,4,5], "amount":[100,200,300,400,500]}
    df = pd.DataFrame(data)
    df.to_csv("/data/sales.csv", index=False)

def transform():
    df = pd.read_csv("/data/sales.csv")
    df["tax"] = df["amount"] * 1.2
    df.to_csv("/data/transformed.csv", index=False)

def load():
    hook = PostgresHook(postgres_conn_id="postgres_dbms")
    conn = hook.get_conn()
  
    cur = conn.cursor()
    df = pd.read_csv("/data/transformed.csv")

    cur.execute("CREATE TABLE sales ( id INT, Amount FLOAT, tax FLOAT)")

    for _, row in df.iterrows():
        cur.execute("INSERT INTO sales(id, amount, tax) VALUES (%s,%s,%s)", (row.id, row.amount, row.tax))

    conn.commit()
    cur.close()
    conn.close()


with DAG(
    "etl_csv_postgres",
    start_date = datetime(2023, 1, 1),
    schedule="@daily",
    catchup=False
) as dag:


    t1 = PythonOperator(task_id="extract", python_callable=extract)
    t2 = PythonOperator(task_id="transform", python_callable=transform)
    t3 = PythonOperator(task_id="load", python_callable=load)

    t1 >> t2 >> t3
