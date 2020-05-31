import time

async def waitResponse(client, channel, question):
    time.sleep(0.1)
    await channel.send("What would you like to name this automation? e.g. ``CommandDave``")
    return await client.wait_for('message', timeout=30.0).content
