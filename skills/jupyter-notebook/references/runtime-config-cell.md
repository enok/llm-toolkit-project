# Runtime Config Cell for Notebooks

Hardcoded bucket and profile names in code cells leak into committed notebook outputs and are not portable across environments. Environment-specific values live in configuration files or environment variables; `config/runtime_config.json` exists for this purpose. Replace the hardcoded values (by script, since `.ipynb` is JSON) with a config-loading cell:

```python
import json as _json

_rtcfg_path = os.path.join('..', 'config', 'runtime_config.json')
if os.path.exists(_rtcfg_path):
    with open(_rtcfg_path) as _f:
        _rtcfg = _json.load(_f)
else:
    _rtcfg = {}

S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', _rtcfg.get('aws', {}).get('s3_bucket_name', ''))
AWS_PROFILE = os.environ.get('AWS_PROFILE', _rtcfg.get('aws', {}).get('profile', None))
```

Reference `S3_BUCKET_NAME` and `AWS_PROFILE` throughout the notebook instead of hardcoded strings.

Critical: never add `print()` statements for `S3_BUCKET_NAME` or `AWS_PROFILE`; they leak into committed notebook outputs.
