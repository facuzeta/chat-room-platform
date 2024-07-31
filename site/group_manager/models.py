from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string
from dateutil.parser import parse
from cms.models import Config
COLORS = ['#D81B60', '#1E88E5', '#FFC107', '#2ebda5']


class Participant(models.Model):

    #If a participant is a real person, it is linked to the AUTH_USER_MODEL
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    #If a participant is a bot, it is linked to the bot model
    bot = models.ForeignKey('bot.Bot', null=True, blank=True, on_delete=models.CASCADE)

    hash = models.CharField(max_length=12, default=get_random_string(length=32))
    group = models.ForeignKey(
        'Group', null=True, blank=True, on_delete=models.SET_NULL, related_name='participants')

    last_beacon = models.DateTimeField(null=True, blank=True)
    invitation_send = models.BooleanField(default=False)
    invitation_send_when = models.DateTimeField(null=True, blank=True)
    experiment_timestamp = models.DateTimeField(null=True, blank=True)

    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=128, null=True, blank=True)
    education = models.CharField(max_length=128, null=True, blank=True)
    nickname = models.CharField(max_length=128, null=True, blank=True)
    
    screener_value = models.FloatField(default=-1)

    def is_bot(self):
        return not(self.bot is None)
        
    def get_nickname(self):
        if (self.nickname is None) or len(self.nickname) < 2:
            return self.user.username
        else:
            return self.nickname

    def get_color(self):
        return dict(zip(self.group.participants.all().order_by('id'),COLORS))[self]

    def update_beacon_state(self):
        self.last_beacon = timezone.now()
        self.save()

    def get_current_stage(self):
        query = StageParticipant.objects.filter(
            participant=self).order_by('timestamp')
        if query.exists():
            return query.last().stage
        else:
            return Stage.get_first_stage()

    def get_current_stage_timestart(self):
        stage = self.get_current_stage()
        query = StageParticipant.objects.filter(stage=stage, participant=self)
        if query:
            return query[0].timestamp

    def get_current_stage_timeout(self):
        stage = self.get_current_stage()
        has_timeout = stage.has_timeout(self.group)
        timestart = self.get_current_stage_timestart()
        has_timestart = timestart is not None
        if has_timeout and has_timestart:
            extra_seconds = stage.get_timeout_in_seconds(self.group)
            return timestart + timezone.timedelta(seconds=extra_seconds)

    def check_is_active(self):
        if self.last_beacon is not None:
            diff = (timezone.now() - self.last_beacon).total_seconds()
            return diff < Config.get('MAX_TIME_ACTIVE_PARTICIPANT_SECONDS')

    def has_completed_s1():
        # TODO
        return True

    def participant_has_completed(self, stage):
        # if stage.name == 'ws2': return True
        return Answer.objects.filter(participant=self, stage=stage).exists()

    def answers(self, stage):
        t0 = StageParticipant.objects.get(participant=self,stage=stage).timestamp
        data = self.answer_set.get(stage=stage).data
        data = list(data.values())
        for d in data:
            d['timestamp'] = parse(d['timestamp'])
        data = sorted(data, key=lambda x: x['timestamp'])
        t_before = t0
        for d in data:
            d['duration'] = (d['timestamp'] - t_before).total_seconds()
            t_before = d['timestamp']
        return data

    def answers_s1(self):
        try:
            stage = Stage.objects.get(name='s1')
            return self.answers(stage)
        except: return []

    def answers_s3(self):
        try:
            stage = Stage.objects.get(name='s3')
            return self.answers(stage)
        except: return []

    def answers_s2(self):
        try:
            res = {}
            for i in range(1,5):
                query = Answer.objects.filter(participant=self, stage__name=f's2_{i}')
                if query.exists():
                    r = query[0].data
                    res[f's2_{i}'] = r
            return res
        except: return []
        


