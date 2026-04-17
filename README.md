# Ferramenta de Comunicacao em Rede

Aplicacao de chat em rede local desenvolvida em Python usando TCP/IP. O projeto permite que dois ou mais usuarios troquem mensagens e arquivos dentro da mesma LAN, com tres formas principais de uso:

- interface visual multiplataforma pelo navegador local;
- interface nativa de desktop baseada em GTK/WebKit no Linux;
- modo terminal, com servidor e cliente TCP tradicionais.

O codigo tambem inclui descoberta automatica por UDP broadcast. Com isso, no modo automatico, o primeiro computador que abrir a sala vira o servidor TCP e os outros computadores encontram essa sala sem precisar digitar o IP manualmente.

## Funcionalidades

- Chat multi-cliente por TCP.
- Suporte a varios usuarios conectados ao mesmo servidor.
- Mensagens identificadas por usuario e horario.
- Envio de arquivos codificados em Base64.
- Recebimento de arquivos pelo terminal na pasta `downloads/`.
- Download de arquivos diretamente pela interface web.
- Descoberta automatica de sala na rede local usando UDP broadcast.
- Interface web responsiva com tela de entrada, tela de conexao e tela de chat.
- Interface visual que reaproveita o mesmo HTML, CSS e JavaScript no Linux e no Windows.
- Interface nativa GTK/WebKit opcional no Linux.
- Cliente automatico para terminal, que procura uma sala existente ou hospeda uma nova.
- Protocolo proprio simples baseado em JSON com prefixo de tamanho para preservar os limites das mensagens TCP.

## Estrutura do projeto

```text
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
```

### Arquivos principais

`src/server.py`
: Servidor TCP central. Aceita varios clientes, controla nomes de usuario, recebe mensagens e arquivos e retransmite os pacotes para os participantes conectados.

`src/client.py`
: Cliente de terminal. Conecta em um servidor TCP conhecido, envia mensagens digitadas pelo usuario e permite enviar arquivos com o comando `/file`.

`src/auto_chat.py`
: Cliente automatico de terminal. Primeiro procura uma sala ativa na rede local. Se encontrar, conecta nela. Se nao encontrar, inicia um servidor TCP local, anuncia a sala por UDP e conecta o proprio usuario.

`src/gui_chat.py`
: Modo grafico e modo web. Sobe um pequeno servidor HTTP local para servir o frontend e expor endpoints de controle do chat. Tambem pode abrir a interface em uma janela nativa com GTK/WebKit.

`src/discovery.py`
: Descoberta automatica por UDP broadcast. Usa uma porta UDP para procurar servidores e responder com o endereco da sala TCP.

`src/protocol.py`
: Camada de protocolo usada sobre TCP. Cada pacote e um objeto JSON UTF-8 precedido por 4 bytes informando o tamanho da carga.

`src/frontend/`
: Interface visual do chat. O HTML define as telas, o CSS define o layout e o JavaScript chama a API local, abre o fluxo de eventos e renderiza mensagens e arquivos.

## Requisitos

- Python 3.10 ou superior recomendado.
- Computadores na mesma rede local para comunicacao entre maquinas.
- Porta TCP `5050` liberada para o chat, por padrao.
- Porta UDP `5052` liberada para descoberta automatica, por padrao.
- Para o modo web: navegador moderno.
- Para o modo nativo desktop no Linux: GTK 3, WebKit2GTK e PyGObject.
- Para Windows: Python 3.10 ou superior e navegador moderno.

O arquivo `requirements.txt` declara:

```text
PyGObject; platform_system == "Linux"
```

Essa dependencia e necessaria para a janela nativa no Linux. O modo terminal e o modo web usam apenas bibliotecas da biblioteca padrao do Python.
No Windows, essa dependencia e ignorada automaticamente pelo marcador `platform_system == "Linux"`.

