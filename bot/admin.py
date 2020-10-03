from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ngettext
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
    actions = ['update_to_unlimited','update_to_inactive']

    def update_to_unlimited(self,request,queryset):
        updated = queryset.update(limited=False)
        self.message_user(request, ngettext(
            '%d worker was successfully marked as unlimited.',
            '%d workers were successfully marked as unlimited.',
            updated,
        ) % updated, messages.SUCCESS)
    
    
    def update_to_inactive(self,request,queryset):
        updated = queryset.update(active=False)
        self.message_user(request, ngettext(
            '%d worker was successfully marked as inactive.',
            '%d workers were successfully marked as inactive.',
            updated,
        ) % updated, messages.SUCCESS)

    
    update_to_unlimited.short_description = "تغییر وضعیت انتخاب شده ها به حالت بدون محدودیت"
    update_to_inactive.short_description = "تغییر وضعیت انتخاب شده ها به حالت غیرفعال"


admin.site.register(Target_Groups)
admin.site.register(Source_Groups)
admin.site.register(Members , BotAdminMembers)
admin.site.register(Workers , BotAdminWorkers)
