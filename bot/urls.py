from django.urls import path
from . import views

urlpatterns = [
    path('' , views.IndexView.as_view() , name='index'),
    path('bot/add-source-group', views.AddSourceGroupView.as_view() , name='add-source-group'),
    path('bot/add-target-group', views.AddTargetGroupView.as_view() , name='add-target-group'),
    path('bot/add-worker', views.AddWorkerView.as_view() , name='add-worker'),
    path('bot/scrap-members-from-source-groups',views.ScrapMembersView.as_view() , name='scrap-members'),
    path('bot/add-members-to-target-groups', views.AddMembersView.as_view() , name='add-members'),
    path('bot/list-of-members' ,views.ListOfMembersView.as_view() , name='list-of-members'),
    path('bot/list-of-privacy-restricted-mebers', views.ListOfPrivacyRestrictedMembersView.as_view() , name='list-of-privacy-restricted-mebers'),
    path('bot/list-of-members-display' , views.ListOfMembersDisplayView.as_view() , name='list-of-members-display'),
    path('bot/authenticate-worker' , views.AuthenticateWorkerView.as_view() , name='authenticate-worker'),
    path('bot/num-of-members-scrp-by-each-wrk' , views.NumberOfMembersScrapedByEachWorkerView.as_view() , name='number-of-members-scraped-by-each-worker'),
    path('bot/num-of-members-scrp-by-each-wrk-dis',views.NumberOfMembersScrapedByEachWorkerDisplayView.as_view(),name='number-of-members-scraped-by-each-worker-display'),

    
]
