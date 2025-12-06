# contact/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'messages', views.ContactMessageViewSet, basename='contact')
router.register(r'stats', views.ContactStatsViewSet, basename='contact-stats')

urlpatterns = [
    path('', include(router.urls)),  
]