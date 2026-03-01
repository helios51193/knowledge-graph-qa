from gqlalchemy import Memgraph
from django.conf import settings

class MemgraphClient:
    def __init__(self):
        self.db = Memgraph(host=settings.MG_HOST, port=settings.MG_PORT)

    def execute(self, query, parameters=None):
        return self.db.execute(query, parameters or {})

    def query(self, query, parameters=None):
        return list(self.db.execute_and_fetch(query, parameters or {}))