class Stage(models.Model):
    name = models.CharField(max_length=200, unique=True)
    label = models.CharField(max_length=200)

    @classmethod
    def get_first_stage(cls):
        return cls.objects.get(name='ws1')

    def has_timeout(self, group):
        if group is None: return False
        return self.get_timeout_in_seconds(group) > 0 

    def __str__(self): return self.name

    def next(self):
        stages_names = 'ws1 s1 s2_1 s2_2 s2_3 s2_4 s3 thanks'.split()
        dic = dict(zip(stages_names, stages_names[1:]))
        return Stage.objects.get(name=dic[self.name])

    def get_timeout_in_seconds(self, group):
        return self.stagetimes_set.get(experiment=group.experiment).timeout_in_seconds

class StageParticipant(models.Model):
    participant = models.ForeignKey(
        Participant, null=True, blank=True, on_delete=models.SET_NULL)
    stage = models.ForeignKey(
        Stage, null=True, blank=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('participant', 'stage')

class StageTimes(models.Model):
    stage = models.ForeignKey(Stage, null=True, blank=True, on_delete=models.CASCADE)
    experiment = models.ForeignKey('Experiment', null=True, blank=True, on_delete=models.CASCADE)
    timeout_in_seconds = models.IntegerField(default=1*60)
    class Meta:
        unique_together = ('stage', 'experiment')


class Answer(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)
    data = models.JSONField(null=True, blank=True)

    class Meta:
        unique_together = ('participant', 'stage')


def func_create_list8(): return list(range(1,9))
def func_create_list4(): return list(range(1,5))


class Group(models.Model):
    name = models.CharField(max_length=200)
    question_order = models.JSONField(default=func_create_list8)
    question_order_s2 = models.JSONField(default=func_create_list4)
    timestamp = models.DateTimeField(auto_now_add=True)
    experiment = models.ForeignKey('Experiment', on_delete=models.SET_NULL, null=True)

    is_testing = models.BooleanField(default=False)
    
    def get_active_participants(self):
        return [p
                for p in Participant.objects.filter(group=self)
                if p.check_is_active()
                ]

    # def get_current_stage_active_participants(self):
    #     return [p.get_current_stage() for p in Participant.objects.filter(group=self) if p.check_is_active()]

    # def are_active_participants_in_same_stage(self):
    #     return len(set(self.get_current_stage_active_participants()))==1

    # def get_current_group_stage(self):
    #     if self.are_active_participants_in_same_stage():
    #         return self.get_current_stage_active_participants()[0]

    def have_active_participants_completed(self, stage):
        res = [
            p.participant_has_completed(stage)
            for p in self.get_active_participants()
        ]

        return all(res)

    def get_participants_status(self):
        return [(p, p.get_current_stage(), p.get_current_stage_timestart()) for p in self.participants.all()]



class Experiment(models.Model):

    class InputType(models.TextChoices):
        VALUE_AND_CONFIDENCE = 'VALUE_AND_CONFIDENCE','VALUE_AND_CONFIDENCE'
        SLIDER_AGREEMENT = 'SLIDER_AGREEMENT','SLIDER_AGREEMENT'


    name = models.TextField()
    input_type = models.CharField(
        max_length=128,
        choices=InputType.choices,
        default=InputType.VALUE_AND_CONFIDENCE,
    )
    instructions_s2 = models.TextField(default="", null=True, blank=True)

    def __str__(self):
        return self.name

    def has_instructions_s2(self):
        return self.instructions_s2 != ""

        

class Question(models.Model):
    text = models.CharField(max_length=256)
    experiment = models.ForeignKey(Experiment, on_delete=models.SET_NULL, null=True)

class Chat(models.Model):
    text = models.CharField(max_length=2048)
    participant = models.ForeignKey(
        Participant, null=True, blank=True, on_delete=models.SET_NULL)
    stage = models.ForeignKey(
        Stage, null=True, blank=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(auto_now_add=True)
    class Meta:
        indexes = [
            models.Index(fields=['participant', 'stage']),            
        ]

class ChatExpertEvaluationQuestion(models.Model):
    text = models.CharField(max_length=2048)
    def __str__(self): return str(self.id)+' '+self.text


class ChatExpertEvaluatioAnswer(models.Model):
    question = models.ForeignKey('ChatExpertEvaluationQuestion',
        on_delete=models.CASCADE
    )
    group = models.ForeignKey('Group',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    value = models.IntegerField(null=True, blank=True)
    stage = models.ForeignKey('Stage',
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('question', 'user', 'group', 'stage')

