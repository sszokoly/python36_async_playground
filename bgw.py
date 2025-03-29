#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import re
from typing import AsyncIterator, Iterable, Iterator, Optional, Tuple, Union, TypeVar, Any, Dict, List, Set
from asyncio import Lock, Queue, Semaphore
from datetime import datetime

data ={
    "host": "192.168.111.111",
    "proto": "encrypted",
    "gw_name": "AvayaG450A",
    "gw_number": "001",
    "last_seen": "2025-03-21,08:49:27",
    
    "commands": {
        "show running-config": '''
        ! version 42.24.0
        Config info release 42.24.0 time "08:49:27 16 OCT 2024 " serial_number 10IS41452851
        !
        encrypted-username /6uCADuD2GZ7GGjZ2jGkbg== password cTV1Osm73kZMwAPq/E55vGir27ynys7m/YgbZZbsaX8= access-type 9os8uRcP3F
        lbMEqSff81ew==
        !
        encrypted-username N1uDac4hxp2ssYrs+tjY2A== password xDfcwOLBsCkmdlht+IJRcUFp6vBqHw0CAFhpioBeZ0E= access-type NETEZ/WGjk
        uL84gOKeBsww==
        hostname "AvayaG450A"
        no ip telnet
        ip tftp-server file-system-size 2288
        set port redundancy 10/5 10/4 on red1
        !
        ds-mode t1
        !
        interface Vlan 1
        icc-vlan
        server-blade-vlan 5
        ip address 192.168.111.111     255.255.255.0
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
        !# End of configuration file. Press Enter to continue.
        ''',

        "show system": '''
        System Name :
        System Location : townhall
        System Contact :
        Uptime (d,h:m:s) : 8,00:23:27
        Call Controller Time : 11:11:22 22 JUL 2020
        Serial No : 09IS48315342
        Model : G450v3
        Chassis HW Vintage : 1
        Chassis HW Suffix : A
        Mainboard HW Vintage : 3
        Mainboard HW Suffix : A
        Mainboard HW CS : 3.0.2
        Mainboard FW Vintage : 41.31.0
        LAN MAC Address : 34:75:c7:64:ef:08
        WAN1 MAC Address : 34:75:c7:64:ef:09
        WAN2 MAC Address : 34:75:c7:64:ef:0a
        SERVICES MAC address : 34:75:c7:64:ef:0b
        Memory #1 : 256MB
        Memory #2 : 256MB
        Compact Flash Memory : No CompactFlash card is installed
        PSU #1 : Not present
        PSU #2 : AC 400W
        Media Socket #1 : MP80 VoIP DSP Module
        Media Socket #2 : MP80 VoIP DSP Module
        Media Socket #3 : MP80 VoIP DSP Module
        Media Socket #4 : MP80 VoIP DSP Module
        FAN Tray #1 : Present
        ''',

        "show faults": '''
        CURRENTLY ACTIVE FAULTS
        -------------------------------------------------------------------
        -- Hardware Faults --
                + Multiple fans outage, 01/01-18:26:35.00
                + PSU fan brief outage, 01/01-18:26:35.00
        -- MGP Faults --
                + No controller found, 01/01-00:00:01.00
        ''',

        "show capture": '''
        The sniffing service is enabled and active
        Capturing started at:
        21:22:01, February 21, 2010 / 7,9:55:55 (uptime)
        stopped at: not-stopped
        Buffer size: 1000 KB
        Buffer mode is cyclic
        Maximum number of bytes captured from
        each frame: 128
        Packet filter: Capture List 503
        Number of frames in buffer: 200
        Size of capture file: 50 KB (5%)
        ''',

        "show voip-dsp": '''
        DSP #1 PARAMETERS
        --------------------------------------------------------------
        Board type     : MP160
        Hw Vintage     : 0 B
        Fw Vintage     : 182

        DSP#1 CURRENT STATE
        --------------------------------------------------------------
        In Use         : 0 of 160 channels, 0 of 4800 points (0.0% used)
        State          : Idle
        Admin State    : Release

        Core# Channels Admin     State
            In Use   State
        ----- -------- --------- -------
            1  0 of 40   Busyout Idle
            2  0 of 40   Busyout Idle
            3  0 of 40   Release Idle
            4  0 of 40   Release Idle


        DSP #2 Not Present



        DSP #3 Not Present


        DSP #4 Not Present

        Done!
        ''',

        "show sla-monitor": '''
        show sla-monitor
        SLA Monitor: Disabled
        Server Address: 0.0.0.0
        Registered Server IP Address: 0.0.0.0
        Server Port: 50010
        Capture Mode: With Payload
        Version: 1.3.4
        ''',

        "show rtp-stat summary": '''
        Total QoS traps: 2
        QoS traps Drop : 0
        Qos Clear
        Engine                            Active   Total    Mean      Tx
        ID   Description     Uptime       Session  Session  Duration  TTL
        ---  --------------  -----------  -------  -------  --------  ----
        010        internal  53,05:23:06   123/12   32442/1443   00:05:17    64
        ''',

        "show lldp config": '''
        Lldp Configuration
        -------------------
        Application status: disable
        Tx interval: 30 seconds
        Tx hold multiplier: 4 seconds
        Tx delay: 2 seconds
        Reinit delay: 2 seconds
        ''',

        "show port": '''
        Port   Name             Status    Vlan Level  Neg     Dup. Spd. Type
        ------ ---------------- --------- ---- ------ ------- ---- ---- ----------------
        10/5   NO NAME          connected 1     0     enable  full 1G   Avaya Inc., G450 Media Gateway 10/100/1000BaseTx Port 10/5

        10/6   NO NAME          no link   1     0     enable  full 1G   Avaya Inc., G450 Media Gateway 10/100/1000BaseTx Port 10/6
        ''',

        "show mg list": '''
        G430-5-005(super)# show mg l
        SLOT   TYPE         CODE        SUFFIX  HW VINTAGE  FW VINTAGE
        ----   --------     ----------  ------  ----------  -----------
        v1     S8300        ICC         E       1           0
        v2     Analog       MM714       B       31          104
        v3     -- Not Installed --
        v5     -- Not Installed --
        v6     -- Not Installed --
        v7     -- Not Installed --
        v8     -- Not Installed --
        v10    Mainboard    G430        A       3           42.32.0(A)
        '''
        },
    "rtp_sessions": {
        "2004-10-20,11:09:07,001,00001": '''
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
        G711U 200B 20mS srtpAesCm128HmacSha180, Silence-suppression(Tx/Rx) Disabled/Disabled, Play-Time 15.010sec, Loss 0.3% #0, Avg-Loss 0.3%, RTT 0mS #0, Avg-RTT 0mS, JBuf-under/overruns
        0.0%/0.0%, Jbuf-Delay 15mS, Max-Jbuf-Delay 15mS

        Received-RTP:
        Packets 846, Loss 0.0% #0, Avg-Loss 0.0%, RTT 0mS #0, Avg-RTT 0mS, Jitter 1mS #0, Avg-Jitter 0mS, TTL(last/min/max) 56/56/56, Duplicates 0, Seq-Fall 0, DSCP 0, L2Pri 0, RTCP 0, Flow
        -Label 0

        Transmitted-RTP:
        VLAN 0, DSCP 46, L2Pri 0, RTCP 12, Flow-Label 0


        Remote-Statistics:
        Loss 0.0% #0, Avg-Loss 0.0%, Jitter 0mS #0, Avg-Jitter 0mS

        Echo-Cancellation:
        Loss 0dB #4, Len 0mS

        RSVP:
        Status Unused, Failures 0

        Done!'''
    },
}

