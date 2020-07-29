from django.shortcuts import render , redirect
from django.core import exceptions
from django.http import HttpResponse

from .models import Source_Groups
from .models import Target_Groups
from .models import Workers
from .models import Members

from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest , CheckChatInviteRequest , ImportChatInviteRequest , AddChatUserRequest
from telethon.tl.types import InputPeerEmpty , InputPeerChannel , InputPeerUser ,UserStatusLastMonth , UserStatusLastWeek
from telethon.tl.functions.channels import InviteToChannelRequest , JoinChannelRequest , LeaveChannelRequest
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
            sleep(5)
            client.disconnect()
        else:
            # send a 'this worker already exists' message
            logger.error('This worker already exists')

        return redirect('add-worker')
    
    else:
        return render(request , 'bot/add-worker.html')
        


def Scrap_Members(request):

    if request.method == 'POST':

        threading.Thread(target=Scraping).start()
        return redirect('scrap-members')

    else:
        return render(request , 'bot/scrap-members.html')




def Add_Members(request):

    if request.method == 'POST':

        group = request.POST['target_group_link']
        number_of_members = int(request.POST['number_of_members'])
        rate = int(request.POST['rate'])

        try:
            print('getting members from database')
            members_list = Members.objects.exclude(member_joined_groups__contains=[group])[:number_of_members]
            print('type-member-list:',type(members_list))
            print('size-member-lits:',len(members_list))
            #print('member-list:\n',members_list)
            sleep(60)

        except exceptions.ObjectDoesNotExist as err:
            logger.error(err)
            return
        except Exception as err:
            logger.error(err)
            return

        try:
            print('getting workers from database')
            workers_list = Workers.objects.all()
            print('type-worker-list:',type(workers_list))
            print('size-worker-lits:',len(workers_list))
            print('worker-list:\n',workers_list)
            sleep(60)
        except exceptions.ObjectDoesNotExist as err:
            logger.error(err)
            return
        except Exception as err:
            logger.error(err)
            return


        splited_members_list = [members_list[x:x+rate] for x in range(0, len(members_list), rate)]
        print('splited-members-list :\n',splited_members_list)
        i = 0
        for worker in workers_list:
            if i < len(splited_members_list):
                threading.Thread(target=Add_Members_To_Target_Groups , args=(worker,group,splited_members_list[i])).start()
                i = i + 1
            else:
                break
            
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
    
        print('worker client connected....')

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
                                    group_entity.id,
                                    group_entity.access_hash
            )
        print('vared halghe mishim....')
        for member in members_list:
            print('dor halghe.....')
            try:
                logger.info("Adding {} ...".format(member.member_id))
                user_ready_to_add = InputPeerUser(
                                                    int(member.member_id),
                                                    int(member.member_access_hash)
                )
                if chat_status == "public":
                    client(InviteToChannelRequest(
                                                target,
                                                [user_ready_to_add]
                    ))
                else:
                    client(AddChatUserRequest(
                                              int(group_entity.id),
                                              user_ready_to_add,
                                              fwd_limit=10
                    ))
                this_member = Members.objects.get(member_id=member.member_id)
                this_member.member_joined_groups.append(group)
                this_member.save()
                logger.info("User Added ... going to sleep for 800-900 sec")
                sleep(random.randrange(500,600))
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
                sleep(random.randrange(500,600))
                continue
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
            worker = Workers.objects.get(id=1)
            api_id = worker.worker_api_id
            api_hash = worker.worker_api_hash
            phone = worker.worker_phone
        except exceptions.MultipleObjectsReturned as err:
            logger.error(err)
            return
        except exceptions.ObjectDoesNotExist as err:
            logger.error(err)
            return
        
        client = TelegramClient(
                                phone,
                                api_id,
                                api_hash
        )
        client.connect()
        if not client.is_user_authorized():
            client.send_code_request(phone)
            code = input("Enter the code for {0}: ".format(phone))
            client.sign_in(
                            phone,
                            code     
            )

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


        groups_entity = []
        for group in groups:
            try:
                g_entity = client.get_entity(group.link)
                groups_entity.append(g_entity)
                sleep(random.randrange(120,200))
                client(JoinChannelRequest(g_entity))
                logger.info('Joined source channel')
                sleep(random.randrange(120,200))
            except Exception:
                try:
                    client(ImportChatInviteRequest(group.link.split('/')[-1]))
                    logger.info('Joined source chat')
                    sleep(random.randrange(120,200))
                    groups_entity.append(
                                    client.get_entity(group.link)
                    )
                    sleep(random.randrange(120,200))

                except Exception as err:
                    logger.error(err)
                    sleep(random.randrange(120,200))
                    continue
        
        
        if groups_entity:
            for group in groups_entity:
    
                all_members = []

                logger.info("Getting members from {0} ...".format(group.title))

                try:
                    all_members.extend(client.get_participants(group,aggressive=True))
                    logger.info('Members scraped successfully !')
                    logger.info('Now saving members into database ...')
                except ChatAdminRequiredError:
                    logger.error('Chat admin privileges does not allow you to scrape members ... Skipping this group')
                    logger.error('Going for 800-900 sec sleep')
                    sleep(random.randrange(800,900))
                    continue
                except FloodWaitError as err:
                    logger.error('Something wrong with the server , Have to sleep ' + err.seconds + ' seconds')
                    sleep(err.seconds)
                    continue
                except PeerFloodError as err:
                    logger.error(err)
                    logger.error('Going for 900-1000 sec sleep')
                    sleep(random.randrange(900,1000))
                except Exception as err:
                    logger.error('Unexpected error while scraping ... Skipping this group')
                    logger.error('Going for 800-900 sec sleep')
                    sleep(random.randrange(800,900))
                    continue
                

                for member in all_members:
                    if not Members.objects.filter(member_id=member.id).exists():
                        accept = False
                        try:
                            if (member.status == UserStatusLastWeek()) or (member.status == UserStatusLastMonth()) :
                                accept = True
                        except Exception as err:
                            continue
                        if accept == True:
                            if member.username:
                                username = member.username
                            else:
                                username = ""
                            a_member = Members.objects.create(
                                                                member_id=member.id,
                                                                member_access_hash=member.access_hash,
                                                                member_username=username
                            )
                            a_member.save()
                        

                logger.info('Saved successfuly !')
                logger.info('Going for 800-900 sec sleep')
                sleep(random.randrange(800,900))

            logger.info('Done ... All members scraped and saved successfully !')
            client.disconnect()
            return
        
        else:
            logger.error('Could not get the entity of source groups , there is a problem with source groups')
            logger.error('Maybe source group links are Invalid or Wrong')
            sleep(7)
            client.disconnect()
            return

        # Deleting source links , cause all members are extracted from these groups 
        # and has been saved in database
        Source_Groups.objects.all().delete()

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