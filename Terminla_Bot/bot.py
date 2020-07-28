from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest , CheckChatInviteRequest , ImportChatInviteRequest
from telethon.tl.types import InputPeerEmpty , InputPeerChannel , InputPeerUser ,UserStatusLastMonth , UserStatusLastWeek
from telethon.tl.functions.channels import InviteToChannelRequest , JoinChannelRequest , LeaveChannelRequest
from telethon.errors import PeerFloodError , UserPrivacyRestrictedError , ChatAdminRequiredError 
from telethon.errors import FloodWaitError

from time import sleep
import datetime
import logging
import json
import os
import socks
import csv
import sys
import random
from multiprocessing import Process
import threading



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




MEMBERS_CSV_PATH = '/home/mohsen/VSCode/Telethon_Bot_project/Terminla_Bot/members.csv'
PENDING_QUEUE_PATH = '/home/mohsen/VSCode/Telethon_Bot_project/Terminla_Bot/group_pending_queue.txt'
TARGET_GROUP_PATH = '/home/ubuntu/telethonproj/target_groups.txt'
WORKER_ACCOUNTS_PATH = '/home/mohsen/VSCode/Telethon_Bot_project/workers.json'



def Scrap_Members_From_Client_Dialog(number_of_chats_to_be_extracted):

    chats = []
    groups = []
    response = client(GetDialogsRequest(
                                        offset_date=None,
                                        offset_id=0,
                                        offset_peer=InputPeerEmpty(),
                                        limit=number_of_chats_to_be_extracted,
                                        hash=0
    ))

    sleep(random.randrange(200,250))
    
    chats.extend(response.chats)
    
    for chat in chats:
        try:
            if chat.megagroup:
                groups.append(chat)
        except:
            continue


    print('CHATS :')
    i = 0
    for group in groups:
        print(str(i) + '-'  , group.title)
        i = i + 1

    sleep(5)

    File_Pointer_On_First_Row = True
    for group in groups:
        
        all_members = []

        logger.info("Getting members from {0} ...".format(group.title))

        try:
            all_members.extend(client.get_participants(group,aggressive=True))
            logger.info('Members scraped successfully !')
            logger.info('Now saving members into file ...')
        except ChatAdminRequiredError:
            logger.error('Chat admin privileges does not allow you to scrape members ... Skipping this group')
            logger.info('Going for 200-250 sec sleep')
            sleep(random.randrange(200,250))
            continue
        except FloodWaitError as err:
            logger.error('Something wrong with the server , Have to sleep ' + err.seconds + ' seconds')
            sleep(err.seconds)
            continue
        except PeerFloodError as err:
            logger.error(err)
            logger.info('Going for 800-900 sec sleep')
            sleep(random.randrange(800,900))
            continue
        except Exception as err:
            logger.error('Unexpected error while scraping ... Skipping this group')
            logger.info('Going for 200-250 sec sleep')
            sleep(random.randrange(200,250))
            continue
        

        with open(MEMBERS_CSV_PATH, 'a' , encoding="UTF-8") as fout:
            writer = csv.writer(fout , delimiter="," , lineterminator="\n")
            if File_Pointer_On_First_Row == True:
                writer.writerow(['username','user id', 'access hash','name','group', 'group id']) 
            for member in all_members:
                if member.username:
                    username = member.username
                else:
                    username = ""
                if member.first_name:
                    firstname = member.first_name
                else:
                    firstname = ""
                if member.last_name:
                    lastname = member.last_name
                else:
                    lastname = ""
                fullname = (firstname + " " + lastname).strip()
                writer.writerow([username , member.id , member.access_hash , fullname , group.title , group.id])
                
        logger.info('Saved successfuly !')
        logger.info('Going for 400-450 sec sleep')
        sleep(random.randrange(400,450))
        File_Pointer_On_First_Row = False


    logger.info('Done ... All members scraped and save successfully !')




