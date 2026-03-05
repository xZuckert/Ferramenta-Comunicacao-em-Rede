import socket
import threading

HOST = input("Digite o IP do servidor: ")
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Cria o socket TCP/IPv4 do usuario
client.connect((HOST, PORT)) # Conecta o usuario ao server

name = input("Digite seu nome: ") # Define o nome do usuario


def receive(): # Função para receber as mensagens do chat
    while True:
        try:
            message = client.recv(1024).decode() # Transforma bytes em texto
            print(message)
        except:
            print("Erro na conexão")
            client.close()
            break


def write(): # Envia mensagnes para o chat
    while True:
        msg = input("")

        if msg.strip() == "":
            continue

        message = f"{name}: {msg}"
        client.send(message.encode()) # Transforma texto em bytes


threadReceive = threading.Thread(target=receive) # Thread para receber mensagens sem bloquear o envio
threadReceive.start()

threadWrite = threading.Thread(target=write) # Thread para enviar mensagens ao mesmo tempo
threadWrite.start()
