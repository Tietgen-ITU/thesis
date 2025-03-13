import duckdb

class Database:
    def __init__(self, connection: duckdb.DuckDBPyConnection):
        self.connection = connection

    def query(self, query: str):
        return self.connection.execute(query)

def connect(db_path:str, device: str, backend: str, use_fdp: bool) -> Database:
    # TODO: Use parameters and insert them into the connection string
    duckdb.query("CREATE OR REPLACE PERSISTENT SECRET nvmefs://  ")
    
    connection: duckdb.DuckDBPyConnection = duckdb.connect(db_path)

    return Database(connection)
