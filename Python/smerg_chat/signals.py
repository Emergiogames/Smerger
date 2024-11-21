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

    # async def async_notify():
    #     channel_layer = get_channel_layer()
    #     await channel_layer.group_send(
    #         'room_updates',
    #         {
    #             'type': 'room_message',
    #             'room_data': {
    #                 'id': instance.id,
    #                 'first_person': instance.first_person.id,
    #                 'first_name': instance.first_person.first_name,
    #                 'first_image': instance.first_person.image.url if instance.first_person.image else None,
    #                 'second_person': instance.second_person.id,
    #                 'second_name': instance.second_person.first_name,
    #                 'second_image': instance.second_person.image.url if instance.second_person.image else None,
    #                 'last_msg': decrypt_message(instance.last_msg),
    #                 'updated': instance.updated.strftime('%Y-%m-%d %H:%M:%S')
    #             }
    #         }
    #     )

    # async_to_sync(async_notify)()

@receiver(post_save, sender=Notification)
def notify_noti_update(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'noti_updates',
        {
            'type': 'notification',
            'noti': {
                'title': instance.title,
                'description': instance.description,
            }
        }
    )

@receiver(post_save, sender=ChatMessage)
def send_noti(sender, instance, created, **kwargs):
    if created:
        room = Room.objects.get(id=instance.room.id)
        recieved = instance.sended_to
        send_notifications(instance.message, instance.sended_by.first_name, recieved.onesignal_id)

        # channel_layer = get_channel_layer()
        # async_to_sync(channel_layer.group_send)(
        #     'noti_updates',
        #     {
        #         'type': 'notification',
        #         'noti': {
        #             'title': "New message",
        #             'description': f"You have a new message from {instance.sended_by.first_name}",
        #         }
        #     }
        # )