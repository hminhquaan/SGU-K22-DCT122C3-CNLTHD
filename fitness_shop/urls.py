from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static

from shop.admin_site import admin_site

urlpatterns = [
    path("admin/", admin_site.urls),
    path("", include("shop.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
