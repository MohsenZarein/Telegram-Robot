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
from telethon.tl.functions.messages import GetDialogsRequest , CheckChatInviteRequest , ImportChatInviteRequest , AddChatUserRequest 
from telethon.tl.types import InputPeerEmpty , InputPeerChannel  ,UserStatusLastMonth  , ChannelParticipantsSearch , InputUser,InputPeerChat
from telethon.tl.functions.channels import InviteToChannelRequest , JoinChannelRequest , GetParticipantsRequest , GetFullChannelRequest
from telethon.errors import PeerFloodError , UserPrivacyRestrictedError , ChatAdminRequiredError , FloodWaitError ,ChannelPrivateError 

from time import sleep
import threading
import datetime
import logging
import os
import socks
import sys
import random



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
        
        threading.Thread(target=Scraping).start()
        messages.success(request , 'استخراج کاربران آغاز شد , میتوانید لاگ های ربات را در کنسول مشاهده کنید')
        return redirect('index')

    else:
        return render(request , 'bot/index.html')





def Add_Members(request):

    if request.method == 'POST':

        group = request.POST['target_group_link']
        rate = int(request.POST['rate'])
        rate = rate + 5
   

        try:
            workers_list = Workers.objects.filter(limited=False)
        except exceptions.ObjectDoesNotExist as err:
            logger.error(err)
            return
        except Exception as err:
            logger.error(err)
            return


        for worker in workers_list:
            members_list =  Members.objects.filter(Q(scraped_by=worker) & ~Q(member_joined_groups__contains=[group]) & Q(adding_permision=True))[:rate]
            threading.Thread(target=Add_Members_To_Target_Groups , args=(worker,group,members_list)).start()
            sleep(2)

        messages.success(request , 'اضافه کردن کاربران به گروه هدف آغاز شد , میتوانید لاگ های ربات را در کنسول مشاهده کنید')
        return redirect('add-members')

    
    else:
        return render(request , 'bot/add-members.html')


        


def Add_Members_To_Target_Groups(worker , group , members_list):

    logger.info('START ADDING TO {0}...'.format(group))
    sleep(5)
    try:
        client = TelegramClient(
                                worker.worker_phone,
                                worker.worker_api_id,
                                worker.worker_api_hash
        )
        client.connect()
        if not client.is_user_authorized():
            logger.error('worker with {0} api_id is not signed in , skiping this worker'.format(worker.worker_api_id))
            return

        chat_status = ""
        try:
            group_entity = client.get_entity(group)
            sleep(random.randrange(120,200))
            client(JoinChannelRequest(group_entity))
            logger.info('Joined source channel')
            chat_status = "public"
            sleep(random.randrange(120,200))
        except Exception:
            try:
                client(ImportChatInviteRequest(group.split('/')[-1]))
                logger.info('Joined source chat')
                sleep(random.randrange(300,350))
                group_entity = client.get_entity(group)
                chat_status = "private"
                sleep(random.randrange(120,200))

            except Exception as err:
                logger.error(err)
                logger.error('Skipping This Worker...')
                client.disconnect()
                return
        
        target = InputPeerChannel(
                                int(group_entity.id),
                                int(group_entity.access_hash)
        )

        max_retry_for_peerflood = 7
        for member in members_list:
    
            try:
                logger.info("Adding {0}  {1} ...".format(int(member.member_id),member.member_username))
                
                user_ready_to_add = InputUser(
                    user_id=int(member.member_id),
                    access_hash=int(member.member_access_hash)
                )

                client(InviteToChannelRequest(
                                            target,
                                            [user_ready_to_add]
                ))
                this_member = Members.objects.get(member_id=member.member_id)
                this_member.member_joined_groups.append(group)
                this_member.save()
                max_retry_for_peerflood = 5
                logger.info("User Added ... going to sleep for 900-1000 sec")
                sleep(random.randrange(900,1000))
            except PeerFloodError:
                logger.info("Peer flood error ! Too many requests on destination server !")
                logger.info('Going for 1000 - 1100 sec sleep')
                max_retry_for_peerflood = max_retry_for_peerflood - 1
                if max_retry_for_peerflood <= 0 :
                    logger.error("This worker is limited ... Returned")
                    this_worker = Workers.objects.get(worker_api_hash=worker.worker_api_hash)
                    this_worker.limited = True
                    this_worker.save()
                    return
                sleep(random.randrange(1000,1100))
                continue
            except FloodWaitError as err:
                logger.error('Something wrong with the server , Have to sleep ' + err.seconds + ' seconds')
                sleep(err.seconds)
                continue
            except UserPrivacyRestrictedError:
                logger.info("This user's privacy does not allow you to do this ... Skipping this user")
                logger.info("Going for 900-1000 sec sleep")
                this_member = Members.objects.get(member_id=member.member_id)
                this_member.adding_permision = False
                this_member.save()
                max_retry_for_peerflood = 5
                sleep(random.randrange(800,900))
                continue
            except Exception as err:
                logger.error(err)
                try:
                    user_ready_to_add = InputUser(
                        user_id=int(member.member_id),
                        access_hash=int(member.member_access_hash)
                    )
                    chat_target = InputPeerChat(int(group_entity.chat_id))
                    client(AddChatUserRequest(
                                              chat_target,
                                              user_ready_to_add,
                                              fwd_limit=100
                    ))
                    this_member = Members.objects.get(member_id=member.member_id)
                    this_member.member_joined_groups.append(group)
                    this_member.save()
                    logger.info("User Added ... going to sleep for 900-1000 sec")
                    sleep(random.randrange(900,1000))
                except Exception as err:
                    logger.error(err)
                    logger.error("Going for 800-900 sec sleep")
                    sleep(random.randrange(800,900))
                    continue

        logger.info('Action completed')
        client.disconnect()
    

    except ConnectionError as err:
        logger.error(err)
        logger.info('----Use a proxy or VPN-----')
        return
    except KeyboardInterrupt:
        print('keyboard interupt...')
        client.disconnect()
        return
    except Exception as err:
        logger.error(err)
        print('EXEPTION')
        client.disconnect()
        return





