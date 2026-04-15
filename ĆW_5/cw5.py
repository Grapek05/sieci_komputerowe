import subprocess
import socket
import os
import re
 
class NetworkManager:
    """Klasa implementująca zadania sieciowe przy użyciu Pythona."""
 
    def run_cmd(self, cmd):
        """Pomocnicza funkcja do bezpiecznego wywoływania komend."""
        try:
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            return result.decode('utf-8').strip()
        except subprocess.CalledProcessError as e:
            return f"Błąd wykonania: {e.output.decode('utf-8')}"
 
    # 1. Lista interfejsów (Nazwa - Status)
    def list_interfaces(self):
        return self.run_cmd("ip -br link")
 
    # 2. MAC Routera (bramy)
    def get_router_mac(self):
        # Najpierw szukamy IP bramy, potem MAC w tablicy ARP
        brama_ip = self.run_cmd("ip route | grep default | awk '{print $3}'")
        return self.run_cmd(f"ip neigh show {brama_ip} | awk '{{print $5}}'")
 
    # 3. Zmiana MAC (wymaga uprawnień roota)
    def change_mac(self, interface, new_mac):
        cmd = f"sudo ip link set dev {interface} down && " \
              f"sudo ip link set dev {interface} address {new_mac} && " \
              f"sudo ip link set dev {interface} up"
        return self.run_cmd(cmd)
 
    # 4. Ping podsieci (wykorzystuje fping dla szybkości)
    def ping_subnet(self, subnet):
        return self.run_cmd(f"fping -g {subnet} -a 2>/dev/null")
 
    # 5. Skan portu 22 w podsieci
    def scan_ssh_port(self, subnet):
        return self.run_cmd(f"nmap -p 22 {subnet} --open")
 
    # 6. Skan portów na lo
    def scan_loopback(self):
        return self.run_cmd("nmap -p- 127.0.0.1")
 
    # 7. Otwarte porty + PID + Program
    def get_listening_processes(self):
        return self.run_cmd("sudo ss -tulpn")
 
    # 8. Trasa domyślna
    def get_default_route(self):
        return self.run_cmd("ip route show default")
 
    # 9. Traceroute do kosmatka.pl
    def trace_kosmatka(self):
        return self.run_cmd("traceroute kosmatka.pl")
 
    # 10. Adres DNS systemu
    def get_dns_server(self):
        with open('/etc/resolv.conf', 'r') as f:
            content = f.read()
            return re.findall(r'^nameserver\s+(.+)', content, re.MULTILINE)
 
    # 11. Statyczne wpisy DNS
    def get_hosts_file(self):
        with open('/etc/hosts', 'r') as f:
            return f.read()
 
    # 12. Rekord MX przez 8.8.8.8
    def get_mx_record(self):
        return self.run_cmd("dig @8.8.8.8 kosmatka.pl MX +short")
 
    # 13. Adres IPv6 google.pl (Użycie natywnego socketu)
    def get_google_ipv6(self):
        try:
            info = socket.getaddrinfo("google.pl", None, socket.AF_INET6)
            return info[0][4][0]
        except Exception as e:
            return str(e)
 
    # 14. Dane domeny whois
    def get_whois_info(self):
        return self.run_cmd("whois kosmatka.pl | grep -E 'created|expire'")
 
    # 15. Usunięte domeny .pl
    def get_deleted_domains_url(self):
        return "https://www.dns.pl/lista_domen_usunietych"
 
# Przykład użycia:
net = NetworkManager()
print("INTERFEJSY:\n", net.list_interfaces())
print("\nDNS SYSTEMOWY:", net.get_dns_server())