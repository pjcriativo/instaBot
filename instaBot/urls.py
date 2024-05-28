from django.urls import path
from painel_web import views

urlpatterns = [
    path('', views.bot_view, name="bot"),
]
