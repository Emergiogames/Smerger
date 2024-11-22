#################################  S E R I A L I Z E  A S Y N C  D A T A S  #################################
from smerg_app.serializers import *
from smerg_app.models import *
from asgiref.sync import sync_to_async

@sync_to_async
def serialize_data(data, serial):
    serializer = serial(data, many=True)
    return serializer.data

@sync_to_async
def get_serialize_data(data, serial):
    serializer = serial(data)
    return serializer.data

@sync_to_async
def create_serial(serial, data):
    serializer = serial(data = data)
    if serializer.is_valid():
        return True, serializer.save()
    return False, serializer.errors

@sync_to_async
def update_serial(serial, data, model):
    serializer = serial(model, data=data, partial=True)
    if serializer.is_valid():
        return True, serializer.save()
    return False, serializer.errors