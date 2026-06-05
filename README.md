# artemis_gnss
<b>A</b>utomated <b>R</b>econstruction of <b>T</b>rips and <b>E</b>xtraction of <b>M</b>obility <b>I</b>ndicators from GNSS <b>S</b>ignals

<img src="https://raw.githubusercontent.com/Mobidec/artemis_gnss/refs/heads/main/doc/assets/France2030-Logo-1024x576.png" alt="logo">


---


## Description

This package is under development. It consumes geospatial timeseries coming from e.g. GNSS acquisitions or other geolocalisation methods.
The features planned to for implementation are the following:
- [ ] Extraction of individual displacements, origin/destination, POIs; 
- [ ] Projection of a trace on a map system; 
- [ ] Identification of the means of transport; 
- [ ] Identification of the motivation class of a trip; 
- [ ] Marking missing, abnormal or inconsistent parts of a trace; 
- [ ] Anonymization of a trace. 


## Definitions

- A _trace_ is a geospatial timeseries with at least a timestamp, a latitude and a longitude for each data point.
- A _unitary displacement_ is the movement between two stops.
- A _trip_ groups unitary displacements using a same means of transport.
- A _displacement_ groups trips, from an origin to its final destination. It is usually associated to one motivation class.


## Useful links

Links to resources and documentation:
- [Documentation](https://mobidec.github.io/artemis_gnss/index.html)
- [GitHub Repository](https://github.com/Mobidec/artemis_gnss.git)
- [Issues](https://github.com/Mobidec/artemis_gnss/issues)
- [Changelog](https://github.com/Mobidec/artemis_gnss/blob/main/CHANGELOG.md)
- [PyPI](https://pypi.org/project/artemis_gnss/)


## Python Package Template Architecture


```
.
├── sphinx
│   ├── pages
│   │    └── Directory for pages to include in sphinx documentation
│   ├── notebooks
│   │    └── Directory for Jupyter Notebooks to include in sphinx documentation
│   ├── conf.py
│   │    └── Sphinx documentation configuration file
│   └── index.rst
│        └── Root file for Sphinx documentation, structuring and linking source documents into complete documentation.
├── src
│   └── artemis_gnss
│        ├── __init__.py
│        ├── main.py
│        │    └── Main file of your package, it references what is usable in your package
│        └── module_name
│             ├── __init__.py
│             └── module.py
│                  └── Module file, each module holds a logic of the package
├── tests
│   ├── unit
│   │    └── Directory for unit tests. These tests are run after each push.
│   ├── integration
│   │    └── Directory for integration tests. These tests are run after each push.
│   ├── local
│   │    └── Directory for tests run only locally. These tests are not run with Github actions.
│   └── ignored
│        └── Directory for tests run manually. These tests are ignored by the command pytest.
├── .gitattributes
│    └── Ensures that all text files use LF as the line ending, improving consistency across different development environments.
├── .bumpversion.toml
│    └── Configuration file for bumping the package version
├── .gitignore
│    └── File explicitly instructed for Git to ignore
├── .github
│    └── workflows
│         └── Github Ci/CD files
├── .pre-commit-config.yaml
│    └── Pre-commit configuration file
├── CONTRIBUTING.md
│    └── Contribution guidelines file
├── LICENSE
├── README.md
│    └── File with general information about the project
├── pyproject.toml
│    └── Package configuration file
└── tox.ini
     └── Configuration file for `tox`, used to automate testing and linting tasks across multiple Python environments. This file is configured to use Python 3.12 and runs commands for the linter `ruff` as well as for tests with `pytest`. The specified commands check code style, format files according to defined standards, and run unit tests to ensure the code works as expected. This file is also used to facilitate version management tasks with `bump-my-version`.
```


## Getting Started

### Prerequisites

This project requires **Python 3.12**. Python 3.12 introduces many new features and improvements that are essential for the proper functioning of this project. Ensure that Python is correctly installed on your system by running `python --version`.


### About the `pyproject.toml` File

The `pyproject.toml` file is a central configuration file for the Python project. It contains TOML tables specifying the basic metadata of the project, the dependencies needed to build your project, and specific configurations for the tools used.
The `[project]` table is used to specify the basic metadata of your project, such as dependencies, your name, etc. The `[tool]` table contains sub-tables specific to each tool, such as `[tool.setuptools]` or `[tool.ruff]`. For more information on configuring your `pyproject.toml`, refer to the [Python documentation](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/).


### Installing Dependencies

The `pyproject.toml` file is used to manage the dependencies of this project. To install these dependencies, follow these steps:

1. Open a terminal and navigate to the project directory.
2. Run the command `pip install .` to install the necessary dependencies for the project.

This process ensures that all required dependencies are correctly installed in your environment, allowing you to work on the project with all necessary resources.

To add or modify project dependencies, you must list them in your `pyproject.toml` file under the `dependencies` section.

```bash
dependencies = [
    # add necessary dependencies
    "pytest == 8.0.1",  # example which can be removed
]
```


### Developing the Package

The `CONTRIBUTING.md` file is an essential guide for developing this Python package. It describes the steps to set up the development environment, the coding conventions to follow, and how to submit changes. 
Once your changes are ready, push your contribution to the desired branch to trigger the integration pipeline, which will create the Python package and deploy it to the Python server.
For more details on contributing and best practices, please refer to the `CONTRIBUTING.md` file.


## Using the Python Package

### Installation

Run:

```bash
pip install artemis_gnss
```


### Example Usage of the Python Package in Your Code

After installation, you can import and use your package and its functions in your Python code:

```python
from package import hello_world

hello_world()
```

To use sub-modules defined in the package:

```python
from package.divider import divide

a = 4.0
b = 2.0

c = divide(4., 2.)
```

These instructions will allow you to access the package and utilize its features effectively and in line with your development configuration.


## License

This project is licensed under the MIT License, which means it is freely usable for personal and commercial purposes. The MIT License is one of the most permissive open source licenses. It allows you to do almost anything with the source code, as long as you retain the original license notice and copyright information when redistributing the software or substantial portions of it. This license comes without any warranties, so the software is provided "as is." For more details, please refer to the included LICENSE file.

---