from django.urls import path
from .views import ParseIntentView

urlpatterns = [path('ai/parse-intent/', ParseIntentView.as_view())]
