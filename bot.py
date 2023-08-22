import os
from dotenv import load_dotenv 
import ssl
from flask import Flask, request, Response
from slack_sdk import WebClient
from slackeventsapi import SlackEventAdapter

load_dotenv()
print(os.getenv("SLACK_TOKEN"))
load_dotenv()
print(os.getenv("SIGNING_SECRET"))
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

slack_event_adapter = SlackEventAdapter(os.getenv("SIGNING_SECRET"), '/slack/events')
app = slack_event_adapter.server

client = WebClient(token=os.getenv("SLACK_TOKEN"), ssl=ssl_context)

env_path = ".env"
load_dotenv(env_path)

#client.chat_postMessage(channel="#test", text="Hello World!")
BOT_ID = client.api_call("auth.test")["user_id"]

message_counts = {} #makes sense to put it in a database implement later 
welcome_messages = {}

class WelcomeMessage():
    START_TEXT = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                "Welcome to this channel! \n\n"
                "*Get started by completing the tasks!*"
            )
        }
    }

    DIVIDER = {"type": "divider"}

    def __init__(self, channel, user):
        self.channel = channel
        self.user = user
        self.icon_emoji = ":robot_face:"
        self.timestamp = ""
        self.completed = False

    def get_message(self):
        checkmark = ":white_check_mark:" if self.completed else ":white_large_square:"
        text = f"{checkmark} *React to this message!*"
        return {
            "ts": self.timestamp,
            "channel": self.channel,
            "username": "Welcome Robot!",
            "icon_emoji": self.icon_emoji,
            "blocks": [
                self.START_TEXT,
                self.DIVIDER,
                {"type": "section", "text": {"type": "mrkdwn", "text": text}}
            ]
        }

    def _get_reaction_task(self):
        checkmark = ":white_check_mark:" if self.completed else ":white_large_square:"
        text = f"{checkmark} *React to this message!*"
        return {"type": "section", "text": {"type": "mrkdwn", "text": text}}



def send_welcome_message(channel, user):
     welcome = WelcomeMessage(channel, user)
     message = welcome.get_message()
     response = client.chat_postMessage(**message)
     welcome.timestamp = response["ts"]

     if channel not in welcome_messages:
          welcome_messages[channel] = {}
     welcome_messages[channel][user] = welcome

# Reactions to Messages Sent 
@slack_event_adapter.on("message")
def handle_message(payload):
    print(payload)
    event = payload.get("event", {})
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")

    if user_id != None and BOT_ID != user_id:
        if user_id in message_counts:
             message_counts[user_id] += 1
        else :
             message_counts[user_id] = 1

        if text.lower() == "start":
             send_welcome_message(f"@{user_id}", user_id)

# Message Count Function 
@app.route("/message-count", methods=["POST"])
def message_count():
     data = request.form
     user_id = data.get("user_id")
     channel_id = data.get("channel_id")
     message_count = message_counts.get(user_id, 0)

     client.chat_postMessage(channel=channel_id, text=f"Message: {message_count}")
     return Response(), 200

if __name__ == "__main__":
        app.run(port=3000, debug=True)

