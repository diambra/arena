# Development

## Release
- Bump version in setup.py
- Install build and twine:
```
python3 -m pip install --upgrade build
python3 -m pip install --upgrade twine
```
- Create `~/.pypirc`:
```
[pypi]
  username = __token__
  password = pypi-XXX
```
- Build and upload package:
```
python3 -m build
python3 -m twine upload --repository pypi dist/*
```