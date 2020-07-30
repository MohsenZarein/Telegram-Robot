from django.shortcuts import render , redirect
from django.core import exceptions
from django.http import HttpResponse
from django.db.models import Q


from .models import Source_Groups
from .models import Target_Groups
from .models import Workers
from .models import Members

from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest , CheckChatInviteRequest , ImportChatInviteRequest , AddChatUserRequest 
from telethon.tl.types import InputPeerEmpty , InputPeerChannel , InputPeerUser ,UserStatusLastMonth , UserStatusLastWeek , ChannelParticipantsSearch , InputUser
from telethon.tl.functions.channels import InviteToChannelRequest , JoinChannelRequest , GetParticipantsRequest , GetFullChannelRequest
from telethon.errors import PeerFloodError , UserPrivacyRestrictedError , ChatAdminRequiredError , FloodWaitError ,ChannelPrivateError

import threading
from time import sleep
import datetime
import logging
import json
import os
import socks
import csv
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
    return render(request , 'bot/index.html')


def list_of_members(request):

    if request.method == 'POST':
        
        link = request.POST['link']
        desired_members = Members.objects.filter(member_joined_groups__contains=[link])
        context = {
            "members":desired_members
        }
        return render(request , 'bot/list-of-members.html' , context)

    else:
        return render(request , 'bot/list-of-members.html')


def Add_Source_Group(request):

    if request.method == 'POST':

        link = request.POST['source_group_link']
        if not Source_Groups.objects.filter(link=link).exists():
            source_link = Source_Groups.objects.create(link=link)
            source_link.save()
        else:
            logger.error('This source group already exists in database')

        return redirect('add-source-group')
            
    else:
        return render(request , 'bot/add-source-group.html')



def Add_Target_Group(request):

    if request.method == 'POST':

        link = request.POST['target_group_link']
        if not Target_Groups.objects.filter(link=link).exists():
            target_link = Target_Groups.objects.create(link=link)
            target_link.save()
        else:
            logger.error('This target group already exists in database')

        return redirect('add-target-group')

    else:
        return render(request , 'bot/add-target-group.html')



def Add_Worker(request):

    if request.method == 'POST':

        worker_api_id = request.POST['api_id']
        worker_api_hash = request.POST['api_hash']
        worker_phone = request.POST['phone']

        if not Workers.objects.filter(worker_api_hash=worker_api_hash).exists():
            worker_acc = Workers.objects.create(
                                                worker_api_id=worker_api_id,
                                                worker_api_hash=worker_api_hash,
                                                worker_phone=worker_phone
            )
            worker_acc.save()

            # Register Worker Account by entering code into terminal
            try:
                client = TelegramClient(
                                        worker_phone,
                                        worker_api_id,
                                        worker_api_hash
                )
                client.connect()
                if not client.is_user_authorized():
                    client.send_code_request(worker_phone)
                    code = input("Enter the code for {0}: ".format(worker_phone))
                    client.sign_in(
                                    worker_phone,
                                    code     
                    )
                logger.info('client authenticated')
                sleep(5)
                client.disconnect()
            except Exception as err:
                logger.error(err)
                
        else:
            logger.error('This worker already exists')

        return redirect('add-worker')
    
    else:
        return render(request , 'bot/add-worker.html')
        


def Scrap_Members(request):

    if request.method == 'POST':
        
        threading.Thread(target=Scraping).start()
        return redirect('index')

    else:
        return render(request , 'bot/index.html')




def Add_Members(request):

    if request.method == 'POST':

        group = request.POST['target_group_link']
        number_of_members = int(request.POST['number_of_members'])
        rate = int(request.POST['rate'])
   

        try:
            workers_list = Workers.objects.all()
        except exceptions.ObjectDoesNotExist as err:
            logger.error(err)
            return
        except Exception as err:
            logger.error(err)
            return


        for worker in workers_list:
            members_list =  Members.objects.filter(Q(scraped_by=worker) & ~Q(member_joined_groups__contains=[group]))[:3]
            threading.Thread(target=Add_Members_To_Target_Groups , args=(worker,group,members_list)).start()

        return redirect('add-members')

    
    else:
        return render(request , 'bot/add-members.html')


        


def Add_Members_To_Target_Groups(worker , group , members_list):
    logger.info('START ADDING ...')
    print(group)
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
                sleep(random.randrange(120,200))
                groups_entity.append(
                                client.get_entity(group)
                )
                chat_status = "private"
                sleep(random.randrange(120,200))

            except Exception as err:
                logger.error(err)
                logger.error('Skipping This Worker...')
                client.disconnect()
                return
        
        if chat_status == "public" :
            target = InputPeerChannel(
                                    int(group_entity.id),
                                    int(group_entity.access_hash)
            )

        for member in members_list:
    
            try:
                logger.info("Adding {} ...".format(int(member.member_id)))
                
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
                logger.info("User Added ... going to sleep for 800-900 sec")
                sleep(random.randrange(800,900))
            except PeerFloodError:
                logger.error("Peer flood error ! Too many requests on destination server !")
                logger.error('Going for 900 -1000 sec sleep')
                sleep(random.randrange(900,1000))
                members_list.append(member)
                continue
            except FloodWaitError as err:
                logger.error('Something wrong with the server , Have to sleep ' + err.seconds + ' seconds')
                sleep(err.seconds)
                continue
            except UserPrivacyRestrictedError:
                logger.error("This user's privacy does not allow you to do this ... Skipping this user")
                logger.error("Going for 800-900 sec sleep")
                sleep(random.randrange(800,900))
                continue
            except Exception:
                try:
                    user_ready_to_add = InputUser(
                        user_id=int(member.member_id),
                        access_hash=int(member.member_access_hash)
                    )
                    client(AddChatUserRequest(
                                              int(group_entity.id),
                                              user_ready_to_add,
                                              fwd_limit=100
                    ))
                    this_member = Members.objects.get(member_id=member.member_id)
                    this_member.member_joined_groups.append(group)
                    this_member.save()
                    logger.info("User Added ... going to sleep for 800-900 sec")
                    sleep(random.randrange(800,900))
                except Exception as err:
                    logger.error(err)
                    logger.error("Going for 800-900 sec sleep")
                    print('inja......')
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
        print('ExePTION')
        client.disconnect()
        return


