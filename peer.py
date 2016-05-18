#!/usr/bin/env python3

# -*- coding: iso-8859-15 -*-

# This code is distributed under the GNU General Public License (see
# THE_GENERAL_GNU_PUBLIC_LICENSE.txt for extending this information).
# Copyright (C) 2014, the P2PSP team.
# http://www.p2psp.org

# PYTHON_ARGCOMPLETE_OK

# {{{ Imports

from __future__ import print_function
import sys
import socket
import struct
import time
import threading
import os
import argparse
try:
    import argcomplete                    # Bash tab completion for argparse in Unixes
except ImportError:
    pass

try:
    import colorama # Enable console color using ANSI codes in Windows
except ImportError:
    pass

from color import Color
from _print_ import _print_
sys.path.append('lib/p2psp/bin/')
from libp2psp import PeerDBS, MonitorDBS, PeerSTRPEDS
from malicious_peer import MaliciousPeer

# }}}

# Some useful definitions.
ADDR = 0
PORT = 1

class Peer():
    
    def console(self, peer):
        
        print("+-----------------------------------------------------+")
        print("| Received = Received kbps, including retransmissions |")
        print("|     Sent = Sent kbps                                |")
        print("|       (Expected values are between parenthesis)     |")
        print("------------------------------------------------------+")
        print()
        print("         |     Received (kbps) |          Sent (kbps) |")
        print("    Time |      Real  Expected |       Real  Expected | Team description")
        print("---------+---------------------+----------------------+-----------------------------------...")

        last_chunk_number = peer.GetPlayedChunk()
        peer.sendto_counter = 0
        last_sendto_counter = 0
        last_recvfrom_counter = peer.recvfrom_counter
        
        while peer.IsPlayerAlive():
            kbps_expected_recv = ((peer.GetPlayedChunk() - last_chunk_number) * peer.chunk_size * 8) / 1000
            last_chunk_number = peer.GetPlayedChunk()
            kbps_recvfrom = ((peer.recvfrom_counter - last_recvfrom_counter) * peer.chunk_size * 8) / 1000
            last_recvfrom_counter = peer.recvfrom_counter
            team_ratio = len(peer.GetPeerList()) /(len(peer.GetPeerList()) + 1.0)
            kbps_expected_sent = int(kbps_expected_recv*team_ratio)
            kbps_sendto = ((peer.sendto_counter - last_sendto_counter) * peer.chunk_size * 8) / 1000
            last_sendto_counter = peer.sendto_counter
            
            if kbps_recvfrom > 0 and kbps_expected_recv > 0:
                nice = 100.0/float((float(kbps_expected_recv)/kbps_recvfrom)*(len(peer.GetPeerList())+1))
            else:
                nice = 0.0
            _print_('|', end=Color.none)
            
            if kbps_expected_recv < kbps_recvfrom:
                sys.stdout.write(Color.red)
            elif kbps_expected_recv > kbps_recvfrom:
                sys.stdout.write(Color.green)
                
            print(repr(int(kbps_expected_recv)).rjust(10), end=Color.none)
            print(repr(int(kbps_recvfrom)).rjust(10), end=' | ')
            
            if kbps_expected_sent > kbps_sendto:
                sys.stdout.write(Color.red)
            elif kbps_expected_sent < kbps_sendto:
                sys.stdout.write(Color.green)
                
            print(repr(int(kbps_sendto)).rjust(10), end=Color.none)
            print(repr(int(kbps_expected_sent)).rjust(10), end=' | ')
            print(len(peer.GetPeerList()), end=' ')
            
            counter = 0
            for p in peer.GetPeerList():
                if (counter < 5):
                    print(p, end=' ')
                    counter += 1
                else:
                    break
            print()
        try:
            if Common.CONSOLE_MODE == False :
                GObject.idle_add(speed_adapter.update_widget,str(0)+' kbps',str(0)+' kbps',str(0))
        except  Exception as msg:
            pass
            # }}}
    
    def __init__(self):
        
        try:
            colorama.init()
        except Exception:
            pass

        _print_("Running in", end=' ')
        if __debug__:
            print("debug mode")
        else:
            print("release mode")
            
        peer = PeerSTRPEDS()
        parser = argparse.ArgumentParser(description='This is the peer node of a P2PSP team.')
        
        parser.add_argument('--enable_chunk_loss', help='Forces a lost of chunks')
        parser.add_argument('--max_chunk_debt', help='The maximun number of times that other peer can not send a chunk to this peer. Defaut = {}'.format(peer.max_chunk_debt))
        parser.add_argument('--player_port', help='Port to communicate with the player. Default = {}'.format(peer.player_port))
        parser.add_argument('--port_step', help='Source port step forced when behind a sequentially port allocating NAT (conflicts with --chunk_loss_period). Default = {}')#.format(Symsp_Peer.PORT_STEP))
        parser.add_argument('--splitter_addr', help='IP address or hostname of the splitter. Default = {}.'.format(peer.splitter_addr))
        parser.add_argument('--splitter_port', help='Listening port of the splitter. Default = {}.'.format(peer.splitter_port))
        parser.add_argument('--port', help='Port to communicate with the peers. Default {} (the OS will chose it).'.format(peer.team_port))
        parser.add_argument('--use_localhost', action="store_true", help='Forces the peer to use localhost instead of the IP of the adapter to connect to the splitter. Notice that in this case, peers that run outside of the host will not be able to communicate with this peer.')
        parser.add_argument('--malicious', action="store_true", help='Enables the malicious activity for peer.')
        parser.add_argument('--persistent', action="store_true", help='Forces the peer to send poisoned chunks to other peers.')
        parser.add_argument('--on_off_ratio', help='Enables on-off attack and sets ratio for on off (from 1 to 100)')
        parser.add_argument('--selective', nargs='+', type=str, help='Enables selective attack for given set of peers.')
        parser.add_argument('--bad_mouth', nargs='+', type=str, help='Enables Bad Mouth attack for given set of peers.')
        parser.add_argument('--trusted', action="store_true", help='Forces the peer to send hashes of chunks to splitter')
        parser.add_argument('--checkall', action="store_true", help='Forces the peer to send hashes of every chunks to splitter (works only with trusted option)')
        parser.add_argument('--strpeds', action="store_true", help='Enables STrPe-DS')
        parser.add_argument('--strpeds_log', help='Logging STrPe & STrPe-DS specific data to file.')
        parser.add_argument('--show_buffer', action="store_true", help='Shows the status of the buffer of chunks.')
        parser.add_argument('--monitor', action="store_true", help='Enables monitor')
        try:
            argcomplete.autocomplete(parser)
        except Exception:
            pass

        args = parser.parse_args()

         # {{{ Args handling and object instantiation
        if args.malicious:
            peer = MaliciousPeer(PeerSTRPEDS())
            if args.persistent:
                peer.setPersistentAttack(True)
        elif args.monitor:
            #peer = MonitorDBS()
            print("PeerSTRPEDS Initialized")
            #peer = PeerSTRPEDS()
        else:
            print("Nothing")
            #peer = PeerDBS() #change for strpeds
            #peer = PeerSTRPEDS()
            
        if args.splitter_addr:
            peer.splitter_addr = socket.gethostbyname(args.splitter_addr)
        _print_('Splitter address =',  peer.splitter_addr)

        if args.splitter_port:
            peer.splitter_port = int(args.splitter_port)
        _print_('Splitter port =', peer.splitter_port)

        if args.port:
            peer.team_port = int(args.port)
        _print_('(Peer) PORT =', peer.team_port)

        if args.player_port:
            peer.player_port = int(args.player_port)
        _print_('Listening port (player) =', peer.player_port)

        if args.max_chunk_debt:
            peer.max_chunk_debt = int(args.max_chunk_debt)
        _print_('Maximun chunk debt =',  peer.max_chunk_debt)

        if args.use_localhost:
            peer.use_localhost = True
            _print_('Using localhost address')

        peer.WaitForThePlayer()
        peer.ConnectToTheSplitter()
        peer.ReceiveTheMcastEndpoint()
        peer.ReceiveTheHeaderSize()
        peer.ReceiveTheChunkSize()
        peer.ReceiveTheHeader()
        peer.ReceiveTheBufferSize()
        _print_("Using IP Multicast address =", peer.mcast_addr)

        if args.show_buffer:
            peer.show_buffer = True

        # A multicast address is always received, even for DBS peers.
        if peer.mcast_addr == "0.0.0.0":
            # {{{ IP unicast mode.

            _print_("Peer DBS enabled")
            peer.ReceiveMyEndpoint()
            peer.ReceiveMagicFlags()
            #_print_("Magic flags =", bin(peer.magic_flags))
            peer.ReceiveTheNumberOfPeers()
            _print_("Number of peers in the team (excluding me) =", peer.GetNumberOfPeers())
            _print_("Am I a monitor peer? =", peer.AmIAMonitor())
            peer.ListenToTheTeam()
            peer.ReceiveTheListOfPeers()
            _print_("List of peers received")
            
            
            # After receiving the list of peers, the peer can check
            # whether is a monitor peer or not (only the first
            # arriving peers are monitors)
            if peer.AmIAMonitor():
                #peer = Monitor_DBS(peer)
                _print_("Monitor DBS enabled")

                # The peer is a monitor. Now it's time to know the sets of rules that control this team.
            else:
                _print_("Peer DBS enabled")
                # The peer is a normal peer. Let's know the sets of rules that control this team.

            '''
           
            if args.strpeds:
                peer = Peer_StrpeDs(peer)
                peer.receive_dsa_key()
            
            if args.malicious and not args.strpeds: # workaround for malicous strpeds peer
                peer = MaliciousPeer(peer)
                if args.persistent:
                    peer.setPersistentAttack(True)
                if args.on_off_ratio:
                    peer.setOnOffAttack(True, int(args.on_off_ratio))
                if args.selective:
                    peer.setSelectiveAttack(True, args.selective)
            '''
            if args.malicious:
                #peer = Peer_StrpeDsMalicious(peer)
                peer.firshMainTarget()
                if args.persistent:
                    peer.setPersistentAttack(True)
                if args.on_off_ratio:
                    peer.setOnOffAttack(True, int(args.on_off_ratio))
                if args.selective:
                    peer.setSelectiveAttack(True, args.selective)
                if args.bad_mouth:
                    peer.setBadMouthAttack(True, args.bad_mouth)
            '''
            if args.trusted:
                peer = TrustedPeer(peer)
                if args.checkall:
                    peer.setCheckAll(True)
            '''
            if args.strpeds_log != None:
                peer.SetLogging(True)
                peer.SetLogFile(args.strpeds_log)

            print(Color.red, "Receiving DSA Key", Color.none)
            peer.ReceiveDsaKey()
            

            
            # }}}
        else:
            # {{{ IP multicast mode

            peer.ListenToTheTeam()

            # }}}

        # }}}

        #print("Created new peer of type %s\n" % peer.__class__.__name__)

        # {{{ Run!
    
        peer.DisconnectFromTheSplitter()
        peer.BufferData()

        _print_("RUN")
        threading.Thread(target=peer.Run, args=()).start()
        self.console(peer)

                
        
if __name__ == "__main__":
    x = Peer()

    
