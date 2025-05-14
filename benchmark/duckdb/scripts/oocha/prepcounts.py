import os
import sys
import duckdb


BASE_DIR = f"{os.path.dirname(__file__)}/../.."
OOCHA_DIR = f"{BASE_DIR}/runner/oocha"

scale_factors = [2, 8, 32, 128]

def _getqueries():
    queries_dir = "./queries"
    thin_queries_dir = os.path.join(queries_dir, "thin")
    wide_queries_dir = os.path.join(queries_dir, "wide")
    
    wides = [False, True]
    queries = []
    for wide in wides:
        source_dir = wide_queries_dir if wide else thin_queries_dir
        for file_name in os.listdir(source_dir):
            file_path = f'{source_dir}/{file_name}'
            with open(file_path, 'r') as f:
                queries.append((file_name.split('.')[0], wide, f.read()))

    return queries

def main(oocha_data_dir: str):
    data_con = duckdb.connect(f'{SYSTEM_DIR}/data.db', read_only=True)
    data_con.execute("""SET preserve_insertion_order=false;""")
    data_con.execute("""SET memory_limit='20GB';""")

    # get the 'thin' queries
    queries = get_queries(thin_only=True)
    
    counts_con = duckdb.connect(f'{QUERIES_DIR}/counts.db')
    counts_con.execute("""CREATE TABLE IF NOT EXISTS counts (grouping VARCHAR, sf USMALLINT, c UBIGINT);""")
    for sf in scale_factors:
        print(f'Counting SF{sf} ...')
        for grouping, _, query in queries:
            if counts_con.execute(f"""SELECT count(*) FROM counts WHERE grouping = '{grouping}' AND sf = {sf};""").fetchall()[0][0] == 0:
                count = data_con.execute(f"""SELECT count(*) FROM ({query.replace('lineitem', f'lineitem{sf}').replace('OFFSET offset', '')}) sq;""").fetchall()[0][0]
                counts_con.execute(f"""INSERT INTO counts VALUES ('{grouping}', {sf}, {count});""")
        print(f'Counting SF{sf} done.')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python prepcounts.py <oocha_data_dir>")
        sys.exit(1)

    oocha_data_dir = sys.argv[1]

    main(oocha_data_dir)