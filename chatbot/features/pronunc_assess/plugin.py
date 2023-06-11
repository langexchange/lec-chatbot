from slixmpp.plugins.base import BasePlugin
from slixmpp.xmlstream.handler import CoroutineCallback
from slixmpp.xmlstream.matcher.xpath import MatchXPath
from slixmpp.xmlstream import  register_stanza_plugin

import io 
import aiohttp
import urlextract
import re
from Bio import Align
import functools
from jinja2 import Environment, FileSystemLoader
      
from chatbot.models.whisper.model import whisperModel
from chatbot.features.pronunc_assess.stanza import PronuncAssessStanza
import mimetypes
from chatbot.stanza.chatbot import LangExBot
import os
from chatbot.db.vcard.query import vcard_model
import environ
from settings import ROOT_DIR
import logging

env = environ.Env()
environ.Env.read_env(os.path.join(ROOT_DIR,'env/.dev.env'))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)

class PronuncAssessFeatures(BasePlugin):
    """
    This plugin is used to create langex audio transcript chatbot
    """
    name = "Pronunciation Assessment",
    dependencies = {'xep_0030', 'xep_0066'}
    assess_list = [[0, "You must be a newbie with this language"], [0.3, "You need to practice more :(("], [0.5, "Not very bad, you have some errors"], [0.9, "You are good. A little bit to be perfect"], [1, "Perfect!! You have no error in your pronunciation"]]
    
    supported_commands = {
      "pronunc_assess": {
          "languages_iso_6391": ['af', 'ar', 'az', 'be', 'bg', 'bs', 'ca', 'cs', 'cy', 'da', 'de', 'el', 'en', 'es', 'et', 'fa', 'fi', 'fr', 'gl', 'he', 'hi', 'hr', 'hu', 'hy', 'id', 'is', 'it', 'ja', 'kk', 'kn', 'ko', 'lt', 'lv', 'mi', 'mk', 'mr', 'ms', 'ne', 'nl', 'no', 'pl', 'pt', 'ro', 'ru', 'sk', 'sl', 'sr', 'sv', 'sw', 'ta', 'th', 'tl', 'tr', 'uk', 'ur', 'vi', 'zh'],

          "country_iso_31661": ['za', 'dz', 'az', 'by', 'bg', 'ba', 'ad', 'cz', 'gb', 'dk', 'de', 'gr', 'us', 'es', 'ee', 'ir', 'fi', 'fr', 'es', 'il', 'in', 'hr', 'hu', 'am', 'id', 'is', 'it', 'ja', 'kz', 'in', 'kr', 'lt', 'lv', 'nz', 'mk', 'in', 'my', 'np', 'nl', 'no', 'pl', 'pt', 'ro', 'ru', 'sk', 'si', 'rs', 'se', 'tz', 'in', 'th', 'ph', 'tr', 'ua', 'pk', 'vn', 'cn'],

          "languages": ['Afrikaans', 'Arabic', 'Azerbaijani', 'Belarusian', 'Bulgarian', 'Bosnian', 'Catalan', 'Czech', 'Welsh', 'Danish', 'German', 'Greek', 'English', 'Spanish', 'Estonian', 'Persian', 'Finnish', 'French', 'Galician', 'Hebrew', 'Hindi', 'Croatian', 'Hungarian', 'Armenian', 'Indonesian', 'Icelandic', 'Italian', 'Japanese', 'Kazakh', 'Kannada', 'Korean', 'Lithuanian', 'Latvian', 'Maori', 'Macedonian', 'Marathi', 'Malay', 'Nepali', 'Dutch', 'Norwegian', 'Polish', 'Portuguese', 'Romanian', 'Russian', 'Slovak', 'Slovenian', 'Serbian', 'Swedish', 'Swahili', 'Tamil', 'Thai', 'Tagalog', 'Turkish', 'Ukrainian', 'Urdu', 'Vietnamese', 'Chinese'],
      },
      "vocab_schedule": [],
    }

    def plugin_init(self):
        self.xmpp.register_handler(
            CoroutineCallback('AudioBotRequest',
                     MatchXPath('{%s}message/body' % (self.xmpp.default_ns)),
                     self.handleLangexChatBotMessage
                     ))
        
        register_stanza_plugin(LangExBot, PronuncAssessStanza)
        template = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR,'templates'))) 
        self.passess_template = template.get_template('pronunc_assess.html')
        

    def post_init(self):
      BasePlugin.post_init(self)

      self.aligner = Align.PairwiseAligner()
      self.aligner.open_gap_score = -0.5
      self.aligner.extend_gap_score = -0.1
      self.aligner.target_end_gap_score = 0.0
      self.aligner.query_end_gap_score = 0.0


    def cal_accuracy_per(self, accuracy_list):
      crr_count = functools.reduce(lambda x,y: x +1 if y[1]==True else x, accuracy_list, 0)
      return crr_count/len(accuracy_list)


    def parseCommand(self, msg_text):
      """
        Command syntax: ![command][*{op1}]*: input
      """
      semi_sep_list = msg_text.split(":")
      command = ""
      opts = None
      if msg_text.startswith("!") and len(semi_sep_list) >=1:
        command_opts = semi_sep_list[0] #Get command and options

        regex = r'^([a-zA-Z_]+)((\*[a-zA-Z_]+)*)$'
        match = re.search(regex, command_opts[1:])
        if match:
          command = match.group(1)
          if not match.group(2):
            opts = []
          else:
            opts = match.group(2)[1:].split("*")

      if not command:
        return "pronunc_assess", [], msg_text, ""  #Treat all string as sample that is gonna assess the pronunciation
      
      if command not in self.supported_commands:
        return None, [], "", "Sorry, I have not supported the command {}".format(command)
      
      body = "".join(semi_sep_list[1:])
    
      return command, opts, body, ""


    async def handleLangexChatBotMessage(self, msg_stanza):
      msg_text =  self.extract_text(msg_stanza["body"]).strip()
      url = msg_stanza["oob"]["url"]
      if len(msg_text) <= 0:
        return self.xmpp.send_message(mto=msg_stanza["from"], mbody="I can not understand you if you don't input anything")

      command, opts, body, warning_msg = self.parseCommand(msg_text)

      if not command:
        return self.xmpp.send_message(mto=msg_stanza["from"], mbody=warning_msg)

      result = None
      if command == "pronunc_assess":
        result = await self.handlePronuncAssessment(opts, url, body, msg_stanza["from"])
      else: 
        return self.xmpp.send_message(mto=msg_stanza["from"], mbody="Other commands have not been supported yet")

      self.sendMessageOnCommand(command, result, msg_stanza)
    

    def sendMessageOnCommand(self, command, result, msg_stanza):
      if command == "pronunc_assess":
        if result["status"] == 1:
          self.send_pronunc_peformance(result["origin_msg"], result["heard_msg"], result["acc_list"], result["language"], result["country"], msg_stanza)
        elif result["status"] == 0:
          self.xmpp.send_message(mto=msg_stanza["from"], mbody=result["msg"])


    async def downloadFile(self, url: str) -> io.BytesIO:
      # Forward url to file server in case the client sends to localhost
      PLATFORM = env("PLATFORM")
      reg = r'(http[s]?://)localhost(/.*)$'
      if (match := re.search(reg, url))  and PLATFORM == "DOCKER":
        FILE_SERVICE = env("FILE_SERVICE")
        url = "{}{}{}".format(match.group(1), FILE_SERVICE, match.group(2))

      # TODO: Feed each chunk into the whisper for optimizing
      MODE = env("MODE")
      async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False) if MODE == "development" else None) as session:
        async with session.get(url) as response:
          content = await response.content.read()
          return io.BytesIO(content)
          

    async def handlePronuncAssessment(self, opts, url, body, user_jid):
      """
      Return: 
        {
            "status": 1 if "success" else 0
            
            if status == 1:
              "heard_msg":
              "language":
              "acc_list":
              "origin_msg"
            else:
              "msg":
        }
      """

      mime_type, _ = mimetypes.guess_type(url)
      if not mime_type or (not mime_type.startswith("audio/") and not mime_type == "video/webm"):
        return {
          "status": 0,
          "msg": "Sorry, May be you missed your file or have sent invalid audio file. I can not perform the pronunciation assessment with text".format(body)
        }
      
      language = ""
      country = ""
      if not opts:
        # TODO: getTargetLanguage from database
        # self.getTargetLanguage(userJid)
        raw_target_lang = await vcard_model.getTargetLanguageWithJid(user_jid.bare)
        if raw_target_lang == None: 
          language = "en" #Default language if the user does not have target language
        else:
          raw_target_lang = raw_target_lang.lower()
          hyphen_index = raw_target_lang.find("-")
          if hyphen_index == -1:
            language = raw_target_lang
          else:
            language, country = raw_target_lang.split("-")
      else:
        language = opts[0]
      
      if language not in self.supported_commands["pronunc_assess"]["languages"] and language not in self.supported_commands["pronunc_assess"]["languages_iso_6391"]:
        return {
          "status": 0,
          "msg": "Sorry, Your language has not been supported to perform the assessment. Try: {}".format(self.supported_commands["pronunc_assess"]["languages"])
        }
      
      if not country:
        country_index = self.supported_commands["pronunc_assess"]["languages"].index(language) if len(language) > 2 else self.supported_commands["pronunc_assess"]["languages_iso_6391"].index(language)
        country = self.supported_commands["pronunc_assess"]["country_iso_31661"][country_index]
      
      audio_file = await self.downloadFile(url)

      # Optimize the model
      try: 
        transcribe_result = whisperModel.inference(audio_file, "transcribe", language)
      except Exception as e:
        logger.exception("Unhandled error")
        raise e
      
      heard_msg = transcribe_result["text"]

      filter_msg = self.filter_seperator(body) # Filter origin text before matching
      filter_heard_msg = self.filter_seperator(heard_msg)
      
      match_coordinates = self.first_matched_coordinates(filter_msg, filter_heard_msg) # Find match coordinates between two string
      
      accuracy_list = self.get_accuracy_list(match_coordinates, filter_msg, filter_heard_msg) # Get accuracy of word tokens

      return {
          "status": 1,
          "origin_msg": body,
          "heard_msg": heard_msg,
          "language": language,
          "country": country,
          "acc_list": accuracy_list,
        }
      

    def encompass_wrong_text(self, str):
      wrong_text = str.strip()

      if not wrong_text:
        return ""
      
      wrong_word_list = wrong_text.split(" ")
      for i, wrong_word in enumerate(wrong_word_list): wrong_word_list[i] = "<r>{}</r>".format(wrong_word)
      return " ".join(wrong_word_list)


    def transform2_match_str(self, accuracy_list, origin_input):
      pre_mindex_end = 0
      result_str = ""
      crr_list = list(filter(lambda x: x[1] == True, accuracy_list))
      # TODO: Add error tag to assessment msg.
      for word, _ in crr_list:
        match = re.search(word, origin_input[pre_mindex_end:])
        
        mindex_start = pre_mindex_end + match.start()
        mindex_end = pre_mindex_end + match.end()
        
        wrong_encompassed_text = self.encompass_wrong_text((origin_input[pre_mindex_end : mindex_start])) 
        result_str += " " if not wrong_encompassed_text else " " + wrong_encompassed_text + " "
        result_str +=("<g>{}</g>".format(origin_input[mindex_start:mindex_end]))

        pre_mindex_end = mindex_end
      
      result_str += " " + self.encompass_wrong_text(origin_input[pre_mindex_end:])
      return result_str
                        
       
    def send_pronunc_peformance(self, origin_msg, heard_msg, accuracy_list, language_iso, country_iso, msg_stanza):
      crr_per = self.cal_accuracy_per(accuracy_list)
      match_text = self.transform2_match_str(accuracy_list, origin_msg)
      assessment = ""
      for assess_pnt, eval in self.assess_list[::-1]:
         if crr_per >= assess_pnt:
            assessment = ("{}, your score is <score>{}</score>, this is how your voice match: ".format(eval, round(crr_per*100)))
            break
      
      # Transform ISO code to language
      index = self.supported_commands["pronunc_assess"]["languages_iso_6391"].index(language_iso)
      msg_params = {
        "language_para": {
           "country_code": country_iso,
           "text": "Pronunciation assessment in language:",
           "language": " {}".format(self.supported_commands["pronunc_assess"]["languages"][index]),
        },
        "heard_para": {
          "text": "This is what you said:",
          "heard_text": heard_msg
        },
        "match_para": {
          "text": assessment,
          "match_text": match_text
        },
      }
      msg = self.passess_template.render(msg_params)
      
      send_msg = self.xmpp.makeLangExBotMessage(mto = msg_stanza["from"], mbody = msg, mtype=msg_stanza["type"], mfrom=self.xmpp.jid)
      send_msg["langexbot"].append(PronuncAssessStanza())
      send_msg.send()
      

    def get_accuracy_list(self, coordinates, input_str, trans_str):
      pre_mati1, pre_mati2 = 0, 0
      path = list(zip(coordinates[0], coordinates[1]))
      align_input_str, align_trans_str = "", ""

      for mati1, mati2 in path[1:]:
        if pre_mati1 < mati1:
          align_input_str += input_str[pre_mati1:mati1]
        if pre_mati2 < mati2:
          align_trans_str += trans_str[pre_mati2:mati2]
        if pre_mati1 == mati1:
          align_input_str += "-"*(mati2 -pre_mati2)
        if pre_mati2 == mati2:
          align_trans_str += "-"*(mati1 -pre_mati1)
        pre_mati1, pre_mati2 = mati1, mati2
      
      accuracy_list = []
      word_findex = 0
      eostr = False
      for index, char in enumerate(align_input_str):
        if index == len(align_input_str)-1:
          eostr= True
          index = index + 1
        if char == " " or eostr:
          if(align_input_str[word_findex:index].lower() == align_trans_str[word_findex:index].lower()):
            accuracy_list.append([align_input_str[word_findex:index], True])
          else:
            accuracy_list.append([align_input_str[word_findex:index], False])
          word_findex = index + 1
      
      return accuracy_list

  
    def first_matched_coordinates(self, str1, str2):
      alignments = self.aligner.align(str1, str2)
      return alignments[0].coordinates
  

    def filter_seperator(self, str):
      letter_pattern = re.compile('[^\W\d_ ]+', re.UNICODE)
      letters_only = ' '.join(letter_pattern.findall(str))

      return letters_only


    def extract_text(self, url_msg):
      extractor = urlextract.URLExtract()
      urls = extractor.find_urls(url_msg)
      text_msg = url_msg
      for url in urls:
          text_msg = text_msg.replace(url, '')

      return text_msg
        