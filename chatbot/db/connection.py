
# import psycopg
# import signal
import logging
from psycopg_pool import AsyncConnectionPool
import environ
import os

logger = logging.getLogger(__file__)

env = environ.Env()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
environ.Env.read_env(os.path.join(BASE_DIR,'env/.dev.env'))
LANGEX_CHATDB_STRING = env('LANGEX_CHATDB_STRING')

pool = AsyncConnectionPool(LANGEX_CHATDB_STRING, open=False)


      

if __name__ == "__main__":
  # asyncio.run(getTargetLanguageWithJid("d5a7dde3-94b5-44a7-bd1c-2fc8b81a2ccf"))
  pass