rtp_stat = {
    "start_time": "10:10:10",
    "end_time": "11:11:11",
    "gw_number": "001",
    "local_addr": "10.10.10.10",
    "local_port": "55555",
    "remote_addr": "11.11.11.11",
    "remote_port": "55556",
    "codec": "G711U",
    "qos": "ok",
}

#System
#+---+--------+---------------+-----------------+-------------+-----+--+--------+
#│BGW│  Name  |     LAN IP    │     LAN MAC     |   Uptime    |Model│HW│Firmware│
#+---+--------+---------------+-----------------+-------------+-----+--+--------+
#|001|        |192.168.111.111|34:75:c7:64:ef:08|153d05h23m06s| g430│1A│43.11.12│
#+---+--------+---------------+-----------------+-------------+-----+--+--------+

SYSTEM_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'color': 'base',
        'fmt': '>3',
        'xpos': 1,
    },
    {
        'column_attr': 'gw_name',
        'column_name': 'Name',
        'color': 'base',
        'fmt': '>8',
        'xpos': 5,
    },
    {
        'column_attr': 'host',
        'column_name': 'LAN IP',
        'color': 'base',
        'fmt': '>15',
        'xpos': 14,
    },
    {
        'column_attr': 'mac',
        'column_name': 'LAN MAC',
        'color': 'base',
        'fmt': '>17',
        'xpos': 30,
    },
    {
        'column_attr': 'uptime',
        'column_name': 'Uptime',
        'color': 'base',
        'fmt': '>13',
        'xpos': 48,
    },
    {
        'column_attr': 'model',
        'column_name': 'Model',
        'color': 'base',
        'fmt': '>5',
        'xpos': 62,
    },
    {
        'column_attr': 'hw',
        'column_name': 'HW',
        'color': 'base',
        'fmt': '>2',
        'xpos': 68,
    },
    {
        'column_attr': 'fw',
        'column_name': 'Firmware',
        'color': 'base',
        'fmt': '>8',
        'xpos': 71,
    },
]

