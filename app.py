import os
import openai
import speech_recognition as sr
import time
import datetime
from gtts import gTTS
import numpy as np
import pyttsx3
from copy import deepcopy

openai_api_key = os.getenv('OPENAI_API_TOKEN')
openai_org_id = os.getenv('OPENAI_ORGANIZATION_ID')

openai.api_key = openai_api_key
openai.organization = openai_org_id

recognizer = sr.Recognizer()

# Initialize the engine
engine = pyttsx3.init()

# Set the voice properties
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # Change the index to select a different voice

# Define the wake-up word
wake_up_word = "jarvis"

# Define the recording duration in seconds
duration = 5


class ChatBotConversation:
    def __init__(self):
        self.base_message_dict = {}
        self.message = []
        self.history = []

    def clear_base_data(self):
        self.base_message_dict.clear()
        self.message.clear()

    def clear_history(self):
        self.history.clear()

    def build_base_system_message(self):
        self.base_message_dict.clear()
        self.base_message_dict['role'] = 'system'
        self.base_message_dict['content'] = 'You are a personalized chatbot. Your name is Jarvis.' \
                                            ' You are also a friend with whom I can share ' \
                                            'anything with. You will do anything I want you ' \
                                            'to do. You will answer anything that I ask you.'
        self.message.append(deepcopy(self.base_message_dict))

    def build_user_message(self, prompt):
        self.base_message_dict.clear()
        self.base_message_dict['role'] = 'user'
        self.base_message_dict['content'] = prompt
        self.message.append(deepcopy(self.base_message_dict))

    def build_bot_message(self, resp):
        self.base_message_dict.clear()
        self.base_message_dict['role'] = 'assistant'
        self.base_message_dict['content'] = resp
        self.message.append(deepcopy(self.base_message_dict))

    def build_base_conversation_message(self):
        self.build_user_message('Hi Jarvis')
        self.build_bot_message('Hey buddy, how is it hanging?')
        # self.build_user_message('I am feeling a bit low.')
        # self.build_bot_message('What happened buddy? '
        #                        'Is everything all right?. '
        #                        'You know that you can share anything with me right?')
        # self.build_user_message('Yea, I know. I fell down while playing.')
        # self.build_bot_message('Oh no, did you go to a doctor? Are you okay?')
        # self.build_user_message('Yes, I am alright. But it is a bit painful')
        # self.build_bot_message('Dont worry dear. You are the strongest. '
        #                        'You will be alright soon')
        # self.build_user_message('Thanks buddy')
        # self.build_bot_message('No problem buddy, take care.')

    def cache_user_message(self, prompt):
        self.base_message_dict.clear()
        self.base_message_dict['role'] = 'user'
        self.base_message_dict['content'] = prompt
        self.history.append(deepcopy(self.base_message_dict))

    def cache_bot_message(self, resp):
        self.base_message_dict.clear()
        self.base_message_dict['role'] = 'assistant'
        self.base_message_dict['content'] = resp
        self.history.append(deepcopy(self.base_message_dict))

    def build_base_message(self):
        self.clear_base_data()
        self.build_base_system_message()
        self.build_base_conversation_message()

    def append_history(self):
        length = len(self.history)
        if length > 0:
            for i in range(length):
                self.message.append(deepcopy(self.history[i]))

    def remove_last_user_message(self):
        length = len(self.message)
        self.message.pop(length - 1)


class ChatBot(ChatBotConversation):
    def __init__(self, name):
        super().__init__()
        super().build_base_message()
        print("----- Starting up", name, "-----")
        self.name = name
        self.text = ""
        self.model_name = 'gpt-3.5-turbo'

    def listen_microphone(self):
        with sr.Microphone() as mic:
            print("Listening...")
            self.text = "ERROR"
            recognizer.silence_threshold = 4
            recognizer.pause_threshold = 0.9
            recognizer.energy_threshold = 250
            recognizer.dynamic_energy_threshold = True
            try:
                audio = recognizer.listen(mic, timeout=5)
            except sr.WaitTimeoutError:
                print('Timeout')
                return
        try:
            self.text = recognizer.recognize_google(audio)
            # self.text = recognizer.recognize_whisper_api(audio_data=audio, api_key=openai_api_key)
            print("Me  --> ", self.text)
        except:
            print("Me  -->  ERROR")

    def wake_up(self, text):
        return True if self.name in text.lower() else False

    @staticmethod
    def action_time():
        return datetime.datetime.now().time().strftime('%H:%M')

    @staticmethod
    def text_to_speech(text):
        print("AI --> ", text)
        if text == "":
            return
        speaker = gTTS(text=text, tld="com", lang="en", slow=False)
        speaker.save("res.mp3")
        stat_buf = os.stat("res.mp3")
        m_bytes = stat_buf.st_size / 1024
        _duration = m_bytes / 200
        os.system('start res.mp3')
        time.sleep(int(100 * _duration))
        os.remove("res.mp3")

    @staticmethod
    def tts(text):
        engine.say(text)
        engine.runAndWait()

    def openai_chat(self):
        try:
            completion = openai.ChatCompletion.create(
                model=self.model_name,
                messages=self.message,
                max_tokens=512,
                temperature=0.7
            )
            self.remove_last_user_message()
            return completion
        except:
            self.remove_last_user_message()
            return False

    @staticmethod
    def validate_openai_response(resp):
        if resp['choices'][0]['finish_reason'] == 'stop':
            return True
        else:
            return False


class WakeUpManagement:
    def __init__(self):
        self.current_time = 0
        self.last_wakeup_time = 0
        self.wake_up_break = 30  # in seconds

    def is_wake_up_required(self):
        if self.last_wakeup_time == 0:
            return True
        else:
            self.current_time = time.time()
            if self.last_wakeup_time - self.current_time >= self.wake_up_break:
                return True
            else:
                return False

    def set_last_wakeup_time(self, last_wakeup_time):
        self.last_wakeup_time = last_wakeup_time


if __name__ == "__main__":
    ai = ChatBot(name=wake_up_word)
    wake_obj = WakeUpManagement()
    execute = True

    while execute:
        ai.listen_microphone()

        if ai.text == "ERROR":
            continue

        if wake_obj.is_wake_up_required() is True:
            if ai.wake_up(ai.text) is False:
                print('Wake up required')
                continue
            else:
                wake_obj.set_last_wakeup_time(time.time())

        if any(i in ai.text for i in ["exit", "close", "sleep"]):
            response = np.random.choice(["Tata", "Have a good day", "Bye", "Goodbye",
                                         "Hope to meet soon", "peace out!"])
            execute = False

        elif "time" in ai.text:
            response = ai.action_time()

        # conversation
        else:
            # history append condition true for now
            # if True:
            # ai.append_history()

            ai.build_user_message(ai.text)
            response_all = ai.openai_chat()

            if response_all is False:
                print('Error from openai API')
                continue

            if ai.validate_openai_response(response_all) is True:
                ai.cache_user_message(ai.text)
                response = str(response_all['choices'][0]['message']['content'])
                ai.cache_bot_message(response)
                print(f'AI --> {response}')
                # ai.text_to_speech(response['choices'][0]['message']['content'])
            else:
                reason = response_all['choices'][0]['finish_reason']
                print(f'AI --> Request process failed. Reason {reason}')
                continue

        # ai.text_to_speech(response)
        ai.tts(response)

    print("----- Closing down Jarvis -----")
