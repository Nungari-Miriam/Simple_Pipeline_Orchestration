# 📊 ETL Pipeline with Apache Airflow and PostgreSQL

## 📌 Project Overview
This project demonstrates a simple **ETL (Extract–Transform–Load) pipeline** orchestrated by **Apache Airflow** and backed by **PostgreSQL**.  

The pipeline follows three main steps:
1. **Extract** – Generate sales data and save it as CSV.  
2. **Transform** – Apply a tax transformation to the dataset.  
3. **Load** – Insert the transformed data into a PostgreSQL table.  

The solution runs in a **Dockerized environment** to keep services isolated and reproducible.

---

## ⚙️ Tools & Technologies
- **Apache Airflow** – Workflow orchestration  
- **PostgreSQL** – Database for storing transformed data  
- **Pandas** – Data manipulation and CSV operations  
- **Docker / Docker Compose** – Containerization  

---
## Prerequisites

- Airflow + Postgres running via Docker Compose.
---

## 🏗️ Pipeline Workflow

### 1. Extract
Generates sample sales data:
```python
def extract():
    data = {"id":[1,2,3,4,5], "amount":[100,200,300,400,500]}
    df = pd.DataFrame(data)
    df.to_csv("/data/sales.csv", index=False)
```
### 2. Transform

Reads the extracted file, computes tax (20%), and saves the result:

```python
def transform():
    df = pd.read_csv("/data/sales.csv")
    df["tax"] = df["amount"] * 1.2
    df.to_csv("/data/transformed.csv", index=False)
```
### 3. Load

Uses Airflow’s PostgresHook to connect to PostgreSQL and insert the transformed data:
```python
def load():
    hook = PostgresHook(postgres_conn_id="postgres_dbms")
    conn = hook.get_conn()
    cur = conn.cursor()

    df = pd.read_csv("/data/transformed.csv")
    cur.execute("CREATE TABLE IF NOT EXISTS sales (id INT, amount FLOAT, tax FLOAT)")

    for _, row in df.iterrows():
        cur.execute("INSERT INTO sales(id, amount, tax) VALUES (%s, %s, %s)", (row.id, row.amount, row.tax))

    conn.commit()
    cur.close()
    conn.close()
```
🗂️ DAG Definition

Defines the pipeline flow in Airflow:
```python
with DAG(
    "etl_csv_postgres",
    start_date=datetime(2023, 1, 1),
    schedule="@daily",
    catchup=False
) as dag:

    t1 = PythonOperator(task_id="extract", python_callable=extract)
    t2 = PythonOperator(task_id="transform", python_callable=transform)
    t3 = PythonOperator(task_id="load", python_callable=load)

    t1 >> t2 >> t3
```
🔑 Airflow Connection Setup

In Airflow UI → Admin → Connections, configure a Postgres connection:
```
Conn Id: postgres_dbms

Conn Type: Postgres

Host: postgres_container

Schema: mydb

Login: ****

Password: ****

Port: 5432
```
## 🛠️ Debugging – Password Authentication Error

During development, I encountered the following critical issue that blocked progress for hours:

```bash
psycopg2.OperationalError: FATAL:  password authentication failed for user "***"
```
### 🔎 Root Causes

Airflow tried connecting to its internal metadata Postgres (postgres) instead of the external postgres.

The Airflow containers and Postgres were on different Docker networks.

### ✅ Step-by-Step Solution

**Step 0 – Check existing networks**
```bash
docker network ls

```
Confirm whether Airflow (airflow-docker_default) and Postgres (postgres_default) are on separate networks.

**Step 1 – Inspect container networks**
```bash
docker inspect postgres_container | grep -A 5 "Networks"
docker inspect airflow-docker-airflow-scheduler-1 | grep -A 5 "Networks"
```

**Step 2 – Connect Postgres to Airflow’s network**
```bash
docker network connect airflow-docker_default postgres_container

```
**Step 3 – Use container name as hostname**

In Airflow connection, set:
```bash
host = postgres_container

```
**Step 4 – Verify connectivity manually**

Verify connectivity from the airflow container
```bash
docker exec -it airflow-docker-airflow-scheduler-1 bash
psql -h postgres_container -U **** -d mydb

```
Step 5 – Refresh Airflow UI

After these steps, the DAG executed successfully ✅
```pgsql

📊 Architecture Diagram
     ┌────────────┐         ┌───────────────┐         ┌──────────────┐
     │            │         │               │         │              │
     │   Airflow  │  ETL →  │   CSV Files   │  Load → │  PostgreSQL  │
     │  DAGs &    │         │   (/data/)    │         │ (External DB)│
     │ Operators  │         │               │         │              │
     └─────┬──────┘         └──────┬────────┘         └─────┬────────┘
           │                        │                        │
           ▼                        ▼                        ▼
      Extract Task             Transform Task            Load Task
```
