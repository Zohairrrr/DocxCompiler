from django.contrib import admin
from .models import Repository,Commit
# Register your models here.
admin.site.register(Repository)
admin.site.register(Commit)