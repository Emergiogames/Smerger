#################################  S E N D  O T P  C O D E  U S I N G  T W I L I O  #################################
import json
from django.conf import settings
from twilio.rest import Client

def twilio_int(otp, number):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        content_sid="HX74f435f5b9a65118273b98cddd6bfc01",
        from_='whatsapp:+917594088814',
        to= f'whatsapp:+91{number}',
        content_variables=json.dumps({"1": str(otp),}),
    )
    print(message.sid)