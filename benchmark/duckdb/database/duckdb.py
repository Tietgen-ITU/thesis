from abc import ABC, abstractmethod
from dataclasses import dataclass
import duckdb

@dataclass
class ConnectionConfig:
    device: str = ""
    backend: str = ""
    use_fdp: bool = False
class Database(ABC):


    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: duckdb.DuckDBPyConnection = None
        self._setup()
    
    @abstractmethod
    def _setup(self):
        pass

    @property
    def get_is_connected(self):
        return self.connection is not None

    def _connect(self):
        if not self.get_is_connected:
            self.connection = duckdb.connect(config={"allow_unsigned_extensions": "true"})

    def query(self, query: str):
        return self.connection.execute(query)

    def add_extension(self, name: str):
        self.connection.load_extension(name)
    
    def install_extension(self, name: str):
        self.connection.install_extension(name)
    
class QuackDatabase(Database):
    """
    QuackDatabase is just a normal Database wrapper of DuckDB
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)
        super()._connect()
    
    def _setup(self):
        print("Setting up QuackDatabase")
        return

class NvmeDatabase(Database):
    """
    NvmeDatabase is a Database wrapper of DuckDB that uses NVMe as the storage backend
    """

    def __init__(self, db_path: str, config: ConnectionConfig):
        self.device_path = config.device
        self.backend = config.backend
        self.use_fdp = config.use_fdp
        self.number_of_fdp_handles = 7
        super().__init__(db_path)
    
    def _setup(self):
        install_extension("../../nvmefs/build/release/extension/nvmefs/nvmefs.duckdb_extension", self)
        super()._connect()
        self.add_extension("nvmefs")
        self.query(f"""CREATE OR REPLACE PERSISTENT SECRET nvmefs (
                        TYPE NVMEFS,
                        nvme_device_path '{self.device_path}',
                        fdp_plhdls       '{self.number_of_fdp_handles}'
                    );""")
        
        self.query(f"ATTACH DATABASE '{self.db_path}' AS bench (READ_WRITE);")
        self.query("USE bench;")

def add_extension(name: str, db: Database = None):
    if db is None or not db.get_is_connected:
        duckdb.load_extension(name)
    else:
        db.add_extension(name)

def install_extension(name: str, db: Database = None):
    if db is None or not db.get_is_connected:
        duckdb.install_extension(name)
    else:
        db.install_extension(name)

def run_query(query: str, db: Database = None):
    if db is None or not db.get_is_connected:
        return duckdb.execute(query)
    else:
        db.query(query)

def connect(db_path:str, config: ConnectionConfig = None) -> Database:
    # TODO: Use parameters and insert them into the connection string
    db: Database = None

    if db_path.startswith("nvmefs://"):
        db = NvmeDatabase(db_path, config)
    else:
        db = QuackDatabase(db_path)

    return db
