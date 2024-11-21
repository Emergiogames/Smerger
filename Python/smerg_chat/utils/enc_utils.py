#################################  E N C R Y P T / D E C R Y P T  M E S S A G E  #################################
from django.core.signing import Signer
import asyncio

signer = Signer()

def encrypt_message(message):
    return signer.sign(message)

def decrypt_message(encrypted_message):
    if encrypted_message != '':
        return signer.unsign(encrypted_message)