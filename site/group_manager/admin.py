from django.contrib import admin
from django.http import HttpResponse
from group_manager.models import *
from django.apps import apps
from django.utils import timezone
import json


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    def download_participant_info(modeladmin, request, queryset):
        res = [(q.id, q.user.email, q.nickname, q.group.id, q.group.experiment.id)
        for q in queryset.all() 
        if len(q.user.email) > 0 and q.group is not None]

        meta = str(timezone.now()).replace("-", "_").replace(" ", "__").replace(":", "_").split(".")[0]
        response = HttpResponse(json.dumps(res, indent=2), content_type="application/json")
        response["Content-Disposition"] = "attachment; filename={}.json".format(meta)

        return response

    def email(self, obj):
        try:
            return obj.user.email
        except:
            return ""

    list_display = ("user", "group", "last_beacon", "nickname", "age", "gender", "education", "email")
    actions = [download_participant_info]


@admin.register(StageParticipant)
class StageParticipantAdmin(admin.ModelAdmin):
    list_display = ("participant", "stage", "timestamp")


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ("name", "label")


@admin.register(StageTimes)
class StageTimesAdmin(admin.ModelAdmin):
    list_display = ("stage", "experiment", "timeout_in_seconds")


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ("participant", "stage", "timestamp", "text")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("participant", "stage", "data")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "text", "experiment")


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    def participants_stage(self, obj):
        return " | ".join(
            [str(p.id) + ":" + stage.name + ":" + str(timeout) for p, stage, timeout in obj.get_participants_status()]
        )

    list_display = (
        "name",
        "participants_stage",
    )


@admin.register(ChatExpertEvaluationQuestion)
class ChatExpertEvaluationQuestionAdmin(admin.ModelAdmin):
    list_display = ("text",)


@admin.register(ChatExpertEvaluatioAnswer)
class ChatExpertEvaluatioAnswerAdmin(admin.ModelAdmin):
    list_display = ("group", "stage", "question", "user", "value")


for model in apps.get_app_config("group_manager").models.values():
    try:
        admin.site.register(model)
    except:
        pass
