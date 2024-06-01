# Square Cloud Manager

## Translations

- [Português](README-pt-BR.md)

Square Cloud Manager is a bot for Discord that allows you to manage your applications hosted on [Square Cloud](https://squarecloud.app/).

## Requirements

- [Python 3.10^](https://python.org)
- [Git](https://git-scm.com/)

## Setup

Follow the steps below to setup.

- Clone the repo.

```bash
git clone https://github.com/Joab0/squarecloud-manager
cd squarecloud-manager
```

- Install dependencies.

```bash
pip install -r requirements.txt
```

- Rename the [.env.example](.env.example) file to `.env`.

- open the `.env` file and make the necessary changes.

- Run the bot.

```bash
python launcher.py
```

## Usage

After configuring and launching the bot, you can now use it. To get started, open Discord and use the `/login` command to setup your API key, which can be obtained from the [Square Cloud dashboard](https://squarecloud.app/dashboard/account). After authenticating, you will be able to use the bot fully. Use `/help` to see the list of available commands.
> [!TIP]
> To host this bot on Square Cloud, use the `/host` command and it will be hosted automatically.

## License

MIT