def Scrap_Members_From_Pending_Queue():
    
    
    groups = []
    try:
        with open(PENDING_QUEUE_PATH , 'r+') as fin:
            groups = fin.readlines()
            if not groups:
                logger.error('Pending Queue File is Empty !!!')
                return

            for i in range(len(groups)):
                groups[i] = groups[i].replace('\n','')
            
            fin.seek(0)
            fin.truncate()

    except FileNotFoundError as err:
        logger.error(err)
        return
    except IOError as err:
        logger.error(err)
        return
    except Exception as err:
        logger.error(err)
        return

    groups_entity = []
    for group in groups:
        try:
            groups_entity.append(
                                client.get_entity(group)
            )
            sleep(random.randrange(120,200))
        except Exception as err:
            logger.error(err)
            continue
    

    print('Groups :')
    i = 0
    for group in groups_entity:
        print(str(i) + '-'  , group.title)
        i = i + 1

    sleep(5)

    File_Pointer_On_First_Row = True
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
        

        with open(MEMBERS_CSV_PATH, 'a' , encoding="UTF-8") as fout:
            writer = csv.writer(fout , delimiter="," , lineterminator="\n")
            if File_Pointer_On_First_Row == True:
                writer.writerow(['username','user id', 'access hash','name','group', 'group id']) 
            for member in all_members:
                if member.username:
                    username = member.username
                else:
                    username = ""
                if member.first_name:
                    firstname = member.first_name
                else:
                    firstname = ""
                if member.last_name:
                    lastname = member.last_name
                else:
                    lastname = ""
                fullname = (firstname + " " + lastname).strip()
                writer.writerow([username , member.id , member.access_hash , fullname , group.title , group.id])

        logger.info('Saved successfuly !')
        logger.info('Going for 400-450 sec sleep')
        sleep(random.randrange(400,450))
        File_Pointer_On_First_Row = False


    logger.info('Done ... All members scraped and save successfully !')



# NOT Complete yset
def Add_Members_To_Target_group():
    users = []
    if os.stat(MEMBERS_CSV_PATH).st_size !=0 :
        try:
            with open(MEMBERS_CSV_PATH ,'r', encoding='UTF-8') as fout:
                rows = csv.reader(fout , delimiter=',' , lineterminator="\n")
                next(rows,None)
                for row in rows:
                    user = {}
                    user['username'] = row[0]
                    user['id'] = int(row[1])
                    user['access_hash'] = int(row[2])
                    user['fullname'] = row[3]
                    users.append(user)

        except FileNotFoundError as err:
            logger.error(err)
            return
        except IOError as err:
            logger.error(err)
            return
        except Exception as err:
            logger.error(err)
            return

    else:
        logger.error("Members file is empty , nothing to add ")
        return

    groups = []
    try:
        with open(TARGET_GROUP_PATH , 'r') as fin:
            groups = fin.readlines()
            if not groups:
                logger.error('Target group file is Empty !!!')
                return

            for i in range(len(groups)):
                groups[i] = groups[i].replace('\n','')
            

    except FileNotFoundError as err:
        logger.error(err)
        return
    except IOError as err:
        logger.error(err)
        return
    except Exception as err:
        logger.error(err)
        return

    groups_entity = []
    for group in groups:
        try:
            groups_entity.append(
                                client.get_entity(group)
            )
            sleep(random.randrange(120,200))
        except Exception as err:
            logger.error(err)
            continue
    

    print('Groups :')
    i = 0
    for group in groups_entity:
        print(str(i) + '-'  , group.title)
        i = i + 1

    sleep(5)

    num = int(input("Adding members to Which group? : "))
    target = groups_entity[num]

    target_entity = InputPeerChannel(
                                     target.id,
                                     target.access_hash
    )

    count = 201
    for user in users:

        if count > 0:
            try:
                logger.info("Adding {} ...".format(user['id']))
                user_ready_to_add = InputPeerUser(
                                                    user['id'],
                                                    user['access_hash']
                )
                client(InviteToChannelRequest(
                                            target_entity,
                                            [user_ready_to_add]
                ))
                logger.info("User Added ... going to sleep for 800-900 sec")
                count = count - 1
                sleep(random.randrange(800,900))
            except PeerFloodError:
                logger.error("Peer flood error ! Too many requests on destination server !")
                logger.error('Going for 900 -1000 sec sleep')
                sleep(random.randrange(900,1000))
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
            except Exception as err:
                logger.error(err)
                logger.error("Going for 800-900 sec sleep")
                sleep(random.randrange(800,900))
                continue
        
        else:
            logger.info("Adding 200 members completed !")
            return # Or wait for some seconds and continu adding ...


    
    logger.info("Action completed successfuly !")




