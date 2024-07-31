from django.db import models

# Create your models here.
class Bot(models.Model):   
    system_prompt = models.CharField(max_length=128) 
    reply_probability = models.FloatField(default=0.5)
    behaviour_nickname= models.CharField(max_length=128) 
    llmodel = models.CharField(max_length=128)
    
    