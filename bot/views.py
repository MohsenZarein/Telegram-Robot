from django.shortcuts import render , redirect
from django.core import exceptions
from django.http import HttpResponse

from .models import Source_Groups
from .models import Target_Groups
from .models import Workers
from .models import Members

from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest , CheckChatInviteRequest , ImportChatInviteRequest
from telethon.tl.types import InputPeerEmpty , InputPeerChannel , InputPeerUser ,UserStatusLastMonth , UserStatusLastWeek
from telethon.tl.functions.channels import InviteToChannelRequest , JoinChannelRequest , LeaveChannelRequest
from telethon.errors import PeerFloodError , UserPrivacyRestrictedError , ChatAdminRequiredError , FloodWaitError

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
        source_link = Source_Groups.objects.create(link=link)
        source_link.save()
        return redirect('add-source-group')
            
    else:
        return render(request , 'bot/add-source-group.html')



def Add_Target_Group(request):

    if request.method == 'POST':
        link = request.POST['target_group_link']
        target_link = Target_Groups.objects.create(link=link)
        target_link.save()
        return redirect('add-target-group')

    else:
        return render(request , 'bot/add-target-group.html')



def Add_Worker(request):

    if request.method == 'POST':
        worker_api_id = request.POST['api_id']
        worker_api_hash = request.POST['api_hash']
        worker_phone = request.POST['phone']
        worker_acc = Workers.objects.create(
                                            worker_api_id=worker_api_id,
                                            worker_api_hash=worker_api_hash,
                                            worker_phone=worker_phone
        )
        worker_acc.save()
        return redirect('add-worker')
    
    else:
        return render(request , 'bot/add-worker.html')
        


def Scrap_Members(request):

    if request.method == 'POST':
        threading.Thread(target=Scraping).start()
        return redirect('scrap-members')

    else:
        return render(request , 'bot/scrap-members.html')



def Scraping():

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
                groups_entity.append(
                                    client.get_entity(group.link)
                )
                sleep(random.randrange(120,200))
            except:
                try:
                    client(ImportChatInviteRequest(group.link))
                    print("JOIN GROUP ")
                    sleep(random.randrange(120,200))
                    groups_entity.append(
                                        client.get_entity(group.link)
                    )
                    sleep(random.randrange(120,200))
                except:
                    try:
                        client(ImportChatInviteRequest(group.link.split('/')[-1]))
                        print("joind group !!!!!!")
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
                    logger.info('Now saving members into file ...')
                except ChatAdminRequiredError:
                    logger.error('Chat admin privileges does not allow you to scrape members ... Skipping this group')
                    logger.error('Going for 200-250 sec sleep')
                    sleep(random.randrange(200,250))
                    continue
                except FloodWaitError as err:
                    logger.error('Something wrong with the server , Have to sleep ' + err.seconds + ' seconds')
                    sleep(err.seconds)
                    continue
                except PeerFloodError as err:
                    logger.error(err)
                    logger.error('Going for 800-900 sec sleep')
                    sleep(random.randrange(800,900))
                except Exception as err:
                    logger.error('Unexpected error while scraping ... Skipping this group')
                    logger.error('Going for 200-250 sec sleep')
                    sleep(random.randrange(200,250))
                    continue
                

                for member in all_members:
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
                logger.info('Going for 400-450 sec sleep')
                sleep(random.randrange(400,450))

            logger.info('Done ... All members scraped and save successfully !')
            client.disconnect()
            return
        
        else:
            logger.error('Could not get the entity of source groups , there is a problem with source groups')
            logger.error('Maybe source group links are Invalid or Wrong')
            client.disconnect()
            return


    except ConnectionError as err:
        logger.error(err)
        logger.info('----Use a proxy or VPN-----')
        return
    except KeyboardInterrupt:
        client.disconnect()
        return
    except Exception as err:
        logger.error(err)
        client.disconnect()
        return