def get_channel_data():
    try:
        entity = client.get_entity('https://t.me/joinchat/MhpGIleYfMNWoQOaq_B8nA')
        print(entity.id)
        print(entity.access_hash)
        print("all good !")
    except:
        try:
            entity = client.get_entity('MhpGIleYfMNWoQOaq_B8nA')
            print(entity.id)
            print(entity.access_hash)
            print("all good !")
        except:
            logger.error('can not get entity of this grp')
            client.disconnect()






def Add_Members_To_Target_group_From_Dialog():
    users = []
    with open(MEMBERS_CSV_PATH , encoding='UTF-8') as f:
        rows = csv.reader(f,delimiter=",",lineterminator="\n")
        next(rows, None)
        for row in rows:
            user = {}
            user['username'] = row[0]
            user['id'] = int(row[1])
            user['access_hash'] = int(row[2])
            user['name'] = row[3]
            users.append(user)

    chats = []
    last_date = None
    chunk_size = 100
    groups=[]

    result = client(GetDialogsRequest(
                                        offset_date=last_date,
                                        offset_id=0,
                                        offset_peer=InputPeerEmpty(),
                                        limit=chunk_size,
                                        hash = 0
    ))

    sleep(random.randrange(200,250))

    chats.extend(result.chats)

    for chat in chats:
        try:
            if chat.megagroup == True:
                groups.append(chat)
        except:
            continue

    print("Groups :")
    i=0
    for group in groups:
        print(str(i) + '- ' + group.title)
        i = i + 1

    num = int(input("Adding members to Which group : "))
    target = groups[num]

    target_entity = InputPeerChannel(
                                           target.id ,
                                           target.access_hash
                          )
    
    count = 201
    for user in users:
        if count > 0:
            try:
                logger.info("Adding {}".format(user['id']))
                user_ready_to_add = InputPeerUser(
                                            user['id'], 
                                            user['access_hash']
                )
                client(InviteToChannelRequest(
                                            target_entity,
                                            [user_ready_to_add]
                ))
                logger.info("User Added ... going to sleep for 800-900 sec")
                count = count - 1
                sleep(random.randrange(800,900))
            except PeerFloodError:
                logger.error("Peer flood error ! Too many requests on destination server !")
                logger.error('Going for 900 -1000 sec sleep')
                sleep(random.randrange(900,1000))
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
            except Exception as err:
                logger.error(err)
                logger.error("Going for 800-900 sec sleep")
                sleep(random.randrange(800,900))
                continue
        
        else:
            logger.info("Adding 200 members completed !")
            return # Or wait for some seconds and continu adding ..

    logger.info("Action completed successfuly !")




def Add_Group_to_Pending_Queue(Group_Link):
    try:
        with open(PENDING_QUEUE_PATH , 'a') as fout:
            fout.write(Group_Link)
            fout.write('\n')

    except FileNotFoundError as err:
        logger.error(err)
        return
    except IOError as err:
        logger.error(err)
        return
    except Exception as err:
        logger.error(err)
        return

    logger.info('Group added to pending queue successfuly !')
    sleep(5)



def Add_Group_To_Target_Groups(Group_Link):

    try:
        with open(TARGET_GROUP_PATH , 'a') as fout:
            fout.write(Group_Link)
            fout.write('\n')

    except FileNotFoundError as err:
        logger.error(err)
        return
    except IOError as err:
        logger.error(err)
        return
    except Exception as err:
        logger.error(err)
        return
    
    logger.info('Group added to targets successfuly !')
    sleep(5)
    


