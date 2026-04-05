from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import landing_page

urlpatterns = [
    path('', landing_page, name='landing_page'),
    path('admin/', admin.site.urls),
    path('passenger/', include('passengers.urls')),
    path('payments/', include('payments.urls')),
    path('tickets/', include('tickets.urls')),
    path('conductor/', include('conductors.urls')),
    path('sysadmin/', include('sysadmin.urls')),
    path('search/', include('search.urls')),
    path('aggregator/', include('aggregator.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
