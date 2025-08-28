from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_lead, name='create_lead'),
] 