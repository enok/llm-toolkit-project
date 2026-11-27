# Sync run state: what a later scheduled run must see

Detail for the Known pitfalls in `workflows/knowledge-base-sync.md`. The sync is a scheduled routine, so every run starts without memory of the last one. State that exists only on the machine, or only in a side document, is invisible to the next run's preflight unless the preflight is told to look for it. Evidence labels are kept exactly: "observed", "observed once", "predicted, not observed", "untested", "candidate".

## An unposted local sync commit

Problem: a sync that cannot push (no credential on the machine) ends with its commit only on the local rolling intake branch. Nothing records that state where the next run decides whether there is work: the inbox items stay pending, no pull request exists, and Phase 5 starts by removing the earlier worktree and re-creating the branch from the default branch with a reset.

- Predicted, not observed: a run that resets the branch drafts and validates the same items again and orphans the earlier commit, on every run until the owner signs in.
- Observed in two later runs: the local branch was ahead of the default branch, had no remote counterpart and no pull request, and the default branch had not moved (it was an ancestor of the local branch). Both runs kept the branch instead of resetting it. The second read the inbox names listed in the commit message, treated those items as in flight, ran the intake check on every item, and added new commits on top. The branch stayed a fast-forward of the default branch; the push was attempted once and reported with its command.
- Candidate fix, untested as a written workflow step: in preflight, when the local rolling branch is ahead of the default branch and has no remote counterpart, treat the inbox items named in its commit message as in flight, skip drafting them, repeat the push probe, and only push (when the standing authorization is recorded) or report the push command. Reset the branch only when it is an ancestor of the default branch.
- Interim practice, used once: list the covered inbox names in the commit message and keep a patch file of the commit outside the repository.
- Untested limits: the default branch moving between runs (the local commits would need a rebase, or a fresh branch with a cherry-pick); a covered inbox item changing after its commit; a branch whose commit messages do not list the inbox names.
- Observed: items whose destination file is not on the default branch yet were deferred and stay pending, so every later run meets them again. Candidate, untested: a recorded deferral list that the preflight reads, so they are not classified again.

## Finished work parked in a side document

Rule: a run that parks finished work (drafts, checksums, a state description) in a side document must leave a pointer where the next run's preflight looks, and the next run reads the routine's hand-off documents before it drafts anything.

Observed once: a scheduled sync lost its connection to the machine after three drafts had been validated and before anything was written, so it parked the drafts with checksums in one document and described the state in a second. The next run's stored prompt and preflight listed the inbox, the run log, the pull request, past chats and memory as sources, but not those documents, and the status command showed nothing about them. That run did not open them, drafted and validated the same three items again (six review lanes plus one refinement round each), committed its own versions, and found the parked drafts only while writing its report. Nothing wrong reached the repository, but the drafting cost was paid twice and the parked drafts were superseded.

Happy path, not yet tested:

- Name the hand-off document in the stored prompt as the first thing to read.
- Or keep the parked state in the routine's own scratch area, where the status command or preflight already looks: a state file next to the worktree, or a marker on the inbox item.
- Agent side: when a session lists documents that the same routine wrote earlier, read them before deciding there is work.

## Overlapping runs of one routine

General guidance (single-run guard, mtime guard, integrity audit): `workflows/automation-maintenance.md` › "Catch-up runs and overlapping sessions". Only what is specific to the sync is here.

Observed once for the sync, and a second observation of overlap overall (a different routine and trigger from the first): two runs of the same routine were active within one minute of each other, because the earlier run's slot was delivered about two hours late and started just before the next slot; the cause of the late delivery is not known. Both did the same pre-check and source comparison, each stored a watermark (the later value won), and both went on to add the same dated section to the shared state file kept next to the worktree. No damage: neither had anything to write to the repository, and the second edit of the state file stopped by itself because its script asserted that the anchor line matched exactly once before writing, and the first run had already changed that line. The decision phase was paid for twice.

Risk when there is work: two writers in one worktree and on one rolling branch, the same inbox item distilled twice, two commits for the same items, and a watermark stored by a run that did not handle the records.

Proposed, not implemented, not tested:

1. The first step after the pre-check reads a run marker in the scratch folder (run id and start time). A marker younger than the expected length of a run means another run is active: report that and stop without writing anything.
2. Otherwise write the marker, and remove it as the last step.
3. Keep every edit of a shared state file anchored and idempotent (assert the anchor matches exactly once before writing).
4. Store the watermark only after the records were handled (already Phase 10 step 1).

## Another open pull request already carries the rolling branch

Phase 0 handles three states: an open pull request for the rolling branch, a merged one, and none. A fourth is not covered: no pull request exists for the rolling branch, but a different open pull request already contains it. Read literally, the workflow would open a second pull request whose whole diff is a subset of the first. Observed in one run only.

Proposed happy path (untested as a workflow step): list open pull requests, then for each head run

```bash
git merge-base --is-ancestor <rolling-branch-tip> <other-pull-request-head>
```

If it exits 0, record that pull request as the carrier and treat the inbox items named in the rolling branch's commits as in flight; add no commit and open no pull request; re-evaluate when the carrier merges or closes.

Untested: a carrier merged by squash (there the same test run on the rolling branch against the default branch would fail); a carrier closed without merging, where opening the usual pull request is expected.