def Add_Worker_Account(name , api_id , api_hash , phone):

    logger.info("Adding worker account ...")
    acc = {}
    acc[name] = {
        "api_id":api_id,
        "api_hash":api_hash,
        "phone":phone,
        "limited":False
    }

    if os.path.isfile(WORKER_ACCOUNTS_PATH) and os.stat(WORKER_ACCOUNTS_PATH).st_size !=0:

        with open(WORKER_ACCOUNTS_PATH , 'r+') as file_obj:

            workers = json.loads(file_obj.read())
            if workers:

                AlreadyExists = False
                for key in workers:
                    
                    if key == list(acc.keys())[0]:
                        logger.error('Worker account with this name already exists !!!')
                        AlreadyExists = True
                        break
                    
                    if workers[key]['api_id'] == acc[name]["api_id"] or workers[key]['api_hash'] == acc[name]["api_hash"]:
                        logger.error('There is a Worker account with this hash or id !!!')
                        AlreadyExists = True
                        break


                if AlreadyExists == False:
                    workers.update(acc)
                    logger.info('Worker account added successfuly !!!')

            file_obj.seek(0)
            file_obj.truncate()
            file_obj.write(json.dumps(workers))

    else:

        with open(WORKER_ACCOUNTS_PATH , 'w+') as file_obj:


            file_obj.seek(0)
            file_obj.write(json.dumps(acc))

    sleep(5)






# Just for test
# This method scraps users only with last leen more than a week ago
def Scrap_Members_From_Pending_Queue_2(client):
    
    
    groups = []
    try:
        with open(PENDING_QUEUE_PATH , 'r+') as fin:
            groups = fin.readlines()
            if not groups:
                logger.error('Pending Queue File is Empty !!!')
                return

            for i in range(len(groups)):
                groups[i] = groups[i].replace('\n','')
            
            fin.seek(0)
            fin.truncate()

    except FileNotFoundError as err:
        logger.error(err)
        return
    except IOError as err:
        logger.error(err)
        return
    except Exception as err:
        logger.error(err)
        return

    groups_entity = []
    for group in groups:
        try:
            print(1)
            groups_entity.append(
                                client.get_entity(group)
            )
            sleep(random.randrange(120,130))
        except:
            print(2)
            try:
                #entityCH = client.get_entity('https://t.me/joinchat/MhpGIleYfMNWoQOaq_B8nA') 
                client(ImportChatInviteRequest('https://t.me/joinchat/MhpGIleYfMNWoQOaq_B8nA'))
                print("JOIN GROUP ")
                sleep(5)
                groups_entity.append(
                                    client.get_entity('https://t.me/joinchat/MhpGIleYfMNWoQOaq_B8nA')
                )
                sleep(5)
            except:
                print(3)
                try:
                    client(ImportChatInviteRequest('MhpGIleYfMNWoQOaq_B8nA'))
                    print("joind group !!!!!!")
                    sleep(5)
                    groups_entity.append(
                                    client.get_entity('https://t.me/joinchat/MhpGIleYfMNWoQOaq_B8nA')
                    )
                    sleep(5)

                except Exception as err:
                    print(4)
                    logger.error(err)
                    client.disconnect()
                    return

            
    

    print('Groups :')
    i = 0
    for group in groups_entity:
        print(str(i) + '-'  , group.title)
        i = i + 1

    sleep(5)

    number_of_members_scraped = 0
    File_Pointer_On_First_Row = True
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
        

        with open(MEMBERS_CSV_PATH, 'a' , encoding="UTF-8") as fout:
            writer = csv.writer(fout , delimiter="," , lineterminator="\n")
            if File_Pointer_On_First_Row == True:
                writer.writerow(['username','user id', 'access hash','name','group', 'group id']) 
            for member in all_members:
                accept=False
                try:
                    """
                    lastDate=member.status.was_online
                    num_months = (datetime.now().year - lastDate.year) * 12 + (datetime.now().month - lastDate.month)
                    if not num_months > 1:
                        accept=False
                    """
                    if  (member.status == UserStatusLastWeek()) or (member.status == UserStatusLastMonth()) :
                        accept=True

                except Exception as err:
                    logger.error(err)
                    continue
                if accept:
                    number_of_members_scraped = number_of_members_scraped +1
                    if member.username:
                        username = member.username
                    else:
                        username = ""
                    if member.first_name:
                        firstname = member.first_name
                    else:
                        firstname = ""
                    if member.last_name:
                        lastname = member.last_name
                    else:
                        lastname = ""
                    fullname = (firstname + " " + lastname).strip()
                    writer.writerow([username , member.id , member.access_hash , fullname , group.title , group.id])
            
        logger.info('Saved successfuly !')
        logger.info('Going for 400-450 sec sleep')
        sleep(random.randrange(100,120))
        File_Pointer_On_First_Row = False
            
            
            

    logger.info('Done ... All members scraped and save successfully !')
    print("$$$$$$$$########")
    print("Number of members scraped ",number_of_members_scraped)
    print("$$$$$$$$########")









