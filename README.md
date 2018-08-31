![Mimir3](mimir_logo_small.png)

![Coverage](https://img.shields.io/badge/pytest--cov-91%25-green.svg?longCache=true&style=flat-square)

Custom Database

# General

# Testing
Testing functionality is implemented using `py.test` in the `tests/` directory.      
Run test from repository root directory with the `runTests.sh` script:
```
#Run all tests
./runTests.sh all 
#Run a single test with
./runTests.sh tests/test_[testname].py
```
Adding `cov` as second argument will also run the [pytest-coverage](https://pypi.org/project/pytest-cov/) module and will produce html.
