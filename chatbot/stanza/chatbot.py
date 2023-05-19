from slixmpp.xmlstream import ElementBase
from slixmpp.xmlstream import register_stanza_plugin

class LangExBot(ElementBase):

    """
    """

    name = 'langexbot'
    namespace = 'langex:chatbot'
    plugin_attrib = 'langexbot'

class OnBoard(ElementBase):

    """
    """
    namespace = 'langex:chatbot:onboard'
    name = 'onboard'
    plugin_attrib = 'onboard'

register_stanza_plugin(LangExBot, OnBoard)