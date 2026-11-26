---
title: Local voice-message transcription with faster-whisper - decode with ffmpeg to avoid a PyAV keyword bug
category: toolchain
created: 2026-11-26
tags: [whisper, faster-whisper, transcription, ffmpeg, pyav, windows, venv, audio]
---

# Problem
A voice message had to be transcribed locally. On Windows the model's own audio decoding failed
because of a PyAV keyword-argument bug. These are facts only; the toolkit holds no transcription
script.

# Failed Approaches
- Passing the audio file path straight to the model on that Windows setup.
- Installing into the system Python.

# Solution
- Install faster-whisper (medium model) in a dedicated virtual environment under a user tools
  folder.
- Decode the audio with ffmpeg to float32 little-endian mono at the model's sample rate and pass the
  resulting array to the model.
- Report the duration, the detected language and the transcript, and act only on the parts that
  matter to the task.
- Keep speaker names, file names and audio content out of shared notes.

# Why
The failing step is PyAV's decode call; decoding with ffmpeg first removes it from the path.
Related: `skills/llm-toolchain-provisioning/SKILL.md`.
