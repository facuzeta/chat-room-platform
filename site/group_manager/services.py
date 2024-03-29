from group_manager.models import *
from django.db import transaction
from django.utils.crypto import get_random_string
from django.utils import timezone
import random
from django.core.mail import send_mail
from django.template.loader import get_template
import os
import pandas as pd
import numpy as np

def transition(participant, stage2_name):
    StageParticipant.objects.create(participant=participant,
                                    stage=stage2_name)


# this transition ocurrs when group is created.
# staff member triggers it
def transition_ws1_s1(participant):
    current_stage = participant.get_current_stage()
    assert(current_stage.name == 'ws1')
    transition(participant, Stage.objects.get(name='s1'))


def get_stage_and_change(participant):
    current_stage = participant.get_current_stage()

    if current_stage.name == 'ws1':
        # no hago nada porque de ws1 me saca un admin
        pass

    # if current_stage.name == 'ws2':
    #     group = participant.group

    #     if group.have_active_participants_completed(current_stage):
    #         print('estoy en get_stage_and_change ws2 TRUE')
    #         transition(participant, current_stage.next())

    if current_stage.name in ['s1']:
        group = participant.group

        if group.have_active_participants_completed(current_stage) or \
           stage_timeout(participant, current_stage):
            transition(participant, current_stage.next())

    if current_stage.name in [ 's2_1', 's2_2', 's2_3', 's2_4', 's3']:
        if stage_timeout(participant, current_stage):
            transition(participant, current_stage.next())

    return participant.get_current_stage()


def stage_timeout(participant, stage):
    query = StageParticipant.objects.filter(
        participant=participant, stage=stage)
    if not query.exists():
        return False
    sp = query[0]
    diff_seconds = (timezone.now() - sp.timestamp).total_seconds()
    return diff_seconds >= stage.get_timeout_in_seconds(participant.group)


def create_question_order(experiment):
    questions = [{'question_id': q.id, 'text': q.text}
                 for q in (Question.objects.filter(experiment=experiment))]


    # comment shuffling to repeat experimental desing from tedx
    random.shuffle(questions)
    questions_new_order = list(questions)

    random.shuffle(questions)
    questions_new_order_s2 = questions[:4]

    return questions_new_order, questions_new_order_s2


# create group and move participant to s1
@transaction.atomic
def create_group(list_of_participants, experiment_id=1):
    experiment = Experiment.objects.get(id=experiment_id)
    
    # Check that all participants are in sw1
    for participant in list_of_participants:
        if participant.get_current_stage() == Stage.get_first_stage():
            print(f'create_group: participant {participant.id} no estaba en first_stage')
        assert(participant.get_current_stage() == Stage.get_first_stage())

    group = Group.objects.create(name=get_random_string(), experiment=experiment)

    for participant in list_of_participants:
        transition_ws1_s1(participant)
        participant.group = group
        participant.save()

    questions_new_order, questions_new_order_s2 = create_question_order(experiment)

    group.question_order = questions_new_order
    group.question_order_s2 = questions_new_order_s2

    group.save()



def send_invitation_email(participant, timestamp_experiment):
    participant.invitation_send = True
    participant.invitation_send_when = timezone.now()
    participant.save()
    email = participant.user.email
    link = settings.DOMAIN+f'/login?hash={participant.hash}'
    timestamp_experiment = timestamp_experiment

    calendar_start_datetime = '20220112T200000Z'
    calendar_end_datetime = '20220112T200000Z'
    calendar_details = ''
    calendar_title = ''
    link_mas_info_experiment = 'https://'

    context = {}
    context['first_name'] = participant.user.first_name
    context['last_name'] = participant.user.last_name
    context['link_more_info'] = settings.DOMAIN+'/info'
    context['timestamp_experiment'] = timestamp_experiment.astimezone()
    context['link_experiment'] = link
    
    template_filename = os.path.join(settings.BASE_DIR,
                                     'templates/',
                                     'email_invitation.html')
    template = get_template(template_filename)
    html = template.render(context)

    datetime_subject = str(timestamp_experiment.astimezone()).split('.')[0][:-3]
    send_mail(f'Invitación {datetime_subject}', '', f'Invitación Experimento<{settings.EMAIL}>', [email], html_message=html)



def get_serialized_questions(participant):
    if participant.group is None: return []
    try:
        experiment = participant.group.experiment
        return [
        {"question_id": q.id, "text": q.text} for q in Question.objects.filter(experiment=experiment)
        ]
    except: 
        print('except en get_serialized_questions')
        return []



def update_screener_google_form():
    # version de prueba
    # sheet_id = "1AMzexrvAbVuAGJRLp3nfDfoN0EcZDt5GvDYIF4rPxKs"
    # sheet_name = "Form%20Responses%201"
    try:
        sheet_id = "1P79yI0vkdwJtotx77JJ1vIrVgeD0K0azMJziY8sRMTM"
        sheet_name = "Form%20responses%201"

        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(url)

        headers_preguntas = ['La oferta y demanda de trabajo sexual debería ser legal.',
        'No debería existir ningún límite a la libertad de expresión.',
        'La subrogación de vientres para tener hijos debería ser legal.',
        'Todas las personas deberían ser vegetarianas.',
        'De ser científicamente posible, las personas deberían ser inmortales.',
        ]
        
        df['screener'] = df[headers_preguntas].values.tolist()
        dic = dict(df[['Tu email', 'screener']].values)

        for email in dic:
            try:
                Participant.objects.filter(user__email=email).update(screener_value=np.nanmean(dic[email]))
            except:
                pass
    except:
        pass

def sort_participant_by_screener(l_arg):
    l = list(l_arg)

    # saco los -1 para poner al final
    l_minus1 = [e for e in l if float(e['screener_value']) == -1]
    for e in l_minus1:
        l.remove(e)

    new_order = list()
    while len(l) > 2:
        l_max = max(l, key=lambda x: float(x['screener_value']))
        l.remove(l_max)

        l_min = min(l, key=lambda x: float(x['screener_value']))
        l.remove(l_min)

        l_median = sorted(l, key=lambda x: float(x['screener_value']))
        l_median = l_median[int(len(l_median)/2)]
        l.remove(l_median)

        new_order.append(l_max)
        new_order.append(l_median)
        new_order.append(l_min)

    if len(l) > 0 :
        new_order += l

    new_order += l_minus1

    return new_order



def sort_participant_by_screener_test():
    def sort_participant_by_screener_test_builder(a=4,b=4,c=4):
        l_test = []

        for i in range(a):
            r = {'screener_value': 9+random.randint(-1,1), }
            r['name'] = get_random_string()
            l_test.append(r)

        for i in range(b):
            r = {'screener_value': 5+random.randint(-1,1), }
            r['name'] = get_random_string()
            l_test.append(r)

        for i in range(c):
            r = {'screener_value': 1+random.randint(-1,1), }
            r['name'] = get_random_string()
            l_test.append(r)
        return l_test

    for i in range(100):
        a = random.randint(3,10)
        b = random.randint(3,4)
        c = random.randint(3,100)
        # print(len(l_test),a,b,c)
        l_test = sort_participant_by_screener_test_builder(a,b,c)
        assert(sorted([e['name'] for e in l_test]) == sorted([e['name'] for e in sort_participant_by_screener(l_test)]))
        assert(sorted([e['screener_value'] for e in l_test]) == sorted([e['screener_value'] for e in sort_participant_by_screener(l_test)]))
        assert(len(l_test)==len(sort_participant_by_screener(l_test)))