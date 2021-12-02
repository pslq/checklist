# Based on the solution from :
# https://stackoverflow.com/questions/59371631/send-automated-messages-to-microsoft-teams-using-python

import urllib3
import json
from socket import timeout


class ConnectorCard:
  def __init__(self, hookurl, http_timeout=60):
    self.http = urllib3.PoolManager()
    self.payload = {}
    self.hookurl = hookurl
    self.http_timeout = http_timeout

  def text(self, mtext):
    self.payload["text"] = mtext
    return self

  def send(self):
    headers = {"Content-Type":"application/json"}
    r = self.http.request(
            'POST',
            f'{self.hookurl}',
            body=json.dumps(self.payload).encode('utf-8'),
            headers=headers, timeout=self.http_timeout)
    if r.status == 200:
      return True
    else:
      raise Exception(r.reason)

#
#if __name__ == "__main__":
#    myTeamsMessage = ConnectorCard(MSTEAMS_WEBHOOK)
#    myTeamsMessage.text("this is my test message to the teams channel.")
#    myTeamsMessage.send()
