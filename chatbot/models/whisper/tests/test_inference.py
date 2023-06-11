import unittest
from ..model import whisperModel
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class TestInference(unittest.TestCase):
  def setUp(self) -> None:
    self.audioPath= os.path.join(BASE_DIR, "audios")
  def test_basic_inference(self):
    with open("{}/audio1.mp3".format(self.audioPath), "rb") as f:
      result = whisperModel.inference(f, "transcribe", "en")
      self.assertEqual(result["text"], " Our voices pronounce your texts in their own language using a specific accent.")