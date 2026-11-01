import paramiko
import os
import time
from datetime import datetime

# === CONFIGURATION ===
DEVICES = [
    {"ip": "172.20.0.10", "name": "router-edge"},
    {"ip": "172.20.0.11", "name": "router-core"},
    {"ip": "172.20.0.12", "name": "router-site-a"},
    {"ip": "172.20.0.13", "name": "switch-site-a"},
    {"ip": "172.20.0.14", "name": "switch-site-b"},
]
SSH_USER = "root"
SSH_PASS = "ocp123"
BACKUP_DIR = "backups"

# === LOG ===
def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)

# === ATTENTE QUE LES ÉQUIPEMENTS SOIENT PRÊTS ===
def wait_for_devices():
    log("Attente du démarrage des équipements...")
    for device in DEVICES:
        for attempt in range(12):
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(device["ip"], username=SSH_USER, password=SSH_PASS, timeout=5)
                ssh.close()
                log(f"  {device['name']} ({device['ip']}) prêt.")
                break
            except Exception:
                log(f"  {device['name']} ({device['ip']}) en attente... ({attempt+1}/12)")
                time.sleep(5)
        else:
            log(f"  {device['name']} ({device['ip']}) toujours injoignable après 60s.")

# === BACKUP UN SEUL ÉQUIPEMENT ===
def backup_device(ip, name):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=SSH_USER, password=SSH_PASS, timeout=10)

        # Collecte des informations
        _, stdout1, _ = ssh.exec_command("ip addr")
        ip_addr = stdout1.read().decode()

        _, stdout2, _ = ssh.exec_command("ip route")
        ip_route = stdout2.read().decode()

        _, stdout3, _ = ssh.exec_command("hostname")
        hostname = stdout3.read().decode().strip()

        _, stdout4, _ = ssh.exec_command("iptables -L -n -v")
        iptables = stdout4.read().decode()

        _, stdout5, _ = ssh.exec_command("cat /etc/snmp/snmpd.conf 2>/dev/null || echo 'SNMP non disponible'")
        snmp_conf = stdout5.read().decode()

        ssh.close()

        # Construction du fichier de backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        separator = "=" * 50

        content = f"{separator}\n"
        content += f"BACKUP {name.upper()} ({ip})\n"
        content += f"Date    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"Hostname: {hostname}\n"
        content += f"{separator}\n\n"

        content += "--- IP ADDRESS ---\n" + ip_addr + "\n\n"
        content += "--- IP ROUTING TABLE ---\n" + ip_route + "\n\n"
        content += "--- IPTABLES RULES ---\n" + iptables + "\n\n"
        content += "--- SNMP CONFIG ---\n" + snmp_conf + "\n"

        # Sauvegarde
        filename = f"{BACKUP_DIR}/{name}_{timestamp}.conf"
        with open(filename, "w") as f:
            f.write(content)

        log(f"[OK] {name} ({ip}) -> {filename}")
        return True

    except Exception as e:
        log(f"[ERREUR] {name} ({ip}) : {e}")
        return False

# === FONCTION PRINCIPALE ===
def main():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    log("=== Démarrage du backup des configurations ===")
    wait_for_devices()
    success = 0
    fail = 0

    for device in DEVICES:
        if backup_device(device["ip"], device["name"]):
            success += 1
        else:
            fail += 1

    log(f"=== Backup terminé : {success} réussi(s), {fail} échoué(s) ===")

if __name__ == "__main__":
    main()
