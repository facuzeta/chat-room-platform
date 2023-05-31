from django.contrib import admin
from cms.models import *
from django.apps import apps
from django.utils import timezone

class TextInline(admin.TabularInline):
    model = Text
    extra = 0


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    def all_texts(self, obj):
        return list(obj.text_set.all())
    list_display = ('key', 'all_texts',)
    inlines = [TextInline]




@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ('key', 'value',)

for model in apps.get_app_config('cms').models.values():
    try:
        admin.site.register(model)
    except:
        pass