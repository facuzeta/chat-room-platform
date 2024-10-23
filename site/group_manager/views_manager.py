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
from django.utils.crypto import get_random_string
from cms.models import Content, Config
from collections import defaultdict
from group_manager.views import get_cms
from django.contrib.admin.views.decorators import staff_member_required
import dateutil.parser
from django.contrib.auth import get_user_model
from bot.models import *
from bot.tasks import *
import logging

logger = logging.getLogger(__name__)

@staff_member_required
def manager(request):
    context = {}
    context['MIN_GROUP_SIZE'] = Config.get('MIN_GROUP_SIZE')
    context['MAX_GROUP_SIZE'] = Config.get('MAX_GROUP_SIZE')
    context['cms'] = get_cms()
    context['experiment'] = Experiment.objects.all()
    context['bot'] = Bot.objects.all()
    context['bot_n'] = range(1,5)
    update_screener_google_form()

    return render(request, 'manager.html', context)



def serializeParticipant(p):
    r = {'id':p.id, 'name':p.user.username, 
         'email':p.user.email, 
         'last_beacon':p.last_beacon,
         'has_group':p.group is not None,
         'nickname': p.nickname,
         'stage':p.get_current_stage().name,
    }
    try:
        r['screener_value'] =  str(int(p.screener_value))
    except:
        pass         
    if r['has_group']:
        r['group_id'] = p.group.id
    return r




