import socket
import select
import sys

# Konfiguracja połączenia
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5005
server_address = (SERVER_HOST, SERVER_PORT)

# Tworzenie socketu UDP
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Ustawienie socketu jako nieblokujący
client_socket.setblocking(False)

# Pobranie nickname od użytkownika na starcie
nickname = input("Podaj swój nickname: ").strip()

# Wysyłanie pakietu rejestracyjnego: b"\0" + nickname
registration_msg = b"\0" + nickname.encode('utf-8')
client_socket.sendto(registration_msg, server_address)
print("Połączono z serwerem. Możesz pisać wiadomości. Wpisz 'exit' aby wyjść.\n")

try:
    while True:
        # select monitoruje sys.stdin (0) oraz socket klienta
        # watch_list zawiera obiekty, na które czekamy
        watch_list = [sys.stdin, client_socket]
        
        # Czekamy na gotowość do odczytu (funkcja blokuje do momentu zdarzenia)
        readable, _, _ = select.select(watch_list, [], [])

        for source in readable:
            # Sytuacja A: Użytkownik coś wpisał w terminalu
            if source == sys.stdin:
                line = sys.stdin.readline().strip()
                
                if line == "exit" or not line:
                    # Wysyłanie pustego datagramu (sygnał rozłączenia)
                    client_socket.sendto(b"", server_address)
                    print("Rozłączanie...")
                    sys.exit(0)
                
                # Wysyłanie wiadomości: b"\1" + tekst
                msg = b"\1" + line.encode('utf-8')
                client_socket.sendto(msg, server_address)

            # Sytuacja B: Przyszły dane z serwera
            elif source == client_socket:
                data, addr = client_socket.recvfrom(1024)
                if data:
                    msg_type = data[0:1]
                    payload = data[1:]
                    
                    if msg_type == b"\1":
                        print(payload.decode('utf-8'))

except KeyboardInterrupt:
    # W przypadku Ctrl+C również wysyłamy pusty datagram informujący o wyjściu
    client_socket.sendto(b"", server_address)
    print("\nRozłączono.")
finally:
    client_socket.close()