Em distribuicoes baseadas em Debian/Ubuntu, as dependencias nativas geralmente podem ser instaladas com:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1
```

Se o pacote `gir1.2-webkit2-4.1` nao existir na sua distribuicao, verifique o pacote WebKit2GTK equivalente disponivel nela.

## Instalacao

Clone ou baixe o projeto e entre na pasta:

```bash
cd Ferramenta-Comunicacao-em-Rede
```

Opcionalmente, crie um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependencias Python declaradas:

```bash
pip install -r requirements.txt
```

Observacao: se voce for usar apenas terminal ou web no navegador, o projeto consegue funcionar sem PyGObject. Se a instalacao do PyGObject falhar, instale primeiro as bibliotecas GTK/WebKit do sistema ou use o modo `--web`.

No Windows, use o inicializador `py` se o comando `python` nao estiver configurado:

```powershell
py -m pip install -r requirements.txt
```

## Compatibilidade Linux e Windows

A estrategia de compatibilidade e manter a interface principal como uma aplicacao web local servida pelo proprio Python. O chat continua usando TCP/UDP da biblioteca padrao, e a tela visual roda no navegador padrao do sistema.

Com isso:

- Linux pode usar a janela nativa GTK/WebKit quando as bibliotecas estiverem instaladas.
- Linux sem GTK/WebKit abre automaticamente a interface no navegador.
- Windows abre automaticamente a interface no navegador, sem tentar carregar GTK/WebKit.
- O terminal continua disponivel nos dois sistemas usando os mesmos scripts Python.

O comando principal para uso visual multiplataforma e:

```bash
python src/gui_chat.py
```

No Windows, se necessario:

```powershell
py src\gui_chat.py
```

Para forcar o navegador em qualquer sistema:

```bash
python src/gui_chat.py --web
```

Para exigir a janela nativa no Linux:

```bash
python src/gui_chat.py --native
```

## Uso Pela Interface Web

Este e o modo mais simples para usar com interface visual. Ele abre a mesma tela do chat no navegador.

Execute:

```bash
python3 src/gui_chat.py --web
```

No Windows:

```powershell
py src\gui_chat.py --web
```

Por padrao, o programa sobe uma interface local em:

```text
http://127.0.0.1:8080
```

Se o navegador nao abrir automaticamente, acesse esse endereco manualmente.

### Como entrar no chat pela web

1. Execute `python3 src/gui_chat.py --web`.
2. Digite um nome de usuario no campo `Username`.
3. Clique em `Join`.
4. O programa procura uma sala na rede local.
5. Se encontrar uma sala, conecta automaticamente.
6. Se nao encontrar, este computador passa a hospedar uma nova sala.
7. Digite mensagens no campo inferior e clique em `Send`.
8. Use o botao `+` para escolher e enviar um arquivo.
9. Use o botao `x` no topo para sair da sala.

### Usar em varias maquinas pela web

Em cada computador da mesma rede local, execute:

```bash
python3 src/gui_chat.py --web
```

O primeiro computador que nao encontrar sala ativa inicia o servidor TCP automaticamente. Os proximos computadores devem encontrar essa sala pela descoberta UDP e conectar nela.

Caso a descoberta automatica nao funcione por causa de firewall, isolamento de rede ou bloqueio de broadcast, use o modo manual com `server.py` e `client.py`, explicado mais abaixo.

### Opcoes uteis do modo web

Usar outra porta para a interface HTTP local:

```bash
python3 src/gui_chat.py --web --ui-port 9090
```

Subir a interface sem abrir o navegador automaticamente:

```bash
python3 src/gui_chat.py --web --no-browser
```

Alterar a porta TCP do chat:

```bash
python3 src/gui_chat.py --web --chat-port 6060
```

Alterar a porta UDP de descoberta:

```bash
python3 src/gui_chat.py --web --discovery-port 6062
```

Alterar o nome anunciado da sala quando este computador hospedar:

```bash
python3 src/gui_chat.py --web --server-name "Sala da Turma"
```

## Uso Pelo Aplicativo Visual

O modo padrao escolhe automaticamente como abrir a interface. No Linux com GTK/WebKit instalado, ele abre uma janela desktop. No Windows, ou em Linux sem GTK/WebKit, ele abre a mesma interface no navegador local.

```bash
python src/gui_chat.py
```

No Windows:

```powershell
py src\gui_chat.py
```

O programa cria um servidor HTTP local em `127.0.0.1:8080` e usa a mesma interface HTML/CSS/JavaScript nos dois sistemas.

Para forcar a janela nativa no Linux:

```bash
python3 src/gui_chat.py --native
```

Se as bibliotecas GTK/WebKit nao estiverem instaladas, o script exibe uma mensagem parecida com:

```text
GTK WebKit2 is not available. Falling back to the browser interface.
```

Nesse caso, sem `--native`, o programa cai automaticamente para o navegador. Com `--native`, instale as dependencias nativas ou use:

```bash
python3 src/gui_chat.py --web
```

As opcoes de porta e descoberta tambem funcionam no modo nativo:

```bash
python3 src/gui_chat.py --ui-port 9090 --chat-port 6060 --discovery-port 6062
```

## Uso Automatico Pelo Terminal

O modo automatico de terminal nao usa interface grafica. Ele procura uma sala na LAN e, se nao encontrar, hospeda uma nova sala automaticamente.

Em cada computador, execute:

```bash
python3 src/auto_chat.py --username SEU_NOME
```

Exemplo:

```bash
python3 src/auto_chat.py --username maria
```

Fluxo de funcionamento:

1. O programa envia uma mensagem UDP de descoberta na rede local.
2. Se algum servidor responder, o cliente conecta no endereco informado.
3. Se nenhum servidor responder, o proprio computador inicia um servidor TCP em `0.0.0.0:5050`.
4. Esse computador passa a responder as descobertas UDP na porta `5052`.
5. O usuario entra no chat pelo cliente de terminal.

Comandos dentro do cliente de terminal:

```text
/file CAMINHO_DO_ARQUIVO
/quit
```

Exemplo de envio de arquivo:

```text
/file ./documento.pdf
```

Arquivos recebidos no terminal sao salvos em:

```text
downloads/
```

O nome do arquivo recebido inclui o nome do usuario remetente. Se ja existir um arquivo com o mesmo nome, o cliente cria uma variacao com sufixo numerico.

## Uso Manual Pelo Terminal

O modo manual e util quando voce quer controlar exatamente qual maquina sera o servidor ou quando a descoberta automatica por UDP nao funciona na rede.

### 1. Iniciar o servidor

No computador que sera o servidor:

```bash
python3 src/server.py
```

Por padrao, o servidor escuta em:

```text
0.0.0.0:5050
```

Isso significa que ele aceita conexoes vindas de outras maquinas da rede, desde que firewall e roteador permitam.

Para escolher outra porta:

```bash
python3 src/server.py --port 6060
```

Para escolher uma interface especifica:

```bash
python3 src/server.py --host 192.168.1.10 --port 5050
```

### 2. Descobrir o IP do servidor

No computador servidor, descubra o IP da rede local. Em Linux, comandos comuns sao:

```bash
hostname -I
```

ou:

```bash
ip addr
```

Use o IP da interface conectada a mesma rede dos outros computadores, por exemplo `192.168.1.10`.

### 3. Conectar clientes

Em cada computador cliente:

```bash
python3 src/client.py IP_DO_SERVIDOR --username SEU_NOME
```

Exemplo:

```bash
python3 src/client.py 192.168.1.10 --username joao
```

Se o servidor estiver usando outra porta:

```bash
python3 src/client.py 192.168.1.10 --port 6060 --username joao
```

### 4. Usar o chat no terminal

Digite uma mensagem e pressione Enter para enviar.

Enviar arquivo:

```text
/file ./imagem.png
```

Sair:

```text
/quit
```

Tambem e possivel encerrar com `Ctrl+C`.

## Portas e Comunicacao

| Porta | Protocolo | Uso |
| --- | --- | --- |
| `5050` | TCP | Chat principal: entrada de clientes, mensagens e arquivos |
| `5052` | UDP | Descoberta automatica de salas na rede local |
| `8080` | HTTP local | Interface web servida pelo `gui_chat.py` |

Esses valores sao padrao e podem ser alterados por argumentos de linha de comando.

Importante: a porta `8080` serve apenas a interface local da aplicacao. A comunicacao real entre usuarios acontece pelo servidor TCP do chat.

## Como o Protocolo Funciona

O chat usa TCP, que entrega um fluxo continuo de bytes. Como TCP nao separa mensagens automaticamente, o arquivo `protocol.py` implementa enquadramento de pacotes.

Cada pacote enviado tem:

1. Cabecalho de 4 bytes em ordem de rede, representando o tamanho do JSON.
2. Conteudo JSON codificado em UTF-8.

Exemplo conceitual de pacote de mensagem:

```json
{
  "type": "message",
  "text": "Ola"
}
```

O servidor retransmite a mensagem com metadados:

```json
{
  "type": "message",
  "timestamp": "2026-04-17 14:30:00",
  "from": "maria",
  "text": "Ola"
}
```

Tipos de pacote usados:

| Tipo | Origem | Descricao |
| --- | --- | --- |
| `join` | cliente | Primeiro pacote enviado ao servidor, contendo o nome do usuario |
| `message` | cliente/servidor | Mensagem de texto |
| `file` | cliente/servidor | Arquivo com nome e dados em Base64 |
| `system` | servidor | Avisos como entrada e saida de usuarios |
| `error` | servidor/interface | Erros de protocolo, conexao ou validacao |
| `ping` | cliente | Pacote de teste |
| `pong` | servidor | Resposta ao `ping` |
| `status` | interface local | Status interno usado pelo modo web/nativo |

O tamanho maximo configurado para um pacote e `64 MB`, definido em `MAX_PACKET_SIZE` no `protocol.py`.

## Como a Descoberta Automatica Funciona

A descoberta automatica nao substitui o TCP. Ela apenas encontra o servidor.

Quando um cliente automatico inicia:

1. Envia via UDP broadcast uma mensagem `DISCOVER` para a porta `5052`.
2. Um computador que esteja hospedando responde com `OFFER`.
3. A resposta informa o nome da sala e a porta TCP do chat.
4. O cliente conecta no IP de origem dessa resposta usando TCP.

O identificador usado para evitar confusao com outros pacotes UDP e:

```text
CHAT_TCP_LAN_DISCOVERY_V1
```

Se a rede bloquear broadcast UDP, a descoberta pode falhar mesmo com o servidor funcionando. Nesse caso, use o modo manual informando o IP do servidor.

## API Local Usada Pela Interface Web

O arquivo `gui_chat.py` cria um servidor HTTP local com endpoints usados pelo JavaScript do frontend.

| Metodo | Caminho | Funcao |
| --- | --- | --- |
| `GET` | `/` | Serve `index.html` |
| `GET` | `/app.css` | Serve os estilos |
| `GET` | `/app.js` | Serve o JavaScript |
| `GET` | `/events` | Abre fluxo Server-Sent Events com mensagens do chat |
| `POST` | `/api/start` | Inicia a sessao com o nome de usuario |
| `POST` | `/api/message` | Envia uma mensagem de texto |
| `POST` | `/api/file` | Envia arquivo em Base64 |
| `POST` | `/api/stop` | Encerra a sessao local |

Essa API foi feita para uso local pela propria interface, nao como API publica exposta na internet.

## Exemplos de Execucao

### Dois usuarios no mesmo computador

Terminal 1:

```bash
python3 src/server.py
```

Terminal 2:

```bash
python3 src/client.py 127.0.0.1 --username ana
```

Terminal 3:

```bash
python3 src/client.py 127.0.0.1 --username bruno
```

### Uma sala automatica com interface web

Em cada computador:

```bash
python3 src/gui_chat.py --web
```

Depois, cada usuario entra pelo navegador usando um nome diferente.

### Uma sala automatica no terminal

Em cada computador:

```bash
python3 src/auto_chat.py --username nome_do_usuario
```

## Solucao de Problemas

### `Connection refused`

O cliente tentou conectar, mas nao encontrou servidor naquela porta.

Verifique:

- se `server.py`, `auto_chat.py` ou `gui_chat.py` esta rodando em alguma maquina;
- se o IP informado esta correto;
- se a porta TCP e a mesma no servidor e no cliente;
- se o firewall permite conexoes na porta usada.

### A interface web abre, mas ninguem conecta entre maquinas

A interface HTTP em `127.0.0.1:8080` e local de cada computador. Para conversar entre maquinas, os computadores precisam estar na mesma LAN e conseguir acessar a porta TCP do chat.

Verifique:

- firewall da porta TCP `5050`;
- se os computadores estao na mesma rede;
- se redes de convidados ou corporativas bloqueiam comunicacao entre clientes;
- se todos estao usando a mesma porta de chat.

### Descoberta automatica nao encontra a sala

A descoberta usa UDP broadcast na porta `5052`. Algumas redes bloqueiam broadcast.

Solucoes:

- liberar UDP `5052` no firewall;
- executar todos na mesma sub-rede;
- usar o modo manual com `server.py` e `client.py`;
- informar portas iguais em todos os computadores com `--discovery-port`.

### Modo nativo nao abre

Instale GTK/WebKit2 ou use o navegador:

```bash
python3 src/gui_chat.py --web
```

### Porta ja esta em uso

Altere a porta.

Para a interface:

```bash
python3 src/gui_chat.py --web --ui-port 9090
```

Para o chat:

```bash
python3 src/gui_chat.py --web --chat-port 6060
```

No modo manual, servidor e cliente precisam usar a mesma porta:

```bash
python3 src/server.py --port 6060
python3 src/client.py 192.168.1.10 --port 6060 --username ana
```

## Licenca

Consulte o arquivo `LICENSE` deste repositorio.
