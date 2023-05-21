from chatbot.db.connection import pool
from typing import Optional
from lxml import etree

class VcardQuery(object):
  def __new__(cls):
    if not hasattr(cls, 'instance'):
      cls.instance = super(VcardQuery, cls).__new__(cls)
    return cls.instance
  

  def __init__(self):
    pass


  async def getVcardWithJid(self, jid) -> Optional[str]:
    user_id = jid.split("@")[0]
    async with pool.connection() as aconn:
      async with aconn.cursor() as acur:    
        await acur.execute("SELECT vcard FROM vcard WHERE username = %s", (user_id,))
        user_vcard = await acur.fetchone()
        if not user_vcard:
          return None
        return user_vcard[0]


  async def getTargetLanguageWithJid(self, jid) -> Optional[str]:
    user_vcard = await self.getVcardWithJid(jid)
    if user_vcard == None:
      return None
    
    root_el = etree.fromstring(user_vcard)
    target_lang_tag = "{{{}}}{}".format('vcard-temp', "TITLE")
    update_el = root_el.find(target_lang_tag)
    if update_el is None:
      return None

    return update_el.text
  
vcard_model = VcardQuery()