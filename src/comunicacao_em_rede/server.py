import socket
import threading

HOST = "0.0.0.0" # Aceita conexão de qualquer IP da rede
PORT = 5000 # Porta para testes

clients = [] # Guarda todos os sockets dos usuarios conectados

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Socket do servidor TCP/IPv4
server.bind((HOST, PORT)) # Conecta o socket ao IP e porta
server.listen() # Deixa o servidor em aguardo de conexoes

print("Servidor iniciado")
print("Aguardando conexões...")


# Envia a mensagem a todos os usuarios conectados
def broadcast(message, sender):
    for client in clients:
        if client != sender:
            try:
                client.send(message)
            except:
                clients.remove(client) # Se o usuario desconectou, remove ele da lista


# Tratamento de usuarios
def handleClient(client):
    while True: # Mantem o usuario ativo enquanto conectado
        try: # Recebe dados enviados pelo usuario e distribui a mensagem para os outros usuarios
            message = client.recv(1024) # (1024) = Tamanho do buffer
            if not message: break # Evita erros ao desconectar
            broadcast(message, client)
        except: # Tratamento de desconexão
            clients.remove(client)
            client.close()
            break


def receiveConnections(): # Função para receber conexões
    while True: # O servidor permanece esperando novos usuarios
        client, address = server.accept()
        print(f"Conectado com {address}")

        clients.append(client) # Adiciona o cliente conectado à lista de usuarios

        thread = threading.Thread(target=handleClient, args=(client,)) # Thread para cada cliente rodar em paralelo
        thread.start()

receiveConnections() # Inicializa
