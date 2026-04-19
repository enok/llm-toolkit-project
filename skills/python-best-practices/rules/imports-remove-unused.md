---
title: Always Remove Unused Imports
impact: HIGH
impactDescription: Dead imports clutter the namespace, slow startup, and hide real dependencies
tags: python, imports, code-quality, cleanup
---

## Always Remove Unused Imports

When modifying a Python file, remove any imports that are not used. Never leave dead imports behind.

**Incorrect (unused imports left behind):**

```python
import os
import json
import csv          # ← not used anywhere in the file
import boto3
from time import time  # ← not used
import math            # ← not used
```

**Correct (only imports that are actually used):**

```python
import json
import boto3
```

- Check every import against actual usage in the file before committing.
- Wildcard imports (`from Module import *`) are exempt from this rule when they are the established pattern in the codebase.
- When adding new imports, verify they are actually needed.
- When removing code, check if its imports became unused.
