import pandas as pd
import time


##PANDAS
# Start the timer
start_time = time.time()
df = pd.read_excel("dataset/train/data/biz_121/DuLieuXuat.xlsx")
execution_time = time.time() - start_time
print(df.head())
print(f"\n Pandas Execution time: {execution_time:.4f} seconds")
# #Execution time: 0.6972 seconds

##POLARS
import polars as pl
start_time = time.time()

df = pl.read_excel('dataset/train/data/biz_121/DuLieuXuat.xlsx', read_options={"n_rows": 5})

execution_time = time.time() - start_time
print(df)
print(f"\nPolars Execution time: {execution_time:.4f} seconds")
# Polars Execution time: 0.0086 seconds

##DUCKDB
import duckdb

conn = duckdb.connect()
start_time = time.time()

# Read directly and limit the output to the first 5 rows
df = conn.execute(
    "SELECT * FROM read_xlsx('dataset/train/data/biz_121/DuLieuXuat.xlsx') LIMIT 5"
).df()
execution_time = time.time() - start_time

print(df)
print(f"\nDuckDB Execution time: {execution_time:.4f} seconds")
#Execution time: 0.0138 seconds

import duckdb
import time

conn = duckdb.connect(database=":memory:")
conn.execute("ATTACH 'dataset/train/data/biz_123/pos.sqlite' AS my_sqlite (TYPE sqlite);")

# --- QUERY 1: CSV FILE ---
start_csv = time.time()
df_csv = conn.execute("SELECT * FROM read_csv('dataset/train/data/biz_101/ban_hang.csv') LIMIT 5").df()
time_csv = time.time() - start_csv

print("--- CSV Data ---")
print(df_csv)
print(f"DuckDB CSV Execution time: {time_csv:.4f} seconds\n")
#DuckDB CSV Execution time: 0.2496 seconds

##POLARS
import polars as pl

# Start the timer
start_time = time.time()

# Scan the CSV lazily, apply the limit, and collect the results
df = pl.scan_csv('dataset/train/data/biz_101/ban_hang.csv').limit(5).collect()

# Calculate total execution time
execution_time = time.time() - start_time

print(df)
print(f"\nPolars Execution time: {execution_time:.4f} seconds")
#Polars CSV Execution time: 0.0093 seconds

# --- QUERY 2: SQLITE FILE ---
start_sqlite = time.time()
df_sqlite = conn.execute("SELECT * FROM my_sqlite.the_kho LIMIT 5").df()
time_sqlite = time.time() - start_sqlite

print("--- SQLite Data ---")
print(df_sqlite)
print(f"DuckDB SQLite Execution time: {time_sqlite:.4f} seconds")
#DuckDB SQLite Execution time: 0.0040 seconds