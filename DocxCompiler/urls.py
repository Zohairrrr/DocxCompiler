from django.urls import path
from . import views

urlpatterns = [
    path('', views.docx_compiler_view, name='compiler_home'),
    path('api/compile/', views.compile_api_view, name='compiler_api'),
]