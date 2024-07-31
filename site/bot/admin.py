from django.contrib import admin
from bot.models import *
# Register your models here.
@admin.register(Bot)
class BottAdmin(admin.ModelAdmin):
    list_display = ("system_prompt", "reply_probability", "behaviour_nickname", "llmodel")
    