@staff_member_required
def manager_update(request):
    if not request.user.is_staff:
        raise PermissionDenied
    
    res = {}
    min_time_active = timezone.now() - timezone.timedelta(seconds=Config.get('MAX_TIME_ACTIVE_PARTICIPANT_SECONDS'))
    query = Participant.objects.filter(last_beacon__gt=min_time_active)
    participant_list = [serializeParticipant(p) for p in query]

    # # // TODO: test, borrar
    # for i in range(10):
    #     ra = random.randint(1,10)
    #     participant_list.append(
    #         {'id':10000+i, 'name':"fruta", 
    #         'email': f'r{ra}@gmail.com', 
    #         'last_beacon': timezone.now(),
    #         'has_group': False,
    #         'nickname': get_random_string(),
    #         'stage': 'ws1',
    #         'screener_value': str(ra),
    #         }
    #     )
    # for i in range(2):
    #     participant_list.append(
    #         {'id':11000+i, 'name':"fruta", 
    #         'email': f'r-1@gmail.com', 
    #         'last_beacon': timezone.now(),
    #         'has_group': False,
    #         'nickname': get_random_string(),
    #         'stage': 'ws1',
    #         'screener_value': str(-1),
    #         }
    #     )

    # participant_list  = [{'id': '10000',
    # 'name': 'fruta',
    # 'email': 'r4@gmail.com',
    # 'last_beacon': timezone.datetime(2022, 5, 26, 16, 58, 44, 22931),
    # 'has_group': False,
    # 'nickname': 'BCw93N8LKgUB',
    # 'stage': 'ws1',
    # 'screener_value': '4'},
    # {'id': '10001',
    # 'name': 'fruta',
    # 'email': 'r2@gmail.com',
    # 'last_beacon': timezone.datetime(2022, 5, 26, 16, 58, 44, 23111),
    # 'has_group': False,
    # 'nickname': 'Hw6bTezAmdR6',
    # 'stage': 'ws1',
    # 'screener_value': '2'},
    # {'id': '10002',
    # 'name': 'fruta',
    # 'email': 'r9@gmail.com',
    # 'last_beacon': timezone.datetime(2022, 5, 26, 16, 58, 44, 23171),
    # 'has_group': False,
    # 'nickname': 'gtZup7fbjHxu',
    # 'stage': 'ws1',
    # 'screener_value': '9'},
    # {'id': '10003',
    # 'name': 'fruta',
    # 'email': 'r9@gmail.com',
    # 'last_beacon': timezone.datetime(2022, 5, 26, 16, 58, 44, 23228),
    # 'has_group': False,
    # 'nickname': 'LSTQThezMVI8',
    # 'stage': 'ws1',
    # 'screener_value': '9'},
    # {'id': '10004',
    # 'name': 'fruta',
    # 'email': 'r6@gmail.com',
    # 'last_beacon': timezone.datetime(2022, 5, 26, 16, 58, 44, 23297),
    # 'has_group': False,
    # 'nickname': '3G0rYgTez18b',
    # 'stage': 'ws1',
    # 'screener_value': '6'},
    # {'id': '10005',
    # 'name': 'fruta',
    # 'email': 'r2@gmail.com',
    # 'last_beacon': timezone.datetime(2022, 5, 26, 16, 58, 44, 23387),
    # 'has_group': False,
    # 'nickname': 'KZGczxzMFmeH',
    # 'stage': 'ws1',
    # 'screener_value': '2'},
    # {'id': '10006',
    # 'name': 'fruta',
    # 'email': 'r4@gmail.com',
    # 'last_beacon': timezone.datetime(2022, 5, 26, 16, 58, 44, 23454),
    # 'has_group': False,
    # 'nickname': 'TXMGrzqo0O0W',
    # 'stage': 'ws1',
    # 'screener_value': '4'},
    # {'id': '10007',
    # 'name': 'fruta',
    # 'email': 'r7@gmail.com',
    # 'last_beacon': timezone.datetime(2022, 5, 26, 16, 58, 44, 23524),
    # 'has_group': False,
    # 'nickname': 'f5RG4NkAdkaA',
    # 'stage': 'ws1',
    # 'screener_value': '7'},
    # {'id': '10008',
    # 'name': 'fruta',
    # 'email': 'r3@gmail.com',
    # 'last_beacon': timezone.datetime(2022, 5, 26, 16, 58, 44, 23576),
    # 'has_group': False,
    # 'nickname': 'BbBOPjbgUGM2',
    # 'stage': 'ws1',
    # 'screener_value': '3'},
    # {'id': '10010',
    # 'name': 'fruta',
    # 'email': 'r-1@gmail.com',
    # 'last_beacon': timezone.datetime(2022, 5, 26, 16, 58, 44, 23981),
    # 'has_group': False,
    # 'nickname': 'gtAIfdhYm13j',
    # 'stage': 'ws1',
    # 'screener_value': '-1'},
    # {'id': '10011',
    # 'name': 'fruta',
    # 'email': 'r-1@gmail.com',
    # 'last_beacon': timezone.datetime(2022, 5, 26, 16, 58, 44, 24067),
    # 'has_group': False,
    # 'nickname': 'zjPHrqXZBfHp',
    # 'stage': 'ws1',
    # 'screener_value': '-1'}]



    try: 
        new_order = sort_participant_by_screener(participant_list)
        res['participants_list'] = new_order
        # Agrego este chequeo por las dudas
        assert(sorted([e['name'] for e in participant_list]) == sorted([e['name'] for e in new_order]))
        assert(sorted([e['screener_value'] for e in participant_list]) == sorted([e['screener_value'] for e in new_order]))
    except:
        logger.error('Entro en except')
        res['participants_list'] = participant_list

    cancel_sort_en_true = request.GET.get('cancel_sort', "false") == 'true'
    if  cancel_sort_en_true:
        logger.info('Parametro get cancel_sort en True' + str(request.GET.get('cancel_sort', "false")))        
        res['participants_list'] = participant_list

    return JsonResponse(res)

@csrf_exempt
@staff_member_required
def create_group_view(request):
    if not request.user.is_staff:
        raise PermissionDenied

    participants_ids_list = request.POST.getlist('participants_ids_list[]', [])    
    experiment_id = request.POST.get('experiment_id', 1)
    bots_n = request.POST.getlist('bot_list[]', [])
    logger.info(str(bots_n))
    #In this way we create a bot participant each time a new group
    # We could add more options in the manager.html to configure there which bots are created/added to a group
    bots_participants = create_bots_participants(bots_n)  
    logger.info(f"create_group_view: participants_ids_list={participants_ids_list}")
    g_id = create_group([Participant.objects.get(id=int(e)) for e in participants_ids_list] + bots_participants, experiment_id)
    return JsonResponse({"group_id":g_id})


