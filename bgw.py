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
        System Location :
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
        ---------------------------------------------------------
        Slot : 1
        Board type : 8122
        Hw Vintage : 3
        FW Vintage : 235
        DSP #1 CURRENT STATE
        ---------------------------------------------------------
        In Use : 10 of 80 channels, 37 of 300 points (0.0% used)
        State : InUse
        Admin State: Release
        Core# Channels Admin state State Error
        In Use Msg
        ---- ------- ----------- ----- ------------------
        1 4 of 20 Release InUse No Status Messages
        2 1 of 20 Camp-on InUse No Status Messages
        3 5 of 20 Release InUse No Status Messages
        4 0 of 20 Busyout Idle No Status Messages
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

# System
# +---+---------------+-----+--+--------+------------+------+---+---+-----+----+
# |BGW|     LAN IP    |Model|HW|Firmware|  Serial No |Memory|DSP|PSU|Fault|Anns|   
# +---+---------------+-----+--+--------+------------+------+---+---+-----+----+
# |001|192.168.111.111| g430|1A|43.11.12|13TG01116522| 256MB|160|  1|    3| 999|
# +---+---------------+-----+--+--------+------------+------+---+---+-----+----+

SYSTEM_ATTRS = [
    {'xpos':  1, 'name': 'gw_number', 'fmt': '', 'color': 'base'},
    {'xpos':  5, 'name': 'host', 'fmt': '>15', 'color': 'base'},
    {'xpos': 21, 'name': 'model', 'fmt': '>5', 'color': 'base'},
    {'xpos': 27, 'name': 'hw', 'fmt': '', 'color': 'base'},
    {'xpos': 30, 'name': 'fw', 'fmt': '>8', 'color': 'base'},
    {'xpos': 39, 'name': 'serial', 'fmt': '', 'color': 'base'},
    {'xpos': 52, 'name': 'memory', 'fmt': '>6', 'color': 'base'},
    {'xpos': 59, 'name': 'dsp', 'fmt': '>3', 'color': 'base'},
    {'xpos': 63, 'name': 'psu', 'fmt': '>3', 'color': 'base'},
    {'xpos': 68, 'name': 'faults', 'fmt': '>5', 'color': 'base'},
    {'xpos': 73, 'name': 'announcements', 'fmt': '>4', 'color': 'base'},
]

# Port
# +---+----+---------+-------+-----+----+----+---------+-------+-----+----+----+
# |BGW|Port| Status  |  Neg  |Speed|Dupl|Port| Status  |  Neg  |Speed|Dupl|Redu|
# +---+----+---------+-------+-----+----+----+---------+-------+-----+----+----+
# |001|10/4|connected|disable| 100M|half|10/5|connected|disable| 100M|half| 4&5|
# +---+----+---------+-------+-----+----+----+---------+-------+-----+----+----+

PORT_ATTRS = [
    {'xpos':  1, 'name': 'gw_number', 'fmt': '', 'color': 'base'},
    {'xpos':  5, 'name': 'port1', 'fmt': '>4', 'color': 'base'},
    {'xpos': 10, 'name': 'port1_status', 'fmt': '>9', 'color': 'base'},
    {'xpos': 20, 'name': 'port1_neg', 'fmt': '>7', 'color': 'base'},
    {'xpos': 28, 'name': 'port1_speed', 'fmt': '>5', 'color': 'base'},
    {'xpos': 34, 'name': 'port1_duplex', 'fmt': '>4', 'color': 'base'},
    {'xpos': 39, 'name': 'port2', 'fmt': '>4', 'color': 'base'},
    {'xpos': 54, 'name': 'port2_status', 'fmt': '>9', 'color': 'base'},
    {'xpos': 54, 'name': 'port2_neg', 'fmt': '>7', 'color': 'base'},
    {'xpos': 62, 'name': 'port2_speed', 'fmt': '>5', 'color': 'base'},
    {'xpos': 68, 'name': 'port2_duplex', 'fmt': '>4', 'color': 'base'},
    {'xpos': 73, 'name': 'port_redu', 'fmt': '>4', 'color': 'base'},
]

