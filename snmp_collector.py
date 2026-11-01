import struct
import json
import socket
import subprocess
import time
from common import log_action, CHECK_INTERVAL

ZABBIX_SERVER = "zabbix-server"
ZABBIX_PORT = 10051

DEVICES = [
    {"hostname": "Router-Edge", "ip": "172.20.0.10"},
    {"hostname": "Router-Core", "ip": "172.20.0.11"},
    {"hostname": "Router-Site-A", "ip": "172.20.0.12"},
    {"hostname": "Switch-Site-A", "ip": "172.20.0.13"},
    {"hostname": "Switch-Site-B", "ip": "172.20.0.14"},
]

ITEMS = [
    {"key": "snmp.route", "oid": ".1.3.6.1.4.1.8072.1.3.2.3.1.2.11.114.111.117.116.101.45.99.104.101.99.107"},
    {"key": "snmp.iptables", "oid": ".1.3.6.1.4.1.8072.1.3.2.3.1.2.14.105.112.116.97.98.108.101.115.45.99.104.101.99.107"},
    {"key": "snmp.syslog", "oid": ".1.3.6.1.4.1.2021.2.1.5.1"},
]

def snmp_get(ip, oid):
    try:
        out = subprocess.check_output(
            ["snmpget", "-v2c", "-c", "public", "-Oqv", ip, oid],
            timeout=5, stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except subprocess.TimeoutExpired:
        log_action(f"Timeout SNMP {ip} OID {oid}")
    except subprocess.CalledProcessError as e:
        log_action(f"SNMP error {ip} OID {oid}: {e.returncode}")
    except Exception as e:
        log_action(f"SNMP exception {ip} OID {oid}: {e}")
    return None

def zabbix_send(data_list):
    if not data_list:
        return "no data"
    payload = json.dumps({"request": "sender data", "data": data_list})
    pkt = b"ZBXD\x01" + struct.pack("<Q", len(payload)) + payload.encode()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ZABBIX_SERVER, ZABBIX_PORT))
        sock.sendall(pkt)
        resp = sock.recv(4096)
        sock.close()
        if resp[:5] == b"ZBXD\x01":
            rlen = struct.unpack("<Q", resp[5:13])[0]
            r = json.loads(resp[13 : 13 + rlen])
            return r.get("info", str(r))
    except Exception as e:
        return f"error: {e}"

def main():
    log_action("SNMP Collector démarré (snmpget)")
    while True:
        data_batch = []
        for dev in DEVICES:
            for item in ITEMS:
                val = snmp_get(dev["ip"], item["oid"])
                if val is not None:
                    data_batch.append({"host": dev["hostname"], "key": item["key"], "value": val})
        if data_batch:
            info = zabbix_send(data_batch)
            log_action(f"Envoyé {len(data_batch)} valeurs: {info}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
