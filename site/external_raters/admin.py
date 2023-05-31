from django.contrib import admin
from django.apps import apps
from external_raters.models import *

@admin.register(ExternalRateValue)
class ExternalRateValueAdmin(admin.ModelAdmin):
    def complete(self,obj):
        return obj.value_fermi is not None and obj.value_number is not None
    complete.boolean = True
    list_display = ("stage", "group", "rater","value_fermi","value_number", "complete")


@admin.register(ExternalRater)
class ExternalRaterAdmin(admin.ModelAdmin):
    list_display = ("hash",)



for model in apps.get_app_config("external_raters").models.values():
    try:
        admin.site.register(model)
    except:
        pass
