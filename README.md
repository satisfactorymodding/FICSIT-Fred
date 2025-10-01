# FICSIT-Fred

A Discord bot for the Satisfactory Modding Discord

---

## Development

Want to contribute to Fred? Here's everything you need to know to get started.

### Prerequisites

#### A Discord token

First of all, you'll need a Discord bot token for Fred to connect to Discord with.
To get one, you can go to <https://discord.com/developers/applications>, register a new application, add a bot to the
application and **activate the "Message Content" and the "Server Members" intents**.
These intents are needed to receive the content of messages and receive member join events.

#### Docker

Docker is for making containers. If you're not sure what that means, look it up it's real cool! In our case, it helps
use set up all needed dependencies for Fred without you needing to do anything other than install Docker.
You can get docker [here](https://docs.docker.com/engine/install/). For Linux, make sure to **not** use Docker Desktop.
For Windows, it is the easiest way.
If you don't want to install Docker (especially on Windows where Docker Desktop can take up resources and requires
virtualization to be enabled), you can also manually set up a PostgreSQL DB and configure Fred to point to it. 

---

### Setup

Two choices here: All through docker or hybrid local/docker.
We recommend the hybrid way for ease of development. We don't have a proper devcontainer setup so debugging Fred when
running in Docker is not great.
Instead, in a hybrid setup, you'll use Docker for the Postgres DB only and run Fred locally using Poetry.

#### Docker-only

Run `FRED_TOKEN=<your_token> docker compose up -d` and that's it! Fred should run.
(Note: This command assumes you're using bash as your shell. For Powershell or other, set the environment variable
differently. You can also use a `.env` file.).

You can verify that the database was properly created and manage it by going to <http://localhost:8080> where pgadmin
should show.
You can use `fred@fred.com` for the user and `fred` for the password. All of this is customizable in
`docker-compose.yml`.

#### Hybrid

For this, you'll need [poetry](https://python-poetry.org/).

**Make sure you are using a compatible version of python, or Fred will not build!** 
You can find the version requirements in the [`pyproject.toml`](pyproject.toml).
We recommend the use of [pyenv](https://github.com/pyenv/pyenv) to install the best version.

Create a virtual environment with `poetry env use`, using the python version mentioned above. Then run`poetry install`.
This should create a `.venv` folder that contains the virtualenv with all the necessary packages. 
Activate it using the script pointed to by `poetry env activate`.

Now, run `docker compose -f docker-compose-deps.yml up -d`. This should spin up the postgres DB.
You can verify that the database was properly created and manage it by going to <http://localhost:8080> where pgadmin
should show.
The default pgadmin credentials are `fred@fred.com` for the user and `fred` for the password. You can change these and more in your
[`docker-compose-deps.yml`](docker-compose-deps.yml).

Almost there! You'll now have to configure Fred. This just means setting the following env vars (found in
[`fred/__init__.py`](fred/__init__.py)).

```sh
FRED_IP
FRED_PORT
FRED_TOKEN
FRED_SQL_DB
FRED_SQL_USER
FRED_SQL_PASSWORD
FRED_SQL_HOST
FRED_SQL_PORT
```

For convenience, an `example.env` file is included. If you copy this into your `.env`, Fred will load them
automatically. It includes defaults that will work with the config of the docker-compose-deps.yml. You'll only have to
set `FRED_TOKEN` and maybe change the others if the defaults don't suit you.

Finally, run `python -m fred` or `poetry run fred`. You can now adapt this to your setup and run the
script from your IDE instead. Don't forget to use the virtualenv python!

---

## Thanks

This project is maintained by Feyko and Borketh, with contributions from the Satisfactory Modding dev team.
Thank you to everyone who has written code for this project!