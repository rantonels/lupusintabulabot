#!/usr/bin/python
# -*- coding: utf-8 -*-

import engine   #game engine
import requests
import random
import time

import os,sys

reload(sys)
sys.setdefaultencoding("utf-8")

delay = 0.4

authf = open('/home/riccardo/.ltauth','r')
auth = authf.read().strip()
authf.close()

class StatusNotOk(Exception):
    pass

def exprint(e):
    # turns out some exceptions are so brutal
    # they throw an exception when you try to print them.
    print "Exception encountered."
    try:
        print e
    except:
        print "Error printing exception."


startTime = time.time()

class Chat:
    pass

class LupusBot:
    def __init__(self):
        self.updates = []
        self.groupchats = {}
        self.pvtchats = {}
        self.lastid = 0

    
    def safe_request(self,http,params,files=None):
        # run a requests.get but catching exceptions.
        # params and files are the usual requests.get arguments, http is the url
        # returns the request object, None if there were errors.

        try:
            if files:
                r = requests.get(http,params=params,files=files,timeout=2)
            else:
                r = requests.get(http,params=params,timeout=2)
            if r.status_code != 200:
                raise StatusNotOk
        except requests.exceptions.RequestException as e:
            exprint(e)
            return None
        except StatusNotOk:
            print "HTTP error %d"%r.status_code

            print r.text
            print r.url

            if r.json()[u'description'] == "Error: Bad Request: Not in chat":
                print "sembrerebbe che non siamo in questa chat."
                del self.chats[params[u'chat_id']]
                del self.excitements[params[u'chat_id']]

            return None
        except:
            print "Unexpected error:",sys.exc_info()[0]
            return None

        return r


    def getMessages(self):
        http = "https://api.telegram.org/bot%s/getUpdates"%auth+"?offset=%d"%self.lastid
        #print http

        r = self.safe_request(http,{})
 
        if r == None:
            return
        
        toadd = r.json()[u'result']

        if(len(toadd)==0):
            return

        self.lastid = int(toadd[-1][u'update_id'])+1

        #print self.lastid

        self.updates = self.updates + toadd
        print "New %d updates"%len(toadd)

        for u in toadd:
            if u'message' in u:
                cht = u[u'message'][u'chat']
                if not ((cht[u'id'] in self.pvtchats) or (cht[u'id'] in self.groupchats)):
                    CH = Chat()
                    if u'first_name' in cht:
                        nname = cht[u'first_name']
                        CH.name = nname
                        
                        for gpc in self.groupchats:
                            if self.groupchats[gpc].game:
                                for pp in self.groupchats[gpc].wantplay:
                                    pass
                                   # if (cht[u'id'] == pp['id']) and (not pp['confirmed']):
                                   #     pp['confirmed'] = True
                                   #     self.sendMessage(cht[u'id'],"You are confirmed.")
                                   #     self.sendMessage(gpc, 
                                   #             "Giocatori confermati: %d/%d"%(
                                   #                 len([p for p in self.groupchats[gpc].wantplay if p['confirmed']]),
                                   #                 len(self.groupchats[gpc].game.rolelist)
                                   #                 )
                                   #             )
                                   #     

                                   #     self.pvtchats[cht[u'id']]=CH
                                   #     
                                   #     if len([p for p in self.groupchats[gpc].wantplay if p['confirmed']]) == len(self.groupchats[gpc].game.rolelist):
                                   #         self.startGame(gpc)
                                   #     
                                   #     break

                    else:
                        nname = cht[u'title']
                        CH.name = nname
                        CH.game = None
                        self.groupchats[cht[u'id']]=CH
                        

                    print "New chat detected! id %s name %s"%(cht[u'id'],nname)

                    #self.chats[ cht[u'id']] = nname

    def startGame(self,gpc):
        nameslist = []
        
        for p in self.groupchats[gpc].wantplay:
            nn = p['user'][u'first_name']
            if u'last_name' in p['user']:
                nn += " " + p['user'][u'last_name']
            nameslist.append(nn)
            

        print nameslist

        self.groupchats[gpc].players = self.groupchats[gpc].wantplay

        self.groupchats[gpc].game.setPlayers(nameslist)

        for i in range(len(nameslist)):
            self.groupchats[gpc].game.players[i].chat_id = self.groupchats[gpc].players[i]['id']

        self.sendMessage(gpc,"Tutti i giocatori confermati. I vostri ruoli vi sono stati comunicati in chat privata. La partita inizierà fra 7 secondi.")
        for i in range(len(self.groupchats[gpc].players)):
            self.sendMessage(self.groupchats[gpc].players[i][u'id'],
                "Il tuo ruolo è %s."%(self.groupchats[gpc].game.players[i].role.__str__().upper())
                )

        self.groupchats[gpc].counter = 7.0


    def sendMessage(self,chid,message,replyto=None):
        try:
            print "writing to chat",chid
        except KeyError:
            print "ERROR: not in chat"
            return
        print "BODY:",message.split('\n')[0]

        try:
            decotex = unicode(message,"utf-8")
        except TypeError:
            decotex = message

        args = {'chat_id':chid,'text':decotex}
        if replyto:
            args[u'reply_to_message_id'] = replyto
        http = "https://api.telegram.org/bot%s/sendMessage"%auth
                
        r = self.safe_request(http,args)


    def processUpdate(self,u):
        if u'message' in u:
            mm = u[u'message']
            if (u'text' in mm) and (mm[u'text'][0] == "/"):
                nude = mm[u'text'][1:].strip()
                ll = nude.split("@")
                if len(ll) == 1 or (ll[1] == "lupusintabulabot"):
                    self.runCommand(ll[0],mm,u'title' in mm[u'chat'])
                else:
                    print "command was not for me!"
            else:
                pass
                #wolf relay
                #if (

    def stopGame(self,chat):
        del self.groupchats[chat].game
        self.groupchats[chat].game = None

        try:
            del self.groupchats[chat].players
        except AttributeError:
            pass

        self.groupchats[chat].wantplay = []


    def runCommand(self,command,m,isgroup):
        print "executing command %s"%command

        chat = m[u'chat'][u'id']
        mid = m[u'message_id']

        comw = command.split()

        if comw[0] == "start":
            if not isgroup:
                self.sendMessage(chat,"Esegui questo comando in una chat di gruppo.",mid)
                return
            elif self.groupchats[chat].game:
                self.sendMessage(chat,"C'è già una partita in corso in questo gruppo.",mid)
            elif len(comw)<2:
                self.sendMessage(chat,
                        '''Perfavore, dimmi anche i ruoli che desideri. Ad esempio:\n\n/start ccccccvll''',mid)
            else:
                try:
                    self.groupchats[chat].game = engine.Game(comw[1].lower().strip())
                    self.groupchats[chat].wantplay = []
                    self.groupchats[chat].counter = None
                    self.sendMessage(chat,"Nuova partita creata. Cliccate qui: /in per entrare nella partita.",mid)


                except engine.UnrecognizedRole:
                    self.sendMessage(chat,"Mi spiace, non sono riuscito ad interpretare la stringa dei ruoli.",mid)
                
        elif comw[0] == "in":
            if not isgroup: #comando /in in chat privata
                pass
            else:           #comando /in in chat pubblica 

                if not self.groupchats[chat].game:  #non c'è la partita
                    self.sendMessage(chat,"Non c'è una partita in corso. Inizia una partita col comando /start",mid)
                else:   #c'è la partita

                    if self.groupchats[chat].game.state != -2:     #partita già in corso
                        self.sendMessage(chat,"La partita è già in corso, come minimo sei un po' in ritardo.",mid)
                    else:                                           #partita in PRE
                        p = m[u'from'][u'id']
                    
                        alread = False
                        for i in range(len(self.groupchats[chat].wantplay)):
                            if self.groupchats[chat].wantplay[i]['id'] == p:
                                alread = True
                                iddp = i
                        if alread:      #già /in
                            if self.groupchats[chat].wantplay[iddp]['confirmed']:
                                self.sendMessage(chat,"Sei già inserito e confermato, attendi gli altri giocatori.",mid)
                            else:
                                self.sendMessage(chat,"Sei già inserito, ora scrivimi qualsiasi cosa *in privato* per confermare.",mid)
                        else:
                            if len(self.groupchats[chat].wantplay) < len(self.groupchats[chat].game.rolelist):
                                self.groupchats[chat].wantplay.append( {'id':p,'user':m[u'from'],'confirmed':True} )
                                self.sendMessage(chat,"Inserito. (%d/%d)"%(len(self.groupchats[chat].wantplay),len(self.groupchats[chat].game.rolelist)),mid)
                                if len(self.groupchats[chat].wantplay) == len(self.groupchats[chat].game.rolelist):
                                    self.startGame(chat)
                            else:
                                self.sendMessage(chat,"Mi spiace, numero totale di giocatori già raggiunto.",mid)
        elif comw[0] == "stop":
            self.sendMessage(chat,"Sei veramente sicuro di voler arrestare la partita? Se sì, dai il comando / stopstop (senza spazio)",mid)
        
        elif comw[0] == "stopstop":
            if not isgroup:
                alread = False
                alreadpre = False
                for gpc in self.groupchats:
                    if self.groupchats[gpc].game:  
                        if self.groupchats[gpc].game.state != -2:
                            for i in range(len(self.groupchats[gpc].players)):
                                if self.groupchats[gpc].players[i]['id'] == chat:
                                    alread = True
                                    iddp = i
                                    gpcp = gpc
                                    break
                        else:
                            for i in range(len(self.groupchats[gpc].wantplay)):
                                if self.groupchats[gpc].wantplay[i]['id'] == chat:
                                    alreadpre = True
                                    iddp = i
                                    gpcp = gpc
                                    break
                                
                
                if alread:
                    self.sendMessage(chat,"Ti sei suicidato.",mid)
                    self.groupchats[gpc].game.euthanise(iddp)
                    self.sendMessage(gpc,"%s si è suicidato."%self.groupchats[gpc].game.players[iddp].name,mid)
                elif alreadpre:
                    self.sendMessage(chat,"Hai abbandonato la partita.",mid)
                    self.sendMessage(gpc,"%s ha lasciato la partita."%self.groupchats[gpc].wantplay[iddp]['user'][u'first_name'],mid)
                    del self.groupchats[gpc].wantplay[iddp]

                else:
                    self.sendMessage(chat,"Non mi risulta tu sia in nessuna partita.",mid)

            else:
                if not self.groupchats[chat].game:
                    self.sendMessage(chat,"Nessun gioco attivo, niente da interrompere.",mid)
                else:
                   
                    self.sendMessage(chat,"Partita terminata.",mid)
                    try:
                        for p in self.groupchats[chat].wantplay:
                            self.sendMessage(p[u'id'],"La partita è stata interrotta.")
                    except ValueError:
                        pass
                    
                    self.stopGame(chat) 
                    
        
        elif comw[0] == "info":
            if isgroup:
                if self.groupchats[chat].game:
                    if self.groupchats[chat].game.state == -2:
                        self.sendMessage(chat,"In attesa di conferma dei giocatori.",mid)
                    else:
                        st = engine.stateName(self.groupchats[chat].game.state) + "\n"
                        if self.groupchats[chat].counter != None:
                            st += "(meno %d secondi)\n"%int(self.groupchats[chat].counter)
                        st += "\nGiocatori vivi:\n\n"
                        for p in self.groupchats[chat].game.alivePlayers():
                            st += p.name + "\n"
                        self.sendMessage(chat,st,mid)
                else:
                    self.sendMessage(chat,"Nessuna partita attiva. Usa /start per iniziare una nuova partita, /help per maggiori informazioni.",mid)
            else:
                self.sendMessage(chat,"Questo comando è veramente utile sono nella chat della partita. Prova /help.",mid)

        elif comw[0] == "help":
            st =    "Per iniziare una nuova partita, eseguire /start seguito da una stringa di ruoli:\n"
            st +=   "C - Contadino\n"
            st +=   "L - Lupo\n"
            st +=   "V - Veggente\n"
            st +=   "\nPer fermare la partita, esegui /stop"
            self.sendMessage(chat,st,mid)

        elif comw[0].isdigit():
            n = int(comw[0])

            if not isgroup:
                alread = False
                for gpc in self.groupchats:
                    if self.groupchats[gpc].game and self.groupchats[gpc].game.state in [0]:  
                        for i in range(len(self.groupchats[gpc].players)):
                            if self.groupchats[gpc].players[i]['id'] == chat:
                                alread = True
                                iddp = i
                                gpcp = gpc
                                break

                if alread:
                    if self.groupchats[gpcp].game.state == 0:
                        pl = self.groupchats[gpcp].game.players[iddp]
                      
                        if (pl.role == engine.lupo) or (pl.role == engine.veggente):
                            try:
                                if self.groupchats[gpcp].game.players[n].alive:
                                    pl['choice'] = n
                                    self.sendMessage(chat,"Selezionato.",mid)
                                else:
                                    self.sendMessage(chat,"Quel giocatore non è vivo.",mid)
                            except IndexError,KeyError:
                                self.sendMessage(chat,"Quel giocatore non esiste.",mid)
                        
            else:
                alread = False
                if self.groupchats[chat].game and self.groupchats[chat].game.state in [1]:  
                    for i in range(len(self.groupchats[chat].players)):
                        if self.groupchats[chat].players[i]['id'] == m[u'from'][u'id']:
                            alread = True
                            iddp = i
                            break
                if alread:
                    pl = self.groupchats[chat].players[iddp]
                    try:
                        if self.groupchats[chat].game.players[n].alive:
                            pl['choice'] = n
                            self.repeatVotes(chat)
                        else:
                            self.sendMessage(chat,"Quel giocatore non è vivo.",mid)
                    except IndexError,KeyError:
                        self.sendMessage(chat,"Quel giocatore non esiste.",mid)
                else:
                    self.sendMessage(chat,"O non è il momento di mandare quel messaggio, oppure non appartieni a questa partita.",mid)

    def repeatVotes(self,gpc):
        st = ""
        votes = [0 for p in self.groupchats[gpc].players]
        for i in range(len(self.groupchats[gpc].players)):
            p = self.groupchats[gpc].players[i]
            if ('choice' in p) and ( p['choice']!=None):
                votes[p['choice']]+=1

        for i in range(len(votes)):
            v = votes[i]
            st +=  self.groupchats[gpc].game.players[i].name + " " + "👎"*v + "\n"

        self.sendMessage(gpc,st)

        if sum(votes) >= len(self.groupchats[gpc].game.alivePlayers()):
            #counter = 1
            self.doStep(gpc)

            
                

    def nightMessage(self,gpc):
        for p in self.groupchats[gpc].game.wolves():
            self.sendMessage(p.chat_id,"Seleziona chi vuoi mangiare (mandami il numero). Puoi comunicare con gli altri lupi in questa chat. Dovete fare una scelta unanime entro la fine della notte (30 secondi).")
            f = ""
            ap = self.groupchats[gpc].game.alivePlayers()
            for i in range(len(ap)):
                f += "/"+str(i) + " " + ap[i].name + "\n"

            self.sendMessage(p.chat_id,f)

        for p in self.groupchats[gpc].game.watchers():
            self.sendMessage(p.chat_id,"Seleziona chi vuoi esaminare (mandami il numero). Hai 30 secondi")
            f = ""
            ap = self.groupchats[gpc].game.alivePlayers()
            for i in range(len(ap)):
                f += str(i) + " " + ap[i].name + "\n"
            
            self.sendMessage(p.chat_id,f)

        for p in self.groupchats[gpc].players:
            p['choice'] = None

    def doStep(self,gpc):
        gpco = self.groupchats[gpc]
        ggame = gpco.game


        if ggame.state == -3:
            ggame.state = 0
            self.groupchats[gpc].counter = 10.0
            self.sendMessage(gpc,"Partita iniziata, scende la NOTTE.\n\nSiete pregati di non comunicare se non nella conversazione di gruppo o in chat privata *con il bot*. I giocatori morti sono pregati di restare in silenzio.")
            self.nightMessage(gpc)
            return

        if ggame.state == 0:
            wolchoice =  [self.groupchats[gpc].players[i]['choice'] for i in range(len(self.groupchats[gpc].players)) if (ggame.players[i].role == engine.lupo) ] 

            if None in wolchoice: wolchoice.remove(None)

            wolchoice = list(set(wolchoice))

            if (len(wolchoice) == 0) or (len(wolchoice) > 1):
                for p in ggame.wolves():
                    self.sendMessage(p.chat_id,"Non avete fatto una scelta, nessuno morirà.")
                wolf_action = {'tomurder':None}
            else:
                wolf_action = {'tomurder': wolchoice[0]}

            view_action = None
            if len(ggame.watchers())>0:
                view_action = {'toview': self.groupchats[gpc].players[ggame.watchers()[0].index ]['choice'] }
                if view_action['toview'] == None:
                    view_action = None

            ret = ggame.inputNight(wolf_action,view_action)

            self.sendMessage(gpc,"è GIORNO.")

            if len(ret['killed_now'])==0:
                self.sendMessage(gpc,"Nessuno è morto stanotte.")
            elif len(ret['killed_now']) == 1:
                self.sendMessage(gpc,ggame.players[ret['killed_now'][0]].name + " è morto.")
            else:
                m = ""
                for k in ret['killed_now']:
                    m+=self.groupchats[gpc].players[k.name] + ", "
                m+= "sono morti."

                self.sendMessage(gpc,m)
            
            for k in ret['killed_now']:
                self.sendMessage(ggame.players[k].chat_id, "Sei morto. Astieniti dal commentare nel gruppo.")

            if view_action:
                self.sendMessage(ggame.watchers()[0].chat_id, 
                        "la persona in questione è "+ {True:"BUONA",False:"CATTIVA"}[ggame.players[view_action['toview']].role.good]
                        )

            if ggame.state != -1: #solo se la partita non è finita
                f = "Votate il giocatore da uccidere entro la fine del giorno (2 minuti).\n\n"
                
                ap = ggame.alivePlayers()
                f += "".join([  "/"+str(i)+" "+p.name + "\n" for i,p in enumerate(ap)])

                self.sendMessage(gpc,f)


                self.groupchats[gpc].counter = 120.0
                    
                #p = ggame.alivePlayers()
                #for i in range(len(ap)):
                #    f += "/"+str(i) + " " + ap[i].name + "\n"
                                                
                for p in self.groupchats[gpc].players: p['choice'] = None
               
            return

        if ggame.state == 1:
            votes = [0 for p in self.groupchats[gpc].players]
            for i in range(len(self.groupchats[gpc].players)):
                p = self.groupchats[gpc].players[i]
                if ('choice' in p) and ( p['choice']!=None):
                    votes[p['choice']]+=1

            vmax = max(votes)

            besters = [i for i,v in enumerate(votes) if v == vmax]


            if len(besters) == 0:
                print "ERROR"
            elif len(besters) == 1:
                self.sendMessage(gpc,ggame.players[i].name + " è stato impiccato.")
                di = i
            else:
                st = "I seguenti giocatori sono in parità di voti:\n"
                for i in besters:
                    st += ggame.players[i].name + "\n"
                di = random.choice(besters)
                st += "\nViene sorteggiato a caso %s, che viene impiccato."%ggame.players[di].name
                self.sendMessage(gpc,st)


            ggame.inputDay(di)
            self.sendMessage(ggame.players[di].chat_id, "Sei stato impiccato. Astieniti dal commentare nel gruppo.")
            gpco.counter = 10.0

            return


    def cycle(self,pastdelay):
        self.getMessages()

        for gpc in self.groupchats:
            if self.groupchats[gpc].game and (self.groupchats[gpc].counter != None):
                
                self.groupchats[gpc].counter = self.groupchats[gpc].counter - pastdelay

                if self.groupchats[gpc].counter < 0:
                    self.doStep(gpc)

            if (self.groupchats[gpc].game):
                if (self.groupchats[gpc].game.state == -1):
                    self.sendMessage(gpc,"La partita è CONCLUSA. Risultato:\n\n"+engine.sideName(self.groupchats[gpc].game.win))
                    self.stopGame(gpc)
                
                

        while self.updates:
            print "processing update..."
            u = self.updates.pop(0)
            self.processUpdate(u)


        

        try:
            print "Attivo in %d,%d chat."%(len(self.groupchats),len(self.pvtchats))
        except KeyError:
            print "KEYERROR"



bot = LupusBot()

pastdelay = delay

while True:
    pretime = time.time()
    bot.cycle(delay)

    try:
        pastdelay = delay-time.time()+pretime
        time.sleep(max(0,pastdelay))
    except KeyboardInterrupt:
        sys.exit()
