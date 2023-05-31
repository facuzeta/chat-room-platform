# mysite/urls.py
from django.conf.urls.static import static

from django.conf import settings
from django.conf.urls import include
from django.urls import path
from django.contrib import admin

import external_raters.views as views_external_raters

urlpatterns = [
    path('create_external_rater/<slug:hash>/', views_external_raters.create_external_rater, name='create_external_rater'),
    path('rate/<slug:hash>/', views_external_raters.rate, name='rate'),
    path('save_rate/<slug:hash>/<int:erv_id>/<int:value_fermi>/<int:value_number>', views_external_raters.save_rate, name='rate'),
    path('status', views_external_raters.external_raters_status),
    path('download_raters_data', views_external_raters.download_raters_data),
]