#!/usr/bin/env python3
import time
import sys
import random

RTP_NOSESSION = '''
No sessions to show.
Done!
AvayaG450A-001(super)#'''

RTP_SESSIONS = '''
ID    QoS Start date and time End Time Type            Destination
----- --- ------------------- -------- --------------- ---------------------------------------
00001     2024-10-04,14:32:07 14:32:19           G711U                            10.10.48.192
00002     2024-10-04,14:32:07 14:32:19           G711U                            10.10.48.168
00003     2024-10-04,14:45:37 14:46:45           G711U                            10.10.48.192
00004     2024-10-04,14:45:37 14:46:45           G711U                            10.10.48.168
00005     2024-10-07,07:19:16 07:20:15           G711U                            10.10.48.192
00006     2024-10-07,07:19:16 07:19:22           G711U                            10.10.48.168
00007     2024-10-07,07:19:27 07:20:15           G711U                            10.10.48.168
00008     2024-10-15,10:21:52 10:24:15           G711U                            10.10.48.192
00009     2024-10-15,10:21:54 10:24:15           G711U                            10.10.48.168
00010     2024-10-15,14:30:15 14:30:24           G711U
--type q to quit or space key to continue-- 
\r\u001b[K 10.10.48.192
00011     2024-10-15,14:30:17 14:30:24           G711U                            10.10.48.168
00012     2024-10-15,14:30:51 14:31:19           G711U                            10.10.48.192
00013     2024-10-15,14:30:53 14:31:19           G711U                            10.10.48.168
00014     2024-10-15,14:31:34 14:32:03           G711U                            10.10.48.192
00015     2024-10-15,14:31:35 14:32:03           G711U                            10.10.48.168
Note that field "Type" indicates the codec in use, which may not match the call manager ip-codec configuration.
Done!
AvayaG450-001(ss)# '''


RTP_SESSIONS_ACTIVE = '''
ID    QoS Start date and time End Time Type            Destination
----- --- ------------------- -------- --------------- ---------------------------------------
00001     2024-10-04,14:32:07 14:32:19           G711U                            10.10.48.192
00002     2024-10-04,14:32:07 14:32:19           G711U                            10.10.48.168
00003     2024-10-04,14:45:37 14:46:45           G711U                            10.10.48.192
Note that field "Type" indicates the codec in use, which may not match the call manager ip-codec configuration.
Done!
AvayaG450-001(ss)# '''


RTP_SESSIONS_LAST5 = '''
ID    QoS Start date and time End Time Type            Destination
----- --- ------------------- -------- --------------- ---------------------------------------
00011     2024-10-15,14:30:17 14:30:24           G711U                            10.10.48.168
00012     2024-10-15,14:30:51 14:31:19           G711U                            10.10.48.192
00013     2024-10-15,14:30:53 14:31:19           G711U                            10.10.48.168
00014     2024-10-15,14:31:34 14:32:03           G711U                            10.10.48.192
00015     2024-10-15,14:31:35 14:32:03           G711U                            10.10.48.168
Note that field "Type" indicates the codec in use, which may not match the call manager ip-codec configuration.
Done!
AvayaG450-001(ss)# '''

RTP_SESSIONS_DETAILED = '''
Session-ID: 1
Status: Terminated, QOS: Ok, EngineId: 10
Start-Time: 2024-10-04,14:32:07, End-Time: 2024-10-04,14:32:19
Duration: 00:00:12
CName: gwp@10.10.48.58
Phone:
Local-Address: 10.10.48.58:2054 SSRC 1910942191
Remote-Address: 10.10.48.192:35000 SSRC 1073745424 (0)
Samples: 2 (5 sec)

Codec:
G711U 200B 20mS srtpAesCm128HmacSha180, Silence-suppression(Tx/Rx) Disabled/Disabled, Play-Time 15.010sec, Loss 0.3% #0, Avg-Loss 0.3%, RTT 0mS #0, Avg-RTT 0mS, JBuf-under/overruns 0.0%/0.0%, Jbuf-Delay 15mS, Max-Jbuf-Delay 15mS

Received-RTP:
Packets 846, Loss 0.0% #0, Avg-Loss 0.0%, RTT 0mS #0, Avg-RTT 0mS, Jitter 1mS #0, Avg-Jitter 0mS, TTL(last/min/max) 56/56/56, Duplicates 0, Seq-Fall 0, DSCP 0, L2Pri 0, RTCP 0, Flow-Label 0

Transmitted-RTP:
VLAN 0, DSCP 46, L2Pri 0, RTCP 12, Flow-Label 0


Remote-Statistics:
Loss 0.0% #0, Avg-Loss 0.0%, Jitter 0mS #0, Avg-Jitter 0mS

Echo-Cancellation:
Loss 0dB #4, Len 0mS

RSVP:
Status Unused, Failures 0

Done!
AvayaG450A-001(super)# show rtp-stat detailed 0001

Session-ID: 1
Status: Terminated, QOS: Ok, EngineId: 10
Start-Time: 2024-10-04,14:32:07, End-Time: 2024-10-04,14:32:19
Duration: 00:00:12
CName: gwp@10.10.48.58
Phone:
Local-Address: 10.10.48.58:2054 SSRC 1910942191
Remote-Address: 10.10.48.192:35000 SSRC 1073745424 (0)
Samples: 2 (5 sec)

Codec:
G711U 200B 20mS srtpAesCm128HmacSha180, Silence-suppression(Tx/Rx) Disabled/Disabled, Play-Time 15.010sec, Loss 0.3% #0, Avg-Loss 0.3%, RTT 0mS #0, Avg-RTT 0mS, JBuf-under/overruns 0.0%/0.0%, Jbuf-Delay 15mS, Max-Jbuf-Delay 15mS

Received-RTP:
Packets 846, Loss 0.0% #0, Avg-Loss 0.0%, RTT 0mS #0, Avg-RTT 0mS, Jitter 1mS #0, Avg-Jitter 0mS, TTL(last/min/max) 56/56/56, Duplicates 0, Seq-Fall 0, DSCP 0, L2Pri 0, RTCP 0, Flow-Label 0

Transmitted-RTP:
VLAN 0, DSCP 46, L2Pri 0, RTCP 12, Flow-Label 0


Remote-Statistics:
Loss 0.0% #0, Avg-Loss 0.0%, Jitter 0mS #0, Avg-Jitter 0mS

Echo-Cancellation:
Loss 0dB #4, Len 0mS

RSVP:
Status Unused, Failures 0

Done!
AvayaG450-001(ss)# '''

