from gqlalchemy import Memgraph
from django.conf import settings

class MemgraphClient:

    def __init__(self):
        self.db = Memgraph(
            host= settings.MG_HOST,
            port=int(settings.MG_PORT)
        )

    def execute(self, query, params=None):
        if params is None:
            params = {}

        return list(self.db.execute_and_fetch(query, params))