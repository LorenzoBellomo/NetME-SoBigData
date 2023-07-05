import logging
from   Logging.LoggingFormat import LogEntityFormat
from   Utility.Utility       import Utility
from   pymongo.collection    import Collection
from   pymongo.errors        import OperationFailure


# GLOBAL VARIABLE
_connection = None


class MongoHandler(logging.Handler):
    def __init__(
        self,
        level             = logging.NOTSET,
        host              = 'localhost',
        port              = 27017,
        database_name     = 'logs',
        collection        = 'logs',
        username          = None,
        password          = None,
        authentication_db = 'admin',
        fail_silently     = False,
        formatter         = None,
        capped            = False,
        capped_max        = 1000,
        capped_size       = 1000000,
        reuse             = True
    ):
        logging.Handler.__init__(self, level)
        self.host                         = host
        self.port                         = port
        self.database_name                = database_name
        self.collection_name              = collection
        self.username                     = username
        self.password                     = password
        self.authentication_database_name = authentication_db
        self.fail_silently                = fail_silently
        self.connection                   = None
        self.db                           = None
        self.collection                   = None
        self.authenticated                = False
        self.formatter                    = formatter or LogEntityFormat()
        self.capped                       = capped
        self.capped_max                   = capped_max
        self.capped_size                  = capped_size
        self.reuse                        = reuse
        self.utility                      = Utility()
        self._connect()

    def _connect(self):
        global _connection
        if self.reuse and _connection:
            self.connection = _connection
        else:
            self.connection = self.utility.mongo_db(True)
            _connection     = self.connection
        if _connection is None: return
        self.db = self.connection[self.database_name]
        if self.db is None: return
        if self.capped:
            try:
                self.collection = Collection(
                    self.db,
                    self.collection_name,
                    capped = True,
                    max    = self.capped_max,
                    size   = self.capped_size
                )
            except OperationFailure:
                self.collection = self.db[self.collection_name]
        else:
            self.collection = self.db[self.collection_name]

    def close(self):
        if self.connection is None: return
        self.connection.close()

    def emit(self, record):
        if self.connection is None: return
        try: self.collection.insert_one(self.format(record))
        except Exception as e: print(str(e))

    def __exit__(self, type, value, traceback):
        self.close()
