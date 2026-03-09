from .memgraph_client import MemgraphClient

class CypherRunner:

    def __init__(self):
        self.client = MemgraphClient()

    def run(self, query):
        return self.client.execute(query)