def Scraping():
    logger.info("START SCRAPING ...")
    try:
        try:
            workers_list = Workers.objects.all()
        except exceptions.ObjectDoesNotExist as err:
            logger.error(err)
            return
        except Exception as err:
            logger.error(err)
            return

        clients = []
        for worker in workers_list:
            client = TelegramClient(
                                    worker.worker_phone,
                                    worker.worker_api_id,
                                    worker.worker_api_hash
            )
            client.connect()
            if not client.is_user_authorized():
                logger.error('worker with {0} api_id is not signed in , skiping this worker'.format(worker.worker_api_id))
                continue

            worker_obj = [client,worker]
            clients.append(worker_obj)
            logger.info('a client connected...')
            sleep(5)
        
        if not clients:
            logger.error('None of clients connected ! try again...')
            return
        
        logger.info('some clients connected successfuly ! ...')
        sleep(10)

        try:
            groups = Source_Groups.objects.all()
        except exceptions.ObjectDoesNotExist:
            logger.error('There is not any source groups in database !')
            client.disconnect()
            return
        except Exception as err:
            logger.error(err)
            client.disconnect()
            return

        
        for group in groups:
            offset = 0
            for i in range(len(clients)):
                try:
                    g_entity = clients[i][0].get_entity(group.link)
                    sleep(random.randrange(60,70))
                    clients[i][0](JoinChannelRequest(g_entity))
                    logger.info('Joined source channel')
                except Exception:
                    try:
                        clients[i][0](ImportChatInviteRequest(group.link.split('/')[-1]))
                        logger.info('Joined source chat')
                        sleep(random.randrange(60,70))
                        g_entity = clients[i][0].get_entity(group.link)
                        sleep(random.randrange(60,70))

                    except Exception as err:
                        logger.error(err)
                        sleep(random.randrange(60,70))
                        continue
                
                logger.info("Getting members from {0} ...".format(g_entity.title))

                try:
                            
                    data = clients[i][0](GetFullChannelRequest(group.link))
                    limit = int(data.full_chat.participants_count / len(clients))
              
                    some_members = []
                    while len(some_members) < limit:
                        participants = clients[i][0](GetParticipantsRequest(
                            g_entity, ChannelParticipantsSearch(''), offset, limit,
                            hash=0
                        ))
                        if not participants.users:
                            break
                        some_members.extend(participants.users)
                        offset += len(participants.users)

                    logger.info('Members scraped successfully !')
                    logger.info('Now saving members into database ...')
                    for member in some_members:
                        if not Members.objects.filter(member_id=member.id).exists():
                        
                            if member.username:
                                username = member.username
                            else:
                                username = ""
                            a_member = Members.objects.create(
                                                                member_id=member.id,
                                                                member_access_hash=member.access_hash,
                                                                member_username=username,
                                                                scraped_by=clients[i][1]
                            )
                            a_member.save()


                    logger.info('saved successfuly!')
                    logger.info('Going to sleep for 120 sec')
                    sleep(120)
                    
                    
                except ChatAdminRequiredError:
                    logger.error('Chat admin privileges does not allow you to scrape members ... Skipping this group')
                    logger.error('Going for 800-900 sec sleep')
                    sleep(random.randrange(800,900))
                    break
                except FloodWaitError as err:
                    logger.error('Something wrong with the server , Have to sleep ' + err.seconds + ' seconds')
                    sleep(err.seconds)
                    continue
                except PeerFloodError as err:
                    logger.error(err)
                    logger.error('Going for 900-1000 sec sleep')
                    sleep(random.randrange(900,1000))
                    continue
                except Exception as err:
                    logger.error('Unexpected error while scraping ... Skipping this group')
                    logger.error(err)
                    logger.error('Going for 800-900 sec sleep')
                    sleep(random.randrange(800,900))
                    continue



            logger.info('1 group complted ....')

        
        logger.info('Action completed !')

        for i in range(len(clients)):
            clients[i][0].disconnect()
            sleep(1)

    except ConnectionError as err:
        logger.error(err)
        logger.info('----Use a proxy or VPN-----')
        return
    except KeyboardInterrupt:
        client.disconnect()
        logger.error('EXITED')
        return
    except Exception as err:
        logger.error(err)
        logger.error('EXITED')
        client.disconnect()
        return

        

