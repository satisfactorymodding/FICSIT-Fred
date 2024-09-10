import json

from nextcord import Role

from ._baseclass import BaseCmds, commands, config


class DialogflowCmds(BaseCmds):

    @BaseCmds.add.command(name="dialogflow")
    async def add_dialogflow(self, ctx: commands.Context, intent_id: str, response: bool | str, followup: bool, *args):
        """Usage: `add dialogflow (intent_id: str) (response: bool/str) (has_followup: bool)`
        Purpose: Adds a natural language processing trigger
        Notes: probably don't mess around with this, Mircea is the only wizard that knows how these works"""
        if len(args) == 0:
            data = None
        else:
            data = {arg.split("=")[0]: arg.split("=")[1] for arg in args}

        if response is True:
            await self.bot.reply_to_msg(
                ctx.message, "Response should be a string or False (use the response from dialogflow)"
            )
            return
        elif response is False:
            response = None

        if config.Dialogflow.fetch(intent_id, data):
            try:
                question = "Dialogflow response with this parameters already exists. Do you want to replace it?"
                if await self.bot.reply_yes_or_no(ctx.message, question):
                    await self.remove_dialogflow(ctx, intent_id, *args)
                else:
                    return
            except ValueError:
                return

        config.Dialogflow(intent_id=intent_id, data=data, response=response, has_followup=followup)
        await self.bot.reply_to_msg(
            ctx.message,
            f"Dialogflow response for '{intent_id}' " f"({json.dumps(data) if data else 'any data'}) added!",
        )

    @BaseCmds.remove.command(name="dialogflow")
    async def remove_dialogflow(self, ctx: commands.Context, intent_id: str, *args):
        """Usage: `add dialogflow (intent_id: str)`
        Purpose: Removes a natural language processing trigger
        Notes: probably don't mess around with this, Mircea is the only wizard that knows how these works"""
        if len(args) == 0:
            data = None
        else:
            data = {arg.split("=")[0]: arg.split("=")[1] for arg in args}

        if not config.Dialogflow.fetch(intent_id, data):
            await self.bot.reply_to_msg(ctx.message, "Couldn't find the dialogflow reply")
            return

        config.Dialogflow.deleteBy(intent_id=intent_id, data=data)
        await self.bot.reply_to_msg(ctx.message, "Dialogflow reply deleted")

    @BaseCmds.add.command(name="dialogflowRole")
    async def add_dialogflow_role(self, ctx: commands.Context, role: commands.RoleConverter):
        """Usage: `add dialogflowRole (role)`
        Purpose: Adds role to the list of roles that natural language processing is not applied to"""
        role: Role
        role_id = role.id

        if config.DialogflowExceptionRoles.check(role_id):
            await self.bot.reply_to_msg(ctx.message, "This role is already a dialogflow exception role")
            return

        config.DialogflowExceptionRoles(role_id=role_id)
        await self.bot.reply_to_msg(ctx.message, f"Dialogflow role {ctx.message.guild.get_role(role_id).name} added!")

    @BaseCmds.remove.command(name="dialogflowRole")
    async def remove_dialogflow_role(self, ctx: commands.Context, role: commands.RoleConverter):
        """Usage: `remove dialogflowRole (role)`
        Purpose: Removes role from the list of roles that natural language processing is not applied to"""
        role: Role
        role_id = role.id

        if config.DialogflowExceptionRoles.check(role_id):
            config.DialogflowExceptionRoles.deleteBy(role_id=role_id)
            await self.bot.reply_to_msg(ctx.message, "Dialogflow role removed!")
        else:
            await self.bot.reply_to_msg(ctx.message, "Dialogflow role could not be found!")

    @BaseCmds.set.command(name="NLP_state")
    async def set_NLP_state(self, ctx: commands.Context, enabled: bool):
        """Usage: `set NLP_state (true/false)`
        Purpose: turns NLP on or off
        Notes: no touchy"""
        if not enabled:
            config.Misc.change("dialogflow_state", False)
            await self.bot.reply_to_msg(ctx.message, "The NLP is now off!")
        else:
            config.Misc.change("dialogflow_state", True)
            await self.bot.reply_to_msg(ctx.message, "The NLP is now on!")

    @BaseCmds.set.command(name="NLP_debug")
    async def set_NLP_debug(self, ctx: commands.Context, enabled: bool):
        """Usage: `set NLP_debug (true/false)`
        Purpose: turns NLP debug (ignores all ignore rules) on or off
        Notes: no touchy, can get very spammy"""
        if not enabled:
            config.Misc.change("dialogflow_debug_state", False)
            await self.bot.reply_to_msg(ctx.message, "The NLP debugging mode is now off!")
        else:
            config.Misc.change("dialogflow_debug_state", True)
            await self.bot.reply_to_msg(ctx.message, "The NLP debugging mode is now on!")