# NOT Complete yset
#Test for multi proccess
def Add_Members_To_Target_group_2(client , members_file , target_grp ):
    try:
        users = []
        if os.stat(members_file).st_size !=0 :
            try:
                with open(members_file ,'r', encoding='UTF-8') as fout:
                    rows = csv.reader(fout , delimiter=',' , lineterminator="\n")
                    #next(rows,None)
                    for row in rows:
                        user = {}
                        user['username'] = row[0]
                        user['id'] = int(row[1])
                        user['access_hash'] = int(row[2])
                        user['fullname'] = row[3]
                        users.append(user)

            except FileNotFoundError as err:
                logger.error(err)
                return
            except IOError as err:
                logger.error(err)
                return
            except Exception as err:
                logger.error(err)
                return

        else:
            logger.error("Members file is empty , nothing to add ")
            return


        # xxxx
        try:
            grp_entity = client.get_entity(target_grp)
            target_entity = InputPeerChannel(
                                        grp_entity.id,
                                        grp_entity.access_hash
            )
        except Exception as err:
            logger.error(err)
            logger.error('PROCCESS IS RETURNING {0}'.format(client.get_me()))
            return
    
    
        # xxxx


        count = 201
        for user in users:

            if count > 0:
                try:
                    logger.info("Adding {} ...".format(user['id']))
                    user_ready_to_add = InputPeerUser(
                                                        user['id'],
                                                        user['access_hash']
                    )
                    client(InviteToChannelRequest(
                                                target_entity,
                                                [user_ready_to_add]
                    ))
                    logger.info("User Added ... going to sleep for 800-900 sec")
                    count = count - 1
                    sleep(random.randrange(800,900))
                except PeerFloodError:
                    logger.error("Peer flood error ! Too many requests on destination server !")
                    logger.error('Going for 900 -1000 sec sleep')
                    sleep(random.randrange(900,1000))
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
                except Exception as err:
                    logger.error(err)
                    logger.error("Going for 800-900 sec sleep")
                    sleep(random.randrange(800,900))
                    continue
            
            else:
                logger.info("Adding 200 members completed !")
                client.disconnect()
                return # Or wait for some seconds and continu adding ...


        
        logger.info("Action completed successfuly !")
        client.disconnect()

    except KeyboardInterrupt:
        client.disconnect()
        return
    





