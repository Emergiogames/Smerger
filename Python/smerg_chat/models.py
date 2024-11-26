from django.db import models
from django.db.models import Q
from smerg_app.models import *

class Room(models.Model):
    first_person = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='first_person')
    second_person = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='second_person')
    last_msg = models.TextField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    created_date = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['first_person', 'second_person']

class ChatMessage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    sended_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='sended')
    sended_to = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='recieved')
    message = models.TextField(null=True, blank=True)
    audio = models.FileField(storage=MediaStorage(), upload_to="chat/records/", null=True, blank=True)
    duration = models.CharField(max_length=100, default='', null=True, blank=True)
    attachment = models.FileField(storage=MediaStorage(), upload_to="chat/attachments/", null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sended_by} to {self.sended_to}..."