import aiokafka
import environ
import os
import logging
import json
import asyncio

env = environ.Env()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
environ.Env.read_env(os.path.join(BASE_DIR,'env/.dev.env'))
APP_BROKERS = env('APP_BROKERS')
logger = logging.getLogger(__file__)


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
    
    def callHandler(self, message):
      topicName = message.topic
      if topicName not in self.handlers:
        logger.error('There is no handler for this {}'.format(topicName))
      logger.info('Call handler {} for msg {}'.format(self.handlers[topicName], message.value))
      self.handlers[topicName](message.value)
    
    # def createTopicsIfNotExists(self, num_partitions=1, replication_factor=1):
    #   admin_client = AdminClient({'bootstrap.servers': self.conf["bootstrap.servers"]})
    #   topic_metadata = admin_client.list_topics(timeout = 5)

    #   new_topics = []
    #   for topic in self.handlers:
    #     if topic not in topic_metadata.topics:
    #       new_topic = NewTopic(topic=topic, num_partitions=num_partitions, replication_factor=replication_factor)
    #       new_topics.append(new_topic)

    #     else:
    #       logger.debug("Topic {} already exists".format(topic))

    #   if not new_topics:
    #     return

    #   futures = admin_client.create_topics(new_topics)
    #   for topic_name in futures:
    #     try:
    #       futures[topic_name].result()
    #       logger.debug("Create topic {} with num_partitions {} and replication_factor {}".format(topic_name, num_partitions, replication_factor))
    #     except Exception as e:
    #       logger.warn("Failed to create topic {}: {}".format(topic_name, e))
    
    def value_deserializer(self, value: bytes) -> dict:
      try:
        payload = json.loads(value)
      except ValueError:
        logger.exception("Message received from %s fail to be parsed", payload)
        raise('Decoding JSON has failed')
      return payload
    
    async def initChatBotConsumer(self):
      self.consumer = aiokafka.AIOKafkaConsumer("chathelper-userinfo", bootstrap_servers= self.bootstrap_servers, group_id= self.group_id, auto_offset_reset= self.auto_offset_reset, enable_auto_commit= self.enable_auto_commit, value_deserializer = self.value_deserializer)
      await self.consumer.start()
      try:
        async for msg in self.consumer:
          self.callHandler(msg)
      finally:
        await self.consumer.stop()

