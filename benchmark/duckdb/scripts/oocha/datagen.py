import sys
import os
import duckdb

temp_db = "temp.db"
temp_csv = "temp.csv"
scaling_factors = [2, 8, 32, 128]

def generate_data(scale_factor: int, output_dir: str):
    """
    Generate data using the dbgen function in DuckDB.
    """

    output_file = os.path.join(output_dir, f"oocha-{scale_factor}.db")

    if os.path.exists(temp_csv):
        os.remove(temp_csv)

    if os.path.exists(temp_db):
        os.remove(temp_db)

    if os.path.exists(output_file):
        os.remove(output_file)

    # Create a new DuckDB database
    con = duckdb.connect()
    con.execute(f"ATTACH DATABASE '{temp_db}' AS tempdatagen (READ_WRITE);")
    con.execute("USE tempdatagen;")

    con.install_extension("tpch")
    con.load_extension("tpch")

    con.execute("""PRAGMA enable_progress_bar;""")
    con.execute("""SET preserve_insertion_order=false""")

    # Generate the data using the dbgen function
    con.execute(f"CALL dbgen(sf={scale_factor});")

    # Move data temporarily to CSV in order to only copy lineitem table
    con.execute(f"COPY lineitem TO '{temp_csv}';")

    # Save the generated data to the output directory
    con.execute(f"ATTACH DATABASE '{output_file}' AS oocha (READ_WRITE);")
    con.execute("USE oocha;")
    con.execute("CREATE TABLE IF NOT EXISTS lineitem(l_orderkey INTEGER NOT NULL, l_partkey INTEGER NOT NULL, l_suppkey INTEGER NOT NULL, l_linenumber INTEGER NOT NULL, l_quantity DECIMAL(15,2) NOT NULL, l_extendedprice DECIMAL(15,2) NOT NULL, l_discount DECIMAL(15,2) NOT NULL, l_tax DECIMAL(15,2) NOT NULL, l_returnflag VARCHAR NOT NULL, l_linestatus VARCHAR NOT NULL, l_shipdate DATE NOT NULL, l_commitdate DATE NOT NULL, l_receiptdate DATE NOT NULL, l_shipinstruct VARCHAR NOT NULL, l_shipmode VARCHAR NOT NULL, l_comment VARCHAR NOT NULL);")
    con.execute(f"""COPY lineitem FROM '{temp_csv}' (HEADER TRUE);""")

    # Close the connection
    con.close()

def main(output_dir: str):

    for scale_factor in scaling_factors:
        generate_data(scale_factor, output_dir)


if __name__ == '__main__':

    if len(sys.argv) != 2: 
        print("Usage: python datagen.py <output_dir>")
        os.exit(1)

    main(sys.argv[1])