#Hardware
#+---+---------------+------------+-------+---------+------+---+------+---------+
#│BGW│    Location   | Serial Num |Chassis|Mainboard|Memory│DSP│Announ| C.Flash |
#+---+---------------+------------+-------+---------+------+---+------+---------+
#|001|               |13TG01116522|     1A|       3A| 256MB│160│   999|installed|
#+---+---------------+------------+-------+---------+------+---+------+---------+

HARDWARE_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'color': 'base',
        'fmt': '>3',
        'xpos': 1,
    },
    {
        'column_attr': 'location',
        'column_name': 'Location',
        'color': 'base',
        'fmt': '>15',
        'xpos': 5,
    },
    {
        'column_attr': 'serial',
        'column_name': 'Serial',
        'color': 'base',
        'fmt': '>12',
        'xpos': 21,
    },
    {
        'column_attr': 'chassis_hw',
        'column_name': 'Chassis',
        'color': 'base',
        'fmt': '>9',
        'xpos': 34,
    },
    {
        'column_attr': 'mainboard_hw',
        'column_name': 'Mainboard',
        'color': 'base',
        'fmt': '>7',
        'xpos': 42,
    },
    {
        'column_attr': 'memory',
        'column_name': 'Memory',
        'color': 'base',
        'fmt': '>6',
        'xpos': 52,
    },
    {
        'column_attr': 'dsp',
        'column_name': 'DSP',
        'color': 'base',
        'fmt': '>3',
        'xpos': 59,
    },
    {
        'column_attr': 'announcements',
        'column_name': 'Announ',
        'color': 'base',
        'fmt': '>6',
        'xpos': 63,
    },
    {
        'column_attr': 'comp_flash',
        'column_name': 'C.Flash',
        'color': 'base',
        'fmt': '>9',
        'xpos': 70,
    },
]

#Module
#+---+------+------+------+------+------+------+------+------+--------+----+----+
#│BGW│  v1  |  v2  |  v3  |  v4  |  v5  |  v6  |  v7  |  v8  |   v10  |PSU1|PSU2|
#+---+------+------+------+------+------+------+------+------+--------+----+----+
#|001|S8300E│MM714B│MM714B│MM714B│MM714B│MM714B│S8300E│S8300E│Mainboar|400W│400W|
#+---+------+------+------+------+------+------+------+------+--------+----+----+

MODULE_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'color': 'base',
        'fmt': '>3',
        'xpos': 1,
    },
    {
        'column_attr': 'mm_v1',
        'column_name': 'v1',
        'color': 'base',
        'fmt': '>6',
        'xpos': 5,
    },
    {
        'column_attr': 'mm_v2',
        'column_name': 'v2',
        'color': 'base',
        'fmt': '>6',
        'xpos': 12,
    },
    {
        'column_attr': 'mm_v3',
        'column_name': 'v3',
        'color': 'base',
        'fmt': '>6',
        'xpos': 19,
    },
    {
        'column_attr': 'mm_v4',
        'column_name': 'v4',
        'color': 'base',
        'fmt': '>6',
        'xpos': 27,
    },
    {
        'column_attr': 'mm_v5',
        'column_name': 'v5',
        'color': 'base',
        'fmt': '>6',
        'xpos': 33,
    },
    {
        'column_attr': 'mm_v6',
        'column_name': 'v6',
        'color': 'base',
        'fmt': '>6',
        'xpos': 40,
    },
    {
        'column_attr': 'mm_v7',
        'column_name': 'v7',
        'color': 'base',
        'fmt': '>6',
        'xpos': 47,
    },
    {
        'column_attr': 'mm_v8',
        'column_name': 'v8',
        'color': 'base',
        'fmt': '>6',
        'xpos': 54,
    },
    {
        'column_attr': 'mm_v10',
        'column_name': 'v10',
        'color': 'base',
        'fmt': '>6',
        'xpos': 61,
    },
    {
        'column_attr': 'psu1',
        'column_name': 'PSU1',
        'color': 'base',
        'fmt': '>4',
        'xpos': 70,
    },
    {
        'column_attr': 'psu2',
        'column_name': 'PSU2',
        'color': 'base',
        'fmt': '>4',
        'xpos': 75,
    },
]

#Port
#+---+----+---------+--------+---------+----+---------+--------+----+----+------+
#|BGW|Port| Status  |  Neg.  |Spd.|Dup.|Port| Status  |  Neg.  |Spd.|Dup.|Redund|
#+---+----+---------+--------+----+----+----+---------+--------+----+----+------+
#|001|10/4|connected| enabled|100M|full|10/5|  no link| enabled|100M|half|   5/4|
#+---+----+---------+--------+----+----+----+---------+--------+----+----+------+

