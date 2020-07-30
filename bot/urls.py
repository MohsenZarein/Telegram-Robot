from django.urls import path
from . import views

urlpatterns = [
    path('' , views.index , name='index'),
    path('bot/add-source-group', views.Add_Source_Group , name='add-source-group'),
    path('bot/add-target-group', views.Add_Target_Group , name='add-target-group'),
    path('bot/add-worker', views.Add_Worker , name='add-worker'),
    path('bot/scrap-members-from-source-groups',views.Scrap_Members , name='scrap-members'),
    path('bot/add-members-to-target-groups', views.Add_Members , name='add-members'),
    path('bot/list-of-members' ,views.list_of_members , name='list-of-members'),
    
]
