---
title: Coding-round patterns in Java - cues, skeletons, complexity, edge cases
tags: [interview, coding-round, java, hashmap, merge, heap, priority-queue, two-pointers, sliding-window, regex, complexity]
---

# Coding-Round Patterns In Java

Short (10-20 minute) coding rounds draw from a small set of patterns. Recall the
skeleton for the pattern, then fill in the problem. Every solution below states
time and space separately.

## Pattern Cue Table

| The prompt says... | Pattern | Skeleton |
| --- | --- | --- |
| count, frequency, group by, deduplicate | hash map | `map.merge(key, value, combiner)` |
| top K, K largest or most frequent | heap of size K | offer, poll when size > K |
| palindrome, pair from both ends, sorted pair sum | two pointers converging | `i` from start, `j` from end, `while (i < j)` |
| longest or shortest contiguous substring/subarray with a condition | sliding window | expand `right`, shrink `left` while invalid, measure |
| keep most recent per key, preserve first-seen order | `LinkedHashMap` + `merge` | resolver keeps the newer value |

When blank: say the brute force aloud with its complexity (all substrings is
O(n^2) to enumerate, O(n^3) with a check), then ask "what am I recomputing?" -
that question usually lands on one of the rows above.

## The `Map.merge` Idiom

`map.merge(key, value, fn)` inserts `value` when the key is absent; otherwise it
stores `fn.apply(oldValue, value)`. `freq.merge(w, 1, Integer::sum)` is a
counter: first sighting stores 1, every later sighting stores old + 1
(`Integer::sum` is not called on the first sighting). It appears in two of the
three most common warm-up problems below.

## Top-K Frequent Words (ties alphabetical)

```java
public List<String> topKFrequent(String[] words, int k) {
    Map<String, Integer> freq = new HashMap<>();
    for (String w : words) freq.merge(w, 1, Integer::sum);
    PriorityQueue<Map.Entry<String, Integer>> heap = new PriorityQueue<>(
        (a, b) -> a.getValue().equals(b.getValue())
            ? b.getKey().compareTo(a.getKey())          // tie-break inverted
            : Integer.compare(a.getValue(), b.getValue()));
    for (Map.Entry<String, Integer> e : freq.entrySet()) {
        heap.offer(e);
        if (heap.size() > k) heap.poll();              // drop the weakest
    }
    LinkedList<String> result = new LinkedList<>();
    while (!heap.isEmpty()) result.addFirst(heap.poll().getKey());
    return result;
}
```

- **Min-heap by frequency.** A comparator returning negative when `a` should come
  first puts the smallest frequency on top, so `poll` always removes the weakest
  candidate. `PriorityQueue` is Java's binary-heap implementation.
- **Inverted tie-break.** On equal frequency, `b.getKey().compareTo(a.getKey())`
  puts the alphabetically larger word on top, so it is the one discarded and the
  alphabetically smaller words survive. Example, k = 2, `apple`, `banana`,
  `cherry` all at 3: after the third offer the heap holds three, and `poll`
  removes `cherry`.
- **Reversal.** Polling a min-heap yields weakest first; `addFirst` reverses it,
  so the result runs from most to least frequent.
- **Complexity.** Time O(n + m log k) - n words to count, m distinct words each
  offered to a heap capped at k. Space O(m) for the map. Sorting all entries
  instead would be O(m log m).
- **Edge cases.** Empty input, k = 0, k larger than m, all ties.

## Palindrome Ignoring Punctuation And Case

```java
public boolean isPalindrome(String s) {
    int i = 0, j = s.length() - 1;
    while (i < j) {
        while (i < j && !Character.isLetterOrDigit(s.charAt(i))) i++;
        while (i < j && !Character.isLetterOrDigit(s.charAt(j))) j--;
        if (Character.toLowerCase(s.charAt(i++)) != Character.toLowerCase(s.charAt(j--))) {
            return false;
        }
    }
    return true;
}
```

