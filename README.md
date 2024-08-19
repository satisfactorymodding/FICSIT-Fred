# FICSIT-Fred

A Discord bot for the Satisfactory Modding Discord

## Development

Want to contribute to Fred? Here's everything you need to know to get started.

### Prerequisites

#### A Discord token

First of all, you'll need a Discord bot token for Fred to connect to Discord with.
To get one, you can go to <https://discord.com/developers/applications>, register a new application, add a bot to the application and **activate the "message content intent" and the "server members intent"**.
These intents are needed to receive the content of messages and receive member join events.

#### Docker

Docker is for making containers. If you're not sure what that means, look it up it's real cool! In our case, it helps use set up all needed dependencies for Fred without you needing to do anything other than install Docker.
You can get docker [here](https://docs.docker.com/engine/install/). For Linux, make sure to **not** use Docker Desktop. For Windows, it is the easiest way.
If you don't want to install Docker (especially on Windows where Docker Desktop can take up resources and requires virtualisation to be enabled), you can also manually set up a PostgreSQL DB and configure Fred to point to it. More on that later.

#### (Optional) Dialogflow auth

This is optional because this feature is currently disabled in Fred.
You'll have get authentication information for dialogflow if you want to work on that.

### Setup

Two choices here: All through docker or hybrid local/docker.
I recommend the hybrid way for ease of development. We don't have a proper devcontainer setup so debugging Fred when running in Docker is not great.
Instead, in a hybrid setup, you'll use Docker for the postgres DB only and run Fred locally using Poetry.

#### Docker-only

Run `FRED_TOKEN=<your_token> docker compose up -d` and that's it! Fred should run.
(Note: This command assumes you're using bash as your shell. For Powershell or other, set the environment variable differently. You can also use a `.env` file.).

You can verify that the database was properly created and manage it by going to <http://localhost:8080> where pgadmin should show.
You can use `fred@fred.com` for the user and `fred` for the password. All of this is customizable in `docker-compose.yml`.

#### Hybrid

For this, you'll need [poetry](https://python-poetry.org/) installed.

Once Poetry is installed, run `poetry install`. This should create a `.venv` folder that contains the virtualenv with all the necessary packages. Activate it using `poetry shell` or manually.

Now, run `docker compose up -d -f docker-compose-deps.yml`. This should spin up the postgres DB.
You can verify that the database was properly created and manage it by going to <http://localhost:8080> where pgadmin should show.
You can use `fred@fred.com` for the user and `fred` for the password. All of this is customizable in `docker-compose-deps.yml`.

Almost there! You'll now have to configure Fred. This just means setting the following env vars (found in `fred/__main__.py`).

```sh
"FRED_IP",
"FRED_PORT",
"FRED_TOKEN",
"FRED_SQL_DB",
"FRED_SQL_USER",
"FRED_SQL_PASSWORD",
"FRED_SQL_HOST",
"FRED_SQL_PORT",
```

For convenience, an `example.env` file is included. If you copy this into your `.env`, Fred will load them automatically. It includes defaults that will work with the config of the docker-compose-deps.yml. You'll only have to set `FRED_TOKEN` and maybe change the others if the defaults don't suit you.

Finally, run `python -m fred` or `poetry run fred`. Fred should run! You can now adapt this to your setup and run the script from your IDE instead. Don't forget to use the virtualenv python!

## Thanks

Massive thanks to Borketh, Mircea and everyone else that has contributed!
