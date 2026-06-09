import socket
import threading
import json

HOST = "127.0.0.1"
PORT = 5555

# Struktury danych w pamięci RAM
registered_users = {}  # {"username": "password"}
active_clients = {}    # {"username": socket_object}

# Mutex do synchronizacji dostępu do powyższych struktur
data_lock = threading.Lock()

def send_json(client_socket, data):
    """Pomocnicza funkcja do wysyłania spakowanego JSON-a z nową linią."""
    try:
        encoded_data = (json.dumps(data) + "\n").encode('utf-8')
        client_socket.sendall(encoded_data)
    except Exception:
        pass

def broadcast(message_dict, exclude_user=None):
    """Wysyła powiadomienie/wiadomość do wszystkich zalogowanych użytkowników."""
    with data_lock:
        for username, client_sock in active_clients.items():
            if username != exclude_user:
                send_json(client_sock, message_dict)

def handle_client(client_socket, client_address):
    print(f"[+] Nowe połączenie niskopoziomowe z adresu: {client_address}")
    current_user = None
    
    # Tworzymy bufor na dane strumieniowe TCP
    buffer = ""
    
    try:
        while True:
            # Odbieranie paczki danych
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break # Klient zamknął połączenie
            
            buffer += data
            # Przetwarzamy wiadomości linia po linii (obsługa tzw. TCP stream splitting)
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                
                try:
                    request = json.loads(line)
                except json.JSONDecodeError:
                    continue

                action = request.get("action")

                # ==========================================
                # Opcja 1: REJESTRACJA
                # ==========================================
                if action == "register":
                    user = request.get("username")
                    pwd = request.get("password")
                    
                    with data_lock:
                        if user in registered_users:
                            send_json(client_socket, {"status": "error", "message": "Użytkownik już istnieje!"})
                        elif not user or not pwd:
                            send_json(client_socket, {"status": "error", "message": "Login/hasło nie mogą być puste!"})
                        else:
                            registered_users[user] = pwd
                            send_json(client_socket, {"status": "success", "message": "Rejestracja pomyślna. Możesz się zalogować."})
                            print(f"[Reg] Zarejestrowano użytkownika: {user}")

                # ==========================================
                # Opcja 2: LOGOWANIE
                # ==========================================
                elif action == "login":
                    user = request.get("username")
                    pwd = request.get("password")
                    
                    with data_lock:
                        if user in active_clients:
                            send_json(client_socket, {"status": "error", "message": "Ten użytkownik jest już zalogowany!"})
                        elif registered_users.get(user) == pwd and user is not None:
                            current_user = user
                            active_clients[user] = client_socket
                            
                            # Pobieramy listę obecnych (wewnątrz locka)
                            online_users = list(active_clients.keys())
                            
                            send_json(client_socket, {
                                "status": "success", 
                                "message": f"Zalogowano jako {user}",
                                "online_users": online_users
                            })
                            print(f"[Log] {user} zalogował się.")
                        else:
                            send_json(client_socket, {"status": "error", "message": "Błędny login lub hasło!"})
                    
                    # Notyfikacja dla innych (poza lockiem w funkcji broadcast)
                    if current_user:
                        broadcast({"type": "notification", "message": f"[+] Użytkownik {current_user} dołączył do czatu."}, exclude_user=current_user)

                # ==========================================
                # Opcja 3: WIADOMOŚĆ (Prywatna lub Globalna)
                # ==========================================
                elif action == "msg":
                    if not current_user:
                        send_json(client_socket, {"status": "error", "message": "Musisz się najpierw zalogować!"})
                        continue
                    
                    target = request.get("to") # Może być nazwą użytkownika lub "all"
                    text = request.get("text")
                    
                    payload = {
                        "type": "chat",
                        "from": current_user,
                        "to": target,
                        "text": text
                    }
                    
                    if target == "all":
                        broadcast(payload, exclude_user=current_user)
                    else:
                        # Prywatna wiadomość
                        with data_lock:
                            target_sock = active_clients.get(target)
                        
                        if target_sock:
                            send_json(target_sock, payload)
                        else:
                            send_json(client_socket, {"status": "error", "message": f"Użytkownik {target} jest nieosiągalny."})

    except Exception as e:
        print(f"[!] Błąd obsługi klienta {client_address}: {e}")
    finally:
        # Obsługa rozłączenia klienta i czyszczenie struktur danych
        client_socket.close()
        if current_user:
            with data_lock:
                if current_user in active_clients:
                    del active_clients[current_user]
            print(f"[-] {current_user} rozłączył się.")
            broadcast({"type": "notification", "message": f"[-] Użytkownik {current_user} opuścił czat."})

# Uruchomienie głównej pętli serwera
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind((HOST, PORT))
server_sock.listen()

print(f"[*] Wielowątkowy serwer TCP działa na {HOST}:{PORT}...")

try:
    while True:
        c_sock, c_addr = server_sock.accept()
        # Każdy klient dostaje swój dedykowany wątek
        t = threading.Thread(target=handle_client, args=(c_sock, c_addr), daemon=True)
        t.start()
except KeyboardInterrupt:
    print("\n[*] Zamykanie serwera.")
finally:
    server_sock.close()