Time O(n), each character visited at most once. Space O(1): two indexes, no new
structure. Edge cases: empty string, only punctuation, single character.

## Deduplicate Records By A Normalised Key, Keeping The Newest

```java
record Profile(String id, String email, String name, Instant updatedAt) {}

private static final Pattern EMAIL = Pattern.compile("[^@\\s]+@[^@\\s]+\\.[^@\\s]+");

public List<Profile> dedupeByEmail(List<Profile> profiles) {
    Map<String, Profile> byEmail = new LinkedHashMap<>();
    for (Profile p : profiles) {
        if (p.email() == null) continue;
        String key = p.email().strip().toLowerCase(Locale.ROOT);
        if (!EMAIL.matcher(key).matches()) continue;
        byEmail.merge(key, p, (a, b) -> b.updatedAt().isAfter(a.updatedAt()) ? b : a);
    }
    return new ArrayList<>(byEmail.values());
}
```

- **Order.** `LinkedHashMap` keeps first-insertion order, and replacing a value
  through `merge` keeps the key's original position, so output follows first
  appearance.
- **`Locale.ROOT`.** `toLowerCase()` without a locale uses the machine default;
  under a Turkish locale `I` does not lower-case to `i`, so the same address
  could become two keys. `Locale.ROOT` makes normalisation deterministic.
- **The regex, piece by piece.** `[^@\s]` is a negated character class: the
  leading `^` inside brackets negates every member, so it means "any character
  except `@` or whitespace" (without the `^` it would mean "only `@` or
  whitespace"). `+` applies to the whole bracket group: one or more. `@` is a
  literal. `\.` is an escaped, literal dot (an unescaped `.` matches any
  character - a classic bug). The shape is: something `@` something `.`
  something.
- **Say this in the interview.** The pattern is deliberately pragmatic; full
  RFC 5322 validation by regex is impractical, and an address is only proven by
  a verification email. Compile the `Pattern` once, outside the method.
- **Complexity.** Time O(n), space O(n). Edge cases: null email, whitespace and
  case variants, invalid format, null `updatedAt`, equal timestamps.

## Longest Substring Without Repeating Characters (sliding window)

```java
public int lengthOfLongestSubstring(String s) {
    Set<Character> window = new HashSet<>();
    int left = 0, best = 0;
    for (int right = 0; right < s.length(); right++) {
        char c = s.charAt(right);
        while (window.contains(c)) {        // invalid: shrink from the left
            window.remove(s.charAt(left++));
        }
        window.add(c);                       // expand on the right
        best = Math.max(best, right - left + 1);
    }
    return best;
}
```

Optimised follow-up - jump `left` using each character's last index:

```java
Map<Character, Integer> last = new HashMap<>();
int left = 0, best = 0;
for (int right = 0; right < s.length(); right++) {
    char c = s.charAt(right);
    if (last.containsKey(c) && last.get(c) >= left) left = last.get(c) + 1;
    last.put(c, right);
    best = Math.max(best, right - left + 1);
}
```

- **Skeleton to memorise.** Expand with `right` in the `for`; shrink with `left`
  while the window is invalid; measure `right - left + 1`.
- **The `>= left` guard** ignores an old occurrence that is already outside the
  window; without it `left` can jump backwards.
- **Traps.** `"pwwkew"` -> 3 (`"wke"`); `"pwke"` is a subsequence, not a
  substring. Empty string -> 0; all identical -> 1.
- **Complexity.** Time O(n): each character enters and leaves the window at most
  once. Space O(min(n, alphabet size)).

## Heap Versus Stack (a common clarifying question)

A stack is LIFO: the top is whatever arrived last, values are ignored. A heap
orders by value through its comparator: the top is the highest-priority element
whenever it arrived. Both expose a "top", the rule that picks it differs.

## Complexity Claims Checklist

- Space is O(1) only when nothing grows with the input.
- Name what each variable counts (n total items, m distinct items, k heap size).
- Give the dominant term and say why the alternative (sorting everything, nested
  loops) is worse.
