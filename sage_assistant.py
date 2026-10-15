"""SAGE voice assistant for Windows 10/11.

Wake detection uses Google Speech Recognition, so an internet connection is needed.
"""

import ctypes
import datetime
import os
import re
import subprocess 
import time
import webbrowser
from urllib.parse import quote_plus

import pyttsx3
import screen_brightness_control as sbc
import speech_recognition as sr
import wikipediaapi

USE_WAKE_WORD = True
WAKE_WORDS = (
    "sage voice assistant", "sage assistant", "sage voice", "sage ai", "sage",
    "hey sage", "hello sage", "hi sage",
    # Google transcription sometimes hears the name "Sage" as "stage".
    "hey stage assistant", "stage assistant", "hey stage", "stage",
)
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sage_assistant.log")

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
is_muted = False

wiki_agent = wikipediaapi.Wikipedia(
    user_agent="SAGEVoiceAssistant/1.0 (update with your contact email)", language="en"
)

CUSTOM_LINKS = [
    (("student login", "student log in", "cuims", "uims", "cuim"), "CUIMS", "https://uims.cuchd.in/"),
    (("my github",), "GitHub", "https://github.com"),
    (("chat gpt", "chatgpt", "chat g p t"), "ChatGPT", "https://chatgpt.com/"),
    (("claude",), "Claude", "https://claude.ai/"),
    (("gemini",), "Gemini", "https://gemini.google.com/app"),
    (("copilot", "co pilot"), "Microsoft Copilot", "https://copilot.microsoft.com/"),
    (("perplexity",), "Perplexity", "https://www.perplexity.ai/"),
    (("deep seek", "deepseek"), "DeepSeek", "https://chat.deepseek.com/"),
    (("grok",), "Grok", "https://grok.com/"),
    (("meta ai", "meta assistant"), "Meta AI", "https://www.meta.ai/"),
    (("poe",), "Poe", "https://poe.com/"),
    (("mistral vibe", "mistral", "le chat"), "Mistral Vibe", "https://chat.mistral.ai/"),
    (("notebook lm", "notebooklm"), "NotebookLM", "https://notebooklm.google.com/"),
    (("google ai studio", "ai studio"), "Google AI Studio", "https://aistudio.google.com/"),
]
SITES = {
    "youtube": ("YouTube", "https://www.youtube.com", "https://www.youtube.com/results?search_query={}"),
    "wikipedia": ("Wikipedia", "https://www.wikipedia.org", None),
    "amazon": ("Amazon", "https://www.amazon.in", "https://www.amazon.in/s?k={}"),
    "flipkart": ("Flipkart", "https://www.flipkart.com", "https://www.flipkart.com/search?q={}"),
    "google": ("Google", "https://www.google.com", "https://www.google.com/search?q={}"),
    "netflix": ("Netflix", "https://www.netflix.com", None),
    "github": ("GitHub", "https://github.com", None),
    "linkedin": ("LinkedIn", "https://www.linkedin.com", None),
    "instagram": ("Instagram", "https://www.instagram.com", None),
}
APPS = [
    (("notepad",), "Notepad", ["notepad"]),
    (("calculator",), "Calculator", ["calc"]),
    (("cmd", "command prompt"), "Command Prompt", ["cmd"]),
    (("chrome",), "Google Chrome", ["chrome"]),
    (("edge",), "Microsoft Edge", ["msedge"]),
    (("firefox",), "Mozilla Firefox", ["firefox"]),
    (("excel",), "Microsoft Excel", ["excel"]),
    (("powerpoint",), "Microsoft PowerPoint", ["powerpnt"]),
    (("word",), "Microsoft Word", ["winword"]),
    (("settings",), "Windows Settings", ["cmd", "/c", "start", "", "ms-settings:"]),
    (("task manager",), "Task Manager", ["taskmgr"]),
    (("file explorer", "explorer"), "File Explorer", ["explorer"]),
    (("control panel",), "Control Panel", ["control"]),
    (("whatsapp",), "WhatsApp", ["cmd", "/c", "start", "", "whatsapp:"]),
    (("steam",), "Steam", ["cmd", "/c", "start", "", "steam://open/main"]),
    (("vs code", "visual studio code"), "Visual Studio Code", ["code"]),
    (("mysql", "my sql", "my sequel", "sequel"), "MySQL Workbench", [
        r"C:\Program Files\MySQL\MySQL Workbench 8.0\MySQLWorkbench.exe"
    ]),
]