PORT_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'color': 'base',
        'fmt': '>3',
        'xpos': 1,
    },
    {
        'column_attr': 'port1',
        'column_name': 'Port',
        'color': 'base',
        'fmt': '>4',
        'xpos': 5,
    },
    {
        'column_attr': 'port1_status',
        'column_name': 'Status',
        'color': 'base',
        'fmt': '>9',
        'xpos': 10,
    },
    {
        'column_attr': 'port1_neg',
        'column_name': 'Neg',
        'color': 'base',
        'fmt': '>8',
        'xpos': 20,
    },
    {
        'column_attr': 'port1_speed',
        'column_name': 'Spd.',
        'color': 'base',
        'fmt': '>4',
        'xpos': 29,
    },
    {
        'column_attr': 'port1_duplex',
        'column_name': 'Dup.',
        'color': 'base',
        'fmt': '>4',
        'xpos': 34,
    },
    {
        'column_attr': 'port2',
        'column_name': 'Port',
        'color': 'base',
        'fmt': '>4',
        'xpos': 39,
    },
    {
        'column_attr': 'port2_status',
        'column_name': 'Status',
        'color': 'base',
        'fmt': '>9',
        'xpos': 44,
    },
    {
        'column_attr': 'port2_neg',
        'column_name': 'Neg',
        'color': 'base',
        'fmt': '>8',
        'xpos': 54,
    },
    {
        'column_attr': 'port2_speed',
        'column_name': 'Spd.',
        'color': 'base',
        'fmt': '>4',
        'xpos': 63,
    },
    {
        'column_attr': 'port2_duplex',
        'column_name': 'Dup.',
        'color': 'base',
        'fmt': '>4',
        'xpos': 68,
    },
    {
        'column_attr': 'port_redu',
        'column_name': 'Redund',
        'color': 'base',
        'fmt': '>6',
        'xpos': 73,
    },
]

#Service
#+---+---------+---------------+----+---------+--------+---------------+--------+
#|BGW|rtp-stats|capture-service|snmp|snmp-trap| slamon | slamon server |  lldp  |
#+---+---------+---------------+----+---------+--------+---------------+--------+
#|001| disabled|       disabled|v2&3|  enabled| enabled|101.101.111.198|disabled|
#+---+---------+---------------+----+---------+--------+---------------+--------+

SERVICE_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'color': 'base',
        'fmt': '>3',
        'xpos': 1,
    },
    {
        'column_attr': 'rtp_stat_service',
        'column_name': 'RTP-Stats',
        'color': 'base',
        'fmt': '>9',
        'xpos': 5,
    },
    {
        'column_attr': 'capture_service',
        'column_name': 'Capture-Service',
        'color': 'base',
        'fmt': '>15',
        'xpos': 15,
    },
    {
        'column_attr': 'snmp',
        'column_name': 'SNMP',
        'color': 'base',
        'fmt': '>4',
        'xpos': 31,
    },
    {
        'column_attr': 'snmp_trap',
        'column_name': 'snmp-trap',
        'color': 'base',
        'fmt': '>9',
        'xpos': 36,
    },
    {
        'column_attr': 'slamon_service',
        'column_name': 'SLAMon',
        'color': 'base',
        'fmt': '>8',
        'xpos': 46,
    },
    {
        'column_attr': 'sla_server',
        'column_name': 'SLAMon Server',
        'color': 'base',
        'fmt': '>15',
        'xpos': 55,
    },
    {
        'column_attr': 'lldp',
        'column_name': 'LLDP',
        'color': 'base',
        'fmt': '>8',
        'xpos': 71,
    },
]

#Status
#+---+-----------+-----------+---------+--------+-----+--------+-------+--------+
#|BGW|Act.Session|Tot.Session|InUse DSP|  Temp  |Fault|PollSecs| Polls |LastSeen|
#+---+-----------+-----------+---------+--------+-----+--------+-------+--------+
#|001|        0/0| 32442/1443|      320|39C/104F|    3|  120.32|      3|11:02:11|
#+---+-----------+-----------+---------+--------+-----+--------+-------+--------+

STATUS_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'color': 'base',
        'fmt': '>3',
        'xpos': 1,
    },
    {
        'column_attr': 'active_session',
        'column_name': 'Act.Session',
        'color': 'base',
        'fmt': '>11',
        'xpos': 5,
    },
    {
        'column_attr': 'total_session',
        'column_name': 'Tot.Session',
        'color': 'base',
        'fmt': '>12',
        'xpos': 17,
    },
    {
        'column_attr': 'voip_dsp',
        'column_name': 'InUse DSP',
        'color': 'base',
        'fmt': '>9',
        'xpos': 29,
    },
    {
        'column_attr': 'temp',
        'column_name': 'Temp',
        'color': 'base',
        'fmt': '>8',
        'xpos': 39,
    },
    {
        'column_attr': 'avg_poll_secs',
        'column_name': 'AvgPollSec',
        'color': 'base',
        'fmt': '>10',
        'xpos': 61,
    },
    {
        'column_attr': 'polls',
        'column_name': 'Polls',
        'color': 'base',
        'fmt': '>5',
        'xpos': 72,
    },
]

