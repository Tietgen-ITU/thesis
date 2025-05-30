import os
import sys
import duckdb


BASE_DIR = f"{os.path.dirname(__file__)}/../.."
OOCHA_DIR = f"{BASE_DIR}/runner/oocha"
OOCHA_QUERIES_DIR = f"{OOCHA_DIR}/queries"

scale_factors = [2, 8, 32, 128]

def _get_thin_queries():
    thin_queries_dir = os.path.join(OOCHA_QUERIES_DIR, "thin")
    
    queries = []
    source_dir = thin_queries_dir
    for file_name in os.listdir(source_dir):
        file_path = f'{source_dir}/{file_name}'
        with open(file_path, 'r') as f:
            queries.append((file_name.split('.')[0], False, f.read()))

    return queries

def generate_counts(oocha_data_dir: str, sf: int, queries: list):
    counts_file = f'{OOCHA_QUERIES_DIR}/counts.db'

    data_con = duckdb.connect(f'{oocha_data_dir}/oocha-{sf}.db', read_only=True)
    data_con.execute("""SET preserve_insertion_order=false;""")
    data_con.execute("""SET memory_limit='20GB';""")

    if os.path.exists(counts_file):
        os.remove(counts_file)

    counts_con = duckdb.connect(f'{OOCHA_QUERIES_DIR}/counts.db')
    counts_con.execute("""CREATE TABLE IF NOT EXISTS counts (grouping VARCHAR, c UBIGINT);""")

    print(f'Counting SF{sf} ...')
    for grouping, _, query in queries:
        count = data_con.execute(f"""SELECT count(*) FROM ({query.replace('OFFSET offset', '')}) sq;""").fetchall()[0][0]
        counts_con.execute(f"""INSERT INTO counts VALUES ('{grouping}', {count});""")
        counts_con.execute(f"""COPY counts TO '{OOCHA_QUERIES_DIR}/counts-{sf}.csv' (DELIMITER ';', HEADER, OVERWRITE);""")
    
    counts_con.close()
    data_con.close()
    print(f'Counting SF{sf} done.')

def main(oocha_data_dir: str):

    # get the 'thin' queries
    queries = _get_thin_queries()
    
    for sf in scale_factors:
        generate_counts(oocha_data_dir, sf, queries)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python prepcounts.py <oocha_data_dir>")
        sys.exit(1)

    oocha_data_dir = sys.argv[1]

    main(oocha_data_dir)