def speak(text):
    log(f"SAGE: {text}")
    try:
        engine = pyttsx3.init(driverName="sapi5")
        engine.setProperty("rate", 170)
        engine.setProperty("volume", 1.0)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as exc:
        print(f"Speech output unavailable: {exc}")


def log(message):
    """Write diagnostics somewhere visible even when started with pythonw."""
    print(message)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {message}\n")
    except OSError:
        pass


def has_word(query, word):
    return re.search(rf"\b{re.escape(word)}\b", query, re.IGNORECASE) is not None


def recognize(recognizer, microphone, timeout=5, phrase_time_limit=5):
    with microphone as source:
        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    return recognizer.recognize_google(audio, language="en-in").lower()


def hear_command(recognizer, microphone):
    """Wait for the wake phrase, then return any command spoken after it."""
    while True:
        try:
            # Give the user time to begin speaking and allow a full command after
            # the wake word. Very short limits clipped phrases in normal speech.
            heard = recognize(recognizer, microphone, timeout=3, phrase_time_limit=8)
            log(f"Heard: {heard}")
            if not USE_WAKE_WORD:
                return heard
            for wake in sorted(WAKE_WORDS, key=len, reverse=True):
                match = re.search(rf"\b{re.escape(wake)}\b", heard, re.IGNORECASE)
                if match:
                    remainder = (heard[:match.start()] + " " + heard[match.end():]).strip(" ,.!?")
                    if remainder:
                        return remainder
                    speak("I'm listening")
                    return recognize(recognizer, microphone, timeout=8, phrase_time_limit=7)
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except sr.RequestError:
            log("Speech service/network error while listening for wake phrase; retrying.")
            time.sleep(2)


def percentage(text):
    for token in text.replace("%", "").split():
        if token.isdigit() and 0 <= int(token) <= 100:
            return int(token)
    return None


def wants_exact_value(query):
    return "to" in query.split() or "set" in query.split() or "%" in query


