import os
from fastapi import HTTPException
from azure.cosmos.aio import CosmosClient
from contextlib import asynccontextmanager
from typing import AsyncIterator
from azure.cosmos import PartitionKey

class CosmosClientSingleton:
    _instance = None

    @staticmethod
    def get_instance():
        if not CosmosClientSingleton._instance:
            CosmosClientSingleton._instance = CosmosClient(os.environ["AZURE_COSMOS_DB_ENDPOINT"], os.environ["AZURE_COSMOS_DB_KEY"])
        return CosmosClientSingleton._instance

class CosmosDBHandler:
    
    def __init__(
        self,
        client: CosmosClient,
        database_name: str,
        container_name: str,
    ) -> None:
        super().__init__()
        self.client = client
        self.database_name = database_name
        self.container_name = container_name

    async def init(self) -> None:
        # Create database if it does not exist
        self.database = await self.client.create_database_if_not_exists(self.database_name)

        # Create container if it does not exist
        # Replace /id with the appropriate partition key if needed
        self.container = await self.database.create_container_if_not_exists(
            id=self.container_name,
            partition_key= PartitionKey(path="/id")
        )

    def __enter__(self):
        return self

    def __exit__(self, endpoint, collection, traceback):
        self.client = None

    @classmethod
    @asynccontextmanager
    async def from_conn_info(
        cls, *, database_name: str, container_name: str
    ) -> AsyncIterator["CosmosDBHandler"]:
        try:
            client = CosmosClientSingleton.get_instance()
            handler = CosmosDBHandler(client, database_name, container_name)
            await handler.init()  # Ensure DB and container exist
            yield handler
        except HTTPException as ex:
            raise ex
        except Exception as ex:
            raise HTTPException(status_code=500, detail=f"CosmosDB error: {ex}")

    # Method to update conversation
    async def update_conversation(self, item):
        await self.container.upsert_item(body=item)