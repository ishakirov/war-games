# P2PSP War Games

Test bed to measure the impact of several types of attacks in a P2PSP Team.

## Cloning
To clone this projects with all submodules, make sure you
clone with `--recursive` argument: `git clone --recursive ...`

## Pre-requisites
### Linux
```
$ [sudo] apt-get install libboost-all-dev
$ [sudo] apt-get install libssl-dev
$ [sudo] apt-get install python3-pip
[sudo] apt-get install python3-numpy
$ [sudo] pip3 install pycrypto

```

## Build the P2PSP Library
### Linux
```
$ cd lib/p2psp
$ ./make.py
$ cd ../..
```

## Run it
```
./simulator [-n -i -t -m -z -d -c]
```
**n** number of peer in the initial team  
**i** number of TPs in the initial team  
**t** total number of TPs  
**m** total number of MPs  
**z** total size of the entire team  
**d** duration of the experiment in seconds  
**c** clean results of the experiment  

## Entities in a Team
- Splitter
- Well-intended peer (WIP)
- Trusted Peer (TP)
- Malicious peer (MP)
