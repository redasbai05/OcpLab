import requests
import paramiko
import time
from datetime import datetime

# === CONFIGURATION COMMUNE ===
ZABBIX_URL = "http://zabbix-web:8080/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "zabbix"
SSH_USER = "root"
SSH_PASS = "ocp123"
CHECK_INTERVAL = 30

# === SSH ===
def ssh_connect(ip):
    """Établit une connexion SSH vers un équipement."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=SSH_USER, password=SSH_PASS, timeout=10)
    return ssh

def ssh_exec(ip, command):
    """Exécute une commande SSH et retourne (exit_code, stdout, stderr)."""
    try:
        ssh = ssh_connect(ip)
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        ssh.close()
        return exit_code, out, err
    except Exception as e:
        return -1, "", str(e)

# === LOG ===
def log_action(message, logfile="logs/auto_remediate.log"):
    """Écrit un message dans le log et l'affiche."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}\n"
    with open(logfile, "a") as f:
        f.write(line)
    print(line.strip())

# === ZABBIX API ===
def get_token():
    """Authentifie et retourne le token Zabbix."""
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "user": ZABBIX_USER,
            "password": ZABBIX_PASSWORD
        },
        "id": 1
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(ZABBIX_URL, json=payload, headers=headers, timeout=10)
        result = response.json()
        return result.get("result")
    except Exception as e:
        log_action(f"[ERREUR AUTH] {e}")
        return None

def get_active_problems(token):
    """Retourne les alertes actives depuis Zabbix."""
    payload = {
        "jsonrpc": "2.0",
        "method": "trigger.get",
        "params": {
            "filter": {"value": "1"},
            "output": ["triggerid", "description"],
            "selectHosts": ["host", "name"],
            "sortfield": "lastchange",
            "sortorder": "DESC"
        },
        "auth": token,
        "id": 2
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(ZABBIX_URL, json=payload, headers=headers, timeout=10)
        result = response.json()
        return result.get("result", [])
    except Exception as e:
        log_action(f"[ERREUR API] {e}")
        return []

def wait_zabbix():
    """Attend que Zabbix soit prêt (max 120s). Retourne le token ou None."""
    log_action("Attente de Zabbix...")
    for i in range(24):
        token = get_token()
        if token:
            log_action("Zabbix est prêt.")
            return token
        time.sleep(5)
    log_action("Zabbix non disponible après 120s.")
    return None