#RTP-Stat
#+--------+--------+---+---------------+-----+---------------+-----+--------+---+
#|  Start |   End  |BGW| Local-Address |LPort| Remote-Address|RPort|Codec/pt|QoS|
#+--------+--------+---+---------------+-----+---------------+-----+--------+---+
#|11:09:07|11:11:27|001|192.168.111.111|55555|100.100.100.100|55555|G711U/20| OK|
#+--------+--------+---+---------------+-----+---------------+-----+--------+---+

RTPSTAT_ATTRS = [
    {
        'column_attr': 'start_time',
        'column_name': 'Start',
        'color': 'base',
        'fmt': '>8',
        'xpos': 1,
    },
    {
        'column_attr': 'end_time',
        'column_name': 'End',
        'color': 'base',
        'fmt': '>8',
        'xpos': 10,
    },
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'color': 'base',
        'fmt': '>3',
        'xpos': 19,
    },
    {
        'column_attr': 'local_addr',
        'column_name': 'Local-Address',
        'color': 'base',
        'fmt': '>15',
        'xpos': 23,
    },
    {
        'column_attr': 'local_port',
        'column_name': 'LPort',
        'color': 'base',
        'fmt': '>5',
        'xpos': 39,
    },
    {
        'column_attr': 'remote_addr',
        'column_name': 'Remote-Address',
        'color': 'base',
        'fmt': '>15',
        'xpos': 45,
    },
    {
        'column_attr': 'remote_port',
        'column_name': 'RPort',
        'color': 'base',
        'fmt': '>5',
        'xpos': 61,
    },
    {
        'column_attr': 'codec',
        'column_name': 'Codec',
        'color': 'base',
        'fmt': '>5',
        'xpos': 67,
    },
    {
        'column_attr': 'qos',
        'column_name': 'QoS',
        'color': 'base',
        'fmt': '^4',
        'xpos': 74,
    },
]


