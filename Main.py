import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# Standard Library Imports
import os
import json
import threading
import subprocess
import sys
from time import sleep
from asyncio import run

# Third Party Imports
from dotenv import dotenv_values

# local application imports
from Frontend.Graphics.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus,
)
from Backend.Model import FirstLayerDMM
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from Backend.RealTime_Search_Engine import RealtimeSearchEngine as RealTime_Search_Engine 

env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "JARVIS")

DefaultMessage = f"""{Username} : Hello {Assistantname}, How are you?
{Assistantname}: Welcome {Username}, I am well. How may I help you?"""

subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]

DATA_PATH = os.path.join("Data", "ChatLog.json")
IMAGE_GEN_PATH = os.path.join("Frontend", "Files", "ImageGeneration.data")

def ensure_directory(path: str):
    """Ensure parent directory exists for a file path."""
    os.makedirs(os.path.dirname(path), exist_ok=True)


def resolve_generator_output(response):
    """
    Converts generator output into proper text.
    This fixes: <generator object search at 0x...>
    """
    if response is None:
        return ""

    if isinstance(response, str):
        return response

    try:
        if hasattr(response, "__iter__"):
            return "".join(str(item) for item in response)
    except Exception:
        pass

    return str(response)


def ShowDefaultChatIfNoChats():
    ensure_directory(DATA_PATH)

    if not os.path.exists(DATA_PATH):
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)

    with open(DATA_PATH, "r", encoding="utf-8") as file:
        content = file.read()

    if len(content.strip()) < 5:
        db_path = TempDirectoryPath("Database.data")
        resp_path = TempDirectoryPath("Responses.data")

        ensure_directory(db_path)
        ensure_directory(resp_path)

        with open(db_path, "w", encoding="utf-8") as file:
            file.write("")
        with open(resp_path, "w", encoding="utf-8") as file:
            file.write(DefaultMessage)

def ReadChatLogJson():
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)

def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"User: {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"assistant: {entry['content']}\n"

    formatted_chatlog = formatted_chatlog.replace("User", Username + " - ")
    formatted_chatlog = formatted_chatlog.replace("JARVIS AI", Assistantname + " - ")

    db_path = TempDirectoryPath("Database.data")
    ensure_directory(db_path)

    with open(db_path, "w", encoding="utf-8") as file:
        file.write(AnswerModifier(formatted_chatlog))

def ShowChatsOnGUI():
    db_path = TempDirectoryPath("Database.data")
    resp_path = TempDirectoryPath("Responses.data")

    with open(db_path, "r", encoding="utf-8") as file:
        Data = file.read()

    if Data.strip():
        ensure_directory(resp_path)
        with open(resp_path, "w", encoding="utf-8") as file:
            file.write(Data)

def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()

