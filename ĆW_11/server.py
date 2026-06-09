import socket

# Konfiguracja serwera
HOST = "127.0.0.1"
PORT = 5005

# Słownik użytkowników: {(ip, port): "nickname"}
clients = {}

# Tworzenie socketu UDP (SOCK_DGRAM)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))

print(f"Serwer Multiplayer Notepad uruchomiony na {HOST}:{PORT}...")

try:
    while True:
        # Odbieranie danych (maksymalnie 1024 bajty)
        data, client_address = server_socket.recvfrom(1024)
        
        # 1. Obsługa rozłączenia (pusty datagram)
        if not data:
            if client_address in clients:
                nickname = clients[client_address]
                del clients[client_address]
                print(f"[-] Użytkownik {nickname} ({client_address}) rozłączył się.")
                
                # Opcjonalnie: powiadom innych o rozłączeniu
                disconnect_msg = b"\1" + f"[System]: {nickname} opuścił czat.".encode('utf-8')
                for addr in clients:
                    server_socket.sendto(disconnect_msg, addr)
            continue

        # Pobieramy typ wiadomości (pierwszy znak) i samą treść
        msg_type = data[0:1]
        payload = data[1:]

        # 2. Rejestracja Nickname (b"\0")
        if msg_type == b"\0":
            nickname = payload.decode('utf-8').strip()
            clients[client_address] = nickname
            print(f"[+] Zarejestrowano użytkownika: {nickname} z adresu {client_address}")
            
            # Opcjonalnie: powiadom innych o dołączeniu nowego gracza
            welcome_msg = b"\1" + f"[System]: {nickname} dołączył do sesji!".encode('utf-8')
            for addr in clients:
                if addr != client_address:
                    server_socket.sendto(welcome_msg, addr)

        # 3. Obsługa wiadomości tekstowej (b"\1")
        elif msg_type == b"\1":
            # Ignorujemy, jeśli użytkownik nie podał wcześniej nickname
            if client_address not in clients:
                print(f"[!] Ignorowanie wiadomości od niezarejestrowanego adresu: {client_address}")
                continue
            
            sender_nickname = clients[client_address]
            message_text = payload.decode('utf-8')
            print(f"[{sender_nickname}]: {message_text}")

            # Przygotowanie wiadomości do rozesłania: b"\1" + "Nick: Treść"
            broadcast_payload = f"{sender_nickname}: {message_text}".encode('utf-8')
            broadcast_msg = b"\1" + broadcast_payload

            # Rozsyłanie (broadcast) do wszystkich INNYCH klientów
            for addr in clients:
                if addr != client_address:
                    server_socket.sendto(broadcast_msg, addr)

except KeyboardInterrupt:
    print("\nZamykanie serwera...")
finally:
    server_socket.close()