# mysite/urls.py
from django.conf.urls.static import static

from django.conf import settings
from django.conf.urls import include
from django.urls import path
from django.contrib import admin
from group_manager.views import get_state, home, \
    answer, login_participant, thanks, info

from group_manager.views_manager import manager, manager_update, \
    create_group_view, group_status, invite_participants, send_invitation, \
    save_participants_data, create_participant, groups_list, no_ssl, \
    export_all, save_expert_valuation, create_participant_mail_list,run_bots,start_bots_v

urlpatterns = [
    path('chat/', include('chat.urls')),
    path('admin/', admin.site.urls),

    path('', no_ssl),
    path('no-ssl', no_ssl),


    path('home', home, name='home'),
    path('get_state', get_state),
    path('answer', answer),
    path('thanks', thanks),

    path('info', info),

    path('login', login_participant),

    path('manager', manager),
    path('manager/groups_list', groups_list),
    path('manager/update', manager_update),
    path('manager/create_group', create_group_view),
    path('manager/group_status/<int:group_id>', group_status),
    path('manager/invite_participants', invite_participants),
    path('manager/send_invitation/<int:participant_id>', send_invitation),
    path('manager/save_participants_data', save_participants_data),
    path('manager/create_participant', create_participant),
    path('manager/create_participant_mail_list', create_participant_mail_list),
    path('manager/export_all', export_all),
    path('manager/expert_valuation', save_expert_valuation, name='save_expert_valuation'),
    path('manager/run_bots', run_bots, name='run_bots'),
    path('manager/start_bots_v/', start_bots_v, name='start_bots_v'),

    path('external_raters/', include('external_raters.urls')),

]

urlpatterns+=static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)