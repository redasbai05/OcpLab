import time
from common import get_token, get_active_problems, ssh_exec, log_action, wait_zabbix, CHECK_INTERVAL

HOST_IP = {
    "Router-Edge": "172.20.0.10",
    "Router-Core": "172.20.0.11",
    "Router-Site-A": "172.20.0.12",
    "Switch-Site-A": "172.20.0.13",
    "Switch-Site-B": "172.20.0.14",
}
GATEWAY = "172.20.0.1"
TRIGGER_DESC = "Route manquante"

def fix(ip):
    log_action(f"Route manquante sur {ip}. Restauration...")
    code, out, err = ssh_exec(ip, f"ip route add default via {GATEWAY}")
    if code == 0:
        code2, verify, _ = ssh_exec(ip, "ip route | grep '^default'")
        log_action(f"Route restauree sur {ip}: {verify}")
    else:
        log_action(f"Erreur restauration route sur {ip}: {err}")

def main():
    log_action("=== [Scenario 2] Demarrage (reacif Zabbix) : Route ===")
    token = wait_zabbix()
    if not token:
        return
    while True:
        problems = get_active_problems(token)
        for p in problems:
            if TRIGGER_DESC in p["description"]:
                for h in p.get("hosts", []):
                    ip = HOST_IP.get(h["host"])
                    if ip:
                        fix(ip)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
