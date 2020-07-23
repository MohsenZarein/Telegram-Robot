from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest , CheckChatInviteRequest
from telethon.tl.types import InputPeerEmpty , InputPeerChannel , InputPeerUser
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors import PeerFloodError , UserPrivacyRestrictedError , ChatAdminRequiredError

from time import sleep
import logging
import json
import socks
import csv
import sys

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
            continue
        except Exception as err:
            logger.error('Unexpected error while scraping ... Skipping this group')
            continue
        

        with open("/home/mohsen/VSCode/Telethon_Bot_project/members.csv", 'a' , encoding="UTF-8") as fout:
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
            sleep(5)
            File_Pointer_On_First_Row = False


    logger.info('Done ... All members scraped and save successfully !')




def Scrap_Members_From_Pending_Queue():
    
    
    groups = []
    try:
        with open('/home/mohsen/VSCode/Telethon_Bot_project/group_pending_queue.txt' , 'r+') as fin:
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
            continue
        except Exception as err:
            logger.error('Unexpected error while scraping ... Skipping this group')
            continue
        

        with open("/home/mohsen/VSCode/Telethon_Bot_project/members.csv", 'a' , encoding="UTF-8") as fout:
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
            sleep(5)
            File_Pointer_On_First_Row = False


    logger.info('Done ... All members scraped and save successfully !')



# NOT Complete yset
def Add_Members_To_Target_group():
    users = []
    with open('/home/mohsen/VSCode/Telethon_Bot_project/members.csv','r',encoding='UTF-8') as fout:
        rows = csv.reader(fout , delimiter=',' , lineterminator="\n")
        next(rows,None)
        for row in rows:
            user = {}
            user['username'] = row[0]
            user['id'] = int(row[1])
            user['access_hash'] = int(row[2])
            user['fullname'] = row[3]
            users.append(user)

    chats = []
    groups = []
    response = client(GetDialogsRequest(
                                        offset_date=None,
                                        offset_id=0,
                                        offset_peer=InputPeerEmpty(),
                                        limit=10,
                                        hash=0
    ))

    chats.extend(response.chats)
    
    for chat in chats:
        groups.append(chat)



    i = 0
    for group in groups:
        print(str(i) , group.title)
        i = i + 1

    sleep(5)

    num = int(input("number of group : "))
    target = groups[num]

    target_entity = InputPeerChannel(
                                     channel_id=target.id,
                                     access_hash=target.access_hash
    )

    for user in users:
        try:
            print("Adding {} ...".format(user['id']))
            user_ready_to_add = InputPeerUser(
                                              user_id=user['id'],
                                              access_hash=user['access_hash']
            )
            client(InviteToChannelRequest(target_entity,[user_ready_to_add]))
            print("User Added ... going to sleep for 30 sec")
            sleep(30)
        except PeerFloodError:
            print("Peer flood error ! Try again later")
        except UserPrivacyRestrictedError:
            print("This user's privacy does not allow you to do this ... Skipping this user")
        except Exception as err:
            print(err)
    
    print("Action completed successfuly !")



"""
def get_channel_data():
    entity = client.get_entity('hideproxi')
    print(entity.id)
    print(entity.access_hash)
    print("all good !")
"""


def Add_Group_to_Pending_Queue(Group_Link):
    try:
        with open('/home/mohsen/VSCode/Telethon_Bot_project/group_pending_queue.txt' , 'a') as fout:
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

    logger.info('Group added successfuly !')
    sleep(5)

    
    


if __name__ == "__main__":
    
    logger.info('START ...')
    proxy_ip = '46.4.129.55'
    proxy_port = 80
    api_id = "Client_app_id"
    api_hash = "Valid_Hash"
    phone = "Phone_Number"
    try:
        client = TelegramClient(
                                phone,
                                api_id,
                                api_hash                     
        )

        client.connect()

        if not client.is_user_authorized():
            client.send_code_request(phone)
            code = input("Enter the code: ")
            client.sign_in(
                            phone,
                            code     
            )

        
        Add_Group_to_Pending_Queue('https://t.me/CompEngDepInfo')
        Add_Group_to_Pending_Queue('https://t.me/PythonLinuxExperts')
        Add_Group_to_Pending_Queue('https://t.me/hideproxi')
        Add_Group_to_Pending_Queue('https://t.me/BASUTAs')
        Add_Group_to_Pending_Queue('https://t.me/joinchat/CAbL_VL0rCMqY6AzbP9yTQ')
        Scrap_Members_From_Pending_Queue()
        #sleep(10)
        #Add_Members_To_Target_group_From_Client_Account()
        client.disconnect()

    except ConnectionError as err:
        logger.error(err)
        print('----Use a proxy or VPN-----')
        sys.exit()
    
