import time
import requests

ZABBIX_URL = "http://zabbix-web:8080/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "zabbix"

HOSTS = {
    "Router-Edge": "172.20.0.10",
    "Router-Core": "172.20.0.11",
    "Router-Site-A": "172.20.0.12",
    "Switch-Site-A": "172.20.0.13",
    "Switch-Site-B": "172.20.0.14",
}

def api(method, params, token=None):
    req = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    if token:
        req["auth"] = token
    return requests.post(ZABBIX_URL, json=req, timeout=10).json()

def main():
    for _ in range(24):
        r = api("apiinfo.version", {})
        if "result" in r:
            break
        time.sleep(5)
    else:
        print("Zabbix indisponible")
        return

    token = api("user.login", {"user": ZABBIX_USER, "password": ZABBIX_PASSWORD})["result"]
    print("=== Correction des IPs des interfaces ===")
    hosts = api("host.get", {
        "output": ["hostid", "host"],
        "selectInterfaces": ["interfaceid", "type", "ip", "port"]
    }, token)["result"]

    for h in hosts:
        if h["host"] not in HOSTS:
            continue
        ip = HOSTS[h["host"]]
        for i in h.get("interfaces", []):
            if i["ip"] != ip:
                print(f"{h['host']}: IP {i['ip']} -> {ip}")
                api("hostinterface.update", {"interfaceid": i["interfaceid"], "ip": ip}, token)
            else:
                print(f"{h['host']}: {ip} (OK)")

    print("http://localhost:8080 (Admin/zabbix)")

if __name__ == "__main__":
    main()
