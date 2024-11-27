from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from bot.models import *
# Register your models here.
@admin.register(Bot)
class BottAdmin(SimpleHistoryAdmin):
    list_display = ("behaviour_nickname","chatroom_nickname","make_random_nickname_on_create", "model", "system_prompt", "reply_probability", "poll_time","know_own_nickname","use_current_topic", "use_all_chat_history","use_time_left_threshold","time_left_threshold", "empty_replies_enabled","temperature","max_tokens")
    