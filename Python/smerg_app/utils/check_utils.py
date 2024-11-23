#################################   U S E R  V E R I F I C A T I O N     #################################
from smerg_app.models import *

async def check_user(token):
    exist = await UserProfile.objects.filter(auth_token=token).aexists()
    if exist:
        user = await UserProfile.objects.aget(auth_token=token)
        if not user.block:
            return True, user
    return False, None

async def check_exists(value):
    exist = await UserProfile.objects.filter(username=value).aexists()
    if exist:
        user = await UserProfile.objects.aget(username=value)
        return True, user
    return False, None

async def check_email(value):
    exist = await UserProfile.objects.filter(email=value).aexists()
    if exist:
        user = await UserProfile.objects.aget(email=value)
        return True, user
    return False, None

async def check_subscription(user, type=None):
    filter_kwargs = {"user": user}
    if type is not None:
        filter_kwargs["plan__type"] = type

    if await Subscription.objects.filter(**filter_kwargs).aexists():
        subscription = await Subscription.objects.aget(**filter_kwargs)
        if subscription.remaining_posts > 0:
            return True, subscription
    return False, None