#Test
All tests are written using the `py.test` framework
#Commands
To run a generic test use
```bash
py.test -v test_$$$.py
```

Run with coverage:
```bash
py.test test_*.py --cov=backend.entry --cov-report=term-missing --cov-report=html
```


