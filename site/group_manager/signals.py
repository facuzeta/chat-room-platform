from django.db.models.signals import post_save
from django.dispatch import receiver

from group_manager.models import Experiment, Stage, StageTimes


@receiver(post_save, sender=Experiment)
def experiment_create_post_save(sender, instance, created, **kwargs):
    if created:
        try:
            for stage in Stage.objects.all():
                StageTimes.objects.get_or_create(experiment=instance, stage=stage, timeout_in_seconds=300)
        except:
            print('Except in signals doctor_create_post_save', instance.id)
