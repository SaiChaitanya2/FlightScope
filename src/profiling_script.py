import time
import psutil
import os
import sys
import duckdb

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.pipeline.config import DB_PATH

def run_profiling():
    print("=" * 50)
    print("FlightScope Performance Profiling")
    print("=" * 50)
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    # Memory baseline
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / (1024 * 1024)
    
    # 1. Connection overhead
    t0 = time.perf_counter()
    conn = duckdb.connect(DB_PATH, read_only=True)
    t1 = time.perf_counter()
    print(f"Database Connection Time: {(t1 - t0) * 1000:.2f} ms")
    
    # 2. Query 1: Heavy GroupBy and Aggregation
    query_heavy = """
        SELECT 
            Origin, 
            Dest, 
            COUNT(*) as weight,
            AVG(CAST(DepDelay AS FLOAT)) as avg_delay
        FROM flights
        WHERE Season = 3
        GROUP BY Origin, Dest
    """
    
    t0 = time.perf_counter()
    res1 = conn.execute(query_heavy).df()
    t1 = time.perf_counter()
    heavy_time = (t1 - t0) * 1000
    
    print(f"Network Graph Query (Origin/Dest GroupBy + Avg Delay): {heavy_time:.2f} ms")
    print(f"  -> Returned {len(res1)} edges")
    
    # 3. Query 2: Sum over massive columns (Sankey Diagram query)
    query_sankey = """
        SELECT 
            SUM(CAST(CarrierDelay AS FLOAT)) AS CarrierDelay,
            SUM(CAST(WeatherDelay AS FLOAT)) AS WeatherDelay,
            SUM(CAST(NASDelay AS FLOAT)) AS NASDelay,
            SUM(CAST(SecurityDelay AS FLOAT)) AS SecurityDelay,
            SUM(CAST(LateAircraftDelay AS FLOAT)) AS LateAircraftDelay
        FROM flights
    """
    t0 = time.perf_counter()
    res2 = conn.execute(query_sankey).df()
    t1 = time.perf_counter()
    sankey_time = (t1 - t0) * 1000
    print(f"Sankey Delay Cause Query (Summing across columns): {sankey_time:.2f} ms")
    
    # 4. Memory footprint after loading DFs
    mem_after = process.memory_info().rss / (1024 * 1024)
    print(f"Memory overhead to hold results in Python: {mem_after - mem_before:.2f} MB")
    print("=" * 50)
    print(f"DuckDB Sub-50ms SLA Check:")
    print(f"  - Network Query: {'PASS' if heavy_time < 50 else 'FAIL'} ({heavy_time:.2f} ms)")
    print(f"  - Sankey Query:  {'PASS' if sankey_time < 50 else 'FAIL'} ({sankey_time:.2f} ms)")
    print("=" * 50)
    
    conn.close()

if __name__ == "__main__":
    run_profiling()