FULL_MEMBER_LIST = []
def Scraping():

    global FULL_MEMBER_LIST

    logger.info("START SCRAPING ...")
    try:

        try:
            workers_list = Workers.objects.filter(limited=False)
        except exceptions.ObjectDoesNotExist as err:
            logger.error(err)
            return
        except Exception as err:
            logger.error(err)
            return

        clients = []
        for worker in workers_list:
            try:
                client = TelegramClient(
                                        worker.worker_phone,
                                        worker.worker_api_id,
                                        worker.worker_api_hash
                )
                client.connect()
                if not client.is_user_authorized():
                    logger.error('worker with {0} api_id is not signed in , skiping this worker'.format(worker.worker_api_id))
                    continue
                    
                worker_and_client_obj = [client,worker]
                clients.append(worker_and_client_obj)
                logger.info('a client connected...')
                sleep(5)
            except Exception as err:
                logger.error(err)
                continue
        
        if not clients:
            logger.error('None of clients connected ! try again...')
            return
        
        logger.info('some clients connected successfuly ! ...')
        sleep(10)

        
        try:
            groups = Source_Groups.objects.all()
        except exceptions.ObjectDoesNotExist:
            logger.error('There is not any source groups in database !')
            for i in range(len(clients)):
                clients[i][0].disconnect()
                sleep(1)
            return
        except Exception as err:
            logger.error(err)
            for i in range(len(clients)):
                clients[i][0].disconnect()
                sleep(1)
            return
        
        for group in groups:
        
            data = clients[0][0](GetFullChannelRequest(group.link))
            limit = int(data.full_chat.participants_count / len(clients))
            
            if limit > 180:
                limit = 180

            print('limit :',limit)
            
            #workers_threads = []
            for i in range(len(clients)):

                th = threading.Thread(target=Scrap , args=(clients[i],group))
                th.start()
                th.join()


                """
                for worker in workers_threads:
                    worker.start()
                    sleep(1)
                

                for worker in workers_threads:
                    worker.join()
                """

                logger.info('Now saving members of {0} into database ...'.format(group.link))
            
                counter = 0
                for member in FULL_MEMBER_LIST[2]:
                    if counter < limit:
                        if not Members.objects.filter(member_id=member.id).exists():
                            if member.username:
                                username = member.username
                            else:
                                username = ""
                            a_member = Members.objects.create(
                                                            member_id=member.id,
                                                            member_access_hash=member.access_hash,
                                                            member_username=username,
                                                            member_source_group=FULL_MEMBER_LIST[1],
                                                            scraped_by=FULL_MEMBER_LIST[0]
                            )
                            a_member.save()
                            counter = counter + 1
                        

                    else: 
                        break
                
                if counter < limit :
                    break 

                FULL_MEMBER_LIST = []
                sleep(15)

            logger.info('saved successfuly!')
            logger.info('Going to sleep for 120 sec')
            sleep(120)
            logger.info('1 group complted ....')

        
        logger.info('Action completed !')
        Source_Groups.objects.all().delete()

        for i in range(len(clients)):
            clients[i][0].disconnect()
            sleep(1)


    except ConnectionError as err:
        logger.error(err)
        logger.info('----Use a proxy or VPN-----')
        return
    except KeyboardInterrupt:
        for i in range(len(clients)):
            clients[i][0].disconnect()
            sleep(1)
        logger.error('EXITED')
        return
    except Exception as err:
        logger.error(err)
        logger.error('EXITED')
        for i in range(len(clients)):
            clients[i][0].disconnect()
            sleep(1)
        return

        



def Scrap(client , group):

    global FULL_MEMBER_LIST

    logger.info('Getting entity of {0}'.format(group.link))
    try:
        g_entity = client[0].get_entity(group.link)
        sleep(random.randrange(80,110))
        client[0](JoinChannelRequest(g_entity))
        logger.info('Joined source channel')
        sleep(random.randrange(80,110))
    except Exception:
        try:
            client[0](ImportChatInviteRequest(group.link.split('/')[-1]))
            logger.info('Joined source chat')
            sleep(random.randrange(80,110))
            g_entity = client[0].get_entity(group.link)
            sleep(random.randrange(80,110))

        except Exception as err:
            logger.error(err)
            return
            
    
    logger.info("Getting members from {0} ...".format(g_entity.title))

    try:        
        
        all_participants = client[0].get_participants(g_entity, aggressive=True)
        #FULL_MEMBER_LIST.append([client[1] , group.link , all_participants])
        FULL_MEMBER_LIST.append(client[1])
        FULL_MEMBER_LIST.append(group.link)
        FULL_MEMBER_LIST.append(all_participants)

        print(len(all_participants))
        logger.info('Members scraped successfully !')

    except ChatAdminRequiredError:
        logger.error('Chat admin privileges does not allow you to scrape members ... Skipping this group')
        return
    except FloodWaitError as err:
        logger.error('Something wrong with the server , Have to sleep ' + err.seconds + ' seconds')
        sleep(err.seconds)
        return
    except PeerFloodError as err:
        logger.info(err)
        logger.info('Going for 300-350 sec sleep')
        sleep(random.randrange(300,350))
        return
    except Exception as err:
        logger.error('Unexpected error while scraping ... Skipping this group')
        logger.error(err)
        return

