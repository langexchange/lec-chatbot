import slixmpp
from slixmpp.exceptions import IqError
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.stanza import Message

from chatbot.chatworker.main import ChatBotConsumer
from chatbot.stanza.chatbot import LangExBot, OnBoard

import json
import logging
from argparse import ArgumentParser
import environ
import os
from jinja2 import Environment, FileSystemLoader
from chatbot.db.connection import pool


env = environ.Env()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
environ.Env.read_env(os.path.join(BASE_DIR,'env/.dev.env'))
BOT_PASSWORD = env('BOT_PASSWORD')
BOT_JID = env('BOT_JID')
LANGEX_XMPP_HOSTNAME = env('LANGEX_XMPP_HOSTNAME')
LANGEX_XMPP_PORT = env('LANGEX_XMPP_PORT')
APP_BROKERS = env('APP_BROKERS')

logger = logging.getLogger(__file__)

class EchoBot(slixmpp.ClientXMPP):
    """
    A simple Slixmpp bot that will echo messages it
    receives, along with a short thank you message.
    """
    name = "LangExchange Bot"
    info_path = "./assets/chatbotinfo.json"
    def __init__(self, jid, password, sasl_mech, plugin_config):

      slixmpp.ClientXMPP.__init__(self, jid, password, sasl_mech=sasl_mech, plugin_config= plugin_config)
      

      self.register_plugin('xep_0030') # Service Discovery
      self.register_plugin('xep_0004') # Data Forms
      self.register_plugin('xep_0060') # PubSub
      self.register_plugin('xep_0199') # XMPP Ping
      self.register_plugin('xep_0054') # Vcard
      self.register_plugin('xep_0066')

      self.add_event_handler("session_start", self.session_start)

      # Register chatbot stanza
      register_stanza_plugin(Message, LangExBot)
      
      # Register ChatBotConsumer
      self.chatBotConsumer =  ChatBotConsumer(bootstrap_servers=APP_BROKERS, group_id="chatbot", auto_offset_reset='latest', enable_auto_commit=False)
      self.chatBotConsumer.register("chathelper-userinfo", self.onBoardUserHandler)

      # Chatbot feature                                                
      self.chatbotFeatureDescriptions = { # TODO: Need have a Langex Plugin manager when the app scales.
         "pronunc_assess": {
            "name": "Pronunciation Assessment",
            "description": "I can help you to evaluate your pronunciation whenever you add your recording voice (See tool bar) accompanying with the text you have said",
            "example": "MOCK",
            "addition_note": "The default language will be accessed is your target language. If you want to assess another language please use command !pronunc_assess*{your_language}*: {The text you intend to say}" 
         }
      }

      self.onBoardHelloMessages = {
        "hello": "Hello %s, Welcome to LangExchange community. I'am LangEx bot " + u'\u1F916' + "!!",
        "intro_feature": "I can help you to practice various of languages. Here are list of features I can support:"
      }
      
      # Init Jinja2 template environment
      self.template = Environment(loader=FileSystemLoader('./assets/templates'))

    def oob_handler(self):
        print("OOB_handler detected")


    async def session_start(self, event):
      self.send_presence()
      await self.get_roster()
      await self.update_vcard()
      await pool.open()

      # This plugin needs resource to be initialized first
      self.register_plugin('PronuncAssessFeatures', module="chatbot.features.pronunc_assess.plugin")
      # Should call at the end
      await self.chatBotConsumer.initChatBotConsumer()
      

    async def update_vcard(self):
      vcard = self.plugin["xep_0054"].make_vcard()
      vcard["FN"] = self.name
      
      with open(self.info_path, 'rb') as fd:
        try: 
          bot_info = json.load(fd)
        except ValueError:
          logger.exception("Chatbot info fail to be parsed")
          raise('Decoding JSON failed')
        vcard["PHOTO"]["EXTVAL"] = bot_info["avatar_url"]     
      try: 
        await self.plugin["xep_0054"].publish_vcard(vcard = vcard, jid = self.jid)
      except IqError as e:
        logger.error("Error when publish_vcard %s", e.iq['error']['condition'])


    def makeLangExBotMessage(self, **attr):
      normal_msg = self.make_message(mto = attr["mto"], mbody = attr["mbody"], mtype= attr["mtype"], mfrom= attr["mfrom"])
      normal_msg.append(LangExBot())
      return normal_msg
    

    def onBoardUserHandler(self, new_user):
      """
      {
        "jid": "user_id1@localhost",
        "fullname": "",
        "is_created": true,
      },
      """
      if "is_created" not in new_user or new_user["is_created"] == False:
        return
      
      # Create onboard message
      msg_t = self.template.get_template('onboard.html')
      msg_params = {
        "hello_msg": self.onBoardHelloMessages["hello"] % (new_user["fullname"]), 
        "feature_intro": self.onBoardHelloMessages["intro_feature"],
        "features": self.chatbotFeatureDescriptions 
      }
      
      msg = msg_t.render(msg_params)
      send_msg = self.makeLangExBotMessage(mto = new_user["jid"], mbody = msg, mtype="chat", mfrom=self.jid)
      send_msg["langexbot"].append(OnBoard())
      send_msg.send()
    


if __name__ == '__main__':
    # Setup the command line arguments.
    parser = ArgumentParser(description=EchoBot.__doc__)

    # Output verbosity options.
    parser.add_argument("-q", "--quiet", help="set logging to ERROR",
                        action="store_const", dest="loglevel",
                        const=logging.ERROR, default=logging.INFO)
    parser.add_argument("-d", "--debug", help="set logging to DEBUG",
                        action="store_const", dest="loglevel",
                        const=logging.DEBUG, default=logging.INFO)

    # JID and password options.
    parser.add_argument("-j", "--jid", dest="jid",
                        help="JID to use")
    parser.add_argument("-p", "--password", dest="password",
                        help="password to use")

    args = parser.parse_args()

    # Setup logging.
    logging.basicConfig(level=args.loglevel,
                        format='%(levelname)-8s %(message)s')

    if args.jid is None:
        args.jid = BOT_JID
    if args.password is None:
        args.password = BOT_PASSWORD

    plugin_config = {
      'feature_mechanisms': {
        'unencrypted_plain': True,
      }
    }

    xmpp = EchoBot(args.jid, args.password, 'PLAIN', plugin_config)
    
    # Connect to the XMPP server and start processing XMPP stanzas.
    xmpp.connect(address=[LANGEX_XMPP_HOSTNAME,LANGEX_XMPP_PORT], force_starttls= False, disable_starttls=True)
    xmpp.process()