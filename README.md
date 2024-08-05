# PTPNperfbound
A performance bound solver for Probabilistic Time Petri Nets

The solver computes:
1. Transitions maximum throughput bound 
2. Transitions minimum cycle times (in case of live nets) and identifies the slowest subnet.

The computation is performed using Linear Programming techniques.

## Structure of the repository


- *dist*: distributions (in ```Wheel``` format and zipped ```tar.gz```)
- *doc*: documentation (see [Solver modules](https://github.com/simber72/PTPNperfbound/blob/main/doc/Solver_modules.md))
- *examples*: PTPN model examples and results
- *src*: source files (solver modules)
- *tests*: source files (test scripts)
- *LICENSE*: license file
- *README.md*: this file
- *README.txt*: short explanation of the solver
- *requirements.txt*: Python libraries required to run the solver
- *pyproject.toml*: setup to package the Python modules and distribute the package

## Dependences
- ```cplex```: the optimization problems are solved using IBM CPLEX Studio or CPLEX Studio Community (up to 1000 variables/ contraints). 

Besides other Python external libraries are needed, which can be installed with
```pip```: all the dependencies are included in the  ```requirements.txt```).

## How to install

The solver can currently run with Python3 (versions 3.8/3.9/3.10).

1. Install a virtual environment of Python3:

```$ python3 -m venv venv```

and activate it:

```$ source venv/bin/activate```

2. Update the pip and setuptools versions:

```python3 -m pip install --upgrade pip setuptools```

3. Install the libraries required to run the solver:

```$ pip install -r requirements.txt``` 

4. The package can be easily installed from the PyPi repository using the command:

```$ pip install PTPNperfbound``` 

In case you clone (or download) this repository, you can install the library using the command:

```$ pip install dist/PTPNperfbound-0.0.1-py3-none-any.whl```

3. Move to the ```PTPNperfbound``` directory and set the Python path environment variable 
to the current path:

```export PYTHONPATH=.```

## How to use

The solver can be run using a Command Line Inferface (CLI):

```ptpnbound --help
Usage: ptpnbound [OPTIONS] NAME TNAME

Options:
  -lp, --lpmodel TEXT          LP model files (CPLEX  models - lp format)
  -lpo, --lpoutput TEXT        Result files (CPLEX model results - xml format)
  -o, --output <TEXT TEXT>     Result file: <name format> (available formats:
                               pnml, dot)
  -v, --verbose                Print results to stdin
  --help                       Show this message and exit.
```
where ```NAME``` is the pathname of the PTPN model (.pnml) and ```TNAME``` is the name of the 
transition of reference for the bound computation. 


## References
S. Bernardi, J. Campos, "A min-max problem for the computation of the cycle time lower bound in interval-based Time Petri Nets," IEEE Transactions on Systems, Man, and Cybernetics: Systems, 43(5), September 2013.

Y. Emzivat, B. Delahaye, D. Lime, O.H. Roux, "Probabilistic Time Petri Nets", HAL Open Science,
https://hal.science/hal-01590900.

T. Le Moigne, "ARPE clinical pathway identification algorithms",  GitLab repository: https://gitlab.crans.org/bleizi/arpe-identification
