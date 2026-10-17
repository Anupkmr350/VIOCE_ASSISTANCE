# SAGE Voice Assistant for Windows

## Install

1. Install Python 3.10 or newer from python.org and select **Add python.exe to PATH**.
2. Open this folder in File Explorer. Right-click `setup_startup.ps1` and choose **Run with PowerShell**. If Windows blocks the script, open PowerShell in this folder and run `powershell -ExecutionPolicy Bypass -File .\setup_startup.ps1`.
3. Approve microphone access for Python in **Settings → Privacy & security → Microphone**. Keep an internet connection available for voice recognition and Wikipedia lookups.
4. Sign out and back in, or restart Windows. SAGE will start at sign-in and wait for **“Alexa”**. On its first run, it downloads the Alexa wake-word model; keep the laptop connected to the internet for this initial download.

Say **“Alexa”**, wait for SAGE to say “I'm listening”, then speak your command, for example **“open ChatGPT”**, **“what time is it?”**, or **“play relaxing music on YouTube.”** Give the wake phrase and command as separate utterances. To exit SAGE, say **“Alexa”**, wait for “I'm listening”, then say **“stop.”**

The Alexa wake phrase is detected locally with openWakeWord. After wake detection, SAGE uses Google's speech recognition through the SpeechRecognition package to transcribe the command, so command audio is sent to that online service. An internet connection is still needed for commands and Wikipedia lookups.

## Commands

- “Open Notepad”, “open Chrome”, “open CUIMS”, “open Discord”, “open ChatGPT”, “open Claude”, “open Gemini”, “open Copilot”, “open Perplexity”, “open DeepSeek”, “open Grok”, “open Meta AI”, “open Poe”, “open Mistral”, “open NotebookLM”, or “open Google AI Studio”
- “Search for [words]”, “play [words]”, “search YouTube for [words]”
- “Wikipedia [topic]”, “what time is it?”
- “Volume up/down”, “set volume to 50 percent”, “mute”, “unmute”
- “Brightness up/down”, “set brightness to 60 percent”
- “Shut down PC” or “restart PC” (Windows begins the action after a five-second delay)

The available application commands depend on what is installed and available on PATH. MySQL Workbench uses its default Windows installation path in the script.

## Manage startup

The installer adds a shortcut to your per-user Windows Startup folder; it does not require administrator access. To disable automatic start, delete **SAGE Voice Assistant.lnk** from the Startup folder. To launch SAGE manually, run `python .\sage_assistant.py` in PowerShell from this folder.
