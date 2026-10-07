---
title: gh api -f contexts[] did not update required status checks; send a JSON body with --input
category: api
created: 2026-10-07
tags: [github, gh-cli, gh-api, branch-protection, required-status-checks, contexts, input, rest-api]
---

# Problem

Updating the required status checks of a protected branch with `gh api` and array form
fields (`-f contexts[]=<check>`) did not update the required checks. The session recorded
this as a low-severity tool-misuse mistake, found as a tool error.

# Failed Approaches

- `gh api -f contexts[]=<check-name> ...` aimed at the branch's `required_status_checks`:
  per the record, it did not update the required status checks. The record does not say
  whether the call returned an error or was accepted without effect.

# Solution

Send the required checks as a JSON body with `--input`, using PATCH on the
`required_status_checks` resource (the form the session recorded). Illustrative command
and file, with placeholders; not executed in the authoring session, and the file shape is
built from the `contexts` field named in
`learnings/branch-protection-required-checks-need-stable-job-names.md`:

```text
gh api -X PATCH repos/<owner>/<repo>/branches/<branch>/protection/required_status_checks --input required-checks.json
```

```json
{ "contexts": ["<job-name>", "<job-name>"] }
```

Read the result back with a GET on the same path and compare the list with the job names
the CI run actually reports (the read-back form is shown in
`learnings/required-checks-must-follow-removed-ci-jobs.md`).

# Why

The record states the failing form and the working form, not the cause. Do not
conclude that `-f` cannot build arrays: `gh api --help` documents `key[]=value` fields as
JSON array items, and notes that adding any field switches the default method from GET to
POST unless `--method` is given. Inference, not observed in this session: the failed call
may have used the wrong method or lost the brackets to shell quoting; `--input` avoids both
because the file is sent as the request body unchanged. The same general guidance, to
prefer `--input <file>` over inline values for request bodies, appears in
`learnings/powershell-gh-jq-quoting-breaks.md`.