# Config
# +---+---------+---------------+----+--------+---------------+--------+-------+
# |BGW|rtp-stats|capture-service|snmp| slamon | slamon server |  lldp  |  lsp  |
# +---+---------+---------------+----+--------+---------------+--------+-------+
# |001| disabled|       disabled|v2&3|disabled|101.101.111.198|disabled| S8300E|
# +---+---------+---------------+----+--------+---------------+--------+-------+

CONFIG_ATTRS = [
    {'xpos':  1, 'name': 'gw_number', 'fmt': '', 'color': 'base'},
    {'xpos':  5, 'name': 'rtp_stat_service', 'fmt': '>9', 'color': 'base'},
    {'xpos': 15, 'name': 'capture_service', 'fmt': '>15', 'color': 'base'},
    {'xpos': 31, 'name': 'snmp', 'fmt': '>4', 'color': 'base'},
    {'xpos': 36, 'name': 'slamon_service', 'fmt': '>8', 'color': 'base'},
    {'xpos': 45, 'name': 'sla_server', 'fmt': '>15', 'color': 'base'},
    {'xpos': 61, 'name': 'lldp', 'fmt': '>8', 'color': 'base'},
    {'xpos': 70, 'name': 'lsp', 'fmt': '>7', 'color': 'base'},
]

# Status
# +---+-------------+------------+------------+---------------+----------+-----+
# |BGW|    Uptime   |Act Sessions|Tot Sessions|In-Use/Tot DSPs|AvgPollSec|Polls|
# +---+-------------+------------+------------+---------------+----------+-----+
# |001|153d05h23m06s|         0/0|  32442/1443|        320/230|    120.32|    3|
# +---+-------------+------------+------------+---------------+----------+-----+

STATUS_ATTR = [
    {'xpos':  1, 'name': 'gw_number', 'fmt': '', 'color': 'base'},
    {'xpos':  5, 'name': 'uptime', 'fmt': '>13', 'color': 'base'},
    {'xpos': 19, 'name': 'active_sessions', 'fmt': '>11', 'color': 'base'},
    {'xpos': 32, 'name': 'total_sessions', 'fmt': '>11', 'color': 'base'},
    {'xpos': 45, 'name': 'voip_dsp', 'fmt': '>14', 'color': 'base'},
    {'xpos': 61, 'name': 'avg_poll_secs', 'fmt': '>9', 'color': 'base'},
    {'xpos': 72, 'name': 'polls', 'fmt': '>5', 'color': 'base'},
]

# RTP-Stat
# +--------+--------+---+---------------+-----+---------------+-----+-----+----+
# |  Start |   End  |BGW| Local-Address |LPort| Remote-Address|RPort|Codec| QoS|
# +--------+--------+---+---------------+-----+---------------+-----+-----+----+
# |11:09:07|11:11:27|001|192.168.111.111|55555|100.100.100.100|55555|G711U|  OK|
# +--------+--------+---+---------------+-----+---------------+-----+-----+----+

