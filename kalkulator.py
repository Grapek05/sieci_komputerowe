ip_value = "12.34.56.78/28"
ip_value = ip_value.split("/")
print (ip_value)
ip = ip_value[0].split(".")
print (ip)
print (int(ip[0])), int(ip[1]), int(ip[2]), int(ip[3])
ip = int(ip[0]) << 24 | int(ip[1]) << 16 | int(ip[2]) << 8 | int(ip[3])
print(ip)
mask = int("1" * int(ip_value[1]) + "0" * (32-int(ip_value[1])), 2)
print(mask)
network = ip & mask
broadcast = network | (~mask & 0xFFFFFFFF)
pierwszy_host = network + 1
ostatni_host = broadcast - 1
hosts = 2 ** (32 - int(ip_value[1])) - 2
def print_ip(label, value):
    a = (value >> 24) & 255
    b = (value >> 16) & 255
    c = (value >> 8) & 255
    d = value & 255
    print(label)
    print(f"{a}.{b}.{c}.{d}")
    print(f"{a:08b}.{b:08b}.{c:08b}.{d:08b}")
    print()


print_ip("Adres sieci:", network)
print_ip("Maska:", mask)

print("Liczba hostów:", hosts)
print()

print_ip("Pierwszy host:", pierwszy_host)
print_ip("Ostatni host:", ostatni_host)
print_ip("Broadcast:", broadcast)