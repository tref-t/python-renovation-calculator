from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.templatetags.static import static

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url=static('favicon.ico'), permanent=True)),
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('calculators/', include('apps.calculators.urls')),
]
