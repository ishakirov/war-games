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
        
    def SendChunk(self, peer):
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
        self.team_socket().sendto(self.receive_and_feed_previous, peer)
        self.sendto_counter += 1

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
