from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='torrent_index'),
    path('start/', views.startDownload, name='start_download'),
]