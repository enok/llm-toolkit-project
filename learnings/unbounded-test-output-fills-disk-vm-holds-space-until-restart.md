---
title: A test that wrote a huge sparse index file filled the disk; deleting it did not free space until the container VM restarted
category: environment
created: 2026-11-24
tags: [disk-space, sparse-file, container, virtual-machine, test-output, tool-misuse]
---

# Problem
A test wrote a huge sparse index file. After the file was deleted, the space stayed held by the
container virtual machine until that VM was restarted. The session classed this as a high-severity
tool misuse: unbounded test output filled the disk.

# Failed Approaches
- Deleting the file. The delete succeeded but did not return the space.

# Solution
- Bound the size of what a test writes.
- Check free space before and after a test that writes large files.
- If space stays held after a delete, restart the container virtual machine to release it.

# Why
The record states that the space remained held by the container virtual machine until it restarted.
The record does not state the mechanism. Inference, not observed: the VM's disk image does not
shrink when a file inside it is deleted, so the host sees the space as used until the VM restarts.
