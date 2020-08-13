from telethon import TelegramClient
from telethon.tl.functions.messages import CheckChatInviteRequest , ImportChatInviteRequest , AddChatUserRequest 
from telethon.tl.types import UserStatusLastMonth  , ChannelParticipantsSearch 
from telethon.tl.functions.channels import JoinChannelRequest , GetParticipantsRequest , GetFullChannelRequest
from telethon.errors import PeerFloodError , ChatAdminRequiredError , FloodWaitError ,ChannelPrivateError 

from django.core import exceptions

from bot.models import Workers
from bot.models import Source_Groups
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
                
                if client.is_connected():
                    worker_and_client_obj = [client,worker]
                    clients.append(worker_and_client_obj)
                    logger.info('a client connected...')
                    sleep(5)
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
                        continue
                    if client.is_connected():
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


                
                #for worker in workers_threads:
                    #worker.start()
                    #sleep(1)
                

                #for worker in workers_threads:
                    #worker.join()
                

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