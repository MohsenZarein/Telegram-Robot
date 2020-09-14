from telethon import TelegramClient
from telethon.tl.functions.messages import ImportChatInviteRequest , AddChatUserRequest 
from telethon.tl.types import InputPeerEmpty , InputPeerChannel  , InputUser , InputPeerChat
from telethon.tl.functions.channels import InviteToChannelRequest , JoinChannelRequest , LeaveChannelRequest
from telethon.errors import PeerFloodError , UserPrivacyRestrictedError , ChatWriteForbiddenError , FloodWaitError  

from bot.models import Source_Groups
from bot.models import Target_Groups
from bot.models import Workers
from bot.models import Members

from time import sleep
import threading
import datetime
import logging
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


campains = []
def Add_Members_To_Target_Groups(worker , group , members_list  , rate , campain):

    global campains
    campains.append(0)
    
    logger.info('START ADDING TO {0}...'.format(group))
    sleep(5)
    try:
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
        except:
            sleep(7)
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
            except Exception as err:
                logger.error(err)
                worker.active = False
                worker.save()
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
                worker.active = False
                worker.save()
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

                max_retry_for_peerflood = 7

                logger.info("User Added ... going to sleep for 900-1000 sec")
                campains[campain] = campains[campain] + 1
                print("added members in cmp {0} so far : {1}".format(campain,campains[campain]))
                if campains[campain] > rate:
                    try:
                        client(LeaveChannelRequest(group_entity))
                    except Exception as err:
                        logger.error(err)
                    client.disconnect()
                    worker.active = False
                    worker.save()
                    logger.info('Action completed')
                    return

                sleep(random.randrange(900,1000))
                
            except PeerFloodError as err:
                logger.info(err)
                logger.info('Going for 1000 - 1100 sec sleep')
                max_retry_for_peerflood = max_retry_for_peerflood - 1
                if max_retry_for_peerflood <= 0 :
                    logger.error("This worker is limited ... Returned")
                    try:
                        client(LeaveChannelRequest(group_entity))
                    except Exception as err:
                        logger.error(err)
                    worker.limited = True
                    worker.active = False
                    worker.save()
                    client.disconnect()
                    return
                if campains[campain] > rate:
                    try:
                        client(LeaveChannelRequest(group_entity))
                    except Exception as err:
                        logger.error(err)
                    client.disconnect()
                    worker.active = False
                    worker.save()
                    logger.info('Action completed')
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
                max_retry_for_peerflood = 7
                if campains[campain] > rate:
                    try:
                        client(LeaveChannelRequest(group_entity))
                    except Exception as err:
                        logger.error(err)
                    client.disconnect()
                    worker.active = False
                    worker.save()
                    logger.info('Action completed')
                    return
                sleep(random.randrange(800,900))
                continue
            except ChatWriteForbiddenError as err:
                logger.error(err)
                try:
                    client(LeaveChannelRequest(group_entity))
                except Exception as err:
                    logger.error(err)
                client.disconnect()
                worker.active = False
                worker.save()
                return
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
                    if campains[campain] > rate:
                        try:
                            client(LeaveChannelRequest(group_entity))
                        except Exception as err:
                            logger.error(err)
                        client.disconnect()
                        worker.active = False
                        worker.save()
                        logger.info('Action completed')
                        return
                    sleep(random.randrange(900,1000))
                except Exception as err:
                    logger.error(err)
                    logger.error("Going for 800-900 sec sleep")
                    if campains[campain] > rate:
                        try:
                            client(LeaveChannelRequest(group_entity))
                        except Exception as err:
                            logger.error(err)
                        client.disconnect()
                        worker.active = False
                        worker.save()
                        logger.info('Action completed')
                        return
                    sleep(random.randrange(800,900))
                    continue

        logger.info('Action completed')
        worker.active = False
        worker.save()

        try:
            client(LeaveChannelRequest(group_entity))
        except Exception as err:
            logger.error(err)

        client.disconnect()
    

    except ConnectionError as err:
        logger.error(err)
        logger.info('----Use a proxy or VPN-----')
        worker.active = False
        worker.save()
        return
    except KeyboardInterrupt:
        print('keyboard interupt...')
        worker.active = False
        worker.save()
        client.disconnect()
        return
    except Exception as err:
        logger.error(err)
        worker.active = False
        worker.save()
        client.disconnect()
        return