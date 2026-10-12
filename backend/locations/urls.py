from django.urls import path
from .views import AmapView, GeocodeView

urlpatterns = [path('locations/search/', AmapView.as_view()), path('locations/geocode/', GeocodeView.as_view())]
