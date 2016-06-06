#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, getopt
import re
import glob

max_buffer_correctness = 0
min_buffer_correctness = 1
max_buffer_filling = 0
min_buffer_filling = 1

experiment_path = ""

def usage():
    print ""
    return

def calcAverageBufferCorrectnes(roundTime):
    fileList = glob.glob("{0}/peer*.log".format(experiment_path))
    correctnesSum = fillingSum = 0.0
    losses = 0
    NN = 0
    for f in fileList:
        info = calcAverageInFile(f, roundTime)
        if (info[0] != None and info[1] != None):
            correctnesSum += info[0]
            fillingSum += info[1]
            losses += info[2]
            NN += 1       

    if NN == 0:
        return (None,None, losses)
    return (correctnesSum / NN, fillingSum / NN, losses / NN)
    
def calcAverageInFile(inFile, roundTime):
    regex_correctness = re.compile("(\d*)\tbuffer\scorrectnes\s(\d*.\d*)")
    regex_filling = re.compile("(\d*)\tbuffer\sfilling\s(\d*.\d*)")
    regex_fullness = re.compile("(\d*)\tchunk\slost\sat\s(\d*)")

    correctness = None
    filling = None
    losses = 0.0
    
    last_round_filling = 0
    last_round_fullness = 0
    
    with open(inFile) as f:
        for line in f:
            
            result_correctness = regex_correctness.match(line)
            #print result_correctness
            result_filling = regex_filling.match(line)
            #print result_filling
            result_fullness = regex_fullness.match(line)
            #print result_fullness
            
            if result_correctness != None:
                ts = int(result_correctness.group(1))
                if ts == roundTime:
                    correctness = float(result_correctness.group(2))
                    
            if result_filling != None:
                ts = int(result_filling.group(1))
                if ts == roundTime:
                    filling = float(result_filling.group(2))
                else:
                    last_round_filling = ts

            if result_fullness != None:
                ts = int(result_fullness.group(1))
                if ts == roundTime:
                    #print ("ts en fullness: "+str(ts)+ " vs roundTime "+str(roundTime))
                    losses += 1.0
                else:
                    last_round_fullness = ts

            if (last_round_filling > roundTime) and ((last_round_fullness  > roundTime) or (last_round_fullness == 0 )):
                return (correctness, filling, losses)
            
            #if correctness != -1.0 and filling != -1.0:
                #return (correctness, filling)

    return (correctness, filling, losses)    
    

def main(args):
    global experiment_path
    inFile = ""
    nPeers = nMalicious = lastRound = 0
    try:
        opts, args = getopt.getopt(args, "r:d:")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-r":
            lastRound = int(arg)
        elif opt == "-d":
            experiment_path = str(arg)

    regex = re.compile("(\d*)\t(\d*)\s(\d*)\s(.*)")
    startParse = False
    roundOffset = 0
    print "round\t#WIPs\t#MPs\t#TPs\tteamsize\tcorrectness\tfilling\tfullness"
    with open("{0}/splitter.log".format(experiment_path)) as f:
        for line in f:
            result = regex.match(line)
            if result != None:
                ts = int(result.group(1))
                currentRound = int(result.group(2))
                currentTeamSize = int(result.group(3))
                peers = result.group(4).split(' ')
                trusted = 0
                malicious = 0

                with open("trusted.txt", "r") as fh:
                    for line in fh:
                        if line[:-1] in peers:
                            trusted += 1
                            
                with open("malicious.txt", "r") as fh:
                    for line in fh:
                        if line[:-1] in peers:
                            malicious += 1

                if currentRound >= lastRound and not startParse:
                    startParse = True
                    roundOffset = currentRound
                if startParse:
                    info = calcAverageBufferCorrectnes(ts)
                    if (info[0] != None and info[1]!=None):
                        print "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}".format(currentRound - roundOffset + 1, len(peers) - malicious - trusted, malicious, trusted, currentTeamSize, info[0], info[1], (1-float(info[2])/float(currentTeamSize)))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
