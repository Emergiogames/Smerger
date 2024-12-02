#################################  S E N D  O T P  C O D E  U S I N G  T W I L I O  #################################
import json
import asyncio
from twilio.rest import Client
from django.conf import settings
from asgiref.sync import async_to_sync
from django.http import JsonResponse
from django.views import View

# This is your original synchronous Twilio function
def send_twilio_message(otp, number):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        content_sid="HX74f435f5b9a65118273b98cddd6bfc01",
        from_='whatsapp:+917594088814',
        to=f'whatsapp:+91{number}',
        content_variables=json.dumps({"1": str(otp)}),
    )
    print(f"Message sent with SID: {message.sid}")

# This wraps the synchronous function inside an asynchronous context
async def twilio_int(otp, number):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, async_to_sync(send_twilio_message), otp, number)