![Mimir3](mimir_logo_small.png)

![PythonVersion](https://img.shields.io/badge/python-3.7-blue.svg?longCache=true&style=flat-square)
![Coverage](https://img.shields.io/badge/pytest--cov-79%25-yellow.svg?longCache=true&style=flat-square)
![Tests](https://img.shields.io/badge/Test%20passing-false-red.svg?longCache=true&style=flat-square)

Custom Database

# General
Mimir3 aims to be a database for files on the file system. The database is initialized on a folder and crawls each subdirectories for certain kind of files (defined in model). Once initialized, Mimir3 will keep track of files, starting form its root directory.
## Database model
A database consists of `Entries` that are indexed by the path+name of the file (in the `mainDB.json` file). Each Entry consists of multiple items. An item always consists of a pair of objects. The first is the `name`, which is used for referencing the item. The second object depends on the type of item. that can be of two types:
* `Single` : `Items` that can only have one `value`
* `List` : `Items` can have multiple `values`

## Terminal Frontend (MTF)
Run with
```bash
python runMTF.py --folder path/to/initialized/folder
```

On the test folder structure it can be run after running `test_mtf_base.py` with
```bash
python runMTF.py --folder tests/testStructure/
```

# Testing, code quality, documentation
## Testing framework
Testing functionality is implemented using `py.test` in the `tests/` directory.      
Run test from repository root directory with the `runTests.sh` script:

```bash
#Run all tests
./runTests.sh all
#Run a single test with
./runTests.sh tests/test_[testname].py
```

Adding `cov` as second argument will also run the [pytest-coverage](https://pypi.org/project/pytest-cov/) module and produce the html output.

## Code quality
A configuration file for pylint is provided. Run with
```bash
python -m pylint [module]
```

## Documentation
Documentation can be generated with `sphinx`. To generate the documentation do:
```bash
cd docs/
make html
```
*Note: The Makefile was modified (from the standard configuration) to make it independent of system `python/`sphinx-build`.*

The `.rst` were created with
```
sphinx-apidoc mimir/ -o docs -n --implicit-namespaces
```
You maybe have to explicitly point to the `sphinx-apidoc` bin directory of you python installation.

# What has a database to do?
[ ] Add entries to database  
[ ] Remove entries from database   
[ ] Read a database  
[ ] Save a database   
[ ] Backup database     
[ ] Find a entry in the database
[ ]  