if __name__ == "__main__":
    
    logger.info('START ...')

    proxy_ip = '46.4.129.55'
    proxy_port = 80

    api_id_me = "1546506"
    api_hash_me = "171a686e23e4b2bebfd3e5fe20ab3c97"
    phone_me = "+989924923959"

    api_id_motion = "1482551"
    api_hash_motion = "ef35c8675241e399e27560682a054d8f"
    phone_motion = "+989336855263"

    api_id_mohsenzr7 = "1606383"
    api_hash_mohsenzr7 = "d7aef8f0798f7c3c810d8b91e8c94fbb"
    phone_mohsenzr7 = "+989393647229"
    
    try:
        """
        client2 = TelegramClient(
                                phone_motion,
                                api_id_motion,
                                api_hash_motion
        )

        client2.connect()

        if not client2.is_user_authorized():
            client2.send_code_request(phone_motion)
            code = input("Enter the code for {0}: ".format(phone_motion))
            client2.sign_in(
                            phone_motion,
                            code     
            )

        """
        
        client1 = TelegramClient(
                                phone_me,
                                api_id_me,
                                api_hash_me                     
        )

        client1.connect()

        if not client1.is_user_authorized():
            client1.send_code_request(phone_me)
            code = input("Enter the code for {0}: ".format(phone_me))
            client1.sign_in(
                            phone_me,
                            code     
            )
        

        """
        try:
            
            client(JoinChannelRequest('https://t.me/jsxjsx'))
            print("Joined jsxjsx")
            sleep(10)
        except:
            try:
                entityCH = client.get_entity('https://t.me/jsxjsx')
                client(JoinChannelRequest(entityCH))
                print("JOINED JSXJSX")
                sleep(10)
            except:
                logger.error(" Didnt join  the CHanel jsxjsx or already left")
                pass

        
        try:
            #entityCH = client.get_entity('https://t.me/joinchat/MhpGIleYfMNWoQOaq_B8nA') 
            client(ImportChatInviteRequest('MhpGIleYfMNWoQOaq_B8nA'))
            print("join CHANNEL ")
            sleep(10)
        except:
            try:
                client(ImportChatInviteRequest('MhpGIleYfMNWoQOaq_B8nA'))
                print("joind group !!!!!!")
                sleep(10)
            except:
                logger.error(" Didnt join the CHanel")
                pass
        """
       
        #Add_Group_to_Pending_Queue('https://t.me/PythonLinuxExperts')
        #Add_Group_to_Pending_Queue('https://t.me/joinchat/CAbL_VL0rCMqY6AzbP9yTQ')

        #Add_Worker_Account('W10',"4343434","fekhrfejr","0999999995")
        #Add_Worker_Account('W10',"4343434","fekhrfejr","0999999995")

        #Add_Group_To_Target_Groups('https://t.me/jsxjsx')
        #Add_Group_To_Target_Groups('https://t.me/mtntest')
        
        #Scrap_Members_From_Pending_Queue_2()
        #Scrap_Members_From_Client_Dialog(10)
        #Scrap_Members_From_Pending_Queue()
        
        sleep(10)

        #Add_Members_To_Target_group_From_Dialog()
        #Process(target= Add_Members_To_Target_group_2 , args= (client1,'/home/ubuntu/telethonproj/members1.csv','https://t.me/jsxjsx')).start()
        #Process(target= Add_Members_To_Target_group_2 , args= (client2,'/home/ubuntu/telethonproj/members2.csv','https://t.me/jsxjsx')).start()
        #Process(target= Add_Members_To_Target_group_2 , args= (client3,'/home/ubuntu/telethonproj/members3.csv','https://t.me/jsxjsx')).start()
        

        #Process(target=Add_Members_To_Target_group_2 , args=(client1,'/home/ubuntu/telethonproj/members1.csv','https://t.me/jsxjsx')).start()
        #Process(target=Add_Members_To_Target_group_2 , args=(client2,'/home/ubuntu/telethonproj/members2.csv','https://t.me/jsxjsx')).start()
        
        #Process(target= Scrap_Members_From_Pending_Queue_2 , args=(client1,)).start()
        threading.Thread(target=Scrap_Members_From_Pending_Queue_2 , args=(client1,)).start()

    except ConnectionError as err:
        logger.error(err)
        print('----Use a proxy or VPN-----')
        sys.exit()
    except KeyboardInterrupt:
        client1.disconnect()
        client2.disconnect()
    except Exception:
        client1.disconnect()
        client2.disconnect()
    
