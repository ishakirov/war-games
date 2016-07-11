#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, getopt, shutil
import time
import datetime
import random
import shlex, subprocess
import re
import glob
import platform
from color import Color
import numpy as np

processes = []
experiment_path = "" #automatically assigned
DEVNULL = open(os.devnull, 'wb')
SEED = 12345678

nPeers = nTrusted = nMalicious = sizeTeam = nPeersTeam = nInitialTrusted = 0

port = 60000
playerPort = 61000

currentRound = 0

LAST_ROUND_NUMBER = 0

INIT_TIME = 0
TOTAL_TIME = 60

trusted_peers = []
mp_expelled_by_tps = []
tp_expelled_by_splitter = []
angry_peers = []
angry_peers_retired = []
weibull_expelled = []
buffer_values = {}

P_IN = 80
P_OUT = 50
P_WIP = 50
P_MP = 100
P_MPL = 100
P_TPL = 100
MPTR = 5
WACLR_max = 1.
WACLR_max_var = 1.
alpha = 0.25
WEIBULL_SHAPE = 1.
WEIBULL_TIME = 60

def checkdir():
    global experiment_path
    experiment_path = datetime.datetime.now().strftime("%d%m%y%H%M") + "n" + str(nPeersTeam) + "t" +  str(nTrusted+nInitialTrusted) + "m" + str(nMalicious) + "z" + str(sizeTeam) + "d" + str(TOTAL_TIME)
    
    if not os.path.exists(experiment_path):
        os.mkdir(experiment_path)

def usage():
    print "args error"

def run(runStr, out = DEVNULL, alias = "", ttl = None, entityType = ""):
    proc = subprocess.Popen(shlex.split(runStr), stdout=out, stderr=out)
    processes.append((proc, alias, ttl, entityType))
    return proc

def killall():
    for proc in processes:
        if proc[0].poll() == None:
            proc[0].kill()

def runStream():
    if platform.system() == "Linux":
        run("cvlc Big_Buck_Bunny_small.ogv --sout \"#duplicate{dst=standard{mux=ogg,dst=:8080/test.ogg,access=http}}\"")
    else:
        run("/Applications/VLC.app/Contents/MacOS/VLC Big_Buck_Bunny_small.ogv --sout \"#duplicate{dst=standard{mux=ogg,dst=:8080/test.ogg,access=http}}\"")
    time.sleep(0.5)

def runSplitter(ds = False):
    prefix = ""
    if ds: prefix = "ds"
    run("./console/bin/splitter --strpeds --team_port 8001 --source_port 8080 --max_number_of_chunk_loss 32 --chunk_size 512 --buffer_size 1024 --strpeds_log " + experiment_path + "/splitter.log --p_mpl " + str(P_MPL) + " --p_tpl " + str(P_TPL), open("{0}/splitter.out".format(experiment_path), "w"))
    time.sleep(0.5)

def runPeer(trusted = False, malicious = False, ds = False):
    global port, playerPort
    #run peer
    runStr = "./console/bin/peer --splitter_port 8001 --use_localhost --team_port {0} --player_port {1}".format(port, playerPort)

    peertype = "WIP"

    if trusted:
        peertype = "TP"
    if malicious:
        peertype = "MP"
        runStr += " --malicious --persistent --mptr {0}".format(MPTR)
    if not malicious:
         runStr += " --strpeds_log " + experiment_path + "/peer{0}.log".format(port)


    #Weibull distribution in this random number:
    ttl = int(round(np.random.weibull(WEIBULL_SHAPE) * WEIBULL_TIME))
    print " / ttl =", ttl,
    ttl = ttl + int(time.time()-INIT_TIME)
    print "("+str(ttl)+")"
    alias = "127.0.0.1:"+str(port)

    if (peertype == "MP"):
        ttl = None
    
    run(runStr, open("{0}/peer{1}.out".format(experiment_path,port), "w"), "127.0.0.1:"+str(port), ttl , peertype)
    time.sleep(1)


    #run netcat
    #proc = run("nc 127.0.0.1 {0}".format(playerPort), DEVNULL, alias, ttl, peertype)

    port, playerPort = port + 1, playerPort + 1



