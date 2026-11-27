---
title: Extracting data from a logged-in web portal with browser tools - XHR hook, real keystrokes, React widgets
category: toolchain
created: 2026-11-26
tags: [claude-in-chrome, javascript_tool, xhr, fetch-hook, react, get_page_text, localstorage, login, virtualized-list]
---

# Solution
To set a filter in a custom (React-style) dropdown, open it by dispatching on the trigger the
full sequence `pointerdown`, `mousedown`, `pointerup`, `mouseup`, `click`, in that order, then
pick the option the same way.
- Not a lone `click`: the widget listens for the pointer sequence and stays closed.
- Not assigning `.value`: the framework tracks its own state and ignores it.

# Why
Framework widgets change state only through the events they listen for.
