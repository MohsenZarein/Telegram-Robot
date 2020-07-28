from django.urls import path
from . import views

urlpatterns = [
    path('add-source-group', views.Add_Source_Group , name='add-source-group'),
    path('add-target-group', views.Add_Target_Group , name='add-target-group'),
    path('add-worker', views.Add_Worker , name='add-worker'),
    path('scrap-members-from-source-groups',views.Scrap_Members , name='scrap-members'),
    
]
