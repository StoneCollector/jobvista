from django.contrib import admin
from accounts.models import *
from jobs.models import Company

admin.site.register(UserProfile)

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
