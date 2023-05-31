from multiprocessing import context
from tokenize import group
from django.shortcuts import render, redirect
from django.http import JsonResponse
from group_manager.views import get_cms
from group_manager.views_manager import create_expert_answers_with_valuation
from group_manager.models import *
from external_raters.models import *
from django.core.exceptions import PermissionDenied
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
import random


def rate(request, hash):
    if request.method == "GET":
        context = {}
        context["cms"] = get_cms()

        query = ExternalRater.objects.filter(hash=hash)
        if not query.exists():
            raise PermissionDenied
        er = query[0]

        erv_this_rater = list(
            ExternalRateValue.objects.filter(rater=er, value_fermi__isnull=True, value_number__isnull=True)
        )
        random.shuffle(erv_this_rater)
        context["erv_this_rater"] = erv_this_rater[:20]
        context["total_real"] = len(erv_this_rater)
        context["total"] = ExternalRateValue.objects.filter(rater=er).count()
        context["n_hechos"] = ExternalRateValue.objects.filter(
            rater=er, value_fermi__isnull=False, value_number__isnull=False
        ).count()

        context["hash"] = hash

        map_color = {}
        for group in Group.objects.all():
            map_color.update({p.id: c for p, c in zip(group.participants.all().order_by("id"), COLORS)})

        context["map_color"] = map_color

        return render(request, "external_raters.html", context)


@csrf_exempt
def save_rate(request, hash, erv_id, value_fermi, value_number):
    query = ExternalRater.objects.filter(hash=hash)
    if not query.exists():
        raise PermissionDenied
    er = query[0]

    query = ExternalRateValue.objects.filter(id=erv_id, rater=er)
    if not query.exists():
        raise PermissionDenied
    erv = query[0]

    erv.value_number = value_number
    erv.value_fermi = value_fermi
    erv.save()
    print(erv.id)
    return JsonResponse({"status": "ok"})


@staff_member_required
def create_external_rater(request, hash):

    query = ExternalRater.objects.filter(hash=hash)
    if query.exists():
        return JsonResponse({"status": "error", "msg": "Ya existe rater con este hash"})

    er = ExternalRater.objects.create(hash=hash)

    # todos los grupos
    groups_to_rate = Group.objects.filter(is_testing=False).exclude(experiment__name="exp_moral")

    # crea todas las ExternalRatevalue con valores vacios
    for group in groups_to_rate:
        for stage in Stage.objects.filter(name__in="s2_1 s2_2 s2_3 s2_4".split()):
            # si el chat es vacio no lo sumo
            if len(Chat.objects.filter(participant__group=group, stage=stage)) > 0:
                ExternalRateValue.objects.create(stage=stage, group=group, rater=er)

    return JsonResponse({"status": "ok", "msg": "Creado usuario con hash " + hash})


@staff_member_required
def external_raters_status(request):

    res = []
    for er in ExternalRater.objects.all():

        erv = ExternalRateValue.objects.filter(rater=er)
        n_todo = erv.filter(value_fermi__isnull=True, value_number__isnull=True).count()
        n_done = erv.filter(value_fermi__isnull=False, value_number__isnull=False).count()

        r = {"name": er.hash, "n_todo": n_todo, "n_done": n_done}
        res.append(r)

    context = {}
    context["res"] = res

    return render(request, "external_raters_status.html", context)


@staff_member_required
def download_raters_data(requests):
    from django.contrib.auth.models import User

    question_fermi = ChatExpertEvaluationQuestion.objects.get(
        text="1 - They reached agreement by doing calculations and/or breaking down the problem into smaller estimation problems.  ( 0 - No usaron esta estrategia, 5- No se si la usaron, 10- Usaron completamente esta estrategia)"
    )
    question_number = ChatExpertEvaluationQuestion.objects.get(
        text="2 - They reached an agreement using their individual answers, either by averaging or any other combination procedure. ( 0 - No usaron esta estrategia, 5- No se si la usaron, 10- Usaron completamente esta estrategia)"
    )

    dic_externalraters_id2hash = {e.id:e.hash for e in ExternalRater.objects.all()}
    res_external_raters = [
        {
            "group_id": e.group_id,
            "stage_id": e.stage_id,
            "rater_id": e.rater_id,
            "rater_hash": dic_externalraters_id2hash[e.rater_id],
            "value_fermi": e.value_fermi,
            "value_number": e.value_number,
        }
        for e in ExternalRateValue.objects.all().exclude(value_fermi=None, value_number=None)
    ]


    dic_ourraters_id2username = {u.id: u.username for u in User.objects.filter(id__in=([e.user_id for e in ChatExpertEvaluatioAnswer.objects.all()]))}

    res_our_raters_fermi = [
        {
            "group_id": e.group_id,
            "stage_id": e.stage_id,
            "rater_id": e.user_id,
            "rater_hash": dic_ourraters_id2username[e.user_id], # todo poner esto como un dic asi termina antes
            "value_fermi": e.value,
        }
        for e in ChatExpertEvaluatioAnswer.objects.filter(question=question_fermi)
    ]



    res_our_raters_number = [
        {
            "group_id": e.group_id,
            "stage_id": e.stage_id,
            "rater_id": e.user_id,
            "rater_hash": dic_ourraters_id2username[e.user_id], # todo poner esto como un dic asi termina antes
            "value_number": e.value,
        }
        for e in ChatExpertEvaluatioAnswer.objects.filter(question=question_number)
    ]
    
    res = {
        'res_external_raters': res_external_raters,
        'res_our_raters_fermi':res_our_raters_fermi,
        'res_our_raters_number':res_our_raters_number,

    }
    return JsonResponse(res, safe=False)
