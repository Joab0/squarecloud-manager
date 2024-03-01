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

## Utilização

Após configurar e iniciar o bot, você já poderá utilizá-lo. Para começar, abra o Discord e utilize o comando `/login` para inserir sua chave da API, que pode ser obtida na [dashboard da Square Cloud](https://squarecloud.app/dashboard/account). Depois de se autenticar, você já poderá utilizar o bot por completo. Use `/ajuda` para ver a lista de comandos disponíveis.

## Licença

MIT
