from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *
from django.utils import timezone  

class UserSerial(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'

class SaleProfilesSerial(serializers.ModelSerializer):
    class Meta:
        model = SaleProfiles
        fields = '__all__'

    def update(self, instance, validated_data):
        # Exclude 'verified' from user updates
        validated_data.pop('verified', None)  # Remove verified from any user input
        instance.verified = False  # Force set to False on updates
        return super().update(instance, validated_data)

class WishlistSerial(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = '__all__'

class RecentSerial(serializers.ModelSerializer):
    class Meta:
        model = RecentActivity
        fields = '__all__'

class ContactSerial(serializers.ModelSerializer):
    class Meta:
        model = Query
        fields = '__all__'

class SuggestSerial(serializers.ModelSerializer):
    class Meta:
        model = Suggestion
        fields = '__all__'

class TestSerial(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = '__all__'

class TransSerial(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = '__all__'

class BannerSerial(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = '__all__'

class PrefSerial(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = '__all__'

class PlanSerial(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'

class SubscribeSerial(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'

class NotiSerial(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class EnqSerial(serializers.ModelSerializer):
    user = UserSerial()

    class Meta:
        model = Enquiries
        fields = '__all__'

class ActivitySerial(serializers.ModelSerializer):
    post = SaleProfilesSerial()

    class Meta:
        model = Activity
        fields = '__all__'

class ReportSerial(serializers.ModelSerializer):
    report_post = SaleProfilesSerial()

    class Meta:
        model = Report
        fields = '__all__'

class AadhaarSerial(serializers.ModelSerializer):
    class Meta:
        model = AadhaarDetails
        fields = '__all__'