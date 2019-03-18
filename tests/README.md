#Test
All tests are written using the `py.test` framework
#Commands
To run a generic test use
```bash
python -m pytest -v  -t ../ test_$$$.py
```

Run with coverage:
```bash
python -m pytest -t ../ test_*.py --cov=backend.entry --cov-report=term-missing --cov-report=html
```
