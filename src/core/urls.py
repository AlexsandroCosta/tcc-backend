from . import views
from rest_framework import routers
from django.urls import path, include

router = routers.DefaultRouter()
router.register(r'tradutor', views.View, basename='texto-braille')

urlpatterns = [
    path('', include(router.urls)),
]