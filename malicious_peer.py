"""
malicious_peer module
"""

# -*- coding: iso-8859-15 -*-

# This code is distributed under the GNU General Public License (see
# THE_GENERAL_GNU_PUBLIC_LICENSE.txt for extending this information).
# Copyright (C) 2015, the P2PSP team.
# http://www.p2psp.org

import struct
import socket
import sys
import threading
import random
import array

from color import Color
from _print_ import _print_

sys.path.append('lib/p2psp/bin/')
from libp2psp import PeerSTRPEDS

def _p_(*args, **kwargs):
    """Colorize the output."""
    #sys.stdout.write(Common.DBS)
    _print_("DBS (malicious):", *args)
    sys.stdout.write(Color.none)

class MaliciousPeer(PeerSTRPEDS):

    persistentAttack = False
    onOffAttack = False
    onOffRatio = 100
    selectiveAttack = False
    selectedPeersForSelectiveAttack = []
    regularPeers = []
    mainTarget = None
    numberChunksSendToMainTarget = 0
    allAttackC = False
    badMouthAttack = False
    MPTR = 5

    def __init__(self, peer):
        # {{{
        PeerSTRPEDS.__init__(self)
        _p_("Initialized")
        # }}}


    def firstMainTarget(self):
        self.mainTarget = self.chooseMainTarget()

    def chooseMainTarget(self):
        attackedPeers = []
        with open('attacked.txt', 'r') as fh:
            for line in fh:
                attackedPeers.append(line)
            fh.close()

        maliciousPeers = []
        with open('malicious.txt', 'r') as fh:
            for line in fh:
                maliciousPeers.append(line)
            fh.close()

        re = None
        while re == None:
            r = random.randint(0, len(self.GetPeerList())-1)
            peerEndpoint = '{0}:{1}'.format(self.GetPeerList()[r][0], self.GetPeerList()[r][1])
            if not ((peerEndpoint+'\n') in attackedPeers) and not ((peerEndpoint+'\n') in maliciousPeers):
                re = self.GetPeerList()[r]
                print ("====>", peerEndpoint, attackedPeers, maliciousPeers)

        with open('attacked.txt', 'a') as fh:
            if not peerEndpoint in attackedPeers:
                fh.write('{0}:{1}\n'.format(re[0], re[1]))
            fh.close()

        self.numberChunksSendToMainTarget = 0
        return re


    def ProcessMessage(self, message, sender):

        if sender in self.GetBadPeerList():
            return -1

        if self.IsCurrentMessageFromSplitter() or self.CheckMessage(bytes(message), sender):
            if self.IsCurrentMessageFromSplitter() and self.allAttackC:
                self.refreshRegularPeers()
                
            if self.IsControlMessage(bytes(message)) and message == 'B':
                return self.HandleBadPeersRequest()
            else:
                return self.DBSProcessMessage(message,sender)
        else:
            self.ProcessBadMessage(bytes(message), sender)
            return -1
        
    def DBSProcessMessage(self, message, sender):
        # {{{ Now, receive and send.
        
        print (Color.red, "PROCESS MESSAGE Malicious python", Color.none)
        if len(message) == self.message_size:
            # {{{ A video chunk has been received
            print("longitud: ", len(message))
            chunk_number, chunk, k1, k2, cr = struct.unpack("=H1024s40s40sI", message)
            self.current_round = cr
            chunk_number = socket.ntohs(chunk_number)
            #self.chunks[chunk_number % self.buffer_size] = chunk
            self.InsertChunk(chunk_number%self.buffer_size, chunk)
            #self.received_flag[chunk_number % self.buffer_size] = True
            #It's not necessary because InsertChunk does it.
            self.received_counter += 1

            #maybe get the splitter tuple as a property would be useful
            if sender == (self.splitter_addr,self.splitter_port):
                # {{{ Send the previous chunk in burst sending
                # mode if the chunk has not been sent to all
                # the peers of the list of peers.

                # {{{ debug

                print (Color.red, "Me <-", chunk_number, "-", str(sender))
                
                #if __debug__:
                   # _print_("DBS:", self.team_socket.getsockname(), \
                     #   Color.red, "<-", Color.none, chunk_number, "-", sender)

                # }}}

                while( (self.receive_and_feed_counter < len(self.GetPeerList())) and (self.receive_and_feed_counter > 0) ):
                    peer = self.GetPeerList()[self.receive_and_feed_counter]
                    print(Color.red, "SENDCHUNK", Color.none)
                    self.send_chunk(peer)

                    # {{{ debug
                    '''
                    if __debug__:
                        print ("DBS:", self.team_socket.getsockname(), "-",\
                            socket.ntohs(struct.unpack(self.message_format, \
                                                           self.receive_and_feed_previous)[0]),\
                            Color.green, "->", Color.none, peer)
                    '''
                    # }}}

                    #self.debt[peer] += 1
                    self.AddDebt(peer)
                    
                    if self.GetDebt(peer) > self.max_chunk_debt:
                        print (Color.red, "DBS:", peer, 'removed by unsupportive (' + str(self.GetDebt(peer)) + ' lossess)', Color.none)
                        self.RemoveDebt(peer)
                        #self.GetPeerList().remove(peer)
                        self.RemovePeer(peer)
                        
                    self.receive_and_feed_counter += 1

                self.receive_and_feed_counter = 0
                self.receive_and_feed_previous = bytes(message)

               # }}}
            else:
                # {{{ The sender is a peer

                # {{{ debug

                #if __debug__:
                #   print ("DBS:", self.team_socket.getsockname(), \
                #        Color.green, "<-", Color.none, chunk_number, "-", sender)

                # }}}

                if sender not in self.GetPeerList():
                    # The peer is new
                    self.InsertPeer(sender)
                    self.SetDebt(sender,0)
                    print (Color.green, "DBS:", sender, 'added by chunk', \
                        chunk_number, Color.none)
                else:
                    self.SetDebt(sender, (self.GetDebt(sender)-1))

                # }}}

            # {{{ A new chunk has arrived and the
            # previous must be forwarded to next peer of the
            # list of peers.
            if ( self.receive_and_feed_counter < len(self.GetPeerList()) and ( self.receive_and_feed_previous != '') ):
                # {{{ Send the previous chunk in congestion avoiding mode.

                peer = self.GetPeerList()[self.receive_and_feed_counter]
                self.send_chunk(peer)

                self.AddDebt(peer)
                
                if  self.GetDebt(peer) > self.max_chunk_debt:
                    print (Color.red, "DBS:", peer, 'removed by unsupportive (' + str(self.GetDebt(peer)) + ' lossess)', Color.none)
                    self.RemoveDebt(peer)
                    self.RemovePeer(peer)

                # {{{ debug

                #if __debug__:
                    #print ("DBS:", self.team_socket.getsockname(), "-", \
                    #    socket.ntohs(struct.unpack(self.message_format, self.receive_and_feed_previous)[0]),\
                    #    Color.green, "->", Color.none, peer)

                # }}}

                self.receive_and_feed_counter += 1

                # }}}
            # }}}

            return chunk_number

            # }}}
        else:
            # {{{ A control chunk has been received
            print("DBS: Control received")

            print("message ", message[0])
            if message[0] == 'H':
                if sender not in self.GetPeerList():
                    # The peer is new

                    self.InsertPeer(sender)
                    self.debt[sender] = 0
                    print (Color.green, "DBS:", sender, 'added by [hello]', Color.none)
            else:
                if sender in self.GetPeerList():
                    sys.stdout.write(Color.red)
                    print ("DBS:", "Me" , '\b: received "goodbye" from', sender)
                    sys.stdout.write(Color.none)
                    self.RemovePeer(sender)
                    self.RemoveDebt(sender)

            return -1
        
            # }}}

        # }}}

    def allAttack(self):
        print("ALL_ATTACK MODE")
        #self.allAttackC = True
        del self.regularPeers[:]
        with open('regular.txt', 'a') as fh:
            fh.write('{0}:{1}\n'.format(self.mainTarget[0], self.mainTarget[1]))
            fh.close()
        self.refreshRegularPeers()


    def refreshRegularPeers(self):
        with open('regular.txt', 'r') as fh:
            for line in fh:
                t = (line.split(':')[0], int(line.split(':')[1]))
                if t in self.GetPeerList():
                    self.regularPeers.append(t)
                if len(self.regularPeers) * 2 > len(self.GetPeerList()):
                    break
            fh.close()
    
    def send_chunk(self, peer):
        if len(self.receive_and_feed_previous) == 1110:
            if self.persistentAttack:
                if (peer == self.mainTarget) and (self.numberChunksSendToMainTarget < self.MPTR):
                    self.SendChunk(self.get_poisoned_chunk(self.receive_and_feed_previous), peer)
                    print("mainTarget attack:", peer)
                    self.sendto_counter += 1
                    self.numberChunksSendToMainTarget += 1
                    print("mainTarget+=1 ({0})".format(self.numberChunksSendToMainTarget))
                elif (peer == self.mainTarget) and (self.numberChunksSendToMainTarget >= self.MPTR):
                    if len(self.regularPeers) < (len(self.GetPeerList())/2):
                        self.allAttack()
                        self.SendChunk(self.get_poisoned_chunk(self.receive_and_feed_previous), peer)
                        print("mainTarget attack:", peer)
                        self.mainTarget = self.chooseMainTarget()
                        #To select a new mainTarget after incorporating a new peer to the regular list
                    else:
                         self.SendChunk(bytes(self.receive_and_feed_previous), peer)
                         print("No poisoned due to attack ratio "+ str(len(self.regularPeers)) + " of " + str(len(self.GetPeerList())))
                elif peer in self.regularPeers:
                    self.SendChunk(self.get_poisoned_chunk(self.receive_and_feed_previous), peer)
                    print("allAttackC attack:", peer)
		     #self.peer_list.remove(peer)                
                else:
                    self.SendChunk(bytes(self.receive_and_feed_previous), peer)
                    print("No poisoned", peer)

                chunk_number, chunk, k1, k2, cr = struct.unpack("=H1024s40s40sI", self.get_poisoned_chunk(self.receive_and_feed_previous))
                print (Color.red, "Persistent Attack: ", str(peer), "CN:", str(socket.ntohs(chunk_number)),  Color.none)
                return
            
            if self.onOffAttack:
                r = random.randint(1, 100)
                if r <= self.onOffRatio:
                    self.SendChunk(self.get_poisoned_chunk(self.receive_and_feed_previous), peer)
                else:
                    self.SendChunk(self.receive_and_feed_previous, peer)
            
                self.sendto_counter += 1
                return
            
            if self.selectiveAttack:
                if peer in self.selectedPeersForSelectiveAttack:
                    self.SendChunk(self.get_poisoned_chunk(self.receive_and_feed_previous), peer)
                else:
                    self.SendChunk(self.receive_and_feed_previous, peer)

                self.sendto_counter += 1
                print (Color.red, "Selective Attack", Color.none)
                return
        
            self.SendChunk(self.receive_and_feed_previous, peer)
            self.sendto_counter += 1
            print (Color.red, "No Attack", Color.none)
        
    def get_poisoned_chunk(self, message):
        chunk_number, chunk, k1, k2, cr = struct.unpack("=H1024s40s40sI", message)
        return struct.pack("=H1024s40s40sI", chunk_number, ("fake_chunk").encode("utf8"), k1, k2,cr)

    def setPersistentAttack(self, value):
        self.persistentAttack = value

    def setOnOffAttack(self, value, ratio):
        self.onOffAttack = True
        self.onOffRatio = ratio

    def setSelectiveAttack(self, value, selected):
        self.selectiveAttack = True
        for peer in selected:
            l = peer.split(':')
            peer_obj = (l[0], int(l[1]))
            self.selectedPeersForAttack.append(peer_obj)
            
    def setBadMouthAttack(self, value, selected):
        self.badMouthAttack = value
        if value:
            for peer in selected:
                l = peer.split(':')
                peer_obj = (l[0], int(l[1]))
                self.bad_peers.append(peer_obj)
        else:
            self.bad_peers = []

    def setMPTR(self, value):
        self.MPTR = int(value)
