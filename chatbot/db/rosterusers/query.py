from typing import List
from chatbot.db.connection import pool
import logging

logger = logging.getLogger(__name__)

class RosterUserQuery():
  def __new__(cls):
    if not hasattr(cls, 'instance'):
      cls.instance = super(RosterUserQuery, cls).__new__(cls)
    return cls.instance
  

  def __init__(self):
    pass
  
  # NOTE: THIS FUNCTION ONLY SUPPORT EQUAL CONDITION
  async def getRosterContact(self, **kwargs) -> List[str]:
    """
      username: str,
      jid: str
    """
    async with pool.connection() as aconn:
      async with aconn.cursor() as acur:
        # Prepare query string
        field_list = list(kwargs.keys())
        value_list = list(kwargs.values())
        query_str = "SELECT id, jid FROM rosterusers WHERE {} = %s".format(field_list[0])
        for field in field_list[1:]:
          query_str += " AND {} = %s ".format(field)
        await acur.execute(query_str, value_list)
        contacts = await acur.fetchall()
        return contacts
      

  async def addRosterContact(self, user_id: str, contact_jid: str) -> None:
    # Check if there exists contact_jid in user's roster
    contacts = await self.getRosterContact(username=user_id, jid=contact_jid)
    if contacts:
      logger.warning("The contact {} has existed in the user roster {}".format(contact_jid, user_id))
      return
    
    async with pool.connection() as aconn:
      async with aconn.cursor() as acur:
        await acur.execute("INSERT INTO rosterusers(username, jid, nick, subscription, ask, askmessage, server, subscribe, type) VALUES (%s, %s, '', 'B', '', '', '', '', 'item')", (user_id, contact_jid,))
        if acur.rowcount == 0:
          logger.warning("Insert contact {} to {}'s roster unsuccessfully for some reason".format(contact_jid, user_id))
          return
        logger.info("Insert contact {} to {}'s roster successfully".format(contact_jid, user_id))


roster_user_model = RosterUserQuery()