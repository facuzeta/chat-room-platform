from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from bot.api import views

urlpatterns = [
    path('bots/', views.bot_list),
    path('bots/<int:pk>/', views.bot_detail),
]

urlpatterns = format_suffix_patterns(urlpatterns)