from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone

@receiver(post_save, sender=SaleProfiles)
def log_model_save(sender, instance, created, **kwargs):
    action = "Created" if created else "Updated"
    if created:

        ## Check and update subscription
        if Subscription.objects.filter(user = instance.user, plan__type = instance.entity_type.lower()).exists() and Subscription.objects.get(user = instance.user, plan__type = instance.entity_type.lower()).remaining_posts != 0:
            subscribe = Subscription.objects.get(user = instance.user, plan__type = instance.entity_type.lower())
            subscribe.remaining_posts -= 1
            subscribe.save()
  
            ## Create Activity Log
            ActivityLog.objects.create(
                user = instance.user,
                action = action,
                title = "New Post Published",
                description = f"{instance.name} has just published an exciting new post! Dive into their latest content to see what's new and stay engaged with their updates.",
                rate = instance.range_starting,
                img = instance.user.image,
                username = instance.user.first_name
            )
        else:
            instance.delete()