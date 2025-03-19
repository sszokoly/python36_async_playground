
#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import re
from typing import AsyncIterator, Iterable, Iterator, Optional, Tuple, Union, TypeVar, Any, Dict, List, Set
from asyncio import Lock, Queue, Semaphore

data ={
    "host": "192.168.111.111",
    "proto": "encrypted",
    "gw_name": "AvayaG450A",
    "gw_number": "001",
    "last_seen": "2023-10-16 08:49:27",
    
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
        set port mirror source-port 10/5 mirror-port 10/6 sampling always direction both
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

        "show temp": '''
        Gxxx-001(super)# show temp
        Ambient
        -------
        Temperature : 40C
        High Warning: 45C
        Low Warning : -5C
        ''',

        "show sla-monitor": '''
        show sla-monitor
        SLA Monitor: Disabled
        Server Address: 0.0.0.0
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
        010        internal  53,05:23:06    0/0     16/2    00:05:17    64
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

MAIN_ATTRS = [
    {'xpos':  1, 'text': 'start_time', 'format_spec': '', 'color': 'normal'},
    {'xpos': 10, 'text': 'end_time', 'format_spec': '', 'color': 'normal'},
    {'xpos': 19, 'text': 'bgw_num', 'format_spec': '0>3', 'color': 'normal'},
    {'xpos': 23, 'text': 'local_ip', 'format_spec': '>15', 'color': 'address'},
    {'xpos': 39, 'text': 'local_port', 'format_spec': '>5', 'color': 'port'},
    {'xpos': 46, 'text': 'remote_ip', 'format_spec': '>15', 'color': 'address'},
    {'xpos': 61, 'text': 'remote_port', 'format_spec': '>5', 'color': 'port'},
    {'xpos': 67, 'text': 'status', 'format_spec': '^6', 'color': 'active'},
    {'xpos': 74, 'text': 'qos', 'format_spec': '^3', 'color': 'ok'},
]

BGW_ATTRS = [
    {'xpos':  1, 'text': 'number', 'format_spec': '', 'color': 'normal'},
    {'xpos':  5, 'text': 'model', 'format_spec': '>6', 'color': 'normal'},
    {'xpos': 12, 'text': 'firmware', 'format_spec': '>8', 'color': 'normal'},
    {'xpos': 21, 'text': 'ip', 'format_spec': '>15', 'color': 'address'},
    {'xpos': 37, 'text': 'serial', 'format_spec': '>12', 'color': 'normal'},
    {'xpos': 50, 'text': 'snmp', 'format_spec': '^4', 'color': 'normal'},
    {'xpos': 55, 'text': 'rtp_stat', 'format_spec': '>8', 'color': 'normal'},
    {'xpos': 64, 'text': 'capture', 'format_spec': '>7', 'color': 'normal'},
    {'xpos': 72, 'text': 'fault', 'format_spec': '>5', 'color': 'normal'},
]

class BGW():
    def __init__(self,
        host: str,
        proto: str = '',
        last_seen = None,
        gw_name: str = '',
        gw_number: str = '',
        show_running_config: str = '',
        show_system: str = '',
        show_faults: str = '',
        show_capture: str = '',
        show_voip_dsp: str = '',
        show_temp: str = '',
        show_sla_monitor: str = '',
        show_lldp_config: str = '',
        show_port: str = '',
        show_mg_list: str = '',
        show_rtp_stat_summary: str = '',
        **kwargs,
    ) -> None:
        self.host = host
        self.proto = proto
        self.last_seen = last_seen
        self.gw_name = gw_name
        self.gw_number = gw_number
        self.show_running_config = show_running_config
        self.show_system = show_system
        self.show_faults = show_faults
        self.show_capture = show_capture
        self.show_voip_dsp = show_voip_dsp
        self.show_temp = show_temp
        self.show_sla_monitor = show_sla_monitor
        self.show_lldp_config = show_lldp_config
        self.show_port = show_port
        self.show_mg_list = show_mg_list
        self.show_rtp_stat_summary = show_rtp_stat_summary
        self.queue = Queue()
        self._active_sessions = None
        self._capture_service = None
        self._dsp = None
        self._faults = None
        self._fw = None
        self._hw = None
        self._lldp = None
        self._lsp = None
        self._mean_duration = None
        self._memory = None
        self._model = None
        self._port1 = None
        self._port1_status = None
        self._port1_neg = None
        self._port1_speed = None
        self._port1_duplex = None
        self._port2 = None
        self._port2_status = None    
        self._port2_neg = None
        self._port2_speed = None
        self._port2_duplex = None
        self._port_redundancy = None
        self._psu = None
        self._qos_traps = None
        self._rtp_stat_service = None
        self._serial = None
        self._slamon_service = None
        self._sla_server = None
        self._snmp = None
        self._temp = None
        self._total_sessions = None
        self._uptime = None
        self._voip_dsp = None

    @property
    def model(self):
        if not self._model:
            m = re.search(r'Model\s+:\s+(\S+)', self.show_system)
            self._model = m.group(1) if m else "?"
        return self._model

    @property
    def hw(self):
        if not self._hw:
            m = re.search(r'HW Vintage\s+:\s+(\S+)', self.show_system)
            hw_vintage = m.group(1) if m else "?"
            m = re.search(r'HW Suffix\s+:\s+(\S+)', self.show_system)
            hw_suffix = m.group(1) if m else "?"
            self._hw = f"{hw_vintage}{hw_suffix}"
        return self._hw

    @property
    def fw(self):
        if not self._fw:
            m = re.search(r'FW Vintage\s+:\s+(\S+)', self.show_system)
            self._fw = m.group(1) if m else "?"
        return self._fw

    @property
    def slamon(self):
        if not self._slamon:
            m = re.search(r'sla-server-ip-address (\S+)', self.show_system)
            self._slamon = m.group(1) if m else ""
        return self._slamon

    @property
    def serial(self):
        if not self._serial:
            m = re.search(r'Serial No\s+:\s+(\S+)', self.show_system)
            self._serial = m.group(1) if m else "?"
        return self._serial

    @property
    def rtp_stat(self):
        if not self._rtp_stat:
            m = re.search(r'rtp-stat-service', self.show_running_config)
            self._rtp_stat = "enabled" if m else "disabled"
        return self._rtp_stat

    @property
    def capture(self):
        if not self._capture:
            m = re.search(r'Capture service is (\w+) and (\w+)', self.show_capture)
            config, state = m.group(1, 2) if m else ("?", "?")
            self._capture = config if config == "disabled" else state
        return self._capture

    @property
    def temp(self):
        if not self._temp:
            m = re.search(r'Temperature\s+:\s+(\S+) \((\S+)\)', self.show_temp)
            cels, faren = m.group(1, 2) if m else ("?", "?")
            self._temp = f"{cels}/{faren}"
        return self._temp

    @property
    def faults(self):
        if not self._faults:
            if "No Fault Messages" in self.show_faults:
                self._faults = "none"
            else:
                self._faults = "faulty"
        return self._faults

    @property
    def uptime(self):
        if not self._uptime:
            m = re.search(r'Uptime.+?:\s+(\S+)', self.show_system)
            self._uptime = m.group(1) if m else "?"
        return self._uptime

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

    @property
    def sla_server(self):
        if not self._sla_server:
            m = re.search(
                r'Registered Server IP Address:\s+(\S+)', self.show_sla_monitor
            )
            self._sla_server = m.group(1) if m.group(1) != "0.0.0.0" else ""
        return self._sla_server

    def update(self, data):
        self.last_seen = data.get("last_seen", self.last_seen)
        self.gw_name = data.get("gw_name", self.gw_name)
        self.gw_number = data.get("gw_number", self.gw_number)
        commands = data.get("commands", {})
        if commands:
            for cmd, value in commands.items():
                bgw_attr = cmd.replace(" ", "_").replace("-", "_")
                setattr(self, bgw_attr, value)

    def __str__(self):
        return f"BGW({self.host})"

    def __repr__(self):
        return f"BGW(host={self.host})"

    def asdict(self):
        return self.__dict__

def iter_session_main_attrs(
    session_dict: Dict[str, str],
    main_attrs: List[Dict[str, Union[int, str]]] = MAIN_ATTRS,
    xoffset: int = 0
) -> Iterator[Tuple[int, str, str]]:
    """
    Iterate over the main attributes of a session dictionary and yield a tuple of 3 values:

    - `ypos`: The y position of the attribute
    - `text`: The text of the attribute, formatted according to the `format_spec`
    - `color`: The color of the attribute

    :param session_dict: A dictionary of key-value pairs of the attributes of the session
    :param main_attrs: A list of dictionaries of the main attributes of the session
    :param xoffset: The offset of xpos
    :return: An iterator of tuples of 3 values
    """
    for attrs in main_attrs:
        text = session_dict.get(attrs['text'], attrs['text'])
        color = attrs['color']
        if attrs['text'] == 'status':
            text = 'active' if text == 'Active' else 'ended'
            color = 'active' if text == 'Active' else 'ended'
        if attrs['text'] == 'qos':
            text = '✔' if text == 'OK' else '✘'
            color = 'ok' if text == 'OK' else 'fault'
        text = f'{text:{attrs["format_spec"]}}'
        yield attrs['xpos'] + xoffset, text, color

def iter_bgw_attrs(
    bgw: BGW,
    bgw_attrs: List[Dict[str, Union[int, str]]] = BGW_ATTRS
) -> Iterator[Tuple[int, str, str]]:
    """
    Iterate over the attributes of a BGW object and yield a tuple of 3 values:

    - `xpos`: The x position of the attribute
    - `text`: The text of the attribute, formatted according to the `format_spec`
    - `color`: The color of the attribute

    :param bgw: A BGW object
    :param bgw_attrs: A list of dictionaries of the attributes of the BGW
    :return: An iterator of tuples of 3 values
    """
    for attrs in bgw_attrs:
        text = getattr(bgw, attrs['text'])
        text = f'{text:{attrs["format_spec"]}}'
        yield attrs['xpos'], text, attrs['color']

def main():
    bgw = BGW(**data)
    bgw.update(data)
    print(bgw.asdict())

if __name__ == '__main__':
    main()