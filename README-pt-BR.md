# Square Cloud Manager

## Traduções

- [English](README.md)

Square Cloud Manager é um bot para Discord que permite gerenciar suas aplicações hospedadas na [Square Cloud](https://squarecloud.app/).

## Requisitos

- [Python 3.10^](https://python.org)
- [Git](https://git-scm.com/)
- [Rich](https://github.com/Textualize/rich/) (opicional)

## Instalação

Siga as etapas abaixo para fazer a instalação.

- Clone o repositório.

```bash
git clone https://github.com/Joab0/squarecloud-manager
cd squarecloud-manager
```

- Insale as dependências.

```bash
pip install -r requirements.txt
```

- Renomeie o arquivo [.env.example](.env.example) para `.env`.

- Abra o arquivo `.env` e faça as devidas alterações.

- Rode o bot.

```bash
python launcher.py
```

## Usage

Depois de configurar e iniciar o bot, você já pode usá-lo. Para começar, abra o Discord e use o comando `/login` para configurar sua chave de API, que pode ser obtida na [dashboard da Square Cloud](https://squarecloud.app/dashboard/account). Após a autenticação, você poderá usar o bot por completo. Use `/ajuda` para ver a lista de comandos disponíveis.
> [!TIP]
> Para hospedar este bot no Square Cloud, use o comando `/host` e ele será hospedado automaticamente.

## Licença

MIT
