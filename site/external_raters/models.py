import uuid
from django.db import models
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string
from dateutil.parser import parse
from cms.models import Config
from group_manager.models import Stage, Group, Chat



class ExternalRater(models.Model):
    hash = models.CharField(max_length=12, default=get_random_string, unique=True)


class ExternalRateValue(models.Model):
    stage = models.ForeignKey(Stage,
        on_delete=models.CASCADE
    )

    group = models.ForeignKey(Group,
        on_delete=models.CASCADE
    )
    rater = models.ForeignKey(
        ExternalRater,
        on_delete=models.CASCADE
    )

    value_fermi = models.IntegerField(null=True, blank=True)
    value_number = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('stage', 'group', 'rater')

    def get_chat(self):
        return Chat.objects.filter(participant__group=self.group, stage=self.stage).order_by('timestamp')

    def get_question(self):
        return self.group.question_order_s2[int(self.stage.name.split("_")[-1])-1]['text']
