---
title: AWS SSO login is an interactive OAuth flow — hand it to the user immediately
category: toolchain
created: 2026-08-21
tags: [aws, sso, oidc, device-authorization, credentials, background-task, buffering]
---

# Problem

Mid-session the cached AWS SSO token expired ("Token has expired and refresh
failed") while autonomous work still needed AWS reads. Trying to recover by
running `aws sso login --no-browser` from the agent burned about ten minutes and
never produced credentials.

# Failed Approaches

- Running `aws sso login ... 2>&1 | head -20` as a background task: the AWS CLI
  block-buffers stdout when writing to a pipe, so the device URL and code never
  appeared in the captured output and the flow looked hung.
- Restarting the login with output redirected to a file (`> sso.log 2>&1`): the
  URL does appear, but completing the flow still requires a human to open it and
  approve in a browser with a live Identity Center session. That is a credential
  grant an agent must not perform. The pending authorization then expires
  unclaimed after about ten minutes ("The pending authorization to retrieve an
  SSO token has expired").

# Solution

Treat SSO expiry as a hard user handoff, not a recoverable error. The moment
`aws configure export-credentials` or `aws sts get-caller-identity` reports an
expired token:

1. Ask the user to run `aws sso login --profile <profile>` themselves — one
   command, and their existing browser session makes it a single Allow click.
2. Immediately reorder the plan: continue every task that does not need AWS
   (docs, git, ticket updates, wiki edits) and park the AWS verifications in a
   named resume list.
3. If you do start a login for the user to claim, write output to a file (never
   through a pipe) so the URL is visible, and say plainly that the window
   expires in about ten minutes.

# Why

Device authorization is an interactive OAuth grant by design: an agent can print
the URL but must not be the party that approves it. Two properties make it look
like a tool bug instead — block buffering hides the prompt whenever stdout is a
pipe, and the authorization expires silently rather than erroring. Recognizing
it as a handoff in the first minute turns a ten-minute stall into a
parallelizable pause.
