from django.contrib import admin
from bot.models import *
# Register your models here.
@admin.register(Bot)
class BottAdmin(admin.ModelAdmin):
    list_display = ("behaviour_nickname","chatroom_nickname","use_random_nickname", "system_prompt", "reply_probability", "llmodel", "poll_time","use_own_nickname","use_current_topic", "use_all_chat_history","use_time_left_threshold","time_left_threshold","temperature","max_tokens")
    