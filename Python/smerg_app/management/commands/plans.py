from django.core.management.base import BaseCommand
from smerg_app.models import *
from django.utils import timezone
from datetime import timedelta, datetime

# Task creation for deleting PLAN SUBSCRIPTION on EXPIRY (Need to be updated at/ before 11.59)
class Command(BaseCommand):
    help = 'Update Daily'
    def handle(self, *args, **kwargs):
        today = datetime.now().date()
        for i in Subscription.objects.all():
            if i.expiry_date == today:
                i.delete()

        for i in Banner.objects.all():
            if i.validity_date == today:
                i.delete()
