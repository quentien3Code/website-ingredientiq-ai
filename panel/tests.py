from django.test import TestCase

# Create your tests here.
import os
from twilio.rest import Client

account_sid = 'TWILIO_ACCOUNT_SID_REMOVED'
auth_token = 'TWILIO_AUTH_TOKEN_REMOVED'
client = Client(account_sid, auth_token)

message = client.messages.create(
    body='Hello from Twilio!',
    from_='+17068625340',   # Your Twilio number (E.164 format)
    to='+917668154063'       # Recipient (E.164 format, no dashes or spaces)
)

print(message.sid)
