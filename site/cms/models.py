from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string


class Content(models.Model):
    key = models.CharField(max_length=1024)

    def text(self):
        return self.text_set.all()[0].text

    def __str__(self):
        return self.text()


class Text(models.Model):
    key = models.ForeignKey(Content, on_delete=models.CASCADE)
    lang = models.CharField(max_length=8)
    text = models.TextField(max_length=2048)

    def __str__(self):
        return f'{[self.lang]}: {self.text}'


class Config(models.Model):
    key = models.CharField(max_length=1024, primary_key=True)
    value = models.CharField(max_length=1024)

    @classmethod
    def get(cls, key):
        query = cls.objects.filter(key=key)
        assert(query.exists()),key
        obj = query[0]
        try:
            return int(obj.value)
        except:
            return obj.value
