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
        no snmp-server community
        !
        encrypted-snmp-server community read-only aC02uV3t/hD2WRQ2KzJZuA== read-write tIWV4hWxJEarok2vUVEgc0dBcaOywSBPgPnkHU0qOuo=
        snmp-server group v3ReadISO v3 priv read iso
        snmp-server host 10.62.17.5 traps v3 priv bbysnmpv3trap
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
        System Name             : cityhall
        System Location         : CityHall
        System Contact          :
        Uptime (d,h:m:s)        : 108,18:21:26
        Call Controller Time    : 17:32:47 29 MAR 2025
        Serial No               : 22TN07201536
        Model                   : G450
        Chassis HW Vintage      : 4
        Chassis HW Suffix       : A
        Mainboard HW Vintage    : 4
        Mainboard HW Suffix     : A
        Mainboard HW CS         : 4.0.0
        Mainboard FW Vintage    : 42.32.0
        LAN MAC Address         : c8:1f:ea:d5:cf:40
        WAN1 MAC Address        : c8:1f:ea:d5:cf:41
        WAN2 MAC Address        : c8:1f:ea:d5:cf:42
        SERVICES MAC address    : c8:1f:ea:d5:cf:43
        Memory #1               : 1GB
        Compact Flash Memory    : 1.0 GB
        PSU #1                  : AC 400W
        PSU #2                  : AC 400W
        Media Socket #1         : MP160 VoIP DSP Module
        Media Socket #2         : MP160 VoIP DSP Module

        Media Socket #3         : Not present
        Media Socket #4         : Not present
        FAN Tray                : Present
        ''',

        "show system2": '''
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
        In Use         : 2 of 160 channels, 0 of 4800 points (0.0% used)
        State          : Idle
        Admin State    : Release

        Core# Channels Admin     State
            In Use   State
        ----- -------- --------- -------
            1  1 of 40   Release Idle
            2  1 of 40   Release Idle
            3  0 of 40   Release Idle
            4  0 of 40   Release Idle

        DSP #2 PARAMETERS
        --------------------------------------------------------------
        Board type     : MP160

        Hw Vintage     : 0 B
        Fw Vintage     : 182

        DSP#2 CURRENT STATE
        --------------------------------------------------------------
        In Use         : 8 of 160 channels, 0 of 4800 points (0.0% used)
        State          : Idle
        Admin State    : Release

        Core# Channels Admin     State
            In Use   State
        ----- -------- --------- -------
            1  4 of 40   Release Idle
            2  0 of 40   Release Idle
            3  0 of 40   Release Idle
            4  4 of 40   Release Idle


        DSP #3 Not Present


        DSP #4 Not Present


        Done!
        ''',

        "show sla-monitor": '''
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
        010        internal  53,05:23:06   123/12   332442/1443   00:05:17    64
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
        v6     Analog       MM714       C       30          104
        v7     -- Not Installed --
        v8     -- Not Installed --
        v10    Mainboard    G430        A       3           42.32.0(A)
        ''',

        "show_temp": '''
        Ambient
        -------
        Temperature : 22C (72F)
        High Warning: 42C (108F)
        Low Warning : -5C (23F)

        Devices
        -------
        CPU     : 38C (100F)
        FPGA    : 29C (84F)
        ''',

        "show announcements files": '''
        ID      File               Description    Size (Bytes)      Date
        ---- ------------------ ------------------ ------------ -------------------
        101   moh_upbeat.wav     announcement file     1268110    2022-08-15,8:48:48
        102   moh_sooth.wav      announcement file      239798    2022-08-15,8:48:48
        103   Fire_Main_Grtg.wa  announcement file      162186    2022-08-25,13:59:00
        104   3441_P&D_Main_Grt  announcement file      179642    2023-02-11,10:48:18
        105   6400_Fire_Main_Gr  announcement file      306098    2023-06-16,8:42:56
        270   6020_RobinMemPkCe  announcement file      162034    2024-12-17,9:56:18
        271   6300_ParksService  announcement file      165034    2024-12-17,9:58:14
        272   3430_P&D_Dec_Grtg  announcement file      363154    2024-12-17,10:00:20
        273   3441_P&D_Dec_Grtg  announcement file      279722    2024-12-17,10:02:22

        Compact-Flash:
        Total bytes used             : 26423808
        Total bytes free             : 96049152
        Total bytes capacity (fixed) : 122472960
        ''',

        '''show utilization''': '''

        Mod   CPU      CPU     RAM      RAM
            5sec     60sec   used(%)  Total(Kb)
        ---   ------   -----  -------  ----------
        10      21%       4%    47%     447489 Kb
        
        ''',

        '''show utilization2''': '''

        Mod   CPU      CPU     RAM      RAM
            5sec     60sec   used(%)  Total(Kb)
        ---   ------   -----  -------  ----------
        10    Appl. Disabled    45%     447489 Kb
        ''',

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
    "qos": "Faulted",
}

#System
#+---+-------------+---------------+------------+-------------+-----+--+--------+
#│BGW│    Name     |     LAN IP    │  LAN MAC   |   Uptime    |Model│HW│Firmware│
#+---+-------------+---------------+------------+-------------+-----+--+--------+
#|001|             |192.168.111.111|3475c764ef08|153d05h23m06s| g430│1A│43.11.12│
#+---+-------------+---------------+------------+-------------+-----+--+--------+

SYSTEM_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'column_color': 'base',
        'column_fmt_spec': '>3',
        'column_xpos': 1,
    },
    {
        'column_attr': 'gw_name',
        'column_name': 'Name',
        'column_color': 'base',
        'column_fmt_spec': '>13',
        'column_xpos': 5,
    },
    {
        'column_attr': 'host',
        'column_name': 'LAN IP',
        'column_color': 'base',
        'column_fmt_spec': '>15',
        'column_xpos': 19,
    },
    {
        'column_attr': 'mac',
        'column_name': 'LAN MAC',
        'column_color': 'base',
        'column_fmt_spec': '>12',
        'column_xpos': 35,
    },
    {
        'column_attr': 'uptime',
        'column_name': 'Uptime',
        'column_color': 'base',
        'column_fmt_spec': '>13',
        'column_xpos': 48,
    },
    {
        'column_attr': 'model',
        'column_name': 'Model',
        'column_color': 'base',
        'column_fmt_spec': '>5',
        'column_xpos': 62,
    },
    {
        'column_attr': 'hw',
        'column_name': 'HW',
        'column_color': 'base',
        'column_fmt_spec': '>2',
        'column_xpos': 68,
    },
    {
        'column_attr': 'fw',
        'column_name': 'Firmware',
        'column_color': 'base',
        'column_fmt_spec': '>8',
        'column_xpos': 71,
    },
]

#Hardware
#+---+----------+--------+------------+-----+----+------+---+----+-------+------+
#│BGW│ Location |  Temp  |   Serial   |Chass|Main|Memory│DSP│Anno|C.Flash|Faults|
#+---+----------+--------+------------+-----+----+------+---+----+-------+------+
#|001|          |42C/108F|13TG01116522|   1A|  3A| 256MB│160│ 999|    1GB|     4|
#+---+----------+--------+------------+-----+----+------+---+----+-------+------+

HW_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'column_color': 'base',
        'column_fmt_spec': '>3',
        'column_xpos': 1,
    },
    {
        'column_attr': 'location',
        'column_name': 'Location',
        'column_color': 'base',
        'column_fmt_spec': '>10',
        'column_xpos': 5,
    },
    {
        'column_attr': 'temp',
        'column_name': 'Temp',
        'column_color': 'base',
        'column_fmt_spec': '>8',
        'column_xpos': 16,
    },
    {
        'column_attr': 'serial',
        'column_name': 'Serial',
        'column_color': 'base',
        'column_fmt_spec': '>12',
        'column_xpos': 25,
    },
    {
        'column_attr': 'chassis_hw',
        'column_name': 'Chass',
        'column_color': 'base',
        'column_fmt_spec': '>5',
        'column_xpos': 38,
    },
    {
        'column_attr': 'mainboard_hw',
        'column_name': 'Main',
        'column_color': 'base',
        'column_fmt_spec': '>4',
        'column_xpos': 44,
    },
    {
        'column_attr': 'memory',
        'column_name': 'Memory',
        'column_color': 'base',
        'column_fmt_spec': '>6',
        'column_xpos': 49,
    },
    {
        'column_attr': 'dsp',
        'column_name': 'DSP',
        'column_color': 'base',
        'column_fmt_spec': '>3',
        'column_xpos': 56,
    },
    {
        'column_attr': 'announcements',
        'column_name': 'Anno',
        'column_color': 'base',
        'column_fmt_spec': '>4',
        'column_xpos': 60,
    },
    {
        'column_attr': 'comp_flash',
        'column_name': 'C.Flash',
        'column_color': 'base',
        'column_fmt_spec': '>7',
        'column_xpos': 65,
    },
    {
        'column_attr': 'faults',
        'column_name': 'Faults',
        'column_color': 'base',
        'column_fmt_spec': '>6',
        'column_xpos': 73,
    },
]

#Module
#+---+------+------+------+------+------+------+------+------+--------+----+----+
#│BGW│  v1  |  v2  |  v3  |  v4  |  v5  |  v6  |  v7  |  v8  | v10 hw |PSU1|PSU2|
#+---+------+------+------+------+------+------+------+------+--------+----+----+
#|001|S8300E│MM714B│MM714B│MM714B│MM714B│MM714B│S8300E│S8300E│      3A|400W│400W|
#+---+------+------+------+------+------+------+------+------+--------+----+----+

MODULE_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'column_color': 'base',
        'column_fmt_spec': '>3',
        'column_xpos': 1,
    },
    {
        'column_attr': 'mm_v1',
        'column_name': 'v1',
        'column_color': 'base',
        'column_fmt_spec': '>6',
        'column_xpos': 5,
    },
    {
        'column_attr': 'mm_v2',
        'column_name': 'v2',
        'column_color': 'base',
        'column_fmt_spec': '>6',
        'column_xpos': 12,
    },
    {
        'column_attr': 'mm_v3',
        'column_name': 'v3',
        'column_color': 'base',
        'column_fmt_spec': '>6',
        'column_xpos': 19,
    },
    {
        'column_attr': 'mm_v4',
        'column_name': 'v4',
        'column_color': 'base',
        'column_fmt_spec': '>6',
        'column_xpos': 27,
    },
    {
        'column_attr': 'mm_v5',
        'column_name': 'v5',
        'column_color': 'base',
        'column_fmt_spec': '>6',
        'column_xpos': 33,
    },
    {
        'column_attr': 'mm_v6',
        'column_name': 'v6',
        'column_color': 'base',
        'column_fmt_spec': '>6',
        'column_xpos': 40,
    },
    {
        'column_attr': 'mm_v7',
        'column_name': 'v7',
        'column_color': 'base',
        'column_fmt_spec': '>6',
        'column_xpos': 47,
    },
    {
        'column_attr': 'mm_v8',
        'column_name': 'v8',
        'column_color': 'base',
        'column_fmt_spec': '>6',
        'column_xpos': 54,
    },
    {
        'column_attr': 'mm_v10',
        'column_name': 'v10 hw',
        'column_color': 'base',
        'column_fmt_spec': '>8',
        'column_xpos': 61,
    },
    {
        'column_attr': 'psu1',
        'column_name': 'PSU1',
        'column_color': 'base',
        'column_fmt_spec': '>4',
        'column_xpos': 70,
    },
    {
        'column_attr': 'psu2',
        'column_name': 'PSU2',
        'column_color': 'base',
        'column_fmt_spec': '>4',
        'column_xpos': 75,
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
        'column_color': 'base',
        'column_fmt_spec': '>3',
        'column_xpos': 1,
    },
    {
        'column_attr': 'port1',
        'column_name': 'Port',
        'column_color': 'base',
        'column_fmt_spec': '>4',
        'column_xpos': 5,
    },
    {
        'column_attr': 'port1_status',
        'column_name': 'Status',
        'column_color': 'base',
        'column_fmt_spec': '>9',
        'column_xpos': 10,
    },
    {
        'column_attr': 'port1_neg',
        'column_name': 'Neg',
        'column_color': 'base',
        'column_fmt_spec': '>8',
        'column_xpos': 20,
    },
    {
        'column_attr': 'port1_speed',
        'column_name': 'Spd.',
        'column_color': 'base',
        'column_fmt_spec': '>4',
        'column_xpos': 29,
    },
    {
        'column_attr': 'port1_duplex',
        'column_name': 'Dup.',
        'column_color': 'base',
        'column_fmt_spec': '>4',
        'column_xpos': 34,
    },
    {
        'column_attr': 'port2',
        'column_name': 'Port',
        'column_color': 'base',
        'column_fmt_spec': '>4',
        'column_xpos': 39,
    },
    {
        'column_attr': 'port2_status',
        'column_name': 'Status',
        'column_color': 'base',
        'column_fmt_spec': '>9',
        'column_xpos': 44,
    },
    {
        'column_attr': 'port2_neg',
        'column_name': 'Neg',
        'column_color': 'base',
        'column_fmt_spec': '>8',
        'column_xpos': 54,
    },
    {
        'column_attr': 'port2_speed',
        'column_name': 'Spd.',
        'column_color': 'base',
        'column_fmt_spec': '>4',
        'column_xpos': 63,
    },
    {
        'column_attr': 'port2_duplex',
        'column_name': 'Dup.',
        'column_color': 'base',
        'column_fmt_spec': '>4',
        'column_xpos': 68,
    },
    {
        'column_attr': 'port_redu',
        'column_name': 'Redund',
        'column_color': 'base',
        'column_fmt_spec': '>6',
        'column_xpos': 73,
    },
]

#Service
#+---+---------+---------------+----+---------+--------+---------------+--------+
#|BGW|RTP-Stats|Capture-Service|SNMP|SNMP-Trap| SLAMon | SLAMon Server |  LLDP  |
#+---+---------+---------------+----+---------+--------+---------------+--------+
#|001| disabled|       disabled|v2&3|  enabled| enabled|101.101.111.198|disabled|
#+---+---------+---------------+----+---------+--------+---------------+--------+

SERVICE_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'column_color': 'base',
        'column_fmt_spec': '>3',
        'column_xpos': 1,
    },
    {
        'column_attr': 'rtp_stat_service',
        'column_name': 'RTP-Stats',
        'column_color': 'base',
        'column_fmt_spec': '>9',
        'column_xpos': 5,
    },
    {
        'column_attr': 'capture_service',
        'column_name': 'Capture-Service',
        'column_color': 'base',
        'column_fmt_spec': '>15',
        'column_xpos': 15,
    },
    {
        'column_attr': 'snmp',
        'column_name': 'SNMP',
        'column_color': 'base',
        'column_fmt_spec': '>4',
        'column_xpos': 31,
    },
    {
        'column_attr': 'snmp_trap',
        'column_name': 'SNMP-Trap',
        'column_color': 'base',
        'column_fmt_spec': '>9',
        'column_xpos': 36,
    },
    {
        'column_attr': 'slamon_service',
        'column_name': 'SLAMon',
        'column_color': 'base',
        'column_fmt_spec': '>8',
        'column_xpos': 46,
    },
    {
        'column_attr': 'sla_server',
        'column_name': 'SLAMon Server',
        'column_color': 'base',
        'column_fmt_spec': '>15',
        'column_xpos': 55,
    },
    {
        'column_attr': 'lldp',
        'column_name': 'LLDP',
        'column_color': 'base',
        'column_fmt_spec': '>8',
        'column_xpos': 71,
    },
]

#Status
#+---+-----------+-----------+--------+----------+-----+-------+-------+--------+
#|BGW|Act.Session|Tot.Session|InUseDSP|CPU 5s/60s| RAM |PollSec| Polls |LastSeen|
#+---+-----------+-----------+--------+----------+-----+-------+-------+--------+
#|001|        0/0| 32442/1443|     320| 100%/100%|  45%| 120.32|      3|11:02:11|
#+---+-----------+-----------+--------+----------+-----+-------+-------+--------+

STATUS_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'column_color': 'base',
        'column_fmt_spec': '>3',
        'column_xpos': 1,
    },
    {
        'column_attr': 'active_session',
        'column_name': 'Act.Session',
        'column_color': 'base',
        'column_fmt_spec': '>11',
        'column_xpos': 5,
    },
    {
        'column_attr': 'total_session',
        'column_name': 'Tot.Session',
        'column_color': 'base',
        'column_fmt_spec': '>12',
        'column_xpos': 17,
    },
    {
        'column_attr': 'inuse_dsp',
        'column_name': 'InUseDSP',
        'column_color': 'base',
        'column_fmt_spec': '>8',
        'column_xpos': 29,
    },
    {
        'column_attr': 'cpu_util',
        'column_name': 'CPU 5s/60s',
        'column_color': 'base',
        'column_fmt_spec': '>10',
        'column_xpos': 38,
    },
    {
        'column_attr': 'ram_util',
        'column_name': 'RAM',
        'column_color': 'base',
        'column_fmt_spec': '>5',
        'column_xpos': 49,
    },
    {
        'column_attr': 'avg_poll_secs',
        'column_name': 'PollSec',
        'column_color': 'base',
        'column_fmt_spec': '>7',
        'column_xpos': 55,
    },
    {
        'column_attr': 'polls',
        'column_name': 'Polls',
        'column_color': 'base',
        'column_fmt_spec': '>7',
        'column_xpos': 63,
    },
    {
        'column_attr': 'last_seen_time',
        'column_name': 'LastSeen',
        'column_color': 'base',
        'column_fmt_spec': '>8',
        'column_xpos': 71,
    },
]

#RTP-Stat
#+--------+--------+---+---------------+-----+---------------+-----+------+-----+
#|  Start |   End  |BGW| Local-Address |LPort| Remote-Address|RPort| Codec| QoS | 
#+--------+--------+---+---------------+-----+---------------+-----+------+-----+
#|11:09:07|11:11:27|001|192.168.111.111|55555|100.100.100.100|55555| G711U|Fault|
#+--------+--------+---+---------------+-----+---------------+-----+------+-----+

RTPSTAT_ATTRS = [
    {
        'column_attr': 'start_time',
        'column_name': 'Start',
        'column_color': 'base',
        'column_fmt_spec': '>8',
        'column_xpos': 1,
    },
    {
        'column_attr': 'end_time',
        'column_name': 'End',
        'column_color': 'base',
        'column_fmt_spec': '>8',
        'column_xpos': 10,
    },
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'column_color': 'base',
        'column_fmt_spec': '>3',
        'column_xpos': 19,
    },
    {
        'column_attr': 'local_addr',
        'column_name': 'Local-Address',
        'column_color': 'base',
        'column_fmt_spec': '>15',
        'column_xpos': 23,
    },
    {
        'column_attr': 'local_port',
        'column_name': 'LPort',
        'column_color': 'base',
        'column_fmt_spec': '>5',
        'column_xpos': 39,
    },
    {
        'column_attr': 'remote_addr',
        'column_name': 'Remote-Address',
        'column_color': 'base',
        'column_fmt_spec': '>15',
        'column_xpos': 45,
    },
    {
        'column_attr': 'remote_port',
        'column_name': 'RPort',
        'column_color': 'base',
        'column_fmt_spec': '>5',
        'column_xpos': 61,
    },
    {
        'column_attr': 'codec',
        'column_name': 'Codec',
        'column_color': 'base',
        'column_fmt_spec': '>6',
        'column_xpos': 67,
    },
    {
        'column_attr': 'qos',
        'column_name': 'QoS',
        'column_color': 'base',
        'column_fmt_spec': '>5',
        'column_xpos': 74,
    },
]


class BGW():
    def __init__(self,
        host: str,
        proto: str = '',
        polling_secs = 10,
        gw_name: str = '',
        gw_number: str = '',
        show_announcements_files = '',
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
        show_utilization: str = '',
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
        self.show_announcements_files = show_announcements_files
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
        self.show_utilization = show_utilization
        self.show_voip_dsp = show_voip_dsp
        self.queue = Queue()
        self._active_session = None
        self._announcements = None
        self._capture_service = None
        self._chassis_hw = None
        self._comp_flash = None
        self._cpu_util = None
        self._dsp = None
        self._faults = None
        self._fw = None
        self._hw = None
        self._inuse_dsp = None
        self._last_seen_time = None
        self._lldp = None
        self._location = None
        self._mac = None
        self._mainboard_hw = None
        self._memory = None
        self._mm_groupdict = None
        self._mm_v1 = None
        self._mm_v2 = None
        self._mm_v3 = None
        self._mm_v4 = None
        self._mm_v5 = None
        self._mm_v6 = None
        self._mm_v7 = None
        self._mm_v8 = None
        self._mm_v10 = None
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
        self._psu1 = None
        self._psu2 = None
        self._ram_util = None
        self._rtp_stat_service = None
        self._serial = None
        self._slamon_service = None
        self._sla_server = None
        self._snmp = None
        self._snmp_trap = None
        self._temp = None
        self._total_session = None
        self._uptime = None

    @property
    def active_session(self) -> str:
        """
        Returns the Active Session column from the RTP-Stat summary.
        """
        if self.show_rtp_stat_summary:
            m = re.search(r'nal\s+\S+\s+(\S+)', self.show_rtp_stat_summary)
            return m.group(1) if m else "?/?"
        return "NA"

    @property
    def announcements(self) -> str:
        """
        Returns the number of announcement files as a string.
        """
        if self.show_announcements_files:
            if self._announcements is None:
                m = re.findall(
                    r"announcement file", self.show_announcements_files
                )
                self._announcements = str(len(m))
            return self._announcements
        return "NA"

    @property
    def capture_service(self) -> str:
        """
        Returns the capture service admin and running state.
        """
        if self.show_capture:
            if self._capture_service is None:
                m = re.search(
                    r' service is (\w+) and (\w+)', self.show_capture
                )
                admin_state = m.group(1) if m else "?"
                running_state = m.group(2) if m else "?"
                if admin_state == "disabled":
                    self._capture_service = "disabled"
                else:
                    self._capture_service = f"{admin_state}/{running_state}"
            return self._capture_service
        return "NA"

    @property
    def chassis_hw(self) -> str:
        """
        Returns the chassis hardware version as a string.
        """
        if self.show_system:
            if self._chassis_hw is None:

                vintage_search = re.search(
                    r'Chassis HW Vintage\s+:\s+(\S+)', self.show_system
                )
                vintage = vintage_search.group(1) if vintage_search else "?"
                
                suffix_search = re.search(
                    r"Chassis HW Suffix\s+:\s+(\S+)", self.show_system
                )
                suffix = suffix_search.group(1) if suffix_search else "?"
                
                self._chassis_hw = f"{vintage}{suffix}"
            return self._chassis_hw
        return "NA"

    @property
    def comp_flash(self) -> str:
        """
        Returns the compact flash memory if installed.
        """
        if self.show_system:
            if self._comp_flash is None:
                m = re.search(r'Flash Memory\s+:\s+(.*)', self.show_system)
                if m:
                    if "No" in m.group(1):
                        self._comp_flash = ""
                    else:
                        self._comp_flash = m.group(1).replace(" ", "")
                else:
                    self._comp_flash = ""
            return self._comp_flash
        return "NA"

    @property
    def cpu_util(self) -> str:
        """
        Returns the last 5s and 60s CPU utilization as a string in percentage.
        """
        if self.show_utilization:
            m = re.search(r'10\s+(\d+)%\s+(\d+)%', self.show_utilization)
            self._cpu_util = f"{m.group(1)}%/{m.group(2)}%" if m else "?/?"
            return self._cpu_util
        return "NA"

    @property
    def dsp(self) -> str:
        """
        Returns the total number of DSPs as a string.
        """
        if self.show_system:
            if self._dsp is None:
                m = re.findall(
                    r"Media Socket .*?: M?P?(\d+) ", self.show_system
                )
                self._dsp = str(sum(int(x) for x in m)) if m else "?"
            return self._dsp
        return "NA"

    @property
    def faults(self) -> str:
        """
        Returns the number of faults as string.
        """
        if self.show_faults:
            if self._faults is None:
                if "No Fault Messages" in self.show_faults:
                    self._faults = 0
                else:
                    m = re.findall(r"\s+\+ (\S+)", self.show_faults)
                    self._faults = str(len(m))
            return self._faults
        return "NA"

    @property
    def fw(self) -> str:
        """
        Returns the firmware version as a string.
        """
        if self.show_system:
            if self._fw is None:
                m = re.search(r'FW Vintage\s+:\s+(\S+)', self.show_system)
                self._fw = m.group(1) if m else "?"
            return self._fw
        return "NA"

    @property
    def hw(self) -> str:
        """
        Returns the hardware version as a string.
        """
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
    def last_seen_time(self) -> str:
        """
        Returns the last seen time as a string in 24h format.
        """
        if self.last_seen:
            return f"{self.last_seen:{'%H:%M:%S'}}"
        return "NA"

    @property
    def lldp(self) -> str:
        """
        Returns the LLDP configuration state.
        """
        if self.show_lldp_config:
            if self._lldp is None:
                if "Application status: disable" in self.show_lldp_config:
                    self._lldp = "disabled"
                else:
                    self._lldp = "enabled"
            return self._lldp
        return "NA"

    @property
    def location(self) -> str:
        """
        Returns the system location as a string.
        """
        if self.show_system:
            if self._location is None:
                m = re.search(r'System Location\s+:\s+(\S+)', self.show_system)
                self._location = m.group(1) if m else ""
            return self._location
        return "NA"

    @property
    def mac(self) -> str:
        """
        Returns the LAN MAC address as a string, without colons.
        """
        if self.show_system:
            if self._mac is None:
                m = re.search(r"LAN MAC Address\s+:\s+(\S+)", self.show_system)
                self._mac = m.group(1).replace(":", "") if m else "?"
            return self._mac
        return "NA"

    @property
    def mainboard_hw(self) -> str:
        """
        Returns the mainboard hardware version as a string.
        """
        if self.show_system:
            if self._mainboard_hw is None:
                
                vintage = re.search(
                    r'Mainboard HW Vintage\s+:\s+(\S+)', self.show_system
                )
                vintage = vintage.group(1) if vintage else "?"

                suffix = re.search(
                    r"Mainboard HW Suffix\s+:\s+(\S+)", self.show_system
                )
                suffix = suffix.group(1) if suffix else "?"

                self._mainboard_hw = f"{vintage}{suffix}"
            return self._mainboard_hw
        return "NA"

    @property
    def memory(self) -> str:
        """
        Returns the total memory as a string in the format "<number>MB".
        """
        if self.show_system:
            if self._memory is None:
                m = re.findall(r"Memory #\d+\s+:\s+(\S+)", self.show_system)
                self._memory = f"{sum(self._to_mbyte(x) for x in m)}MB"
            return self._memory
        return "NA"

    @property
    def mm_groupdict(self) -> Dict[str, Dict[str, str]]:
        """
        Returns a dictionary of module group information.

        Returns:
            Dict[str, Dict[str, str]]: A dictionary where each key is a slot
            and the corresponding values are a dictionary containing module
            details.
        """
        if self.show_mg_list:
            if self._mm_groupdict is None:
                groupdict: Dict[str, Dict[str, str]] = {}
                for l in (l.strip() for l in self.show_mg_list.splitlines()):
                    if l.startswith("v") and "Not Installed" not in l:
                        m = re.search(r"".join((
                            r'.*?(?P<slot>\S+)',
                            r'.*?(?P<type>\S+)',
                            r'.*?(?P<code>\S+)',
                            r'.*?(?P<suffix>\S+)',
                            r'.*?(?P<hw_vint>\S+)',
                            r'.*?(?P<fw_vint>\S+)',
                        )), l)
                        if m:
                            groupdict.update({m.group("slot"): m.groupdict()})
                self._mm_groupdict = groupdict
            return self._mm_groupdict
        return {}

    def _mm_v(self, slot: int) -> str:
        """
        Retrieves the module code and suffix for the given slot.

        Args:
            slot: The slot number to retrieve the module details for.

        Returns:
            str: The module details for the given slot.
        """
        code = self.mm_groupdict.get(f"v{slot}", {}).get("code", "")
        if code == "ICC":
            code = self.mm_groupdict.get(f"v{slot}", {}).get("type", "")
        suffix = self.mm_groupdict.get(f"v{slot}", {}).get("suffix", "")
        return f"{code}{suffix}"

    @property
    def mm_v1(self) -> str:
        """
        Returns the media module code and suffix for slot 1.
        """
        if self.show_mg_list:
            if self._mm_v1 is None:
                self._mm_v1 = self._mm_v(1)
            return self._mm_v1
        return "NA"

    @property
    def mm_v2(self) -> str:
        """
        Returns the media module code and suffix for slot 2.
        """
        if self.show_mg_list:
            if self._mm_v2 is None:
                self._mm_v2 = self._mm_v(2)
            return self._mm_v2
        return "NA"

    @property
    def mm_v3(self) -> str:
        """
        Returns the media module code and suffix for slot 3.
        """
        if self.show_mg_list:
            if self._mm_v3 is None:
                self._mm_v3 = self._mm_v(3)
            return self._mm_v3
        return "NA"

    @property
    def mm_v4(self) -> str:
        """
        Returns the media module code and suffix for slot 4.
        """
        if self.show_mg_list:
            if self._mm_v4 is None:
                self._mm_v4 = self._mm_v(4)
            return self._mm_v4
        return "NA"

    @property
    def mm_v5(self) -> str:
        """
        Returns the media module code and suffix for slot 5.
        """
        if self.show_mg_list:
            if self._mm_v5 is None:
                self._mm_v5 = self._mm_v(5)
            return self._mm_v5
        return "NA"

    @property
    def mm_v6(self) -> str:
        """
        Returns the media module code and suffix for slot 6.
        """
        if self.show_mg_list:
            if self._mm_v6 is None:
                self._mm_v6 = self._mm_v(6)
            return self._mm_v6
        return "NA"

    @property
    def mm_v7(self) -> str:
        """
        Returns the media module code and suffix for slot 7.
        """        
        if self.show_mg_list:
            if self._mm_v7 is None:
                self._mm_v7 = self._mm_v(7)
            return self._mm_v7
        return "NA"

    @property
    def mm_v8(self) -> str:
        """
        Returns the media module code and suffix for slot 8.
        """
        if self.show_mg_list:
            if self._mm_v8 is None:
                self._mm_v8 = self._mm_v(8)
            return self._mm_v8
        return "NA"

    @property
    def mm_v10(self) -> str:
        """
        Returns the media module hw vintage and suffix for slot 10.
        """
        if self.show_mg_list:
            if self._mm_v10 is None:
                suffix = self.mm_groupdict.get("v10", {}).get("suffix", "")
                hw_vint = self.mm_groupdict.get("v10", {}).get("hw_vint", "")
                self._mm_v10 = f"{hw_vint}{suffix}"
            return self._mm_v10
        return "NA"

    @property
    def model(self) -> str:
        """
        Returns the gateway model as a string.
        """
        if self.show_system:
            if self._model is None:
                m = re.search(r'Model\s+:\s+(\S+)', self.show_system)
                self._model = m.group(1) if m else "?"
            return self._model
        return "NA"

    @property
    def port1(self) -> str:
        """
        Returns the LAN port 1 identifier as a string.
        """
        if self._port1 is None:
            pdict = self._port_groupdict(0)
            self._port1 = pdict.get("port", "?") if pdict else "NA"
        return self._port1

    @property
    def port1_status(self) -> str:
        """
        Returns the LAN port 1 link status as a string.
        """
        if self._port1_status is None:
            pdict = self._port_groupdict(0)
            self._port1_status = pdict.get("status", "?") if pdict else "NA"
        return self._port1_status

    @property
    def port1_neg(self) -> str:
        """
        Returns the LAN port 1 auto-negotiation status as a string.
        """
        if self._port1_neg is None:
            pdict = self._port_groupdict(0)
            self._port1_neg = pdict.get("neg", "?") if pdict else "NA"
        return self._port1_neg

    @property
    def port1_duplex(self) -> str:
        """
        Returns the LAN port 1 duplexity status as a string.
        """
        if self._port1_duplex is None:
            pdict = self._port_groupdict(0)
            self._port1_duplex = pdict.get("duplex", "?") if pdict else "NA"
        return self._port1_duplex

    @property
    def port1_speed(self) -> str:
        """
        Returns the LAN port 1 speed as a string.
        """
        if self._port1_speed is None:
            pdict = self._port_groupdict(0)
            self._port1_speed = pdict.get("speed", "?") if pdict else "NA"
        return self._port1_speed

    @property
    def port2(self) -> str:
        """
        Returns the LAN port 2 identifier as a string.
        """
        if self._port2 is None:
            pdict = self._port_groupdict(1)
            self._port2 = pdict.get("port", "?") if pdict else "NA"
        return self._port2

    @property
    def port2_status(self) -> str:
        """
        Returns the LAN port 2 link status as a string.
        """
        if self._port2_status is None:
            pdict = self._port_groupdict(1)
            self._port2_status = pdict.get("status", "?") if pdict else "NA"
        return self._port2_status

    @property
    def port2_neg(self) -> str:
        """
        Returns the LAN port 2 auto-negotiation status as a string.
        """
        if self._port2_neg is None:
            pdict = self._port_groupdict(1)
            self._port2_neg = pdict.get("neg", "?") if pdict else "NA"
        return self._port2_neg

    @property
    def port2_duplex(self) -> str:
        """
        Returns the LAN port 2 duplexity status as a string.
        """
        if self._port2_duplex is None:
            pdict = self._port_groupdict(1)
            self._port2_duplex = pdict.get("duplex", "?") if pdict else "NA"
        return self._port2_duplex

    @property
    def port2_speed(self) -> str:
        """
        Returns the LAN port 2 speed as a string.
        """
        if self._port2_speed is None:
            pdict = self._port_groupdict(1)
            self._port2_speed = pdict.get("speed", "?") if pdict else "NA"
        return self._port2_speed

    @property
    def port_redu(self) -> str:
        """
        Returns the port numbers used for port redundancy.
        """
        if self.show_running_config:
            if self._port_redu is None:
                m = re.search(r'port redundancy \d+/(\d+) \d+/(\d+)',
                    self.show_running_config)
                self._port_redu = f"{m.group(1)}/{m.group(2)}" if m else ""
            return self._port_redu
        return "NA"

    @property
    def psu1(self) -> str:
        """
        Returns the Power Supply Unit 1 as a string.
        """
        if self.show_system:
            if self._psu1 is None:
                m = re.search(r"PSU #1\s+:\s+\S+ (\S+)", self.show_system)
                self._psu1 = m.group(1) if m else ""
            return self._psu1
        return "NA"

    @property
    def psu2(self) -> str:
        """
        Returns the Power Supply Unit 2 as a string.
        """
        if self.show_system:
            if self._psu2 is None:
                m = re.search(r"PSU #2\s+:\s+\S+ (\S+)", self.show_system)
                self._psu2 = m.group(1) if m else ""
            return self._psu2
        return "NA"

    @property
    def ram_util(self) -> str:
        """
        Returns the current RAM utilization as percentage.
        """
        if self.show_utilization:
            m = re.search(r'10\s+S+\s+\S+\s+(\d+)%', self.show_utilization)
            self._ram_util = f"{m.group(1)}%" if m else ""
            return self._ram_util
        return "NA"

    @property
    def rtp_stat_service(self) -> str:
        """
        Returns the RTP-Stat service status as a string.
        """
        if self._rtp_stat_service is None:
            m = re.search(r'rtp-stat-service', self.show_running_config)
            self._rtp_stat_service = "enabled" if m else "disabled"
        return self._rtp_stat_service

    @property
    def serial(self) -> str:
        """
        Returns the serial number of the gateway as a string.
        """
        if self.show_system:
            if self._serial is None:
                m = re.search(r'Serial No\s+:\s+(\S+)', self.show_system)
                self._serial = m.group(1) if m else "?"
            return self._serial
        return "NA"

    @property
    def slamon_service(self) -> str:
        """
        Returns the SLAMon service admin status as a string.
        """
        if self.show_sla_monitor:
            if self._slamon_service is None:
                m = re.search(r'SLA Monitor:\s+(\S+)', self.show_sla_monitor)
                self._slamon_service = m.group(1).lower() if m else "?"
            return self._slamon_service
        return "NA"

    @property
    def sla_server(self) -> str:
        """
        Returns the SLAMon server IP address the gateway is registered to.
        """
        if self.show_sla_monitor:
            if self._sla_server is None:
                m = re.search(r'Registered Server IP Address:\s+(\S+)',
                              self.show_sla_monitor)
                self._sla_server = m.group(1) if m else ""
            return self._sla_server
        return "NA"

    @property
    def snmp(self) -> str:
        """
        Returns the configured SNMP version(s) as a string.

        Returns "v2&3" if both SNMPv2 and SNMPv3 are configured,
        "v2" if only SNMPv2 is configured, "v3" if only SNMPv3
        is configured, and "NA" if neither is configured.
        """
        if self.show_running_config:
            if self._snmp is None:
                snmp = []
                lines = [line.strip() for line in
                    self.show_running_config.splitlines()]
                
                if any(line.startswith("snmp-server community")
                       for line in lines):
                    snmp.append("2")
                
                if any(line.startswith("encrypted-snmp-server community")
                       for line in lines):
                    snmp.append("3")
                
                self._snmp = "v" + "&".join(snmp) if snmp else ""
            return self._snmp
        return "NA"

    @property
    def snmp_trap(self) -> str:
        """
        Returns "enabled" if SNMP traps are configured and "disabled" if not.
        """
        if self.show_running_config:
            if self._snmp_trap is None:
                m = re.search(
                    r'snmp-server host (\S+) traps', self.show_running_config
                )
                self._snmp_trap = "enabled" if m else "disabled"
            return self._snmp_trap
        return "NA"

    @property
    def temp(self) -> str:
        """
        Returns the ambient temperature as a string.
        """
        if self.show_temp:
            if self._temp is None:
                m = re.search(
                    r'Temperature\s+:\s+(\S+) \((\S+)\)', self.show_temp
                )
                self._temp = f"{m.group(1)}/{m.group(2)}" if m else "?/?"
            return self._temp
        return "NA"

    @property
    def total_session(self) -> str:
        """
        Returns the Total Session column from the RTP-Stat summary.
        """
        if self.show_rtp_stat_summary:
            m = re.search(r'nal\s+\S+\s+\S+\s+(\S+)',
                          self.show_rtp_stat_summary)
            return m.group(1) if m else "?/?"
        return "NA"

    @property
    def uptime(self) -> str:
        """
        Returns the gateway's uptime as a string.
        """
        if self.show_system:
            if self._uptime is None:
                m = re.search(r'Uptime \(\S+\)\s+:\s+(\S+)', self.show_system)
                if m:
                    self._uptime = m.group(1)\
                                    .replace(",", "d")\
                                    .replace(":", "h", 1)\
                                    .replace(":", "m") + "s"
                else:
                    self._uptime = "?"
            return self._uptime
        return "NA"

    @property
    def inuse_dsp(self) -> str:
        """
        Returns the total number of in-use DSPs as a string.
        """
        inuse = 0
        dsps = re.findall(r"In Use\s+:\s+(\d+)", self.show_voip_dsp)
        for dsp in dsps:
            try:
                inuse += int(dsp)
            except:
                pass
        return f"{inuse}"

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

    @staticmethod
    def _to_mbyte(str: str) -> int:
        """
        Converts the string representation of Memory to MB as an integer.

        Args:
            str: A Memory string from the output of 'show_system'

        Returns:
            An integer representing the number of megabytes.
        """
        m = re.search(r'(\d+)([MG]B)', str)
        if m:
            num, unit = int(m.group(1)), m.group(2)
            if unit == "MB":
                return num
            elif unit == "GB":
                return 1024 * num
        return 0

    def _chars__(self):
        return f"BGW({self.host})"

    def __repr__(self):
        return f"BGW(host={self.host})"


def iter_attrs(
    obj: object,
    column_attrs: List[str],
    column_names: List[str] = None,
    column_fmt_specs: List[str] = None,
    column_colors: List[str] = None,
    column_xposes: List[int] = None,
    xoffset: int = 0
) -> Iterator[Tuple[int, str, str]]:
    """
    Iterate over the attributes of the given object and yield a tuple of 3 values:

    - `xpos`: The x position of the attribute
    - `attr_value`: The value of the attribute, formatted according to the `fmt_spec`
    - `color`: The color of the attribute

    :param obj: The object whose attributes are to be iterated over
    :param column_attrs: A list of strings, each of which is the name of an attribute
        of the object
    :param column_names: A list of strings, each of which is the name of the attribute
        as it should be displayed in the output
    :param column_fmt_specs: A list of strings, each of which is a format specification
        for the attribute value
    :param column_colors: A list of strings, each of which is the name of a color to be
        used for the attribute
    :param column_xposes: A list of integers, each of which is the x position of the
        attribute in the output
    :param xoffset: An integer that is added to the x position of each attribute
    :return: An iterator of tuples of 3 values
    """
    column_names = column_names or column_attrs
    column_fmt_specs = column_fmt_specs or [f">{len(x)}" for x in column_names]
    column_colors = column_colors or ["base" for x in column_names]
    column_xposes = column_xposes or [None for x in column_names]
    offset = 1
    
    column_params = zip(column_attrs, column_names, column_fmt_specs,
        column_colors, column_xposes)
    
    for attr, name, fmt_spec, color, xpos in column_params:
        _len = len(name)

        if hasattr(obj, attr):
            attr_value = getattr(obj, attr)
        else:
            attr_value = obj.get(attr, attr)

        if isinstance(attr_value, int):
            attr_value = str(attr_value)

        if fmt_spec:
            m = re.search(r"[<>^](\d+)", fmt_spec)
            _len = int(m.group(1)) if m else _len
            attr_value = f"{attr_value:{fmt_spec}}"
        
        if isinstance(attr_value, str):
            attr_value = f"{attr_value[:_len]}"

        if not xpos:
            xpos = offset
        
        yield xpos + xoffset, attr_value, color
        offset += len(attr_value) + 1


def iter_column_names(
    column_names: List[str],
    column_fmt_specs: Optional[List[str]] = None,
    column_colors: Optional[List[str]] = None,
    column_xposes: Optional[List[int]] = None,
    xoffset: int = 0
) -> Iterator[Tuple[int, str, str]]:
    """
    Iterate over the column names with formatting, color, and x position.

    :param column_names: A list of column names as strings
    :param column_fmt_specs: A list of format specifications
    :param column_colors: A list of colors, one per column name
    :param column_xposes: A list of x positions as integers
    :param xoffset: An integer that is added to the x position
    :return: An iterator of tuples with x position, name and color
    """
    column_fmt_specs = column_fmt_specs or [f"^{len(x)}" for x in column_names]
    column_colors = column_colors or ["base" for x in column_names]
    column_xposes = column_xposes or [None for x in column_names]
    offset = 1

    column_name_params = zip(column_names, column_fmt_specs, column_colors, column_xposes)

    for name, fmt_spec, color, xpos in column_name_params:
        _len = len(name)

        if fmt_spec:
            m = re.search(r"[<>^](\d+)", fmt_spec)
            _len = int(m.group(1)) if m else _len
        
        name = f"{name:^{_len}}"

        if not xpos:
            xpos = offset

        yield xpos + xoffset, name, color
        offset += len(name) + 1

def main():
    bgw = BGW("192.168.111.111")
    bgw.update(**data)
    column_attrs = [x["column_attr"] for x in SYSTEM_ATTRS]
    column_names = ["BGW", "    Name     ", "    LAN IP     ", "   LAN MAC  ", "   Uptime    ", "Model", "HW", "Firmware"]
    column_fmt_specs = [x["column_fmt_spec"] for x in SYSTEM_ATTRS]
    column_colors = [x["column_color"] for x in SYSTEM_ATTRS]
    column_xposes = [x["column_xpos"] for x in SYSTEM_ATTRS]
    # for column_xpos, chars, column_color in iter_attrs(bgw, column_attrs, column_names=column_names,
    #     column_fmt_specs=column_fmt_specs, column_colors=column_colors, column_xposes=column_xposes):
    #     print(f"{column_xpos:3} {chars:20} {column_color}")
    # for column_xpos, chars, column_color in iter_attrs(bgw, HW_ATTRS):
    #     print(f"{column_xpos:3} {chars:20} {column_color}")
    # for column_xpos, chars, column_color in iter_attrs(bgw, MODULE_ATTRS):
    #     print(f"{column_xpos:3} {chars:20} {column_color}")
    # for column_xpos, chars, column_color in iter_attrs(bgw, PORT_ATTRS):
    #     print(f"{column_xpos:3} {chars:20} {column_color}")
    # for column_xpos, chars, column_color in iter_attrs(bgw, SERVICE_ATTRS):
    #     print(f"{column_xpos:3} {chars:20} {column_color}")
    # for column_xpos, chars, column_color in iter_attrs(bgw, STATUS_ATTRS):
    #     print(f"{column_xpos:3} {chars:20} {column_color}")
    # for column_xpos, chars, column_color in iter_attrs(rtp_stat, RTPSTAT_ATTRS):
    #     print(f"{column_xpos:3} {chars:20} {column_color}")
    print()
    for xpos, name, _ in iter_column_names(column_names):
        print(' '*xpos + f"{name}")
if __name__ == '__main__':
    main()
