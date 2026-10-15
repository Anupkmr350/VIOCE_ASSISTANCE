# SAGE Voice Assistant for Windows

## Install

1. Install Python 3.10 or newer from python.org and select **Add python.exe to PATH**.
2. Open this folder in File Explorer. Right-click `setup_startup.ps1` and choose **Run with PowerShell**. If Windows blocks the script, open PowerShell in this folder and run `powershell -ExecutionPolicy Bypass -File .\setup_startup.ps1`.
3. Approve microphone access for Python in **Settings → Privacy & security → Microphone**. Keep an internet connection available for voice recognition and Wikipedia lookups.
4. Sign out and back in, or restart Windows. SAGE will start at sign-in and wait for “Sage” or a supported wake phrase.

Say a wake phrase and command together, for example **“Hey Sage, what time is it?”** or say **“Sage”**, wait for “I'm listening”, then give the command. Say **“Sage, stop”** to exit the running assistant.

The assistant uses Google's speech recognition through the SpeechRecognition package, so captured speech is sent to that online service for transcription. It does not use a dedicated offline wake-word engine. The microphone is sampled continuously in short listening windows while SAGE is running.

## Commands

- “Open Notepad”, “open Chrome”, “open CUIMS”, “open Discord”, “open ChatGPT”, “open Claude”, “open Gemini”, “open Copilot”, “open Perplexity”, “open DeepSeek”, “open Grok”, “open Meta AI”, “open Poe”, “open Mistral”, “open NotebookLM”, or “open Google AI Studio”
- “Search for [words]”, “play [words]”, “search YouTube for [words]”
- “Wikipedia [topic]”, “what time is it?”
- “Volume up/down”, “set volume to 50 percent”, “mute”, “unmute”
- “Brightness up/down”, “set brightness to 60 percent”

The available application commands depend on what is installed and available on PATH. MySQL Workbench uses its default Windows installation path in the script.

## Manage startup

The installer adds a shortcut to your per-user Windows Startup folder; it does not require administrator access. To disable automatic start, delete **SAGE Voice Assistant.lnk** from the Startup folder. To launch SAGE manually, run `python .\sage_assistant.py` in PowerShell from this folder.
