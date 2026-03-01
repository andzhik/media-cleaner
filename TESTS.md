# Running Tests

## All tests (backend + worker)

```bat
run_tests
```

## Backend only

```bat
cd backend
python -m pytest
```

## Worker only

```bat
cd worker
python -m pytest
```

## Useful flags

```bat
run_tests -x                        # stop on first failure
run_tests -k test_security          # run tests matching a name pattern
run_tests -v                        # verbose output

python -m pytest --cov=backend --cov-report=term-missing        # backend coverage
python -m pytest --cov=worker --cov-report=term-missing         # worker coverage
```

## First-time setup

```bat
cd backend && pip install -e ".[dev]"
cd worker  && pip install -e ".[dev]"
```
