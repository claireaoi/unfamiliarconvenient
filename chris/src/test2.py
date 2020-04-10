# Example for communicating with Mycroft Message bus
# first launch mycroft services:
# cd ~/mycroft/
# ./start-mycroft.sh all (this starts all services, you can start only the 'bus' instead of 'all')
# now you can launch this scipt, use python3
#python3 test.py
# This will only work for sending and receiving text messages to Christopher
# If you want to have custom user input recognition, like you saying "Christopher, where is Roomba?",
# You have to develop an actual skill with trigger words, in the skills folder
# /home/christopher/mycroft-core/skills  with a standard skills folder structure
# a good starter tutorial here:
# https://medium.com/@augustnmonteiro/creating-a-hello-world-skill-to-mycroft-ai-2e0b493fdad2
# or just copy the 'Hello World' skill from the folder, rename and modify

from mycroft_bus_client import MessageBusClient, Message

client = MessageBusClient()

# Use this if you want Christopher to speak (valid for Examples 1 and 2)

client.run_in_thread()

# Getting Christopher to say something

# Example 1:
# Sends to bus for direct voice synthesis
# Christopher will say 'life starts in a corner'

#client.emit(Message('speak', data={'utterance': 'life starts in a corner'}))

# Example 2:
# Send to message bus for interpretation
# Christopher will trigger the weather skill and announce the weather

client.emit(Message("recognizer_loop:utterance", {'utterances': ['Christopher, tell me about utterance?'], 'lang': 'en-us'}))
client.emit(Message("recognizer_loop:utterance", {'utterances': ['Christopher, tell me more.'], 'lang': 'en-us'}))
client.emit(Message("recognizer_loop:utterance", {'utterances': ['Christopher, who is xi jinping?'], 'lang': 'en-us'}))
client.emit(Message("recognizer_loop:utterance", {'utterances': ['Christopher, what shall I do with my life?'], 'lang': 'en-us'}))

#Example 3:
# Will catch and print out a message from Christopher's MessageBusClient

def print_utterance(message):
    print("Mycroft said {}".format(message.data.get('utterance')))

#client.on('speak', print_utterance)
# use this only for example 3, comment out line 10 in this case
#client.run_forever()
