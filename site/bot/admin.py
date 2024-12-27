from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from bot.models import *
# Register your models here.
@admin.register(Bot)
class BottAdmin(SimpleHistoryAdmin):
    list_display = ("behaviour_nickname","chatroom_nickname", "model", "reply_probability", "poll_time", "temperature")
    
@admin.register(Argument)
class ArgumentAdmin(SimpleHistoryAdmin):
    list_display=("argument_text","question", "bot")