def MainExecution():
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    SetAssistantStatus("Listening ...")
    Query = SpeechRecognition()
    if not Query or Query.strip() == "":
        return False
    ShowTextToScreen(f"{Username} : {Query}")
    SetAssistantStatus("Thinking ...")
    Decision = FirstLayerDMM(Query)

    # Convert generator to list
    Decision = list(Decision)

    print(f"\nDecision : {Decision}\n")

    G = any(i.startswith("general") for i in Decision)
    R = any(i.startswith("realtime") for i in Decision)

    Mearged_query = " and ".join(
        [" ".join(i.split()[1:]) for i in Decision if i.startswith(("general", "realtime"))]
    )

    for queries in Decision:
        if "generate " in queries:
            ImageGenerationQuery = str(queries)
            ImageExecution = True

    for queries in Decision:
        if not TaskExecution and any(queries.startswith(func) for func in Functions):
            try:
                run(Automation(list(Decision))) 
            except TypeError:
                Automation(list(Decision))     
            TaskExecution = True

    if ImageExecution:
        ensure_directory(IMAGE_GEN_PATH)
        with open(IMAGE_GEN_PATH, "w", encoding="utf-8") as file:
            file.write(f"{ImageGenerationQuery},True")
        try:
            p1 = subprocess.Popen(
                [sys.executable, os.path.join("Backend", "ImageGeneration.py")],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=False
            )
            subprocesses.append(p1)
        except Exception as e:
            print(f"Error starting ImageGeneration.py: {e}")

    if (G and R) or R:
        SetAssistantStatus("Searching ...")
        Answer = RealTime_Search_Engine(QueryModifier(Mearged_query))

        # Convert generator answer into text
        Answer = resolve_generator_output(Answer)

        ShowTextToScreen(f"{Assistantname} : {Answer}")
        SetAssistantStatus("Answering ...")
        TextToSpeech(Answer)
        return True

    for Queries in Decision:
        if "general" in Queries:
            SetAssistantStatus("Thinking ...")
            QueryFinal = Queries.replace("general ", "")
            Answer = ChatBot(QueryModifier(QueryFinal))

            # Convert generator answer into text
            Answer = resolve_generator_output(Answer)

            ShowTextToScreen(f"{Assistantname} : {Answer}")
            SetAssistantStatus("Answering ...")
            TextToSpeech(Answer)
            return True

        elif "realtime" in Queries:
            SetAssistantStatus("Searching ...")
            QueryFinal = Queries.replace("realtime ", "")
            Answer = RealTime_Search_Engine(QueryModifier(QueryFinal))

            # Convert generator answer into text
            Answer = resolve_generator_output(Answer)

            ShowTextToScreen(f"{Assistantname} : {Answer}")
            SetAssistantStatus("Answering ...")
            TextToSpeech(Answer)
            return True

        elif "exit" in Queries:
            QueryFinal = "Okay, Bye!"
            Answer = ChatBot(QueryModifier(QueryFinal))

            # Convert generator answer into text
            Answer = resolve_generator_output(Answer)

            ShowTextToScreen(f"{Assistantname} : {Answer}")
            SetAssistantStatus("Answering ...")
            TextToSpeech(Answer)
            try:
                from Backend.SpeechToText import driver
                driver.quit()
            except Exception as e:
                pass
            try:
                import subprocess
                subprocess.run(["pkill", "-f", "chromedriver"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["pkill", "-f", "use-fake-ui-for-media-stream"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            import os
            os._exit(1)

def FirstThread():
    while True:
        CurrentStatus = GetMicrophoneStatus()
        if CurrentStatus == "True":
            MainExecution()
        else:
            AIStatus = GetAssistantStatus()
            if "Available ..." in AIStatus:
                sleep(0.1)
            else:
                SetAssistantStatus("Available ...")

def WakeWordThread():
    """Listens in background for 'Hey JARVIS' only — nothing else activates."""
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 3000
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.6
        mic = sr.Microphone()

        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)

        print("Wake word listener active — say 'Hey JARVIS' to activate!")

        while True:
            # Only listen for wake word when mic is OFF (Available mode)
            if GetMicrophoneStatus() == "False":
                try:
                    with mic as source:
                        audio = recognizer.listen(source, timeout=3, phrase_time_limit=4)
                    text = recognizer.recognize_google(audio).lower().strip()
                    print(f"[Wake] Heard: {text}")

                    # Strict match — must say "hey jarvis" exactly
                    if text == "hey jarvis" or text.startswith("hey jarvis"):
                        print("[Wake] Wake word detected! Activating...")
                        # Instantly update status and icon BEFORE Chrome starts
                        SetAssistantStatus("Listening ...")
                        SetMicrophoneStatus("True")
                        sleep(0.5)  # brief pause so pyaudio mic releases before Chrome grabs it

                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except Exception as e:
                    pass
            else:
                sleep(0.2)
    except Exception as e:
        print(f"[Wake word] Could not start: {e}")

def SecondThread():
    GraphicalUserInterface()

if __name__ == "__main__":
    InitialExecution()
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    thread3 = threading.Thread(target=WakeWordThread, daemon=True)
    thread3.start()
    SecondThread()