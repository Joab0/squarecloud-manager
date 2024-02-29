# Square Cloud Manager

O Square Cloud Manager é um bot para Discord que permtie gerenciar suas aplicações hospedadas na [Square Cloud](https://squarecloud.app/).

## Requisitos

- [Python 3.10^](https://python.org)
- [Git](https://git-scm.com/)

## Instalação

Siga os passoas abaixo para fazer a instalação.

1. Clone o repositório.

```bash
git clone https://github.com/Joab0/squarecloud-manager
cd squarecloud-manager
```

- Instale as dependências.

```bash
pip install -r requirements.txt
```

- Renomeie o arquivo [.env.example](.env.example) para `.env`.

- Abra o arquivo `.env` e faça as devidas alterações.

- Rode o bot.

```bash
python launcher.py
```

## Comandos

- **/help:** Comando de ajuda do bot.
- **/ping:** Comando para testar a conexão com o Discord.
- **/statistics:** Comando para mostar as estatísticas do serviço.
- **/login:** Comando para definir a chave de API.
- **/apps:** Comando para gerenciar as aplicações.
- **/up:** Comando para enviar uma aplicação para a Square Cloud.

## Licença

MIT
