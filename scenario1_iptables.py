import time
from common import get_token, get_active_problems, ssh_exec, log_action, wait_zabbix, CHECK_INTERVAL

HOST_IP = {
    "Router-Edge": "172.20.0.10",
    "Router-Core": "172.20.0.11",
    "Router-Site-A": "172.20.0.12",
    "Switch-Site-A": "172.20.0.13",
    "Switch-Site-B": "172.20.0.14",
}
TRIGGER_DESC = "Iptables bloque ICMP"

def fix(ip):
    log_action(f"iptables bloque ICMP sur {ip}. Suppression...")
    code, out, err = ssh_exec(ip, "iptables -D INPUT -p icmp --icmp-type echo-request -j DROP")
    if code == 0:
        log_action(f"Regle ICMP supprimee sur {ip}")
    else:
        log_action(f"Erreur suppression iptables sur {ip}: {err}")

def main():
    log_action("=== [Scenario 1] Demarrage (reacif Zabbix) : Iptables ===")
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
