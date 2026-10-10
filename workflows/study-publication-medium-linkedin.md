---
description: Publish a merged study repo as a Medium article and a LinkedIn post with AIDA structure, role-positioned titles, README link PRs, bidirectional back-links, and separate approval gates (Phases 7-10 of study-repo-to-publication)
---

# Study Publication: Medium And LinkedIn

Phases 7-10 of `workflows/study-repo-to-publication.md`, split out so both files stay under the size limit; it also runs on its own once the repo is merged and green. Output: a Medium story and a LinkedIn post that link to the repo and to each other in both directions, with the README links merged.

Route through `rules/request-orchestration.md`. The root agent owns all writes, external mutations, and user communication. Constraints: `rules/external-write-authorization.md`, `rules/human-comment-reply-gate.md`, `rules/git-conventions.md`. Browser steps run on the user's machine in the signed-in session; bot checks and captchas go to the user.

Inputs: the merged repo (default branch, merge commit SHA), the tag list (`skills/multi-language-study-repo/references/tags-and-topics.md`), the fact table and principles page, and the intake answers (content angle, target role, approval gates; Phase 0 of the parent). The parent's Known pitfalls on diagram size at the destination and device-commit filenames apply here too.

Merge rule (Phases 8 and 10; same as Phase 6 of the parent): merge only after the user names the specific PR number and base branch in the current session; when CI is green, state both and ask (the intake gate list is not that approval). Merge with squash.

## Phase 7 - Medium Draft, Approval, Publish

Build from the merged repo content, never from memory, in the intake angle order (`skills/medium-publishing/references/content-angle.md`), framed by AIDA (Attention, Interest, Desire, Action), with title and subtitle on the highest-level concept the body supports for the author's target role (`skills/medium-publishing/references/aida-narrative.md`). Use `skills/medium-publishing`: paste-ready HTML (`build`, then `check` until clean) with images pinned to the merged commit SHA.

1. Creating the draft in the user's account is an external write. Show title, subtitle, topics, preview image, the AIDA stage map, and the full article text, labelled `NOT POSTED`, in its own message; ask for approval in a separate turn before creating anything.
2. After approval, paste into a new story and verify in the editor DOM: image count, code-block count and languages, SHA-256 of each block against its repo file, no Markdown leftovers.
3. Fill the publish dialog (title <= 100 characters, subtitle <= 140, <= 5 topics read back as chips; diagram as preview) and stop. Report the verification, ask for the publish approval as its own question; material edits need a new approval.
4. After explicit publish approval, publish, verify the public page after the redirect, record `<story-url>`.

## Phase 8 - README Link PR

Branch plus PR that adds `<story-url>` to the repo README. CI green, then merge under the merge rule.

## Phase 9 - LinkedIn Post With Diagram

1. Draft the post text in AIDA order with the hook at the highest-level concept the body supports (`skills/medium-publishing/references/aida-narrative.md`): Attention hook inside the first ~200 characters, Interest in 2-3 lines, Desire as short items with results and the principles line, Action as `<story-url>` (the primary call to action) plus the repo link and one specific question, hashtags per `tags-and-topics.md` last. Well-known topic: hook = the non-obvious application, image = the architecture-application diagram (else the strongest); one line names the main principles; re-check at feed size.
2. Show the full text, the AIDA stage map, and the image, labelled `NOT POSTED`, in their own message; ask for approval in a separate turn.
3. After explicit approval follow `skills/linkedin-publishing`: image first, text verified by hash; report the hash match and image preview, get a separate go-ahead to click Post, then post, record `<post-url>`, decline boost prompts.
4. Earlier post: edit text or alt text in place. New image: post anew, edit a `More... <post-url>` first line into the old post, repoint the article and README links; delete the old post only if asked (`skills/linkedin-publishing/references/repost-and-delete.md`). Each is its own approval.

## Phase 10 - Back-Links

Edit the Medium story to add `<post-url>`: show the exact change labelled `NOT POSTED`, get approval, apply, "Save and publish", verify on the public page. Open a README PR adding `<post-url>`, CI green, merge under the merge rule. Final check: all six links resolve (repo, Medium, LinkedIn each point to the other two).

Adding AIDA or a positioned title to an already published story or post is the same kind of edit, in place: `skills/medium-publishing/references/aida-narrative.md` (Retrofitting a published piece).

## Known pitfalls

- Put a single space on blank lines inside code blocks before pasting into Medium, then check one code box per listing. (sig: platform-quirk/medium-blank-line-splits-code-block)
- Enforced by `skills/linkedin-publishing/scripts/check_upload_target.py` on every upload snippet; never click Send. (sig: safety-near-miss/linkedin-file-input-is-messaging)
- Click the exact topic suggestion in Medium's publish dialog and read the chips back; Enter adds the first suggestion. (sig: platform-quirk/medium-topic-autocomplete-swaps-topic)
- Attach the LinkedIn diagram before pressing Post; media cannot be added afterwards. (sig: platform-quirk/linkedin-no-media-after-publishing)
- Entity-encode non-ASCII characters before putting HTML on the Windows PowerShell 5.1 clipboard. (sig: env-constraint/powershell-clipboard-html-mangles-non-ascii)
- Scan the editor's rendered HTML, not only the source Markdown, for leftovers such as `](http`. (sig: validation-gap/markdown-leftovers-in-rendered-html)
- Structure every article and post as Attention, Interest, Desire, Action, show the stage map with the draft, and title it at the highest-level concept the body supports. (sig: spec-gap/post-missing-aida-structure)
