from telethon import TelegramClient, events, sync, functions
from telethon.tl.types import InputChannel
import yaml
import sys, datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger('telethon').setLevel(level=logging.WARNING)
logger = logging.getLogger(__name__)

def fetch_feed(client, output_channel, output_channel_entity, input_entities):
    feed_to_forward = []
    contract_time = (datetime.datetime.now() - datetime.timedelta(days = 1)).timestamp()
    for channel in reversed(input_entities):
        if('last_message_occured' in dir(channel)):
            for message in client.iter_messages(entity=channel, min_id=channel.last_message_occured + 1, limit = 3):
                if(message.date.timestamp() > contract_time):
                    feed_to_forward.append(message)
                
        else:
            for message in client.iter_messages(entity=channel, limit = 1):
                if(message.date.timestamp() > contract_time):
                    feed_to_forward.append(message)
    for m in feed_to_forward:
        try:
            client.forward_messages(output_channel, m)
        except:
            print("Forwarding message from " + client.get_entity(channel.channel_id).title + " failed")
            continue

def iter_output(client, output_channel, output_channel_entity, input_entities):
    messages_list = []
    for message in client.iter_messages(output_channel_entity):
        messages_list.append(message)
        for i in input_entities:
            if message.chat.id == i.channel_id:
                if 'last_message_occured' in dir(i) and i.last_message_occured <= message.id:
                    i.last_message_occured = message.id
    for i in input_entities:
        if('last_message_occured' in dir(i)):
            print(client.get_entity(i.channel_id) + " - " + i.last_message_occured)

    client.delete_messages(output_channel_entity, list(map(lambda x: x.id, messages_list)))

def start(config):
    client = TelegramClient(config['session_name'], 
                            config['api_id'], 
                            config['api_hash'])
    client.start()

    output_entity = None
    output_channel = None

    input_channel_names = []
    input_channel_entities = []

    for d in client.iter_dialogs():
        if d.is_channel and not d.is_group:
            if(d.name == config['default_channel']):
                output_entity = client.get_entity(d.entity.id)
                output_channel = InputChannel(client.get_entity(d.entity.id).id, client.get_entity(d.entity.id).access_hash)
            elif(d.name not in config['ignored_channels']):
                input_channel_names.append(d.name)
                input_channel_entities.append(InputChannel(d.entity.id, d.entity.access_hash))

    iter_output(client, output_channel, output_entity, input_channel_entities)

    client.send_message(output_entity, "Fetching messages from: " + ", ".join(map(str, input_channel_names)))

    fetch_feed(client, output_channel, output_entity, input_channel_entities)

    @client.on(events.NewMessage(chats=input_channel_entities))
    async def handler(event):
        for i in input_channel_entities:
            if message.chat.id == i.channel_id:
                if 'last_message_occured' in dir(i) and i.last_message_occured <= message.id:
                    i.last_message_occured = message.id
        await client.forward_messages(output_channel, event.message)

    client.run_until_disconnected()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} {{CONFIG_PATH}}")
        sys.exit(1)
    with open(sys.argv[1], 'rb') as f:
        config = yaml.safe_load(f)
    start(config)
