# Ferramenta de Comunicação em Rede

Aplicação de chat em rede local desenvolvida em Python utilizando
TCP/IP. O projeto permite a comunicação entre múltiplos usuários na
mesma LAN, com suporte a troca de mensagens e arquivos.

## Visão Geral

O sistema oferece três formas principais de uso:

-   Interface web acessível pelo navegador
-   Interface desktop nativa via `pywebview` (Windows e Linux)
-   Modo terminal com cliente e servidor TCP

Além disso, inclui descoberta automática de servidores via UDP
broadcast, permitindo conexão sem necessidade de informar IP
manualmente.

------------------------------------------------------------------------

## Funcionalidades

-   Chat multi-cliente via TCP
-   Identificação de mensagens por usuário e horário
-   Envio e recebimento de arquivos (Base64)
-   Download de arquivos pela interface web
-   Descoberta automática de servidores na rede local (UDP broadcast)
-   Interface web responsiva
-   Interface desktop multiplataforma (pywebview)
-   Cliente automático que cria ou encontra salas
-   Protocolo próprio baseado em JSON com delimitação por tamanho

------------------------------------------------------------------------

## Estrutura do Projeto

    .
    |-- README.md
    |-- LICENSE
    |-- requirements.txt
    `-- src
        |-- auto_chat.py
        |-- client.py
        |-- discovery.py
        |-- gui_chat.py
        |-- protocol.py
        |-- server.py
        `-- frontend
            |-- app.css
            |-- app.js
            `-- index.html

------------------------------------------------------------------------

## Descrição dos Componentes

### Servidor

**`src/server.py`**\
Servidor TCP responsável por gerenciar conexões, usuários e retransmitir
mensagens e arquivos.

### Cliente Terminal

**`src/client.py`**\
Cliente manual que se conecta a um servidor conhecido.

**`src/auto_chat.py`**\
Cliente automático que: - Procura uma sala na rede - Cria uma nova se
nenhuma for encontrada

### Interface Gráfica

**`src/gui_chat.py`**\
Responsável por: - Servir a interface web local - Gerenciar endpoints
HTTP - Integrar com `pywebview` para modo nativo

### Descoberta de Rede

**`src/discovery.py`**\
Implementa descoberta automática via UDP broadcast.

### Protocolo

**`src/protocol.py`**\
Define o protocolo de comunicação: - JSON codificado em UTF-8 - Prefixo
de 4 bytes indicando tamanho

### Frontend

**`src/frontend/`** - HTML: estrutura da interface - CSS: estilo -
JavaScript: comunicação com backend e renderização

------------------------------------------------------------------------

## Requisitos

-   Python 3.10 ou superior
-   Rede local compartilhada
-   Portas abertas:
    -   TCP: `5050`
    -   UDP: `5052`
    -   HTTP local: `8080`

### Dependências

    pywebview>=5.0

Observação:\
O modo terminal e web funcionam apenas com a biblioteca padrão do
Python.

------------------------------------------------------------------------

## Instalação

``` bash
git clone <repositorio>
cd Ferramenta-Comunicacao-em-Rede
```

### (Opcional) Ambiente virtual

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### Instalar dependências

``` bash
pip install -r requirements.txt
```

No Windows:

``` bash
py -m pip install -r requirements.txt
```

------------------------------------------------------------------------

## Compatibilidade

-   Windows e Linux suportados
-   Interface baseada em navegador como fallback
-   Interface nativa disponível via `pywebview`

------------------------------------------------------------------------

## Modos de Uso

### 1. Interface Web (Recomendado)

``` bash
python src/gui_chat.py --web
```

Acesse:

    http://127.0.0.1:8080

#### Fluxo:

1.  Inserir nome de usuário
2.  Entrar na sala
3.  Sistema:
    -   Conecta automaticamente a uma sala existente
    -   Ou cria uma nova

------------------------------------------------------------------------

### 2. Interface Desktop

``` bash
python src/gui_chat.py
```

Forçar modo:

``` bash
--native   # janela nativa
--web      # navegador
```

------------------------------------------------------------------------

### 3. Terminal Automático

``` bash
python src/auto_chat.py --username SEU_NOME
```

Comandos:

    /file caminho_do_arquivo
    /quit

------------------------------------------------------------------------

### 4. Terminal Manual

#### Iniciar servidor

``` bash
python src/server.py
```

#### Conectar cliente

``` bash
python src/client.py IP --username NOME
```

------------------------------------------------------------------------

## Configurações Importantes

### Portas

  Porta   Protocolo   Uso
  ------- ----------- ------------
  5050    TCP         Chat
  5052    UDP         Descoberta
  8080    HTTP        Interface

------------------------------------------------------------------------

## Protocolo de Comunicação

Formato:

    [4 bytes tamanho][JSON UTF-8]

### Tipos de mensagens

-   `join`
-   `message`
-   `file`
-   `system`
-   `error`
-   `ping` / `pong`
-   `status`

Tamanho máximo: **64 MB**

------------------------------------------------------------------------

## Descoberta Automática

Fluxo:

1.  Cliente envia `DISCOVER` via UDP
2.  Servidor responde `OFFER`
3.  Cliente conecta via TCP

Identificador:

    CHAT_TCP_LAN_DISCOVERY_V1

------------------------------------------------------------------------

## API Local (Interface Web)

  Método   Endpoint         Função
  -------- ---------------- -------------------
  GET      `/`              HTML
  GET      `/app.css`       CSS
  GET      `/app.js`        JS
  GET      `/events`        Stream de eventos
  POST     `/api/start`     Iniciar sessão
  POST     `/api/message`   Enviar mensagem
  POST     `/api/file`      Enviar arquivo
  POST     `/api/stop`      Encerrar sessão

------------------------------------------------------------------------

## Exemplos

### Dois usuários no mesmo PC

``` bash
python src/server.py
python src/client.py 127.0.0.1 --username ana
python src/client.py 127.0.0.1 --username bruno
```

------------------------------------------------------------------------

### Sala automática via navegador

``` bash
python src/gui_chat.py --web
```

------------------------------------------------------------------------

### Sala automática via terminal

``` bash
python src/auto_chat.py --username usuario
```

------------------------------------------------------------------------

## Solução de Problemas

### Connection refused

-   Servidor não está rodando
-   Porta incorreta
-   Firewall bloqueando

------------------------------------------------------------------------

### Descoberta não funciona

-   UDP bloqueado
-   Rede isolada

Solução: - Usar modo manual

------------------------------------------------------------------------

### Interface abre, mas não conecta

-   Verificar:
    -   Mesma rede
    -   Porta TCP liberada

------------------------------------------------------------------------

### Porta em uso

Alterar via parâmetros:

``` bash
--ui-port
--chat-port
--discovery-port
```

------------------------------------------------------------------------

## Licença

Consulte o arquivo `LICENSE` do repositório.
