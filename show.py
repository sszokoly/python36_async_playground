#!/usr/bin/env python3
import argparse
import sys

RTP_SESSIONS = '''
AvayaG450-001(ss)#
ID    QoS Start date and time End Time 	  Type Destination
----- --- ------------------- -------- ------- ---------------
00031     2004-10-20,10:51:36 10:59:07    G729 	135.8.76.64
00032  *  2004-10-20,10:53:42 10:57:36    G723 	135.8.76.107
00033  *  2004-10-20,10:58:21 10:59:06    G723 	135.8.76.107
00034     2004-10-20,11:08:40        -    G729 	135.8.76.64
00035  *  2004-10-20,11:09:07 	     -    G723  135.8.76.107
AvayaG450-001(ss)#
Done!
'''

def rtp_stat_sessions(args):
    if not args:
        print(RTP_SESSIONS)

def rtp_stat_detailed(args):
    print(args)

def main(args):
    if "rtp-stat" in args:
        if 'sessions' == args[1]:
            rtp_stat_sessions(args[2:])
        if 'detailed' == args[1]:
            rtp_stat_detailed(args[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))