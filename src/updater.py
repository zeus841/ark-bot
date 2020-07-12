import classes as c # our classes
from helpers import * # our helpers
import config  # config
import discord # main discord libary
from discord.ext import commands # import commands extension
from discord.ext import tasks
import json 
import traceback
import time
from datetime import datetime
import dbl
import os 
import notifications
import io

debug = Debuger('updater') # create debuger (see helpers.py)
conf = config.Config() # load config
game = discord.Game('ping me to get prefix')
bot = commands.Bot(command_prefix=get_prefix,help_command=None,activity=game) # create bot with default prefix and no help command
debug.debug('Inited DB and Bot!') # debug into console !
t = c.Translation() # load default english translation

bot.loop.set_debug(conf.debug)

class Updater(commands.Cog):
    def __init__(self, bot):
        self.index = 0
        self.bot = bot
        self.printer.start()

    def cog_unload(self):
        self.printer.cancel()

    @tasks.loop(seconds=30.0)
    async def printer(self):
        try:
            servers = makeRequest('SELECT * FROM servers') #get all servers
            notifications = makeRequest('SELECT * FROM notifications') # get all notifications
            serverList = [] # will be filled with content [['server_ip',server_online(1 or 0)],...]
            for server in servers: # for each server
                ip = server[1] # get it ip
                id = server[0] # get it id
                try: # standart online/offline check
                    serverObj = c.ARKServer(ip).GetInfo() # get info about server 
                    playersList = c.PlayersList(ip).getPlayersList() # get players list
                    makeRequest('UPDATE servers SET ServerObj=%s , PlayersObj=%s , LastOnline=1 WHERE Ip =%s',(serverObj.toJSON(),playersList.toJSON(),ip)) # update DB record
                    test = [] # ['server_ip',server_online(1 or 0)]
                    test.append(id) # append server id
                    if (server[6] == 0):
                        test.append(1) # append 1 for offline server status
                    else:
                        test.append(3) # fast fix to logic problem (if server was online on past check we don't need to notify user)
                    serverList.append(test) # append our mini list to our main list
                    print(f'Updated record for online server: {ip}') # debug
                except: # if server not online (will throw socket.timeout but I lazy) 
                    test = [] # make our mini list
                    test.append(id) # append server id
                    if (server[6] == 1):
                        test.append(0) # append 1 for offline server status
                    else:
                        test.append(3) # fast fix to logic problem (if server was offline on past check we don't need to notify user)
                    serverList.append(test) # append our mini list to main list
                    makeRequest('UPDATE servers SET LastOnline=0, OfflineTrys=%s  WHERE Ip =%s',(server[6]+1,ip)) # update server
                    print(f'Updated record for offline server: {ip}') # debug
            
            for server in serverList: # process our main list 
                # for each server record 
                for record in notifications: # go throu all notifications
                    idsList = json.loads(record[4]) # load list of server ids in notification record
                    if server[0] in idsList: # if we found our current server id in list
                        if 1 in record[2]  and server[1] == 0 and record[3] == 0: # if we found 1 (id for server went offline notification) AND server status in main list is 0 (offline) AND we didn't sent message already (sent row in DB) 
                            channel = bot.get_channel(record[1]) # get channel id from notification record
                            serverRecord = makeRequest('SELECT * FROM servers WHERE Id=%s',(server[0],)) # get server record for that ip
                            await channel.send(f'Server {serverRecord[0][1]} went down !') # send channel with server ip (server record will be used to get server name) 
                            makeRequest('UPDATE notifications SET Sent=1 WHERE Id=%s',(record[0],)) # update notification record (set sent row to 1 it will be resetted later)
                        if 2 in record[2]  and server[1] == 1 and record[3] == 0: # if we found 2 (id for server went online notification) AND server status in main list is 1 (online) AND we didn't sent message already (sent row in DB) 
                            channel = bot.get_channel(record[1]) # get channel id from notification record
                            serverRecord = makeRequest('SELECT * FROM servers WHERE Id=%s',(server[0],)) # get server record for that ip
                            await channel.send(f'Server {serverRecord[0][1]} went up !') # send channel with server ip (server record will be used to get server name) 
                            makeRequest('UPDATE notifications SET Sent=1 WHERE Id=%s',(record[0],)) # update notification record (set sent row to 1 it will be resetted later)
        except BaseException as e:
            print(e)
    
bot.add_cog(Updater(bot))

bot.run(conf.token)


