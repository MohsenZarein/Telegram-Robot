from django.shortcuts import render , redirect
from django.core import exceptions
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator , PageNotAnInteger , EmptyPage


from .models import Source_Groups
from .models import Target_Groups
from .models import Workers
from .models import Members

from telethon import TelegramClient
"""
from telethon.tl.functions.messages import GetDialogsRequest , CheckChatInviteRequest , ImportChatInviteRequest , AddChatUserRequest 
from telethon.tl.types import InputPeerEmpty , InputPeerChannel  ,UserStatusLastMonth  , ChannelParticipantsSearch , InputUser,InputPeerChat
from telethon.tl.functions.channels import InviteToChannelRequest , JoinChannelRequest , GetParticipantsRequest , GetFullChannelRequest
from telethon.errors import PeerFloodError , UserPrivacyRestrictedError , ChatAdminRequiredError , FloodWaitError ,ChannelPrivateError 
"""
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




def index(request):

    workers = Workers.objects.all()
    context = {
        "workers":workers
    }
    return render(request , 'bot/index.html' , context)



def list_of_members(request):

    return render(request , 'bot/list-of-members.html')



def list_of_members_display(request):

    try:
        link = request.GET['link']
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
        
        return render(request , 'bot/list-of-members-display.html' , context)
    
    except Exception as err:
        logger.error(err)
        return render(request , 'bot/list-of-members-display.html')
    


def list_of_privacy_restricted_members(request):

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
    
    return render(request , 'bot/list-of-privacy-restricted-members.html' , context)





def number_of_members_scraped_by_each_worker(request):

    return render(request , 'bot/number-of-members-scraped-by-each-worker.html')




def number_of_members_scraped_by_each_worker_display(request):
    
    try:
        link = request.GET['link']
        workers = Workers.objects.all()
        data = {}
        for worker in workers:
            num_of_members = Members.objects.filter(member_source_group=link , scraped_by=worker).count()
            data[worker] = num_of_members
        
        context = {
            "data":data
        }

        return render(request,'bot/number-of-members-scraped-by-each-worker-display.html' , context)
    
    except Exception as err:
        logger.error(err)
        return render(request , 'bot/number-of-members-scraped-by-each-worker-display.html')



def Add_Source_Group(request):

    if request.method == 'POST':

        link = request.POST['source_group_link']
        if not Source_Groups.objects.filter(link=link).exists():
            source_link = Source_Groups.objects.create(link=link)
            source_link.save()
            messages.success(request,'این گروه به گروه های مبدا اضافه شد')
            return redirect('add-source-group')
            
        else:
            messages.error(request,'این گروه را قبلا اضافه کرده اید')
            return redirect('add-source-group')
            
    else:
        return render(request , 'bot/add-source-group.html')




def Add_Target_Group(request):

    if request.method == 'POST':

        link = request.POST['target_group_link']
        if not Target_Groups.objects.filter(link=link).exists():
            target_link = Target_Groups.objects.create(link=link)
            target_link.save()
            messages.success(request,'این گروه به گروه های هدف اضافه شد')
            return redirect('add-target-group')
        else:
            messages.error(request,'این گروه را قبلا اضافه کرده اید')
            return redirect('add-target-group')

    else:
        return render(request , 'bot/add-target-group.html')



CLIENT = None
def Add_Worker(request):

    if request.method == 'POST':

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
                return render(request , 'bot/authenticate-worker.html' , context)
            except Exception as err:
                logger.error(err)
                messages.error(request , 'خطا در ذخیره اکانت, دوباره تلاش کنید')
                return redirect('add-worker')
                

        else:
            messages.error(request , 'این اکانت ورکر را قبلا اضافه کرده اید')
            return redirect('add-worker')
    
    else:
        return render(request , 'bot/add-worker.html')
        



def Authenticate_Worker(request):

    if request.method == 'POST':

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
            return render(request , 'bot/authenticate-worker.html' , context) 
    
    else:
        
        return render(request , 'bot/authenticate-worker.html')






def Scrap_Members(request):

    if request.method == 'POST':

        if request.POST['num_of_workers']:
            num_of_workers = int(request.POST['num_of_workers'])
        else:
            num_of_workers = Workers.objects.all().count()
        
        threading.Thread(target=Scraping , args=(num_of_workers,)).start()
        messages.success(request , 'استخراج کاربران آغاز شد , میتوانید لاگ های ربات را در کنسول مشاهده کنید')
        return redirect('index')

    else:
        return render(request , 'bot/index.html')




campain_counter = 0
def Add_Members(request):

    global campain_counter

    if request.method == 'POST':

        target_group = request.POST['target_group_link']
        source_group = request.POST['source_group_link']
        rate = int(request.POST['rate'])
        num_of_workers = int(request.POST['num_of_workers'])
        
        try:
            if source_group:
                workers_list = Workers.objects.filter(limited=False , active=False , worker_source_groups__contains=[source_group])[:num_of_workers]
            else:
                workers_list = Workers.objects.filter(limited=False , active=False)[:num_of_workers]
        except exceptions.ObjectDoesNotExist as err:
            logger.error(err)
            return
        except Exception as err:
            logger.error(err)
            return

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

            
            threading.Thread(target=Add_Members_To_Target_Groups , args=(worker,target_group,members_list,rate,campain_counter - 1)).start()
            worker.active = True
            worker.save()
            sleep(2)

        messages.success(request , 'اضافه کردن کاربران به گروه هدف آغاز شد , میتوانید لاگ های ربات را در کنسول مشاهده کنید')
        return redirect('add-members')

    
    else:
        return render(request , 'bot/add-members.html')


        