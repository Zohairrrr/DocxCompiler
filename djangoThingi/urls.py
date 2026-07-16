from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("polls/", include("polls.urls")),
    path("admin/", admin.site.urls),
    path("", include('DocxCompiler.urls')),
    path('gitfetch/', include('GitFetch.urls')),
    path('torrent/', include('TorrentEngine.urls')),  
]