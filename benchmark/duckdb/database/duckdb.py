from abc import ABC, abstractmethod
import duckdb

class Database(ABC):
    def __init__(self, connection: duckdb.DuckDBPyConnection):
        self.connection = connection
        self.__setup()
    
    @abstractmethod
    def __setup(self):
        pass

    def query(self, query: str):
        return self.connection.execute(query)

    def add_extension(self, name: str):
        self.connection.load_extension(name)
    
class QuackDatabase(Database):
    """
    QuackDatabase is just a normal Database wrapper of DuckDB
    """

    def __init__(self, connection: duckdb.DuckDBPyConnection):
        super().__init__(connection)
    
    def __setup(self):
        pass

class NvmeDatabase(Database):
    """
    NvmeDatabase is a Database wrapper of DuckDB that uses NVMe as the storage backend
    """
    def __init__(self, connection: duckdb.DuckDBPyConnection):
        super().__init__(connection)
    
    def __setup(self):
        add_extension("../../nvmefs/build/release/extension/nvmefs/nvmefs.duckdb_extension", self)
        self.query("CREATE OR REPLACE PERSISTENT SECRET nvmefs:// ")

def add_extension(name: str, db: Database):
    db.add_extension(name)

def connect(db_path:str, device: str, backend: str, use_fdp: bool) -> Database:
    # TODO: Use parameters and insert them into the connection string
    db: Database = None

    if db_path.startswith("nvmefs://"):
        db = NvmeDatabase(duckdb.connect(db_path))
    else:
        db = QuackDatabase(duckdb.connect(db_path))

    return db
