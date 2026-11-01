FROM python:3.11-alpine

WORKDIR /app

RUN apk add --no-cache iptables net-snmp-tools

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common.py .
COPY scenario1_iptables.py .
COPY scenario2_route.py .
COPY scenario3_syslog.py .
COPY backup_configs.py .
COPY configure_zabbix.py .
COPY snmp_collector.py .

CMD ["python", "-u", "scenario1_iptables.py"]