def check(x):
    with open("{0}/splitter.log".format(experiment_path)) as fh:
        for line in fh:
            pass
        result = re.match("(\d*.\d*)\t(\d*)\s(\d*).*", line)
        if result != None and int(result.group(3)) <= x:
            return True
    return False

def initializeTeam(nPeers, nInitialTrusted):

    random.seed()
    print "running stream"
    runStream()

    print "running splitter"
    runSplitter(True)

    # clear the trusted.txt file
    with open("trusted.txt", "w"):
        pass
    # clear the attacked.txt file
    with open("attacked.txt", "w"):
        pass

    with open("malicious.txt", "w"):
        pass

    with open("regular.txt", "w"):
        pass

    print "running peers"

    for _ in range(nInitialTrusted):
        print Color.green, "In: <--", Color.none, "TP 127.0.0.1:{0}".format(port),
        with open("trusted.txt", "a") as fh:
            fh.write('127.0.0.1:{0}\n'.format(port))
            fh.close()
        trusted_peers.append('127.0.0.1:{0}'.format(port))
        runPeer(True, False, True)
    for _ in range(nPeers):
       print Color.green, "In: <--", Color.none, "WIP 127.0.0.1:{0}".format(port),
       runPeer(False, False, True)

def churn():
    global  nTrusted, nPeersTeam, nMalicious, trusted_peers, weibull_expelled, angry_peers_retired

    #while checkForRounds():
    while TOTAL_TIME > (time.time()-INIT_TIME):

        #print("nMalicious: ",nMalicious, "nTrusted: ", nTrusted, "nPeersTeam: ", nPeersTeam)
        
        # Arrival of regular or malicious peers
        r = random.randint(1,100)
        if r <= P_IN:
            addRegularOrMaliciousPeer()

        # Arrival of trusted peers
        r = random.randint(1,100)
        if r <= P_IN and nTrusted>0:
            print Color.green, "In: <--", Color.none, "TP 127.0.0.1:{0}".format(port),
            with open("trusted.txt", "a") as fh:
                fh.write('127.0.0.1:{0}\n'.format(port))
                fh.close()
            trusted_peers.append('127.0.0.1:{0}'.format(port))
            nTrusted-=1
            nPeersTeam+=1
            runPeer(True, False, True)

        # Malicious peers expelled by splitter (using the TP information)
        anyExpelled = checkForPeersExpelled()
        if anyExpelled[0] != None:
             
            if anyExpelled[0] == "MP":
                print Color.red,
                nMalicious+=1
            else:
                print Color.purple,
                nTrusted+=1
            print "Out: -->", anyExpelled[0], anyExpelled[1], Color.none
	    nPeersTeam-=1

        checkForBufferTimes()
            
        # Departure of peers
        for p in processes:

            # Based on times
            r = random.randint(1,100)
            if (r <= P_OUT) and (p[0].poll() == None):
                if p[2] != None and p[2] <= (time.time()-INIT_TIME):
                    if p[1] not in mp_expelled_by_tps and p[1] not in weibull_expelled and p[1] not in angry_peers_retired:
                        print Color.red, "Out:-->", Color.none, p[3], p[1]
                        
                        p[0].terminate()

                        weibull_expelled.append(p[1])
                        
                        if p[3] == "TP":
                            nTrusted+=1

                        nPeersTeam-=1

            # Based on BFR
            r = random.randint(1,100)
            if (r <= P_OUT) and (p[0].poll() == None):
                if (p[1] in angry_peers):
                    if p[1] not in angry_peers_retired:
                        print Color.red, "Out: -->", p[3], p[1], "(by WACLR_max)", "WACLR"  ,buffer_values[p[1]], "WACLR Max" , WACLR_max_var , "round", findLastRound() , Color.none

                        p[0].terminate()

                        angry_peers_retired.append(p[1])

                        nPeersTeam-=1

        #print "Timer: "+ str(TIMER)
        #time.sleep(0.5)


