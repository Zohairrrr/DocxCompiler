from django.urls import path
from . import views
from . import api

urlpatterns = [
    path('',views.repo_list,name='repo_list'),
    path('repo/<int:repo_id>/',views.repo_detail,name='repo_detail'),
    path('api/webhook/',api.GitHubWebHookReciever,name='webhook'),
]