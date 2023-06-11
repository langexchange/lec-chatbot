import os
import logging
from faster_whisper import WhisperModel
# from threading import Lock
from typing import BinaryIO, Union, Optional
import environ
from settings import ROOT_DIR
import time

logger = logging.getLogger(__name__)


env = environ.Env()
environ.Env.read_env(os.path.join(ROOT_DIR,'env/.dev.env'))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class FasterWhisperModel:
    
    def __init__(self):
      model_size= env('MODEL_NAME')
      #TODO: Choose quantization type and device
      logger.info("Starting loading model: ")
      self.model = WhisperModel(model_size, device="cpu", compute_type="int8", download_root="{}/model".format(BASE_DIR))

    """
    - task: enum("transcribe", "translate")
    - language: Language code recorded in audio. See ISO 639-1 Code https://www.loc.gov/standards/iso639-2/php/code_list.php
    - method: enum("openai-whisper", "faster-whisper")
    - encode: Boolean. True if you want to convert binary to wav format first before perform inference
    """
    def inference(self, file: BinaryIO, task: Union[str, None], language: Union[str, None]):
      start_time = time.time()
      options_dict = {"task" : task}
      if language:
          options_dict["language"] = language    

      segments = []
      text = ""
      segment_generator, info = self.model.transcribe(file, beam_size=5, **options_dict)
      for segment in segment_generator:
          segments.append(segment)
          text = text + segment.text
      result = {
          "language": options_dict.get("language", info.language),
          "segments": segments,
          "text": text,
      }
      end_time = time.time()
      logger.info("Audio with duration {} seconds generating text '{}' in {} seconds".format(info.duration, result["text"], end_time - start_time))

      return result

whisperModel = FasterWhisperModel()