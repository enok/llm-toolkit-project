---
title: A JSON nesting guard that waits for RecursionError behaves differently across Python versions
category: testing
created: 2026-11-24
tags: [python, json, recursion-error, hostile-input, interpreter-version, run-retrospective, ci-matrix]
---

# Problem

On a machine running Python 3.15, three hostile-input tests of the run-retrospective script
failed on the default branch. The tests expect deeply nested JSON to raise a `ValueError`
reported as "JSON nesting is too deep". On that interpreter the parser returned a value
instead, so the script answered "record must be a JSON object" or fell back to the
line-size limit. The same tests passed on Python 3.13.

What the source shows (read in the authoring session): the guard in
`skills/run-retrospective/scripts/run_retro.py` (`parse_json`, lines 412-417) calls
`json.loads` and converts `RecursionError` into `ValueError("JSON nesting is too deep")`.
It has no depth check of its own; it only works if the interpreter raises. The tests are in
`HostileInputTests` in `tests/test_run_retro.py` (lines 1457-1497): inputs of 4,000 to
50,000 nested brackets are expected to be rejected.

Not root-caused: whether the JSON decoder stopped raising on deep nesting or the recursion
limit changed in the newer interpreter.

Reproduced when this entry was promoted, in a fresh checkout of the default branch on
Python 3.15.2: `python3 -B -m unittest tests.test_run_retro.HostileInputTests` ran 10 tests
with 3 failures. `test_parse_json_turns_runaway_nesting_into_value_error` reported
"ValueError not raised"; `test_commands_survive_a_nested_line` and
`test_append_of_nested_input_is_exit_1` got "record must be a JSON object" (the first also
the line-size limit) where "too deep" was expected. The full suite there ran 578 tests with
the same 3 failures. On Python 3.13.18 the same 10 tests passed.

# Failed Approaches

None recorded beyond the first attempt described in Problem.

# Solution

No fix is recorded as applied. Candidate fix, NOT implemented and NOT tested: make the guard
explicit instead of relying on the interpreter raising. Either count bracket depth before
parsing (skipping string contents), or bound the depth in the validator, and reject input
above a fixed limit with the same "JSON nesting is too deep" message. Also run the unit
tests on the newest interpreter in CI, so a change in interpreter behaviour shows up there
and not on a user's machine.

# Why

A guard that depends on a `RecursionError` depends on interpreter internals (decoder
implementation and recursion limit), which are not part of the JSON contract and can
change between releases. General guidance, not observed in this session: a depth limit
the code enforces itself gives the same answer on every interpreter. Until then, a test run
on a single interpreter version says nothing about the hostile-input tests on another.