@staff_member_required
def start_bots_v(request):
    try:
        data = json.loads(request.body)
        group_id = data.get('group_id')
        running = len(Group.objects.get(id=int(group_id)).get_active_participants()) > 0
        if running:
            bots_participants = Group.objects.get(id=int(group_id)).get_all_bot_participants()
            logger.info("Starting the bots")
            for b in bots_participants:
                celery_run_bot.delay({'pk': b.id})
            return JsonResponse({'status': 'started'})
        else:
            return JsonResponse({'error': 'No active participants found'},status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    

@csrf_exempt
@staff_member_required
def run_bots(request):
    group_id = request.GET.get('group_id')    
    return render(request, 'run_bots.html', {'g_id': group_id})

def create_expert_answers_with_valuation(user, group):
    res = []
    for stage_name in 's2_1 s2_2 s2_3 s2_4'.split():
        query = ChatExpertEvaluatioAnswer.objects.filter(group=group,user=user, stage__name=stage_name)

        list_of_questions_and_answers = []
        for q in ChatExpertEvaluationQuestion.objects.all():
            query_q = query.filter(question=q)
            r = {}
            r['question'] = q
            if query_q.exists():
                answer = query_q[0]
                r['question'] = answer.question
                r['answer'] = answer
            list_of_questions_and_answers.append(r)

        res.append(list_of_questions_and_answers)
    return res


@staff_member_required
def group_status(request, group_id):
    context = {}
    group = Group.objects.get(id=group_id)
    context['group'] = group
    context['cms'] = get_cms()
    context['chats'] = [(Chat.objects.filter(participant__group=group, stage__name=s).order_by('timestamp'), s, questions_and_answers) for s, questions_and_answers in zip('s2_1 s2_2 s2_3 s2_4'.split(), create_expert_answers_with_valuation(request.user, group))]
    return render(request, 'group_status.html', context)


@staff_member_required
def invite_participants(request):
    context = {}
    context['cms'] = get_cms()
    context['participants'] = Participant.objects.all().order_by('-id')
    return render(request, 'invite_participants.html', context)

@csrf_exempt
@staff_member_required
def send_invitation(request, participant_id):
    is_moral = request.GET.get('is_moral') == 'true'
    logger.info('is_moral=' + str(is_moral))    
    
    participant = Participant.objects.get(id=participant_id)
    send_invitation_email(participant, participant.experiment_timestamp)

    context = {}
    context['cms'] = get_cms()
    context['participants'] = Participant.objects.all()
    return render(request, 'invite_participants.html', context)


def different_s2_question_evaluated_by_me(group, user):
    try:
        return len(group.chatexpertevaluatioanswer_set.filter(user=user).values('stage').distinct())
    except:
        return -1

@staff_member_required
def groups_list(request,):
    context = {}
    context['cms'] = get_cms()
    context['groups'] = [(g,different_s2_question_evaluated_by_me(g, request.user)) for g in Group.objects.all().order_by('-id')]
    return render(request, 'groups_list.html', context)


@csrf_exempt
@staff_member_required
def save_participants_data(request):
    participant_id = request.POST.get('participant_id',-1)
    first_name = request.POST.get('first_name','')
    last_name = request.POST.get('last_name','')
    email = request.POST.get('email','')
    experiment_timestamp = dateutil.parser.parse(request.POST.get('experiment_timestamp',''))
    logger.info(f"Participant Info - ID: {participant_id}, First Name: {first_name}, Last Name: {last_name}, Email: {email}, Timestamp: {experiment_timestamp}")
    participant = Participant.objects.get(id=participant_id)
    participant.user.first_name = first_name
    participant.user.last_name = last_name
    participant.user.email = email
    participant.experiment_timestamp = experiment_timestamp
    participant.user.save()
    participant.save()

    return redirect('/manager/invite_participants')


@csrf_exempt
@staff_member_required
def create_participant(request):
    first_name_list = request.POST.getlist('first_name')
    last_name_list = request.POST.getlist('last_name')
    email_list = request.POST.getlist('email')
    experiment_timestamp_list = request.POST.getlist('experiment_timestamp')

    data = list(zip(first_name_list, last_name_list, email_list, experiment_timestamp_list))
    logger.info(data)
    for first_name, last_name, email, experiment_timestamp in data:
        experiment_timestamp = dateutil.parser.parse(experiment_timestamp)
        random_hash = get_random_string(length = 12)
        User = get_user_model()
        user = User.objects.create(first_name=first_name, last_name=last_name, email=email, username=random_hash)
        participant = Participant.objects.create(user=user, hash=random_hash)
        participant.experiment_timestamp = experiment_timestamp
        participant.save()

    return redirect('/manager/invite_participants')

@csrf_exempt
@staff_member_required
def create_participant_mail_list(request):
    emails = request.POST.getlist('emails[]')
    experiment_timestamp = request.POST.get('experiment_timestamp')
    experiment_timestamp = dateutil.parser.parse(experiment_timestamp)
    created_participants = []
    for email in emails:
        experiment_timestamp = experiment_timestamp
        random_hash = get_random_string(length = 12)
        User = get_user_model()
        user = User.objects.create(first_name=get_random_string(length = 12), last_name=get_random_string(length = 12), email=email, username=random_hash)
        participant = Participant.objects.create(user=user, hash=random_hash)
        participant.experiment_timestamp = experiment_timestamp
        participant.save()
        created_participants.append(participant.id)

    return JsonResponse(created_participants, safe=False)


def no_ssl(request):
    return JsonResponse({})


def clean_dic_to_serialize(d):
    d = dict(d)
    for k,v in d.items():
        try: json.dumps(v)
        except:
            d[k] = str(v)

    if '_state' in d:
        del d['_state']
    return d
    
@staff_member_required
def export_all(request):

    if not request.user.is_staff:
        raise PermissionDenied

    res = []
    for group in Group.objects.all():
        r_group = dict(vars(group))
        del r_group['_state']
        r_group['timestamp'] = str(r_group['timestamp'])
        try:
            s1 = {}
            s2 = {}
            s3 = {}
            for p in group.participants.all():
                ans_s1 = p.answers_s1()
                ans_s2 = p.answers_s2()
                ans_s3 = p.answers_s3()

                s1[p.id] = [clean_dic_to_serialize(d) for d in ans_s1]
                s2[p.id] = ans_s2
                s3[p.id] = [clean_dic_to_serialize(d) for d in ans_s3]

            r_group['s1'] = s1
            r_group['s2'] = s2
            r_group['s3'] = s3
        except: 
            pass            
        try:  r_group['participant'] = [clean_dic_to_serialize(vars(d)) for d in group.participants.all()]
        except: pass

        r_group['expert_answers_valuations'] = []
        for cee in  group.chatexpertevaluatioanswer_set.all():
            try:
                r = {'expert_question_text':cee.question.text, 'expert_question_id':cee.question.id,
                'user': cee.user.username, 'value':cee.value, 'stage':cee.stage.name
                }
                r_group['expert_answers_valuations'].append(r)
            except: pass

        chats = {s: [clean_dic_to_serialize(vars(d)) for d in Chat.objects.filter(participant__group=group, stage__name=s).order_by('timestamp')] for s in 's2_1 s2_2 s2_3 s2_4'.split()}
        r_group['chats'] = chats
        res.append(r_group)

    return JsonResponse(res, safe=False)


@csrf_exempt
@staff_member_required
def save_expert_valuation(request):
    answers = json.loads(request.POST.get('answers'))
    for r in answers:
        logger.info(r)
        question_id = r['question_id']
        stage_name = r['stage_name']
        group_id = r['group_id']
        value = int(r['value'])
        question = ChatExpertEvaluationQuestion.objects.get(id=question_id)
        stage = Stage.objects.get(name=stage_name)
        group = Group.objects.get(id=group_id)
        cee, _ = ChatExpertEvaluatioAnswer.objects.get_or_create(question=question,
                                                              stage=stage,
                                                              group=group,
                                                              user=request.user)
        cee.value = value
        cee.save()                                                           

    return JsonResponse({}, safe=False)


