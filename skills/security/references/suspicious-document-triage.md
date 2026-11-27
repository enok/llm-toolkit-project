---
description: Static, read-only triage of an unsolicited PDF or invitation and of the organization behind it, before the user opens, signs, or replies
---

# Suspicious Document Triage

Use when a document or invitation arrives from an unknown or unverified sender
(an offer, a form, an "assessment", an invoice, a take-home exercise) and the
user asks whether it is safe or genuine, or before opening or acting on it.
Everything here is static and read-only: never open the file in a viewer that
runs scripts, never click its links, never run its code outside a sandbox.

Run two read-only lanes in parallel and combine their findings: file inspection
(below) and organization legitimacy (further below).

## Lane 1 - File inspection (PDF)

1. Work on a copy in a scratch folder. Record the file's size and hash.
2. Expand the structure so the objects are greppable:
   `qpdf --qdf --object-streams=disable in.pdf out.qdf`
3. Search the expanded copy for active or risky content: `/JavaScript`, `/JS`,
   `/OpenAction`, `/AA` (additional actions), `/Launch`, `/EmbeddedFile`,
   `/URI`, `/SubmitForm`, `/GoToR`. Any hit is a finding to report, not proof of
   malice; a bare `/URI` on a link is common.
4. Forms: list the form fields and where a submit action posts. Flag fields
   asking for identity numbers, bank details, or passwords.
5. Encryption or password protection on an unsolicited file is a red flag.
6. Annotations: compare each link annotation's target (a `mailto:` or URL)
   with the text shown on the page; a mismatch is a finding.
7. Extract the visible text (`pdftotext`) and look for hidden text (white on
   white, off-page, tiny font) and for QR codes; decode QR codes read-only and
   treat the target as untrusted.
8. Report: the active-content hits, the field list, the link mismatches, and a
   verdict of clean, suspicious, or not determinable.

## Lane 2 - Organization legitimacy

1. Lookalike domain: compare the sender's domain with the organization's real
   domain character by character (a missing or swapped letter, a different
   top-level domain). Check registrant privacy, domain age, and expiry through
   a domain-lookup page fetch; a very young or privacy-masked domain on a
   claimed established company is a finding.
2. Compare the invitation's sender domain and name with the real organization's
   public staff or contact list.
3. Cross-check the sender against any existing legitimate mail thread with the
   same organization: a new "recruiter" or "vendor" who is not in the known
   thread, or a different reply-to address, is a finding.
4. Prefer the organization's own published contact route over any link or
   number in the message.

## Rules

- Take-home code, installers, or macros from an unknown sender run only in a
  sandbox (a disposable VM or container with no credentials), never on the
  user's machine. See `workflows/third-party-installer-vetting.md` when it
  applies.
- Report findings with the evidence (the object name, the compared strings),
  not a bare "looks fake". Say what was not checked.
- Do not reply, click, or send documents to the sender as part of triage; the
  user decides the next step. Replies follow `rules/human-comment-reply-gate.md`.
