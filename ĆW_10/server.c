#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>

void error_exit(const char *msg) {
    perror(msg);
    exit(EXIT_FAILURE);
}

int main(int argc, char *argv[]) {
    // 1. Sprawdzenie, czy uruchamiającym jest root (uid == 0)
    if (getuid() == 0) {
        fprintf(stderr, "Błąd: Serwer nie może być uruchamiany z konta root!\n");
        exit(EXIT_FAILURE);
    }

    // Ustalenie portu - domyślnie 80 lub z pierwszego parametru
    int port = 80;
    if (argc > 1) {
        port = atoi(argv[1]);
    }

    int server_fd, client_fd;
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len = sizeof(client_addr);

    // 2. socket() - Utworzenie gniazda TCP/IPv4
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) error_exit("Błąd: socket()");

    // 3. setsockopt() - Ustawienie opcji SO_REUSEADDR
    int opt = 1;
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        error_exit("Błąd: setsockopt()");
    }

    // 4. bind() - Bindowanie do portu i adresu INADDR_ANY
    memset((char*)&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY); 
    server_addr.sin_port = htons(port);

    if (bind(server_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        error_exit("Błąd: bind()");
    }

    // 5. listen() - Rozpoczęcie nasłuchiwania
    if (listen(server_fd, 5) < 0) {
        error_exit("Błąd: listen()");
    }

    printf("Serwer nasłuchuje na porcie %d...\n", port);

    // 6. Główna pętla serwera (iteracyjna)
    while (1) {
        // a) accept() - Oczekiwanie na klienta
        client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_len);
        if (client_fd < 0) {
            perror("Błąd: accept()");
            continue; // Zamiast kończyć serwer, przechodzimy do kolejnego nasłuchu
        }

        // b) recv() - Blokujące odebranie zapytania
        char buffer[2048];
        memset(buffer, 0, sizeof(buffer));
        int bytes_received = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
        if (bytes_received < 0) {
            perror("Błąd: recv()");
            close(client_fd);
            continue;
        }

        // Zignorowanie zawartości zapytania (zgodnie z poleceniem)
        // Odczyt uptime systemu
        FILE *uptime_file = fopen("/proc/uptime", "r");
        if (!uptime_file) {
            perror("Błąd otwarcia /proc/uptime");
            close(client_fd);
            continue;
        }
        
        char uptime_str[256];
        // Pobieramy pierwszą wartość (czas od uruchomienia w sekundach)
        fscanf(uptime_file, "%s", uptime_str);
        fclose(uptime_file);

        // c) send() - Wysłanie nagłówków HTTP
        const char* http_header = "HTTP/1.0 200 OK\r\n"
                                  "Content-Type: text/plain; charset=UTF-8\r\n"
                                  "Connection: close\r\n";
        
        char response_headers[512];
        int content_length = strlen(uptime_str);
        
        // Złożenie nagłówków wraz z wymaganą pustą linią na końcu (\r\n\r\n)
        snprintf(response_headers, sizeof(response_headers), 
                 "%sContent-Length: %d\r\n\r\n", http_header, content_length);

        if (send(client_fd, response_headers, strlen(response_headers), 0) < 0) {
            perror("Błąd: send() dla nagłówków");
        }

        // d) send() - Wysłanie ciała odpowiedzi (uptime)
        if (send(client_fd, uptime_str, content_length, 0) < 0) {
            perror("Błąd: send() dla ciała odpowiedzi");
        }

        // e) shutdown() - Zablokowanie wysyłania (klient dowie się, że to koniec danych)
        if (shutdown(client_fd, SHUT_WR) < 0) {
            perror("Błąd: shutdown()");
        }

        // f) close() dla połączenia
        if (close(client_fd) < 0) {
            perror("Błąd: close() dla klienta");
        }
    }

    // g) Zamknięcie głównego gniazda serwera (nigdy tu nie dojdzie przez pętlę nieskończoną, ale dla zasady)
    if (close(server_fd) < 0) {
        error_exit("Błąd: close() dla serwera");
    }

    return 0;
}