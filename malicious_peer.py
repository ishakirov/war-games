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
from libp2psp import PeerDBS

def _p_(*args, **kwargs):
    """Colorize the output."""
    #sys.stdout.write(Common.DBS)
    _print_("DBS (malicious):", *args)
    sys.stdout.write(Color.none)

class MaliciousPeer(PeerDBS):

    persistentAttack = False
    onOffAttack = False
    onOffRatio = 100
    selectiveAttack = False
    selectedPeersForAttack = []

    def __init__(self, peer):
        # {{{
        PeerDBS.__init__(self)
        _p_("Initialized")
        # }}}
        
    def ProcessMessage(self, msg, sender):
        print ("tipo antes: ", type(msg))
        # {{{ Now, receive and send.
        #message[5]
        #message = bytearray(message, 'utf-8')
        message = array.array('B', msg).tostring()
        print ("longitud: ", len(message))
        print (Color.red, "PROCESS MESSAGE Malicious python", Color.none)
        chunk_number, chunk = struct.unpack("H1024s", message)
        print ("Chunk: ",chunk_number, len(message))
        if len(message) == self.message_size:
            # {{{ A video chunk has been received
            
            chunk_number, chunk = struct.unpack("H1024s", message)
            #self.chunks[chunk_number % self.buffer_size] = chunk
            print (type(chunk_number % self.buffer_size), type(msg))
            self.InsertChunk(chunk_number % self.buffer_size, msg)
            #self.received_flag[chunk_number % self.buffer_size] = True
            #It's not necessary because InsertChunk does it.
            self.received_counter += 1

            #maybe get the splitter tuple as a property would be useful
            if sender == (self.splitter_addr,self.splitter_port):
                # {{{ Send the previous chunk in burst sending
                # mode if the chunk has not been sent to all
                # the peers of the list of peers.

                # {{{ debug

                #if __debug__:
                   # _print_("DBS:", self.team_socket.getsockname(), \
                     #   Color.red, "<-", Color.none, chunk_number, "-", sender)

                # }}}

                while( (self.receive_and_feed_counter < len(self.GetPeerList())) and (self.receive_and_feed_counter > 0) ):
                    peer = self.GetPeerList()[self.receive_and_feed_counter]
                    print("SENDCHUNK")
                    self.send_chunk(peer)

                    # {{{ debug

                    if __debug__:
                        print ("DBS:", self.team_socket.getsockname(), "-",\
                            socket.ntohs(struct.unpack(self.message_format, \
                                                           self.receive_and_feed_previous)[0]),\
                            Color.green, "->", Color.none, peer)

                    # }}}

                    self.debt[peer] += 1
                    if self.debt[peer] > self.MAX_CHUNK_DEBT:
                        print (Color.red, "DBS:", peer, 'removed by unsupportive (' + str(self.debt[peer]) + ' lossess)', Color.none)
                        del self.debt[peer]
                        self.GetPeerList().remove(peer)

                    self.receive_and_feed_counter += 1

                self.receive_and_feed_counter = 0
                self.receive_and_feed_previous = message

               # }}}
            else:
                # {{{ The sender is a peer

                # {{{ debug

                if __debug__:
                    print ("DBS:", self.team_socket.getsockname(), \
                        Color.green, "<-", Color.none, chunk_number, "-", sender)

                # }}}

                if sender not in self.GetPeerList():
                    # The peer is new
                    self.InsertPeer(sender)
                    self.debt[sender] = 0
                    print (Color.green, "DBS:", sender, 'added by chunk', \
                        chunk_number, Color.none)
                else:
                    self.debt[sender] -= 1

                # }}}

            # {{{ A new chunk has arrived and the
            # previous must be forwarded to next peer of the
            # list of peers.
            if ( self.receive_and_feed_counter < len(self.GetPeerList()) and ( self.receive_and_feed_previous != '') ):
                # {{{ Send the previous chunk in congestion avoiding mode.

                peer = self.GetPeerList()[self.receive_and_feed_counter]
                print("SENDCHUNK")
                self.send_chunk(peer)

                self.debt[peer] += 1
                if self.debt[peer] > self.MAX_CHUNK_DEBT:
                    print (Color.red, "DBS:", peer, 'removed by unsupportive (' + str(self.debt[peer]) + ' lossess)', Color.none)
                    del self.debt[peer]
                    self.RemovePeer(peer)

                # {{{ debug

                if __debug__:
                    print ("DBS:", self.team_socket.getsockname(), "-", \
                        socket.ntohs(struct.unpack(self.message_format, self.receive_and_feed_previous)[0]),\
                        Color.green, "->", Color.none, peer)

                # }}}

                self.receive_and_feed_counter += 1

                # }}}
            # }}}

            return chunk_number

            # }}}
        else:
            # {{{ A control chunk has been received
            print("DBS: Control received")
            if message == 'H':
                if sender not in self.GetPeerList():
                    # The peer is new
                    self.InsertPeer(sender)
                    self.debt[sender] = 0
                    print (Color.green, "DBS:", sender, 'added by [hello]', Color.none)
            else:
                if sender in self.GetPeerList():
                    sys.stdout.write(Color.red)
                    print ("DBS:", self.team_socket.getsockname(), '\b: received "goodbye" from', sender)
                    sys.stdout.write(Color.none)
                    self.RemovePeer(sender)
                    del self.debt[sender]
            return -1
        
            # }}}

        # }}}

    def send_chunk(self, peer):
        '''
        if self.persistentAttack:
            self.team_socket.sendto(self.get_poisoned_chunk(self.receive_and_feed_previous), peer)
            self.sendto_counter += 1
            print (Color.red, "Persistent Attack", Color.none)
            return

        if self.onOffAttack:
            r = random.randint(1, 100)
            if r <= self.onOffRatio:
                self.team_socket.sendto(self.get_poisoned_chunk(self.receive_and_feed_previous), peer)
            else:
                self.team_socket.sendto(self.receive_and_feed_previous, peer)

            self.sendto_counter += 1
            return

        if self.selectiveAttack:
            if peer in self.selectedPeersForAttack:
                self.team_socket.sendto(self.get_poisoned_chunk(self.receive_and_feed_previous), peer)
            else:
                self.team_socket.sendto(self.receive_and_feed_previous, peer)

            self.sendto_counter += 1
            return
        '''
        print (Color.red, "SENDING....", Color.none)
        #self.team_socket.sendto(self.receive_and_feed_previous, peer)
        #self.sendto_counter += 1

    def get_poisoned_chunk(self, chunk):
        chunk_number, chunk = struct.unpack(self.message_format, chunk)
        return struct.pack(self.message_format, chunk_number, '0')

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
