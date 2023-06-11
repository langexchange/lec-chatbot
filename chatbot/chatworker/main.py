import aiokafka
import environ
import os
import logging
import json
from aiokafka.errors import KafkaConnectionError
from settings import ROOT_DIR

env = environ.Env()
environ.Env.read_env(os.path.join(ROOT_DIR,'env/.dev.env'))
APP_BROKERS = env('APP_BROKERS')
logger = logging.getLogger(__name__)


class ChatBotConsumer:
    """
      self.consumer = aiokafka.AIOKafkaConsumer("chathelper-userinfo", bootstrap_servers=APP_BROKERS, group_id="chatbot", auto_offset_reset='latest', enable_auto_commit=False)
    """

    def __init__(self, bootstrap_servers, group_id, auto_offset_reset, enable_auto_commit):
      
      # self.commitCount = commitCount
      self.bootstrap_servers = bootstrap_servers
      self.group_id = group_id
      self.auto_offset_reset = auto_offset_reset
      self.enable_auto_commit = enable_auto_commit
      self.handlers = {}


    def register(self, topicName: str, handlerInstance):
      self.handlers[topicName] = handlerInstance
    

    async def callHandler(self, message):
      topicName = message.topic
      if topicName not in self.handlers:
        logger.error('There is no handler for this {}'.format(topicName))
      logger.info('Call handler {} for msg {}'.format(self.handlers[topicName], message.value))
      await self.handlers[topicName](message.value)

    
    def value_deserializer(self, value: bytes) -> dict:
      try:
        payload = json.loads(value)
      except ValueError:
        logger.exception("Message received from %s fail to be parsed", payload)
        raise('Decoding JSON has failed')
      return payload
    
    
    async def initChatBotConsumer(self):
      self.consumer = aiokafka.AIOKafkaConsumer("chathelper-userinfo", bootstrap_servers= self.bootstrap_servers, group_id= self.group_id, auto_offset_reset= self.auto_offset_reset, enable_auto_commit= self.enable_auto_commit, value_deserializer = self.value_deserializer)
      try: 
        await self.consumer.start()
        async for msg in self.consumer:
          await self.callHandler(msg)
      except KafkaConnectionError:
        logger.warning("Can not connect to kafka, check if it is available")
        return
      finally:
        await self.consumer.stop()


