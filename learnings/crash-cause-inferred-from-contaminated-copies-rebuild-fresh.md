---
title: A crash blamed on the engine came from test copies of an already damaged index; build fresh from empty, one variable at a time
category: testing
created: 2026-11-24
tags: [debugging, root-cause, wrong-assumption, contaminated-copy, vector-database, one-variable]
---

# Problem
A crash was blamed on the database engine. Every test copy used to reach that conclusion was
derived from an already damaged index, so the tests could not tell the engine from the damage.

# Failed Approaches
- Testing with copies of the existing index. Each copy carried the same damage, so the crash
  reproduced every time and pointed at the wrong cause.

# Solution
Build a fresh index from empty, once inside the suspect folder and once outside it, changing one
variable at a time. The comparison separates the folder from the engine.

# Why
A copy inherits the defect of its source, so a repeatable crash on copies says nothing about the
engine. Inference, not observed: starting from empty removes the inherited damage, and varying one
factor at a time lets a difference be attributed to that factor.
