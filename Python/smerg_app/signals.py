from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *
from django.utils import timezone

@receiver(post_save, sender=SaleProfiles)
def log_model_save(sender, instance, created, **kwargs):
    action = "Created" if created else "Updated"
    if created:

        ## Check and update subscription
        if Subscription.objects.filter(user = instance.user, plan__type = instance.entity_type.lower()).exists() and Subscription.objects.get(user = instance.user, plan__type = instance.entity_type.lower()).remaining_posts != 0:
            instance.subcribed = False
            instance.save()
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

# Signal for updating posts after a subscription is brought
@receiver(post_save, sender=Subscription)
def log_model_save(sender, instance, created, **kwargs):
    if created:

        # updating unsubscribed posts
        posts = SaleProfiles.objects.filter(user=instance.user, entity_type=instance.plan.type, subcribed=False)[:instance.remaining_posts]
        posts.update(subcribed=True)

        # updating remaining posts count
        instance.remaining_posts = max(0, instance.remaining_posts - first_remaining_profiles.count())
        instance.save()