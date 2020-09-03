from django.contrib import admin
from .models import Target_Groups , Source_Groups , Members , Workers


class BotAdminMembers(admin.ModelAdmin):
    search_fields = ('member_id','member_access_hash','adding_permision','member_username','member_joined_groups',)
    list_display = ('member_id','member_username',)
    list_display_links = ('member_id',)
    list_per_page = 100


class BotAdminWorkers(admin.ModelAdmin):
    search_fields = ('worker_api_id','worker_api_hash','worker_phone',)
    list_display = ('worker_api_id','worker_api_hash','worker_phone','limited','active',)
    list_display_links = ('worker_phone',)
    list_per_page = 100


admin.site.register(Target_Groups)
admin.site.register(Source_Groups)
admin.site.register(Members , BotAdminMembers)
admin.site.register(Workers , BotAdminWorkers)
