from django.urls import path

from . import views
from .views import homePageView

urlpatterns = [
    path("", homePageView, name="home"),
]
