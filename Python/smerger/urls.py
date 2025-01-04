from django.contrib import admin
from django.urls import path,include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static

schema_view = get_schema_view(
   openapi.Info(
      title="SMERGER API",
      default_version='v1',
      description="API DESCRIPTIONS FOR SMERGER",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
   path('admins/', admin.site.urls),
   path('api/',include('smerg_app.urls')),
   path('api/admin/',include('smerg_temp.urls')),
   path('chat/',include('smerg_chat.urls')),
   path('docs/', schema_view.with_ui('swagger', cache_timeout=0),name='schema-swagger'),
   path('docs_2/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)