---
title: Storyboard-to-video pipeline - design notes (implementation not in the toolkit)
category: architecture
created: 2026-11-26
tags: [video, storyboard, tts, ffmpeg, srt, sapi, design-notes, fact-check]
---

# Problem
Documentation had to become narrated explainer videos. This note records the design only; the
scripts that implemented it are not part of the toolkit, so treat it as a specification.

# Failed Approaches
- Writing narration free-form: timing and fact checks cannot be automated.
- Fact-checking with prose feedback: refinement needs exact replacement text.

# Solution
- A JSON storyboard: scenes of kind title, bullets, diagram, code, image or qa; beats with a voice
  (narrator, interviewer, candidate, coach), spoken text of 12 to 45 words, an optional on-screen
  line and a tag (point, pitfall, tip, number).
- A TTS step writes one WAV per beat and `timings.json` with frame counts at 30 fps.
- A render step produces 1920x1080, 30 fps H.264 plus AAC and an SRT file.
- On Windows use SAPI through pywin32 (SpFileStream, 22050 Hz mono); elsewhere ffmpeg's flite source.
- Planning figures: about 10 to 12 seconds of render per video minute, about 160 words per minute at
  rate 0.
- The fact-check lane returns defects as exact replacement text in a file, so a refinement pass
  takes about 90 seconds.
- Every claim comes from repository documents; never invent experience.
- Related: `skills/technical-content-publishing/references/visual-assets.md`.

# Why
A schema with per-beat audio gives deterministic timing, and sourcing every claim from the
repository keeps the video verifiable.
