import time
import re
import asyncio

async def waitResponse(client, message, question):
    file = False
    time.sleep(0.1)
    await message.channel.send(question)

    def check(message2):
        return message2.author == message.author
    try:
        response = await client.wait_for('message', timeout=60.0, check=check)
        try:
            response.content = response.attachments[0].url
        except:
            pass
    except asyncio.TimeoutError:
        await message.channel.send("Timed out and aborted after 30 seconds.")
        raise asyncio.TimeoutError
    time.sleep(0.1)
    return response.content

def formatDesc(desc):
    dict = {
        "<b>": "**",
        "</b>": "**",
        "<u>": "__",
        "</u>": "__",
        "<br>": "",
    }
    for x, y in dict.items():
        desc = desc.replace(x, y)
    desc = re.sub('#+ ', "", desc)
    return desc