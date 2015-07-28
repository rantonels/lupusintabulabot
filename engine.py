#!/usr/bin/python
# -*- coding: utf-8 -*-

import random

class GameError(Exception):
    pass

class StateError(GameError):
    pass

class NotAliveError(GameError):
    pass

class WrongPlayerNumberError(GameError):
    pass

class UnrecognizedRole(GameError):
    pass

class Role:
    def __init__(self,name,good,special):
        self.name = name
        self.good = good
        self.special = special

    def __str__(self):
        return self.name
    def __repr__(self):
        return self.__str__()

contadino = Role("Contadino",True,False)
lupo = Role("Lupo",False,False)
veggente = Role("Veggente",True,True)

def ch2role(c):
    if c == "c":
        return contadino
    elif c == "l":
        return lupo
    elif c == "v":
        return veggente
    else:
        raise UnrecognizedRole
        return None

class Player:
    def __str__(self):
        try:
            return str(self.index) + "." + self.name + " " + self.role.__str__()[0]
        except IndexError:
            return "EMPTY"

    def __repr__(self):
        return self.__str__()

    pass

NIGHT = 0
DAY = 1
FINISH = -1
PRE = -2
COUNTER = -3

W_TIE = 0
W_GOOD = 1
W_BAD = 2

def stateName(state):
    if state == NIGHT:
        return "NOTTE"
    elif state == DAY:
        return "GIORNO"
    elif state == FINISH:
        return "PARTITA CONCLUSA"
    elif state == COUNTER:
        return "conto alla rovescia per la notte..."
    else:
        return "ERRORE"

def sideName(side):
    if side == W_TIE:
        return "PATTA"
    elif side == W_GOOD:
        return "i BUONI vincono"
    elif side == W_BAD:
        return "i CATTIVI vincono"
    else:
        return "ERRORE"

class Game:
    def __init__(self,rolestring):
        self.rolelist = []
        for c in rolestring:
            r = ch2role(c)
            if r == None:
                return None
            self.rolelist.append(r)

        self.turn = 0
        self.state = PRE


    def setPlayers(self,nameslist):
        if len(nameslist) != len(self.rolelist):
            raise WrongPlayerNumberError
            return

        random.shuffle(self.rolelist)

        self.players = []

        for i in range(len(nameslist)):
            np = Player()
            np.name = nameslist[i]
            np.role = self.rolelist[i]
            np.alive = True
            np.index = i

            self.players.append(np)
            
        self.state = COUNTER

    def alivePlayers(self):
        return [p for p in self.players if p.alive]

    def goodPlayers(self):
        return [p for p in self.players if (p.alive and p.role.good)]

    def badPlayers(self):
        return [p for p in self.players if (p.alive and (not p.role.good))]

    def wolves(self):
        return [p for p in self.players if (p.alive and p.role == lupo)]

    def watchers(self):
        return [p for p in self.players if (p.alive and p.role == veggente)]

    def checkEnd(self):
        if len(self.alivePlayers()) == 0:
            self.state = FINISH
            self.win = W_TIE
            return
        if len(self.goodPlayers()) == 0:
            self.state = FINISH
            self.win = W_BAD
            return
        if len(self.badPlayers()) == 0:
            self.state = FINISH
            self.win = W_GOOD

    def euthanise(self,toe):
        self.players[toe].alive = False
        self.checkEnd()

    def inputNight(self,wolf_action,view_action):
        # wolf_action is a dict with entries 'tomurder':player_index
        # view_action is a dict with entries 'toview':player_index

        if self.state != NIGHT:
            raise StateError
            return None
        
        killed_now = []

        if wolf_action:
            tm = wolf_action['tomurder']

            if tm != None:
                if not self.players[tm].alive:
                    raise NotAliveError
                    return None
              
                killed_now.append(tm)

        if view_action:
            tv = view_action['toview']

            if not self.players[tv].alive:
                raise NotAliveError
                return None

        for tokill in killed_now:
            self.players[tokill].alive = False

        out={}
        out['killed_now']=killed_now
        if view_action:
            out['viewed']=self.players[tv].role.good

        self.state = DAY

        self.checkEnd()

        return out

    def inputDay(self,voted):
        # voted is the id of the voted player

        if self.state != DAY:
            raise StateError
            return None

        if not self.players[voted].alive:
            raise NotAliveError
            return None

        self.players[voted].alive = False

        self.state = NIGHT

        self.checkEnd()



