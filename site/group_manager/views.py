import json
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import BadRequest, PermissionDenied
from group_manager.models import *
from group_manager.services import *
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseForbidden
from django.contrib.auth import login
from django.contrib.auth import get_user_model
import random
from django.utils.crypto import get_random_string
from cms.models import Content, Config
from collections import defaultdict
from django.conf import settings


def get_cms():
    r = defaultdict(lambda k: k)
    r.update({c.key: c for c in Content.objects.all()})
    return r


def login_participant(request):
    if not request.method == "GET":
        raise BadRequest
    user_hash = request.GET.get("hash", None)
    query = Participant.objects.filter(hash=user_hash)
    print(user_hash, query)
    if query.exists() and user_hash is not None:
        assert query.count() == 1
        user = query[0].user
        login(request, user)

    else:
        if settings.ENV_BEANSTALK:
            return HttpResponseForbidden(request)

        User = get_user_model()
        random_hash = get_random_string(length=32)
        user = User.objects.create(username=random_hash)
        Participant.objects.create(user=user, hash=random_hash)

    login(request, user)
    context = {}
    context["cms"] = get_cms()
    return render(request, "participant_welcome.html", context)


def get_current_participant(request):
    return Participant.objects.get(user=request.user)


@login_required
def get_state(request):
    participant = get_current_participant(request)
    participant.update_beacon_state()
    stage = get_stage_and_change(participant)
    res = {"stage_name": stage.name, "stage_name_clean": stage.label,
    "questions_list": get_serialized_questions(participant)}
    timeout = participant.get_current_stage_timeout()
    if timeout is not None:
        res["timeout"] = timeout

    if stage.name == "s1":
        res["question_order"] = participant.group.question_order
        res["question_order_s2"] = participant.group.question_order_s2
        res["group_name"] = participant.group.name

    if participant.group is not None:
        res['experiment_input_type'] = participant.group.experiment.input_type
        res['experiment_has_instructions_s2'] = participant.group.experiment.has_instructions_s2()
        res['experiment_instructions_s2_content'] = participant.group.experiment.instructions_s2

    return JsonResponse(res)


@csrf_exempt
@login_required
def answer(request):
    if not request.method == "POST":
        raise BadRequest

    participant = get_current_participant(request)
    participant.update_beacon_state()

    stage_frontend = request.POST.get("stage_frontend", None)
    if stage_frontend == "s1":
        data = json.loads(request.POST.get("answer_dic_s1", "{}"))

    if stage_frontend == "s3":
        data = json.loads(request.POST.get("answer_dic_s3", "{}"))

    if "s2" in stage_frontend:
        data = json.loads(request.POST.get("answer_dic_s2", "{}"))

    print(participant.id, participant.get_current_stage(), data)

    stage = Stage.objects.get(name=stage_frontend)
    if not Answer.objects.filter(
        participant=participant,
        stage=stage,
    ).exists():
        Answer.objects.create(participant=participant, stage=stage, data=data)
    return JsonResponse({})


def home(request):
    context = {}

    nickname = request.POST.get("nickname", request.user.first_name)
    age = request.POST.get("age", -1)
    if age == "":
        age = -1
    gender = request.POST.get("gender", "na")
    education = request.POST.get("education", "na")

    participant = Participant.objects.get(user=request.user)
    participant.age = age
    participant.gender = gender
    participant.education = education
    participant.nickname = nickname
    participant.save()

    context["questions_list"] = get_serialized_questions(participant)
    context["POLLINF_FREQ_IN_MS"] = Config.get("POLLINF_FREQ_IN_MS")
    context["MODAL_INSTRUCTIONS_S2_TIMEOUT"] = Config.get("MODAL_INSTRUCTIONS_S2_TIMEOUT")
    context["cms"] = get_cms()
    context["question_order"] = []
    context["question_order_s2"] = []
    context["group_name"] = ""

    current_stage = participant.get_current_stage()
    if current_stage is not None and not current_stage.name == "ws1":
        print("estoy dentro")
        # ya empezo, osea que ya tiene definido variables
        # y entro por que hizo refresh
        context["question_order"] = participant.group.question_order
        context["question_order_s2"] = participant.group.question_order_s2
        context["group_name"] = participant.group.name
        context['experiment_input_type'] = participant.group.experiment.input_type

        print("->", participant.group.question_order)
    return render(request, "index_participant.html", context)


def thanks(request):
    context = {}
    context["cms"] = get_cms()
    return render(request, "thanks.html", context)


def info(request):
    context = {}
    context["cms"] = get_cms()    
    return render(request, "info.html", context)
