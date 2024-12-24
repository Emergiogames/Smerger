from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import *
from smerg_app.models import *
from .utils.enc_utils import *
from .utils.noti_utils import *

@receiver(post_save, sender=Room)
def notify_room_update(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'room_updates',
        {
            'type': 'room_message',
            'room_data': {
                'id': instance.id,
                'first_person': instance.first_person.id,
                'first_name': instance.first_person.first_name,
                'first_image': instance.first_person.image.url  if instance.first_person.image else None,
                'second_person': instance.second_person.id,
                'second_name': instance.second_person.first_name,
                'second_image': instance.second_person.image.url  if instance.second_person.image else None,
                'last_msg': decrypt_message(instance.last_msg),
                'updated': instance.updated.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    )

@receiver(post_save, sender=Notification)
def notify_update(sender, instance, **kwargs):
    print("Signal called")
    channel_layer = get_channel_layer()
    for users in instance.user.all().iterator():
        noti_data = {
            'is_read': instance.read_by.filter(id=users.id).exists(),
            'title': instance.title,
            'description': instance.description,
        }
        print(noti_data, users.id)
        group_name = f'noti_updates_{users.id}'
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'notification',
                'noti': noti_data
            }
        )

@receiver(post_save, sender=ChatMessage)
def send_noti(sender, instance, created, **kwargs):
    if created:
        room = Room.objects.get(id=instance.room.id)
        recieved = instance.sended_to
        if recieved.onesignal_id:
            send_notifications(instance.message, instance.sended_by.first_name, recieved.onesignal_id)