class BGW():
    def __init__(self,
        host: str,
        proto: str = '',
        polling_secs = 10,
        gw_name: str = '',
        gw_number: str = '',
        dir = '',
        show_capture: str = '',
        show_faults: str = '',
        show_lldp_config: str = '',
        show_mg_list: str = '',
        show_port: str = '',
        show_rtp_stat_summary: str = '',
        show_running_config: str = '',
        show_sla_monitor: str = '',
        show_system: str = '',
        show_temp: str = '',
        show_voip_dsp: str = '',
        **kwargs,
    ) -> None:
        self.host = host
        self.proto = proto
        self.polling_secs = polling_secs
        self.gw_name = gw_name
        self.gw_number = gw_number
        self.polls = 0
        self.avg_poll_secs = 0
        self.last_seen = None
        self.dir = dir
        self.show_capture = show_capture
        self.show_faults = show_faults
        self.show_lldp_config = show_lldp_config
        self.show_mg_list = show_mg_list
        self.show_port = show_port
        self.show_rtp_stat_summary = show_rtp_stat_summary
        self.show_running_config = show_running_config
        self.show_sla_monitor = show_sla_monitor
        self.show_system = show_system
        self.show_temp = show_temp
        self.show_voip_dsp = show_voip_dsp
        self.queue = Queue()
        self._active_session = None
        self._announcements = None
        self._capture_service = None
        self._chassis_hw = None
        self._comp_flash = None
        self._dsp = None
        self._faults = None
        self._fw = None
        self._hw = None
        self._lldp = None
        self._location = None
        self._lsp = None
        self._mac = None
        self._mainboard_hw = None
        self._memory = None
        self._model = None
        self._port1 = None
        self._port1_status = None
        self._port1_neg = None
        self._port1_duplex = None
        self._port1_speed = None
        self._port2 = None
        self._port2_status = None
        self._port2_neg = None
        self._port2_duplex = None
        self._port2_speed = None
        self._port_redu = None
        self._psu = None
        self._psu1 = None
        self._psu2 = None
        self._rtp_stat_service = None
        self._serial = None
        self._slamon_service = None
        self._sla_server = None
        self._snmp = None
        self._total_session = None
        self._uptime = None
        self._voip_dsp = None

    @property
    def active_session(self):
        if self.show_rtp_stat_summary:
            m = re.search(r'nal\s+\S+\s+(\S+)', self.show_rtp_stat_summary)
            return m.group(1) if m else "?/?"
        return "NA"

    @property
    def announcements(self):
        if self.dir:
            if self._announcements is None:
                m = re.findall(r"Annc files", self.dir)
                self._announcements = len(m)
            return self._announcements
        return "NA"

    @property
    def capture_service(self):
        if self.show_capture:
            if self._capture_service is None:
                m = re.search(r' service is (\w+)', self.show_capture)
                self._capture_service = m.group(1) if m else "?"
            return self._capture_service
        return "NA"

    @property
    def chassis_hw(self):
        if self.show_system:
            if self._chassis_hw is None:
                v = re.search(r'Chassis HW Vintage\s+:\s+(\S+)', self.show_system)
                s = re.search(r"Chassis HW Suffix\s+:\s+(\S+)", self.show_system)
                self._chassis_hw = v.group(1) if v else "?" + s.group(1) if s else "?"
            return self._chassis_hw
        return "NA"

    @property
    def comp_flash(self):
        if self.show_system:
            if self._comp_flash is None:
                m = re.search(r'Flash Memory\s+:\s+(\S+)', self.show_system)
                if m and "Compact" in m.group(1):
                    self._comp_flash = "installed"
                else:
                    self._comp_flash = ""
            return self._comp_flash
        return "NA"

    @property
    def dsp(self):
        if self.show_system:
            if self._dsp is None:
                m = re.findall(r"Media Socket .*?: M?P?(\d+) ", self.show_system)
                self._dsp = sum(int(x) for x in m) if m else "?"
            return self._dsp
        return "NA"

    @property
    def faults(self):
        if self.show_faults:
            if self._faults is None:
                if "No Fault Messages" in self.show_faults:
                    self._faults = 0
                else:
                    m = re.findall(r"\s+\+ (\S+)", self.show_faults)
                    self._faults = len(m)
            return self._faults
        return "NA"

    @property
    def fw(self):
        if self.show_system:
            if self._fw is None:
                m = re.search(r'FW Vintage\s+:\s+(\S+)', self.show_system)
                self._fw = m.group(1) if m else "?"
            return self._fw
        return "NA"

    @property
    def hw(self):
        if self.show_system:
            if self._hw is None:
                m = re.search(r'HW Vintage\s+:\s+(\S+)', self.show_system)
                hw_vintage = m.group(1) if m else "?"
                m = re.search(r'HW Suffix\s+:\s+(\S+)', self.show_system)
                hw_suffix = m.group(1) if m else "?"
                self._hw = f"{hw_vintage}{hw_suffix}"
            return self._hw
        return "NA"

    @property
    def lldp(self):
        if self.show_lldp_config:
            if self._lldp is None:
                if "Application status: disable" in self.show_lldp_config:
                   self._lldp = "disabled"
                else:
                   self._lldp = "enabled"
            return self._lldp
        return "NA"

    @property
    def location(self):
        if self.show_system:
            if self._location is None:
                m = re.search(r'System Location\s+:\s+(\S+)', self.show_system)
                self._location = m.group(1) if m else ""
            return self._location
        return "NA"

    @property
    def lsp(self):
        if self.show_mg_list:
            if self._lsp is None:
                m = re.search(r'ICC\s+(\S)', self.show_mg_list)
                self._lsp = f"S8300{m.group(1)}" if m else ""
            return self._lsp
        return "NA"

    @property
    def mac(self):
        if self.show_system:
            if self._mac is None:
                m = re.search(r"LAN MAC Address\s+:\s+(\S+)", self.show_system)
                self._mac = m.group(1) if m else "?"
            return self._mac
        return "NA"

    @property
    def mainboard_hw(self):
        if self.show_system:
            if self._mainboard_hw is None:
                v = re.search(r'Mainboard HW Vintage\s+:\s+(\S+)', self.show_system)
                s = re.search(r"Mainboard HW Suffix\s+:\s+(\S+)", self.show_system)
                self._mainboard_hw = v.group(1) if v else "?" + s.group(1) if s else "?"
            return self._mainboard_hw
        return "NA"

    @property
    def memory(self):
        if self.show_system:
            if self._memory is None:
                m = re.findall(r"Memory #\d+\s+:\s+(\S+)", self.show_system)
                self._memory = f"{sum(self._to_mbyte(x) for x in m)}MB"
            return self._memory
        return "NA"

    @property
    def model(self):
        if self.show_system:
            if self._model is None:
                m = re.search(r'Model\s+:\s+(\S+)', self.show_system)
                self._model = m.group(1) if m else "?"
            return self._model
        return "NA"

    @property
    def port1(self):
        if self._port1 is None:
            pdict = self._port_groupdict(0)
            self._port1 = pdict.get("port", "?") if pdict else "NA"
        return self._port1

    @property
    def port1_status(self):
        if self._port1_status is None:
            pdict = self._port_groupdict(0)
            self._port1_status = pdict.get("status", "?") if pdict else "NA"
        return self._port1_status

    @property
    def port1_neg(self):
        if self._port1_neg is None:
            pdict = self._port_groupdict(0)
            self._port1_neg = pdict.get("neg", "?") if pdict else "NA"
        return self._port1_neg

    @property
    def port1_duplex(self):
        if self._port1_duplex is None:
            pdict = self._port_groupdict(0)
            self._port1_duplex = pdict.get("duplex", "?") if pdict else "NA"
        return self._port1_duplex

    @property
    def port1_speed(self):
        if self._port1_speed is None:
            pdict = self._port_groupdict(0)
            self._port1_speed = pdict.get("speed", "?") if pdict else "NA"
        return self._port1_speed

    @property
    def port2(self):
        if self._port2 is None:
            pdict = self._port_groupdict(1)
            self._port2 = pdict.get("port", "?") if pdict else "NA"
        return self._port2

    @property
    def port2_status(self):
        if self._port2_status is None:
            pdict = self._port_groupdict(1)
            self._port2_status = pdict.get("status", "?") if pdict else "NA"
        return self._port2_status

    @property
    def port2_neg(self):
        if self._port2_neg is None:
            pdict = self._port_groupdict(1)
            self._port2_neg = pdict.get("neg", "?") if pdict else "NA"
        return self._port2_neg

    @property
    def port2_duplex(self):
        if self._port2_duplex is None:
            pdict = self._port_groupdict(1)
            self._port2_duplex = pdict.get("duplex", "?") if pdict else "NA"
        return self._port2_duplex

    @property
    def port2_speed(self):
        if self._port2_speed is None:
            pdict = self._port_groupdict(1)
            self._port2_speed = pdict.get("speed", "?") if pdict else "NA"
        return self._port2_speed

    @property
    def port_redu(self):
        if self.show_running_config:
            if self._port_redu is None:
                m = re.search(r'port redundancy \d+/(\d+) \d+/(\d+)',
                    self.show_running_config)
                self._port_redu = f"{m.group(1)}/{m.group(2)}" if m else ""
            return self._port_redu
        return "NA"

    @property
    def psu(self):
        if self.show_system:
            if self._psu is None:
                m = re.findall(r"PSU #\d+", self.show_system)
                self._psu = len(m)
            return self._psu
        return "NA"

    @property
    def psu1(self):
        if self.show_system:
            if self._psu1 is None:
                m = re.search(r"PSU #1\s+:\s+\S+ (\S+)", self.show_system)
                self._psu1 = m.group(1) if m else ""
            return self._psu1
        return "NA"

    @property
    def psu2(self):
        if self.show_system:
            if self._psu2 is None:
                m = re.search(r"PSU #2\s+:\s+\S+ (\S+)", self.show_system)
                self._psu2 = m.group(1) if m else ""
            return self._psu2
        return "NA"

    @property
    def rtp_stat_service(self):
        if self._rtp_stat_service is None:
            m = re.search(r'rtp-stat-service', self.show_running_config)
            self._rtp_stat_service = "enabled" if m else "disabled"
        return self._rtp_stat_service

    @property
    def serial(self):
        if self.show_system:
            if self._serial is None:
                m = re.search(r'Serial No\s+:\s+(\S+)', self.show_system)
                self._serial = m.group(1) if m else "?"
            return self._serial
        return "NA"

    @property
    def slamon_service(self):
        if self.show_sla_monitor:
            if self._slamon_service is None:
                m = re.search(r'SLA Monitor:\s+(\S+)', self.show_sla_monitor)
                self._slamon_service = m.group(1).lower() if m else "?"
            return self._slamon_service
        return "NA"

    @property
    def sla_server(self):
        if self.show_sla_monitor:
            if self._sla_server is None:
                m = re.search(r'Registered Server IP Address:\s+(\S+)',
                              self.show_sla_monitor)
                self._sla_server = m.group(1) if m else ""
            return self._sla_server
        return "NA"

    @property
    def snmp(self):
        if self.show_running_config:
            if self._snmp is None:
                snmp = []
                if "snmp-server comm" in self.show_running_config:
                    snmp.append("2")
                if "encrypted-snmp-server comm" in self.show_running_config:
                    snmp.append("3")
                self._snmp = "v" + "&".join(snmp) if snmp else ""
            return self._snmp
        return "NA"

    @property
    def temp(self):
        if self.show_temp:
            m = re.search(r'Temp\s+:\s+(\S+)', self.show_temp)
            return self._snmp
        return "NA"

    @property
    def total_session(self):
        if self.show_rtp_stat_summary:
            m = re.search(r'nal\s+\S+\s+\S+\s+(\S+)',
                          self.show_rtp_stat_summary)
            return m.group(1) if m else "?/?"
        return "NA"

    @property
    def uptime(self):
        if self.show_system:
            if self._uptime is None:
                m = re.search(r'Uptime \(\S+\)\s+:\s+(\S+)', self.show_system)
                if m:
                    self._uptime = m.group(1).replace(",", "d")\
                                    .replace(":", "h", 1)\
                                    .replace(":", "m") + "s"
                else:
                    self._uptime = "?"
            return self._uptime
        return "NA"

    @property
    def voip_dsp(self):
        inuse, total = 0, 0
        dsps = re.findall(r"In Use\s+:\s+(\d+) of (\d+) channels",
                          self.show_voip_dsp)
        for dsp in dsps:
            try:
                dsp_inuse, dsp_total = dsp
                inuse += int(dsp_inuse)
                total += int(dsp_total)
            except:
                pass
        #total = total if total > 0 else "?"
        #inuse = inuse if inuse > 0 else "?"
        return f"{inuse}/{total}"

    def update(
        self,
        last_seen: Optional[str] = None,
        gw_name: Optional[str] = None,
        gw_number: Optional[str] = None,
        commands: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> None:
        """
        Updates the BGW instance with new data.

        Args:
            last_seen: The last time the BGW was seen, in the format
                "%Y-%m-%d,%H:%M:%S".
            gw_name: The name of the gateway.
            gw_number: The number of the gateway.
            commands: A dictionary of commands and their output.
            **kwargs: Additional keyword arguments.

        Returns:
            None
        """
        if last_seen:
            last_seen = datetime.strptime(last_seen, "%Y-%m-%d,%H:%M:%S")
            if not self.last_seen:
                self.last_seen = last_seen

            delta = last_seen - self.last_seen
            if delta:
                self.avg_poll_secs = round((self.avg_poll_secs + delta) / 2, 1)
            else:
                self.avg_poll_secs = self.polling_secs

            if not self.gw_number and gw_number:
                self.gw_number = gw_number
            if not self.gw_name and gw_name:
                self.gw_name = gw_name

            self.polls += 1

        if commands:
            for cmd, value in commands.items():
                bgw_attr = cmd.replace(" ", "_").replace("-", "_")
                setattr(self, bgw_attr, value)

    def _port_groupdict(self, idx: int) -> Dict[str, str]:
        """
        Extract port information from the 'show_port' string.

        Args:
            idx: The index of the port information to extract.

        Returns:
            A dictionary containing port details.
        """
        if self.show_port:
            matches = re.findall(r'(.*Avaya Inc)', self.show_port)
            if matches:
                line = matches[idx] if idx < len(matches) else ""
                if line:
                    return re.search(r"".join((
                        r'.*?(?P<port>\d+/\d+)',
                        r'.*?(?P<name>.*)',
                        r'.*?(?P<status>(connected|no link))',
                        r'.*?(?P<vlan>\d+)',
                        r'.*?(?P<level>\d+)',
                        r'.*?(?P<neg>\S+)',
                        r'.*?(?P<duplex>\S+)',
                        r'.*?(?P<speed>\S+)')), line).groupdict()
        return {}

    def _mm_groupdict(self):
        if self.show_mg_list:
            return re.search(r'.*?(?P<mm>\S+)', self.show_mg_list).groupdict()
        return {}

    @staticmethod
    def _to_mbyte(str):
        m = re.search(r'(\d+)([MG]B)', str)
        if m:
            num, unit = int(m.group(1)), m.group(2)
            if unit == "MB":
                return num
            elif unit == "GB":
                return 1024 * num
        return 0

    def __str__(self):
        return f"BGW({self.host})"

    def __repr__(self):
        return f"BGW(host={self.host})"

    def properties_asdict(self) -> Dict[str, Any]:
        """
        Return a dictionary of this instance's properties.

        The dictionary will contain the names of the properties as keys and
        the values of the properties as values.

        Returns:
            A dictionary of the instance's properties.
        """
        properties = {}
        for name in dir(self.__class__):
            obj = getattr(self.__class__, name)
            if isinstance(obj, property):
                val = obj.__get__(self, self.__class__)
                properties[name] = val
        return properties   

    def asdict(self) -> Dict[str, Any]:
        """
        Return a dictionary of this instance's properties and attributes.

        The dictionary will contain the names of the properties and attributes
        as keys and the values of the properties and attributes as values.

        Returns:
            A dictionary of the instance's properties and attributes.
        """
        attrs = self.__dict__
        return {**self.properties_asdict(), **attrs}


def iter_attrs(
    obj: object,
    attrs: List[Dict[str, Any]],
    xoffset: int = 0
) -> Iterator[Tuple[int, str, str]]:

    for attr in attrs:
        if hasattr(obj, attr['column_attr']):
            _str = str(getattr(obj, attr['column_attr']))
        else:
            _str = str(obj.get(attr['column_attr'], attr['column_attr']))
        
        if attr['fmt']:
            _len = int(''.join(i for i in attr['fmt'] if i.isdigit()))
            _str = f"{_str[:_len]:{attr['fmt']}}"
        elif attr['column_name']:
            _len = len(attr['column_name'])
            _str = f"{_str[:_len]}"
        else:
            _len = len(attr['column_attr'])
            _str = f"{_str[:_len]}"
        
        color = attr['color']
        xpos = attr['xpos'] if attr['xpos'] else 0
        yield xpos + xoffset, _str, color

def main():
    bgw = BGW("192.168.111.111")
    bgw.update(**data)
    for xpos, str, color in iter_attrs(bgw, HARDWARE_ATTRS):
        print(f"{xpos:3} {str:20} {color}")
    for xpos, str, color in iter_attrs(rtp_stat, RTPSTAT_ATTRS):
        print(f"{xpos:3} {str:20} {color}")

if __name__ == '__main__':
    main()
