---
title: A re-index of a vector store is not done until the stack is restarted and a stored vector is read back
category: testing
created: 2026-11-24
tags: [vector-database, re-index, acceptance-test, restart, validation-gap, state-change]
---

# Problem
A full re-index of a vector store was marked done on counts alone. The service then crashed after
its next restart. The session classed this as a high-severity validation gap: the state change was
not tested across a restart.

# Failed Approaches
- Accepting the re-index because the counts looked right. The record does not state which counts
  were compared. This passed the check, and the crash appeared only after the next restart.

# Solution
Make the acceptance check restart the whole stack after the re-index and then read back a stored
vector with a per-vector lookup. Count the re-index as done only when both succeed. The recorded fix
was a restart plus a per-vector lookup in the acceptance test.

# Why
Counts describe what was written, not whether the service can load and serve it again after a
restart. Inference, not observed: a count check cannot see damage that appears only when the index
is loaded again, which is why the restart and the vector read are the checks that exposed the
failure. The record does not state the underlying defect.
