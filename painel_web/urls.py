from django.urls import path
from painel_web import views

urlpatterns = [
    path('', views.home_view, name='home'),  # Página inicial
    path('bot/', views.bot_view, name='bot'),  # Página do bot
]
