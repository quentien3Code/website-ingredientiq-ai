from django.test import TestCase

# Create your tests here.
import os
from twilio.rest import Client

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

message = client.messages.create(
    body='Hello from Twilio!',
    from_='+17068625340',   # Your Twilio number (E.164 format)
    to='+917668154063'       # Recipient (E.164 format, no dashes or spaces)
)

print(message.sid)
