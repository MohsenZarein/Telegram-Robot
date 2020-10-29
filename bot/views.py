from django.shortcuts import render, render_to_response, redirect
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.core import exceptions
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from .models import Source_Groups
from .models import Target_Groups
from .models import Workers
from .models import Members

from telethon import TelegramClient

from time import sleep
import threading
import datetime
import logging

from .Scripts.Scraper import Scraping
from .Scripts.Adder import Add_Members_To_Target_Groups



""" Logging Configuration """

logger = logging.getLogger(__name__)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

logging.getLogger().setLevel(logging.INFO)
logging.getLogger('telethon').setLevel(level=logging.ERROR)

formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

""" End Configuration """



class IndexView(View):

    @method_decorator(require_GET)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        workers = Workers.objects.all()
        context = {
            "workers":workers
        }
        return render_to_response('bot/index.html', context)
    



class ListOfMembersView(View):

    @method_decorator(require_GET)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request):
        return render(request, 'bot/list-of-members.html')



class ListOfMembersDisplayView(View):

    @method_decorator(require_GET)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        if request.GET['link']:
            link = request.GET['link']
        else:
            link = ""
        desired_members = Members.objects.filter(member_joined_groups__contains=[link]).order_by('member_id')
        paginator = Paginator(desired_members , 100)
        page_number = request.GET.get('page')
        paged_desired_members = paginator.get_page(page_number)

        if page_number == None:
            page_number = "1"

        context = {
            "members":paged_desired_members,
            "link":link,
            "page_number":int(page_number)
        }
        
        return render_to_response('bot/list-of-members-display.html' , context)
        
        


class ListOfPrivacyRestrictedMembersView(View):

    @method_decorator(require_GET)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request):
        privacy_restricted_members = Members.objects.filter(adding_permision=False).order_by('-member_id')

        paginator = Paginator(privacy_restricted_members , 100)
        page_number = request.GET.get('page')
        paged_privacy_restricted_members = paginator.get_page(page_number)

        if page_number == None:
            page_number = "1"

        context = {
            "privacy_restricted_members":paged_privacy_restricted_members,
            "page_number":int(page_number)
        }
        
        return render_to_response('bot/list-of-privacy-restricted-members.html', context)




class NumberOfMembersScrapedByEachWorkerView(View):

    @method_decorator(require_GET)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        return render(request, 'bot/number-of-members-scraped-by-each-worker.html')

    


class NumberOfMembersScrapedByEachWorkerDisplayView(View):

    @method_decorator(require_GET)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request):
        if request.GET['link']:
            link = request.GET['link']
        else:
            link = ""
        workers = Workers.objects.all()
        data = {}
        for worker in workers:
            num_of_members = Members.objects.filter(member_source_group=link , scraped_by=worker).count()
            data[worker] = num_of_members
        
        context = {
            "data":data
        }

        return render_to_response('bot/number-of-members-scraped-by-each-worker-display.html', context)



class AddSourceGroupView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        if request.POST['source_group_link']:
            link = request.POST['source_group_link']
        else:
            link = ""
        if not Source_Groups.objects.filter(link=link).exists():
            source_link = Source_Groups.objects.create(link=link)
            source_link.save()
            messages.success(request,'این گروه به گروه های مبدا اضافه شد')
            return redirect('add-source-group')
            
        else:
            messages.error(request,'این گروه را قبلا اضافه کرده اید')
            return redirect('add-source-group')
    
    def get(self, request):
        return render(request, 'bot/add-source-group.html')



class AddTargetGroupView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        if request.POST['target_group_link']:
            link = request.POST['target_group_link']
        else:
            link = ""
        if not Target_Groups.objects.filter(link=link).exists():
            target_link = Target_Groups.objects.create(link=link)
            target_link.save()
            messages.success(request,'این گروه به گروه های هدف اضافه شد')
            return redirect('add-target-group')
        else:
            messages.error(request,'این گروه را قبلا اضافه کرده اید')
            return redirect('add-target-group')

    def get(self, request):
        return render(request , 'bot/add-target-group.html')




