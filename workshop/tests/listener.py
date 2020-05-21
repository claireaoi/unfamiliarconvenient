import os.path
from os import path

from mycroft_bus_client import MessageBusClient, Message
from mycroft.audio import wait_while_speaking

# To be able to import mycroft.audio module, enable the virtual environment:
# source /mycroft-core/.venv/bin/activate

# The maximum timeout for recorded user message is 10s
# This can be increased in Mycroft conf
# /mycroft-core/mycroft/configuration/mycroft.conf
# Look for recording_timeout
# --
# Alternatively, you can hard code it in
# /mycroft-core/mycroft/client/speech/mic.py
# Look for ResponsiveRecognizer Class
# There you have some additional parameters that you can add to .conf if needed,
# so they can be modified via client interface later


print('Setting up client to connect to a local mycroft instance')
client = MessageBusClient()

def print_user_utterance(message):
    said = str(message.data.get('utterances')[0])
    print(f'Human said "{said}"')

    with open('learnings.txt', 'a+') as t:
        t.write(said + ' ')

client.on('recognizer_loop:utterance', print_user_utterance)

#wait for Mycroft to finish speaking. Useless now, but will be helpful later
wait_while_speaking()

client.run_forever()
