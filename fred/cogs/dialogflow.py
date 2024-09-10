import asyncio
import json
import uuid
from os import getenv

import nextcord
from google.cloud import dialogflow
from google.oauth2 import service_account
from nextcord import Message

from .. import config
from ..libraries import common

if env_auth_str := getenv("DIALOGFLOW_AUTH"):
    DIALOGFLOW_AUTH = json.loads(env_auth_str)
    session_client = dialogflow.SessionsClient(
        credentials=service_account.Credentials.from_service_account_info(DIALOGFLOW_AUTH)
    )
    DIALOGFLOW_PROJECT_ID = DIALOGFLOW_AUTH["project_id"]
    SESSION_LIFETIME = 10 * 60  # 10 minutes to avoid repeated false positives
else:
    DIALOGFLOW_AUTH = None
    session_client = None
    DIALOGFLOW_PROJECT_ID = None


class DialogFlow(common.FredCog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_ids = {}

    async def process_message(self, message: Message):
        self.bot.logger.info("Processing NLP")
        if message.content.startswith(self.bot.command_prefix):
            return
        if not message.content:
            self.logger.info("Ignoring a message because it was empty", extra=common.user_info(message.author))
            return
        if isinstance(message.author, nextcord.User):
            # We're in a DM channel
            self.logger.info("Ignoring a message because it is in a DM channel", extra=common.message_info(message))
            return
        if not config.Misc.fetch("dialogflow_state") or DIALOGFLOW_AUTH is None:
            self.logger.info(
                "Ignoring a message because NLP is disabled or not configured", extra=common.message_info(message)
            )
            return
        if not config.Misc.fetch("dialogflow_debug_state"):
            self.logger.info("Checking someone's permissions", extra=common.user_info(message.author))
            roles = message.author.roles[1:]
            exception_roles = config.DialogflowExceptionRoles.fetch_all()
            # Why the fuck was that here? Probably some optimisation but it was all wrong.
            # Leaving it as a comment just in case
            # if len(roles) != 0 and len(roles) != len(exception_roles):
            #     authorised = True
            for role in roles:
                if role.id not in exception_roles:
                    self.logger.info(
                        "Ignoring someone's message because they are exempt", extra=common.user_info(message.author)
                    )
                    return

        if message.author.id in self.session_ids:
            self.logger.info("Continuing a session", extra=common.user_info(message.author))
            session_id = self.session_ids[message.author.id]
        else:
            self.logger.info("Creating a new session", extra=common.user_info(message.author))
            session_id = uuid.uuid4()
            self.session_ids[message.author.id] = session_id

        session = session_client.session_path(DIALOGFLOW_PROJECT_ID, session_id)

        text_input = dialogflow.TextInput(text=message.content[0:256], language_code="en")

        query_input = dialogflow.QueryInput(text=text_input)

        self.logger.info("Detecting the intent of a message", extra=common.message_info(message))
        response = session_client.detect_intent(request={"session": session, "query_input": query_input})

        response_text = response.query_result.fulfillment_text
        response_data = response.query_result.parameters
        intent_id = response.query_result.intent.name.split("/")[-1]
        formatted_response = str(dict(response_data)).replace("'", '"')
        query = config.Dialogflow.select(
            f"dialogflow.intent_id = '{intent_id}' AND ((dialogflow.data IS NULL) "
            f"OR dialogflow.data = '{formatted_response}')"
        )
        results = list(query)

        if intent_id == config.Misc.fetch("dialogflow_steam_scam_intent_id"):
            self.logger.info("Detected a Steam scam. Deleting", extra=common.message_info(message))
            await message.delete()
            return

        if not len(results):
            self.logger.info("No intent detected", extra=common.message_info(message))
            return

        dialogflow_reply = results[0].as_dict()

        if not dialogflow_reply["response"]:
            self.logger.info("Responding to a message", extra=common.message_info(message))
            await self.bot.reply_to_msg(message, response_text)
        else:
            if dialogflow_reply["response"].startswith(self.bot.command_prefix):
                command_name = dialogflow_reply["response"].lower().lstrip(self.bot.command_prefix).split(" ")[0]
                if command := config.Commands.fetch(command_name):
                    self.logger.info("Responding to a message with a command", extra=common.message_info(message))
                    await self.bot.reply_to_msg(message, command["content"], file=command["attachment"])

            else:
                self.logger.info(
                    "Responding to a message with a predefined response", extra=common.message_info(message)
                )
                await self.bot.reply_to_msg(message, dialogflow_reply["response"])

        if dialogflow_reply["has_followup"]:
            self.logger.info("Setting up a check for a followup", extra=common.message_info(message))

            def check(message2):
                return message2.author == message.author and message2.channel == message.channel

            try:
                await self.bot.wait_for("message", timeout=SESSION_LIFETIME, check=check)
            except asyncio.TimeoutError:
                del self.session_ids[message.author.id]
        else:
            self.logger.info("Deleting a session", extra=common.message_info(message))
            del self.session_ids[message.author.id]