CLIENT = None
class AddWorkerView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):

        global CLIENT

        worker_api_id = request.POST['api_id']
        worker_api_hash = request.POST['api_hash']
        worker_phone = request.POST['phone']

        if not Workers.objects.filter(worker_api_hash=worker_api_hash).exists():
            
            try:
                client = TelegramClient(
                                        worker_phone,
                                        worker_api_id,
                                        worker_api_hash
                )
                client.connect()
                if not client.is_user_authorized():
                    client.send_code_request(worker_phone)
                    

                    
                context = {
                    "phone":worker_phone,
                    "api_id":worker_api_id,
                    "api_hash":worker_api_hash
                }

                CLIENT = client

                messages.success(request,'اکانت ذخیره شد , کد ارسال را شده را برای ثبت وارد کنید')
                return render_to_response('bot/authenticate-worker.html' , context)
            except Exception as err:
                logger.error(err)
                messages.error(request , 'خطا در ذخیره اکانت, دوباره تلاش کنید')
                return redirect('add-worker')
                

        else:
            messages.error(request , 'این اکانت ورکر را قبلا اضافه کرده اید')
            return redirect('add-worker')
    

    def get(self, request):
        return render(request , 'bot/add-worker.html')



class AuthenticateWorkerView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):

        global CLIENT

        try:
            code = request.POST['code']
            phone  = request.POST['phone']
            api_id = request.POST['api_id']
            api_hash = request.POST['api_hash']
        except:
            messages.error(request , 'خطا در ثبت اکانت , دوباره تلاش کنید')
            return redirect('add-worker')


        try:
            CLIENT.sign_in(
                            phone,
                            code
            )

            worker_acc = Workers.objects.create(
                                                worker_api_id=api_id,
                                                worker_api_hash=api_hash,
                                                worker_phone=phone
            )
            worker_acc.save()
            
            CLIENT.disconnect()
            CLIENT = None

            messages.success(request , 'اکانت ثبت شد')
            return redirect('index')
        
        except Exception as err:
            logger.error(err)
            messages.error(request , 'مشگلی در ثبت اکانت وجود دارد , یک بار دیگر تلاش کنید')
            context = {
                    "phone":phone,
                    "api_id":api_id,
                    "api_hash":api_hash
                }
            return render_to_response('bot/authenticate-worker.html' , context)


    def get(self, request):
        return render(request , 'bot/authenticate-worker.html')



class ScrapMembersView(View):

    @method_decorator(require_POST)
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        if request.POST['num_of_workers']:
            num_of_workers = int(request.POST['num_of_workers'])
        else:
            num_of_workers = Workers.objects.all().count()
        if request.POST['limit']:
            limit = int(request.POST['limit'])
        else:
            limit = None
        
        threading.Thread(target=Scraping , args=(num_of_workers,limit)).start()
        messages.success(request , 'استخراج کاربران آغاز شد , میتوانید لاگ های ربات را در کنسول مشاهده کنید')
        return redirect('index')
    
    


campain_counter = 0
class AddMembersView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):

        global campain_counter

        target_group = request.POST['target_group_link']
        source_group = request.POST['source_group_link']
        rate = int(request.POST['rate'])
        leave_after_action_completed = bool(request.POST.get('leave_after_action_completed',''))
        if request.POST['num_of_workers']:
            num_of_workers = int(request.POST['num_of_workers'])
        else:
            num_of_workers = Workers.objects.all().count()
        
        
        try:
            if source_group:
                workers_list = Workers.objects.filter(limited=False , active=False , worker_source_groups__contains=[source_group])[:num_of_workers]
            else:
                workers_list = Workers.objects.filter(limited=False , active=False)[:num_of_workers]
        except exceptions.ObjectDoesNotExist as err:
            logger.error(err)
            messages.error(request , 'خطا در اماده سازی اکانت ورکر')
            return redirect('add-members')
        except Exception as err:
            logger.error(err)
            messages.error(request , 'خطا در اماده سازی اکانت ورکر')
            return redirect('add-members')

        campain_counter = campain_counter + 1
        for worker in workers_list:
            if source_group:
                members_list =  Members.objects.filter(
                                                    Q(scraped_by=worker) & 
                                                    ~Q(member_joined_groups__contains=[target_group]) & 
                                                    Q(adding_permision=True) & 
                                                    Q(member_source_group=source_group)
                    )
            else:
                members_list =  Members.objects.filter(
                                                    Q(scraped_by=worker) & 
                                                    ~Q(member_joined_groups__contains=[target_group]) & 
                                                    Q(adding_permision=True)
                    )

            
            threading.Thread(target=Add_Members_To_Target_Groups, 
                             args=(worker,target_group,members_list,rate,campain_counter - 1,leave_after_action_completed)
                             ).start()
            worker.active = True
            worker.save()
            sleep(1)

        messages.success(request , 'اضافه کردن کاربران به گروه هدف آغاز شد , میتوانید لاگ های ربات را در کنسول مشاهده کنید')
        return redirect('add-members')


    def get(self, request):
        return render(request , 'bot/add-members.html')
