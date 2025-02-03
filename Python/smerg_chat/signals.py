from django.db.models.signals import *
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

@receiver(m2m_changed, sender=Notification.user.through)
def notify_update(sender, instance, action, **kwargs):
    if action == 'post_add':
        print("Notification added")
        channel_layer = get_channel_layer()
        users = instance.user.all()
        if not users.exists():
            print("No users found for notification")
            return
        print(users)
        for user in users:
            print(user, user.id)
            group_name = f'noti_updates_{user.id}'
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'notification',
                    'notification': {
                        'id': instance.id,
                        'title': str(instance.title),
                        'description': str(instance.description),
                        'image': instance.image.url if instance.image else None,
                        'url': instance.url,
                        'created': instance.created_on.strftime('%Y-%m-%d %H:%M:%S')
                    }
                }
            )
            total_second = Room.objects.filter(second_person=user, unread_messages_second__gt=0).count()
            total_first = Room.objects.filter(first_person=user, unread_messages_first__gt=0).count()
            room_group_name =  f'user_{user.id}'
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'room_message',
                    'room_data': {
                        "total_unread": total_first + total_second,
                        "total_noti": Notification.objects.filter(user=user).exclude(read_by=user).count()
                    }
                })

@receiver(m2m_changed, sender=Notification.read_by.through)
def read_update(sender, instance, action, **kwargs):
    channel_layer = get_channel_layer()
    users = instance.user.all()
    if not users.exists():
        print("No users found for notification")
        return
    print(users)
    for user in users:
        print(user, user.id)
        total_second = Room.objects.filter(second_person=user, unread_messages_second__gt=0).count()
        total_first = Room.objects.filter(first_person=user, unread_messages_first__gt=0).count()
        room_group_name =  f'user_{user.id}'
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'room_message',
                'room_data': {
                    "total_unread": total_first + total_second,
                    "total_noti": Notification.objects.filter(user=user).exclude(read_by=user).count()
                }
            })

@receiver(post_save, sender=ChatMessage)
def send_noti(sender, instance, created, **kwargs):
    if created:
        room = Room.objects.get(id=instance.room.id)
        recieved = instance.sended_to

        ## Sending notification to Mobile
        if recieved.onesignal_id:
            send_notifications(instance.message, instance.sended_by.first_name, recieved.onesignal_id)

        ## Sending notification to Web
        channel_layer = get_channel_layer()
        group_name = f'noti_updates_{recieved.id}'
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'notification',
                'notification': {
                    'title': f"You have a new message from {instance.sended_by.first_name}",
                    'description': instance.message,
                }
            }
        )