from django.contrib import admin
from .models import *

admin.site.register(UserProfile)
admin.site.register(SaleProfiles)
admin.site.register(Query)
admin.site.register(Wishlist)
admin.site.register(Suggestion)
admin.site.register(Testimonial)
admin.site.register(RecentActivity)
admin.site.register(ActivityLog)
admin.site.register(Subscription)
admin.site.register(Banner)
admin.site.register(Plan)
admin.site.register(Preference)
admin.site.register(Notification)
admin.site.register(Activity)
admin.site.register(AadhaarDetails)

class EnquiriesAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'room_id', 'created')


admin.site.register(Enquiries, EnquiriesAdmin)