SHOW_RUNNING = '''
! version 42.24.0
Config info release 42.24.0 time "08:49:27 16 OCT 2024 " serial_number 10IS41452851
 !
encrypted-username /6uCADuD2GZ7GGjZ2jGkbg== password cTV1Osm73kZMwAPq/E55vGir27ynys7m/YgbZZbsaX8= access-type 9os8uRcP3FlbMEqSff81ew==
!
encrypted-username N1uDac4hxp2ssYrs+tjY2A== password xDfcwOLBsCkmdlht+IJRcUFp6vBqHw0CAFhpioBeZ0E= access-type NETEZ/WGjkuL84gOKeBsww==
hostname "AvayaG450A"
no ip telnet
ip tftp-server file-system-size 2288
set port mirror source-port 10/5 mirror-port 10/6 sampling always direction both
!
ds-mode t1
!
interface Vlan 1
 icc-vlan
 server-blade-vlan 5
 ip address 10.10.48.58     255.255.255.0
 pmi
 exit
!
interface FastEthernet 10/3
 exit
!
interface FastEthernet 10/4
 exit
!
interface Console
 speed 9600
 exit
!
interface USB-Modem
 description "Default Modem Setup"
 timeout absolute 10
 ppp authentication ras
 no shutdown
 ip address 10.3.248.253    255.255.255.252
 exit
!
capture max-frame-size 1500
login authentication min-password-length 8
!
login authentication lockout 0 attempt 0
! Avaya Login Confirmation Received.
EASGManage enableEASG
product-id 8c2ae2eead3e6cca800be892bb6e3411
!
set logging file enable
set logging file condition all Error
set logging file condition BOOT Debug
!
encrypted-snmp-server community read-only aC02uV3t/hD2WRQ2KzJZuA== read-write tIWV4hWxJEarok2vUVEgc0dBcaOywSBPgPnkHU0qOuo=
!
ip default-gateway 10.10.48.254    1 low
!
rtp-stat-service
rtp-stat qos-trap
no rtp-stat fault
analog-test
exit
!
set sla-monitor enable
set sla-server-ip-address 10.10.48.198
set mgc list 10.10.48.240
set mediaserver 10.10.48.240 10.10.48.240 23 telnet
set mediaserver 10.10.48.240 10.10.48.240 5023 sat
!#
!# End of configuration file. Press Enter to continue.'''



def rtp_stat_sessions(args):
    time.sleep(0.1)
    if not args:
        cmd = "AvayaG450-001(ss)# show rtp-stat sessions"
        print(f'{cmd}\r\n{RTP_SESSIONS}')
    elif "active" in args:
        cmd = "AvayaG450-001(ss)# show rtp-stat sessions active"
        if random.randint(0, 1):
            print(f'{cmd}\r\n{RTP_SESSIONS_ACTIVE}')
        else:
            print(f'{cmd}\r\n{RTP_NOSESSION}')
    elif "last" in args:
        cmd = f"AvayaG450-001(ss)# show rtp-stat sessions {' '.join(args)}"
        print(f'{cmd}\r\n{RTP_SESSIONS_LAST5}')

def rtp_stat_detailed(args):
    time.sleep(0.1)
    id = args[0] if args else '0001'
    cmd = f"AvayaG450-001(ss)# show rtp-stat detailed {id}"
    print(f'{cmd}\r\n{RTP_SESSIONS_DETAILED}')

def running_config():
    time.sleep(0.2)
    cmd = f"AvayaG450-001(ss)# running-config"
    print(f'{cmd}\r\n{SHOW_RUNNING}')
    time.sleep(5)
    print("AvayaG450A-001(super)# ")

def main(args):
    if "rtp-stat" in args:
        if 'session' == args[1]:
            rtp_stat_sessions(args[2:])
        if 'detail' == args[1]:
            rtp_stat_detailed(args[2:])
    elif 'running-config' in args:
        running_config()


if __name__ == "__main__":
    #sys.argv.extend(['rtp-stat', 'detailed', '0001'])
    sys.exit(main(sys.argv[1:]))