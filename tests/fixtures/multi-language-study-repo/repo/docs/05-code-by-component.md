# Code by component - Python and JavaScript

Each role of the pattern is shown in every language. Files are shown whole.

1. [Strategy interface](#1-strategy-interface)
2. [Client (demo)](#2-client-demo)

## 1. Strategy interface

The Strategy declares the single operation every interchangeable algorithm offers.

<details open>
<summary><b>Python 3</b> · <code>strategy.py</code></summary>

<!-- source: python/src/strategy.py -->
```python
"""Strategy contract of the fixture repo."""
from typing import Protocol


class Greeting(Protocol):
    def greet(self, name: str) -> str:
        ...
```

</details>

<details>
<summary><b>JavaScript (ES2026)</b> · <code>strategy.js</code></summary>

<!-- source: javascript/src/strategy.js -->
```javascript
// Strategy contract of the fixture repo.
export const greeting = (name) => `Hello, ${name}`;
```

</details>

## 2. Client (demo)

The client wires the pieces together and prints the result.

<details open>
<summary><b>Python 3</b> · <code>demo.py, __main__.py</code></summary>

<!-- source: python/src/demo.py -->
````python
"""Client of the fixture repo.

Expected output:

```
hello
```
"""


def main() -> None:
    print("hello")
````

<!-- source: python/src/__main__.py -->
```python
from .demo import main

main()
```

</details>

<details>
<summary><b>JavaScript (ES2026)</b> · <code>demo.js</code></summary>

<!-- source: javascript/src/demo.js -->
```javascript
import { greeting } from "./strategy.js";

console.log(greeting("world"));
```

</details>
