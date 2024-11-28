from django.db import models
from django.db.models import Q
from smerg_app.models import *

class Room(models.Model):
    first_person = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='first_person')
    second_person = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='second_person')
    last_msg = models.CharField(max_length=100, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    created_date = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.last_msg and len(self.last_msg) > 100:
            self.last_msg = self.last_msg[:100]
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['first_person', 'second_person']

class ChatMessage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    sended_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='sended')
    sended_to = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='recieved')
    message = models.TextField(null=True, blank=True, db_collation='utf8_unicode_ci')
    audio = models.FileField(storage=MediaStorage(), upload_to="chat/records/", null=True, blank=True)
    duration = models.CharField(max_length=100, default='', null=True, blank=True)
    attachment = models.FileField(storage=MediaStorage(), upload_to="chat/attachments/", null=True, blank=True)
    attachment_size = models.CharField(default='', max_length=50)
    attachment_type = models.CharField(default='', max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sended_by} to {self.sended_to}..."