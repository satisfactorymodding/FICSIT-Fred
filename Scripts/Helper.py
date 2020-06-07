import time
import re
import asyncio

async def waitResponse(client, channel, question):
    time.sleep(0.1)
    await channel.send(question)
    try:
        response = await client.wait_for('message', timeout=30.0)
    except asyncio.TimeoutError:
        await channel.send("Timed out and aborted after 30 seconds.")
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