def press_key(code):
    ctypes.windll.user32.keybd_event(code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(code, 0, 2, 0)


def set_volume(target):
    global is_muted
    try:
        if is_muted:
            press_key(VK_VOLUME_MUTE)
            is_muted = False
        for _ in range(50):
            press_key(VK_VOLUME_DOWN)
            time.sleep(0.01)
        for _ in range(target // 2):
            press_key(VK_VOLUME_UP)
            time.sleep(0.01)
    except Exception as exc:
        print(f"Volume control failed: {exc}")


def change_brightness(delta):
    try:
        current = sbc.get_brightness()
        if isinstance(current, list):
            current = current[0]
        sbc.set_brightness(max(0, min(100, current + delta)))
        speak("Brightness adjusted")
    except Exception:
        speak("Could not adjust screen brightness")


def start_windows_app(command):
    """Launch apps through Windows' app lookup, since many are not on PATH."""
    if command[0].lower() in ("cmd", "cmd.exe") and len(command) == 1:
        subprocess.Popen(["cmd.exe"], shell=False)
    elif command[0].lower() in ("cmd", "cmd.exe"):
        subprocess.Popen(command, shell=False)
    elif len(command) == 1 and os.path.isabs(command[0]):
        os.startfile(command[0])
    else:
        subprocess.Popen(["cmd.exe", "/c", "start", "", command[0]], shell=False)


def launch_app(query):
    if not (has_word(query, "open") or has_word(query, "launch")):
        return False
    for words, name, url in CUSTOM_LINKS:
        if any(has_word(query, word) for word in words):
            speak(f"Opening {name}")
            webbrowser.open(url)
            return True
    if has_word(query, "discord"):
        link = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Discord Inc", "Discord.lnk")
        speak("Opening Discord")
        if os.path.exists(link):
            os.startfile(link)
        else:
            subprocess.Popen(["cmd", "/c", "start", "", "discord"], shell=False)
        return True
    for words, name, command in APPS:
        if any(has_word(query, word) for word in words):
            speak(f"Opening {name}")
            try:
                start_windows_app(command)
            except (OSError, subprocess.SubprocessError):
                speak(f"I could not find {name} on this computer")
            return True
    return False


def extract_search_term(query, site):
    query = re.sub(rf"\b(on|in|at|from)\s+{re.escape(site)}\b", " ", query)
    query = re.sub(rf"\b(search for|search|look up|play|open|{re.escape(site)})\b", " ", query)
    return " ".join(query.split())


def wikipedia_summary(term):
    speak(f"Looking up {term} on Wikipedia")
    try:
        page = wiki_agent.page(term)
        if page.exists():
            sentences = re.split(r"(?<=[.!?])\s+", page.summary.strip())
            speak(" ".join(sentences[:2]) or "The page has no summary")
        else:
            speak(f"I couldn't find a Wikipedia page for {term}")
    except Exception:
        speak("Failed to connect to Wikipedia")


def handle_web(query):
    site = next((key for key in SITES if has_word(query, key)), None)
    if site is None:
        site = "youtube" if has_word(query, "play") else "google" if has_word(query, "search") else None
    if site is None:
        return False
    name, homepage, search_url = SITES[site]
    term = extract_search_term(query, site)
    if site == "wikipedia":
        if term:
            wikipedia_summary(term)
        else:
            speak("Opening Wikipedia")
            webbrowser.open(homepage)
    elif term and search_url:
        speak(f"Searching {name} for {term}")
        webbrowser.open(search_url.format(quote_plus(term)))
    else:
        speak(f"Opening {name}")
        webbrowser.open(homepage)
    return True


def handle_command(query):
    global is_muted
    if has_word(query, "stop") or has_word(query, "exit") or has_word(query, "quit"):
        speak("Goodbye")
        return False
    if "what time" in query or query == "time" or "current time" in query:
        speak("The current time is " + datetime.datetime.now().strftime("%I:%M %p"))
    elif has_word(query, "unmute"):
        if is_muted:
            press_key(VK_VOLUME_MUTE)
            is_muted = False
            speak("Volume unmuted")
        else:
            speak("Volume is not muted")
    elif has_word(query, "mute"):
        if not is_muted:
            press_key(VK_VOLUME_MUTE)
            is_muted = True
        speak("Volume muted")
    elif "volume" in query and wants_exact_value(query):
        value = percentage(query)
        if value is None:
            speak("Please specify a volume percentage from 0 to 100")
        else:
            speak(f"Setting volume to {value} percent")
            set_volume(value)
    elif "volume up" in query or "increase volume" in query:
        for _ in range(5): press_key(VK_VOLUME_UP)
        is_muted = False
        speak("Increasing volume")
    elif "volume down" in query or "decrease volume" in query:
        for _ in range(5): press_key(VK_VOLUME_DOWN)
        speak("Decreasing volume")
    elif "brightness" in query and wants_exact_value(query):
        value = percentage(query)
        if value is None:
            speak("Please specify a brightness percentage from 0 to 100")
        else:
            try:
                sbc.set_brightness(value)
                speak(f"Brightness adjusted to {value} percent")
            except Exception:
                speak("Could not adjust screen brightness")
    elif "brightness up" in query or "increase brightness" in query:
        change_brightness(20)
    elif "brightness down" in query or "decrease brightness" in query:
        change_brightness(-20)
    elif launch_app(query):
        pass
    elif handle_web(query):
        pass
    elif has_word(query, "open") or has_word(query, "launch"):
        speak("I don't know that application yet")
    else:
        speak("I didn't recognize a command")
    return True


def main():
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 1.0
    try:
        microphone = sr.Microphone()
    except Exception as exc:
        print(f"Microphone unavailable: {exc}")
        return
    try:
        with microphone as source:
            print("Calibrating microphone noise level...")
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
    except Exception as exc:
        print(f"Microphone calibration skipped: {exc}")
    speak("SAGE is ready. Say Sage, then your command.")
    while True:
        try:
            command = hear_command(recognizer, microphone)
            print(f"Command: {command}")
            if not handle_command(command):
                break
        except KeyboardInterrupt:
            break
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            continue
        except Exception as exc:
            print(f"Assistant error: {exc}")
            time.sleep(1)


if __name__ == "__main__":
    main()
