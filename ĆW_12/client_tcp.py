import socket
import threading
import json
import sys

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5555

def receive_messages(sock):
    """Wątek odpowiedzialny tylko i wyłącznie za odbiór danych z serwera."""
    buffer = ""
    try:
        while True:
            data = sock.recv(1024).decode('utf-8')
            if not data:
                print("\n[!] Połączenie z serwerem zostało przerwane.")
                break
            
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                
                response = json.loads(line)
                
                # Parsowanie odpowiedzi z serwera i ładne wypisywanie
                if "status" in response:
                    print(f"\n[Serwer] {response.get('message')}")
                    if "online_users" in response:
                        print(f"[Serwer] Osoby online: {', '.join(response['online_users'])}")
                
                elif response.get("type") == "notification":
                    print(f"\n{response.get('message')}")
                
                elif response.get("type") == "chat":
                    sender = response.get("from")
                    target = response.get("to")
                    text = response.get("text")
                    if target == "all":
                        print(f"\n[{sender} do WSZYSTKICH]: {text}")
                    else:
                        print(f"\n[{sender} (PW)]: {text}")
                        
    except Exception:
        pass
    finally:
        print("Zamykanie wątku odbiorczego...")
        sys.exit(0)

def print_menu():
    print("\n--- DOSTĘPNE POLECENIA ---")
    print("1. register <login> <haslo>")
    print("2. login <login> <haslo>")
    print("3. msg all <tresc_wiadomosci>        (Wiadomość do wszystkich)")
    print("4. msg <nick_odbiorcy> <tresc_haslo>  (Wiadomość prywatna)")
    print("5. exit                              (Wyjście z aplikacji)")
    print("---------------------------\n")

# Inicjalizacja połączenia TCP
client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_sock.connect((SERVER_HOST, SERVER_PORT))
except ConnectionRefusedError:
    print("[!] Nie można połączyć się z serwerem. Upewnij się, że serwer działa.")
    sys.exit(1)

# Uruchomienie wątku do odbierania danych w tle
recv_thread = threading.Thread(target=receive_messages, args=(client_sock,), daemon=True)
recv_thread.start()

print_menu()

# Główny wątek: pobieranie poleceń od użytkownika
try:
    while True:
        cmd_input = input().strip()
        if not cmd_input:
            continue
        
        parts = cmd_input.split(" ", 2)
        command = parts[0].lower()

        if command == "exit":
            break
        
        elif command == "register" or command == "login":
            if len(parts) < 3:
                print("[Błąd] Składnia: <register/login> <user> <password>")
                continue
            payload = {
                "action": command,
                "username": parts[1],
                "password": parts[2]
            }
            client_sock.sendall((json.dumps(payload) + "\n").encode('utf-8'))
            
        elif command == "msg":
            if len(parts) < 3:
                print("[Błąd] Składnia: msg <all/nickname> <tekst>")
                continue
            
            target = parts[1]
            text = parts[2]
            
            payload = {
                "action": "msg",
                "to": target,
                "text": text
            }
            client_sock.sendall((json.dumps(payload) + "\n").encode('utf-8'))
        else:
            print("[System] Nieznana komenda.")
            print_menu()

except KeyboardInterrupt:
    pass
finally:
    print("Zamykanie klienta...")
    client_sock.close()