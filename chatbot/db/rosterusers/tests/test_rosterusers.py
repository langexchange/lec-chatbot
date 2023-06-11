# from ..query import roster_user_model
# from psycopg import AsyncConnection
# from psycopg_pool import AsyncConnectionPool
# from settings import ROOT_DIR
# import environ
# import os
# import pytest

# env = environ.Env()
# environ.Env.read_env(os.path.join(ROOT_DIR,'env/.dev.env'))
# LANGEX_CHATDB_STRING = env('LANGEX_CHATDB_STRING')


# async def test_get_empty_rostercontacts(mocker):
#   pool = mocker.Mock()
#   pool.connection.return_value = 
#   mocker.patch("roster_user_model.getRosterContact", pool)
#   contacts = await roster_user_model.getRosterContact("chatbot")
#   assert len(contacts) == 0

# def db_connection():
#   return AsyncConnection.connect()

# def teardown():
#   pass