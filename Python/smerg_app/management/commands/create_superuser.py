from django.core.management.base import BaseCommand
from smerg_app.models import UserProfile
from django.conf import settings
from decouple import config
from rest_framework.authtoken.models import Token

class Command(BaseCommand):
    help = 'Creates a superuser if none exists'

    def handle(self, *args, **options):
        username = config('DJANGO_SUPERUSER_USERNAME', 'admin1@gmail.com')
        email = config('DJANGO_SUPERUSER_EMAIL', 'admin@gmail.com')
        password = config('DJANGO_SUPERUSER_PASSWORD', 'Adminpass111111@')

        if not UserProfile.objects.filter(username=username).exists():
            self.stdout.write('Creating superuser...')
            user = UserProfile.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                onesignal_id='',
                first_name="Investryx",
                image="https://investryx.com/images/white_emergio_inv.svg",
                block=False
            )
            token = Token.objects.create(user=user)
            self.stdout.write(self.style.SUCCESS('Superuser created successfully'))