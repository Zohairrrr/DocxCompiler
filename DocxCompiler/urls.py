from django.urls import path
from .views import docx_compiler_view

urlpatterns = [
    path('', docx_compiler_view, name='compiler_home'),
]