RTP_STAT_ATTRS = [
    {'xpos':  1, 'name': 'start_time', 'fmt': '', 'color': 'base'},
    {'xpos': 10, 'name': 'end_time', 'fmt': '', 'color': 'base'},
    {'xpos': 19, 'name': 'gw_number', 'fmt': '0>3', 'color': 'base'},
    {'xpos': 23, 'name': 'local_addr', 'fmt': '>15', 'color': 'base'},
    {'xpos': 39, 'name': 'local_port', 'fmt': '>5', 'color': 'base'},
    {'xpos': 45, 'name': 'remote_addr', 'fmt': '>15', 'color': 'base'},
    {'xpos': 61, 'name': 'remote_port', 'fmt': '>5', 'color': 'base'},
    {'xpos': 67, 'name': 'codec', 'fmt': '>5', 'color': 'base'},
    {'xpos': 74, 'name': 'qos', 'fmt': '^4', 'color': 'base'},
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
        self.show_voip_dsp = show_voip_dsp
        self.queue = Queue()
        self._active_sessions = None
        self._announcements = None
        self._capture_service = None
        self._dsp = None
        self._faults = None
        self._fw = None
        self._hw = None
        self._lldp = None
        self._lsp = None
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
        self._rtp_stat_service = None
        self._serial = None
        self._slamon_service = None
        self._sla_server = None
        self._snmp = None
        self._total_sessions = None
        self._uptime = None
        self._voip_dsp = None

    @property
    def active_sessions(self):
        if self.show_rtp_stat_summary:
            m = re.search(r'nal\s+\S+\s+(\S+)', self.show_rtp_stat_summary)
            return m.group(1) if m else "?/?"
        return "NA"

    @property
    def announcements(self):
        if self.dir:
            if not self._announcements:
                m = re.findall(r"Announcements.*?", self.dir)
                self._announcements = len(m)
            return self._announcements
        return "NA"

    @property
    def capture_service(self):
        if self.show_capture:
            if not self._capture_service:
                m = re.search(r' service is (\w+)', self.show_capture)
                self._capture_service = m.group(1) if m else "?"
            return self._capture_service
        return "NA"

    @property
    def dsp(self):
        if self.show_system:
            if not self._dsp:
                m = re.findall(r"Media Socket.*?MP(\d+)", self.show_system)
                self._dsp = sum(int(x) for x in m) if m else "?"
            return self._dsp
        return "NA"

    @property
    def faults(self):
        if self.show_faults:
            if not self._faults:
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
            if not self._fw:
                m = re.search(r'FW Vintage\s+:\s+(\S+)', self.show_system)
                self._fw = m.group(1) if m else "?"
            return self._fw
        return "NA"

    @property
    def hw(self):
        if self.show_system:
            if not self._hw:
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
            if not self._lldp:
                if "Application status: disable" in self.show_lldp_config:
                   self._lldp = "disabled"
                else:
                   self._lldp = "enabled"
            return self._lldp
        return "NA"

    @property
    def lsp(self):
        if self.show_mg_list:
            if not self._lsp:
                m = re.search(r'ICC\s+(\S)', self.show_mg_list)
                self._lsp = f"S8300{m.group(1)}" if m else "?"
            return self._lsp
        return "NA"

    @property
    def memory(self):
        if self.show_system:
            if not self._memory:
                m = re.findall(r"Memory #\d+\s+:\s+(\S+)", self.show_system)
                self._memory = f"{sum(self._to_mbyte(x) for x in m)}MB"
            return self._memory
        return "NA"

    @property
    def model(self):
        if self.show_system:
            if not self._model:
                m = re.search(r'Model\s+:\s+(\S+)', self.show_system)
                self._model = m.group(1) if m else "?"
            return self._model
        return "NA"

    @property
    def port1(self):
        if not self._port1:
            portdict = self._port_groupdict(0)
            self._port1 = portdict.get("port", "?") if portdict else "NA"
        return self._port1

    @property
    def port1_status(self):
        if not self._port1_status:
            portdict = self._port_groupdict(0)
            self._port1_status = portdict.get("status", "?") if portdict else "NA"
        return self._port1_status

    @property
    def port1_neg(self):
        if not self._port1_neg:
            portdict = self._port_groupdict(0)
            self._port1_neg = portdict.get("neg", "?") if portdict else "NA"
        return self._port1_neg

    @property
    def port1_duplex(self):
        if not self._port1_duplex:
            portdict = self._port_groupdict(0)
            self._port1_duplex = portdict.get("duplex", "?") if portdict else "NA"
        return self._port1_duplex

    @property
    def port1_speed(self):
        if not self._port1_speed:
            portdict = self._port_groupdict(0)
            self._port1_speed = portdict.get("speed", "?") if portdict else "NA"
        return self._port1_speed

    @property
    def port2(self):
        if not self._port2:
            portdict = self._port_groupdict(1)
            self._port2 = portdict.get("port", "?") if portdict else "NA"
        return self._port2

    @property
    def port2_status(self):
        if not self._port2_status:
            pdict = self._port_groupdict(1)
            self._port2_status = pdict.get("status", "?") if pdict else "NA"
        return self._port2_status

    @property
    def port2_neg(self):
        if not self._port2_neg:
            pdict = self._port_groupdict(1)
            self._port2_neg = pdict.get("neg", "?") if pdict else "NA"
        return self._port2_neg

    @property
    def port2_duplex(self):
        if not self._port2_duplex:
            pdict = self._port_groupdict(1)
            self._port2_duplex = pdict.get("duplex", "?") if pdict else "NA"
        return self._port2_duplex

    @property
    def port2_speed(self):
        if not self._port2_speed:
            pdict = self._port_groupdict(1)
            self._port2_speed = pdict.get("speed", "?") if pdict else "NA"
        return self._port2_speed

    @property
    def port_redu(self):
        if self.show_running_config:
            if not self._port_redu:
                m = re.search(r'port redundancy \d+/(\d+) \d+/(\d+)',
                    self.show_running_config)
                self._port_redu = f"{m.group(1)}/{m.group(2)}" if m else "?/?"
            return self._port_redu
        return "NA"

    @property
    def psu(self):
        if self.show_system:
            if not self._psu:
                m = re.findall(r"PSU #\d+", self.show_system)
                self._psu = len(m)
            return self._psu
        return "NA"

    @property
    def rtp_stat_service(self):
        if not self._rtp_stat_service:
            m = re.search(r'rtp-stat-service', self.show_running_config)
            self._rtp_stat_service = "enabled" if m else "disabled"
        return self._rtp_stat_service

    @property
    def serial(self):
        if self.show_system:
            if not self._serial:
                m = re.search(r'Serial No\s+:\s+(\S+)', self.show_system)
                self._serial = m.group(1) if m else "?"
            return self._serial
        return "NA"

    @property
    def slamon_service(self):
        if self.show_sla_monitor:
            if not self._slamon_service:
                m = re.search(r'SLA Monitor: (\S+)', self.show_sla_monitor)
                self._slamon_service = m.group(1).lower() if m else "?"
            return self._slamon_service
        return "NA"

    @property
    def sla_server(self):
        if self.show_sla_monitor:
            if not self._sla_server:
                m = re.search(
                    r'Registered Server IP Address:\s+(\S+)', self.show_sla_monitor
                )
                self._sla_server = m.group(1) if m else ""
            return self._sla_server
        return "NA"

    @property
    def snmp(self):
        if self.show_running_config:
            if not self._snmp:
                snmp = []
                if "snmp-server comm" in self.show_running_config:
                    snmp.append("2")
                if "encrypted-snmp-server comm" in self.show_running_config:
                    snmp.append("3")
                self._snmp = "v" + "&".join(snmp) if snmp else ""
            return self._snmp
        return "NA"

    @property
    def total_sessions(self):
        if self.show_rtp_stat_summary:
            m = re.search(r'nal\s+\S+\s+\S+\s+(\S+)', self.show_rtp_stat_summary)
            return m.group(1) if m else "?/?"
        return "NA"

    @property
    def uptime(self):
        if self.show_rtp_stat_summary:
            m = re.search(r'nal\s+(\S+)', self.show_rtp_stat_summary)
            return m.group(1) if m else "?"
        return "NA"

    @property
    def voip_dsp(self):
        inuse, total = 0, 0
        dsps = re.findall(
            r"In Use\s+:\s+(\d+) of (\d+) channels", self.show_voip_dsp
        )
        for dsp in dsps:
            try:
                dsp_inuse, dsp_total = dsp
                inuse += int(dsp_inuse)
                total += int(dsp_total)
            except:
                pass
        total = total if total > 0 else "?"
        inuse = inuse if total > 0 else "?"
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

def iter_attrs(obj, attrs, xoffset: int = 0):
    for attr in attrs:
        if hasattr(obj, attr['name']):
            _str = getattr(obj, attr['name'])
        else:
            _str = obj.get(attr['name'], attr['name'])
        color = attr['color']
        _str = f"{_str:{attr['fmt']}}"
        yield attr['xpos'] + xoffset, _str, color

def main():
    bgw = BGW("192.168.111.111")
    bgw.update(**data)
    for xpos, str, color in iter_attrs(bgw, SYSTEM_ATTRS):
        print(f"{xpos:3} {str:20} {color}")
    for xpos, str, color in iter_attrs(rtp_stat, RTP_STAT_ATTRS):
        print(f"{xpos:3} {str:20} {color}")

if __name__ == '__main__':
    main()