def checkForBufferTimes():
    global angry_peers, buffer_values
    fileList = glob.glob("{0}/peer*.log".format(experiment_path))
    for f in fileList:

        regex_peer = re.compile("{0}/peer(\d*).log".format(experiment_path))
        result = regex_peer.match(f)
        if result != None:
            peer_str = "127.0.0.1:"+str(int(result.group(1)))

        if peer_str not in buffer_values:
            buffer_values[peer_str] = 0

        CLR = getLastBufferFor(f)
        if CLR != None:
            buffer_values[peer_str] = alpha * CLR + (1-alpha) * buffer_values[peer_str]

        if (buffer_values[peer_str] > WACLR_max_var):
            if peer_str not in angry_peers and peer_str not in trusted_peers:
                angry_peers.append(peer_str)

def getLastBufferFor(inFile):
    if os.path.getsize(inFile) == 0:
        return None

    regex_fullness = re.compile("(\d*.\d*)\tbuffer\sfullness\s(\d*.\d*)")
    fullness = 0.
    with open(inFile) as f:
        for line in f:
            pass

    result = regex_fullness.match(line)
    if result != None:
        fullness = float(result.group(2))

    return fullness

def addRegularOrMaliciousPeer():
    global nMalicious, nPeersTeam, nTrusted, currentRound, WACLR_max_var
    if sizeTeam > nPeersTeam:
        r = random.randint(1,100)
        if r <= P_MP:
            if nMalicious>0:
                with open("malicious.txt", "a") as fh:
                    fh.write('127.0.0.1:{0}\n'.format(port))
                    fh.close()
                print Color.green, "In: <--", Color.none, "MP 127.0.0.1:{0}".format(port),
	        nMalicious-=1
	        nPeersTeam+=1
                runPeer(False, True, True)

        r = random.randint(1,100)
        if r <= P_WIP:
            #with open("regular.txt", "a") as fh:
            #    fh.write('127.0.0.1:{0}\n'.format(port))
            #    fh.close()
            print Color.green, "In: <--", Color.none, "WIP 127.0.0.1:{0}".format(port),
	    nPeersTeam+=1
            runPeer(False, False, True)

    currentRound = findLastRound()
    round = currentRound - LAST_ROUND_NUMBER
    if round > 0:
        WACLR_max_var = WACLR_max + (1/(round/(round + 100.))) - 1

    progress ="Round "+ str(round)+" Size "+str(nPeersTeam)+"/"+str(sizeTeam)
    sys.stdout.flush()
    print progress,
    print str(int(time.time()-INIT_TIME))+"/"+str(TOTAL_TIME),
    print '\r',

def checkForTrusted():
    with open("{0}/splitter.log".format(experiment_path)) as fh:
        for line in fh:
            pass
        result = re.match("(\d*.\d*)\t(\d*)\s(\d*)\s(.*)", line)

        if result != None:
            peers = result.group(4)
            tCnt = 0
            for peer in peers.split(' '):
                if peer in trusted_peers:
                    tCnt += 1

            return tCnt == nTrusted

    return True

def checkForPeersExpelled():
    global mp_expelled_by_tps, tp_expelled_by_splitter
    peer_type = "WIP"
    with open("{0}/splitter.log".format(experiment_path)) as fh:
        for line in fh:
            result = re.match("(\d*)\tbad peer ([0-9]+(?:\.[0-9]+){3}:[0-9]+)\((.*?)\)", line)
            if result != None:
                if result.group(2) in trusted_peers:
                    if result.group(2) not in tp_expelled_by_splitter:
                        peer_type = "TP"
                        tp_expelled_by_splitter.append(result.group(2))
                elif result.group(2) not in mp_expelled_by_tps:
                    peer_type = "MP"
                    mp_expelled_by_tps.append(result.group(2))
                if peer_type != "WIP":   
                    for p in processes:
                        if (p[1] == result.group(2)) and (p[0].poll() == None):
                            p[0].kill()
                        
                    return (peer_type,result.group(2) +" ("+ result.group(3)+")")
    return (None, None)

def saveLastRound():
    global LAST_ROUND_NUMBER
    LAST_ROUND_NUMBER = findLastRound()

def findLastRound():
    with open("{0}/splitter.log".format(experiment_path)) as fh:
        for line in fh:
            pass
        result = re.match("(\d*)\t(\d*)\s(\d*).*", line)
        if result != None:
             return int(result.group(1))
    return -1

