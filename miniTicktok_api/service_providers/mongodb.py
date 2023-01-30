from miniTicktok_api.config import config
from miniTicktok_api.service_providers.service_prodiver import ServiceProvider


class MongodbDatabaseServiceProvider(ServiceProvider):
    def register(self):
        def create_instance():
            from miniTicktok_api.external.mongodb import MongodbDatabase
            return MongodbDatabase(uri=config.db_uri, database=config.db_default_database)

        self.app.singleton('MongodbDatabase', create_instance)