def main(args):
    global nPeers, nTrusted, nInitialTrusted, nMalicious, sizeTeam, nPeersTeam, INIT_TIME, TOTAL_TIME, WEIBULL_SHAPE, WEIBULL_TIME

    random.seed(SEED)

    try:
        opts, args = getopt.getopt(args, "n:t:i:m:z:s:d:w:c:")
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    ds = False
    nPeers = 2
    nTrusted = nInitialTrusted = 1
    nMalicious = 0
    sizeTeam = nPeersTeam = 2
    for opt, arg in opts:
        if opt == "-n":
            nPeers = int(arg)
        elif opt == "-t":
            nTrusted = int(arg)
        elif opt == "-i":
            nInitialTrusted = int(arg)
        elif opt == "-m":
            nMalicious = int(arg)
        elif opt == "-z":
	    sizeTeam = int(arg)
        elif opt == "-s":
            ds = True
        elif opt == "-d":
            TOTAL_TIME = int(arg)
        elif opt == "-w":
            WEIBULL_SHAPE = float(arg)
        elif opt == "-c":
            WEIBULL_TIME = int(arg)

    print 'running initial team with {0} peers ({1} trusted)'.format(nPeers, nInitialTrusted)

    nPeers = nPeers - nInitialTrusted #- nMalicious # for more friendly user input
    nPeersTeam = nPeers + nInitialTrusted
    nTrusted = nTrusted - nInitialTrusted
    checkdir()

    INIT_TIME = time.time()
    
    initializeTeam(nPeers, nInitialTrusted)

    print "Team Initialized"

    for i in xrange(2,0,-1):
        print "Wait for buffering",
        print str(i)+'  \r',
        sys.stdout.flush()
        time.sleep(1)


    #time.sleep(10) # time for all peers buffering
    saveLastRound()
    print "LAST_ROUND_NUMBER", LAST_ROUND_NUMBER

    print "----- Simulating Churn -----"

    churn() 

    print "******************* End of Simulation *******************"
    currentRound = findLastRound()
    print "Rounds= " + str(currentRound) + " TIME= " + str(TOTAL_TIME) + " LRN= " + str(LAST_ROUND_NUMBER)

    killall()

    print "***************** Summary of Parameters ******************"
    print "P_IN = " + str(P_IN),
    print "P_OUT = " + str(P_OUT),
    print "P_WIP = " + str(P_WIP),
    print "P_MPL = " + str(P_MPL),
    print "MPTR = " + str(MPTR)
    print "WACLR_max = " + str(WACLR_max),
    print "alpha = " + str(alpha),
    print "WEIBULL_SHAPE = " + str(WEIBULL_SHAPE),
    print "WEIBULL_TIME = " + str(WEIBULL_TIME)
  
    print "******************* Parsing Results  ********************"
    path = experiment_path + "/sample.dat"
    print "Target file: "+path
    #process = run("./parse.py -r "+str(LAST_ROUND_NUMBER), open(path,"w"))
    #Initial round is not necessary because log is recorded after buffering.
    process = run("./parse.py -d "+ experiment_path, open(path,"w"))
    process.wait()
    print "Done!"
    
    print "******************* Plotting Results  *******************"
    run("gnuplot -e \"filename='"+path+"'\" plot_team.gp")
    run("gnuplot -e \"filename='"+path+"'\" plot_buffer.gp")
    run("gnuplot -e \"filename='"+path+"'\" plot_fullness.gp 2> /dev/null")

    time.sleep(1)
    
    print "************** Moving Files to Results  *****************"
    os.rename("trusted.txt", experiment_path + "/trusted.txt")
    os.rename("attacked.txt", experiment_path + "/attacked.txt")
    os.rename("regular.txt", experiment_path + "/regular.txt")
    os.rename("malicious.txt", experiment_path + "/malicious.txt")
    os.rename("team.svg", experiment_path + "/team.svg")
    os.rename("buffer.svg", experiment_path + "/buffer.svg")
    os.rename("fullness.svg", experiment_path + "/fullness.svg")
    if os.path.isfile("simulator.txt"):
        os.rename("simulator.txt", experiment_path + "/simulator.txt")

    #raw_input("Press Enter to exit...")

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        killall()
    finally:
        killall()
