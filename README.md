orgmin
====

Minimize the time spent organizing the time spent minimizing.

The functionality supplied are features that proved useful during the
exploration of numerical algorithms for solving one specific minimization
problem. If the addition or modification of some features could be useful for
anyone then I would be very happy to include changes. Also please just download
the pieces that could be useful to you, and use them in bits as you'd like.


Installation
====

Being a very simple piece of software, you can just download the individual
files that you would like to use and add them to your project. If you would
like whole package then you may clone this repository and install through pip
with
```sh
pip install .
```
from within the top-level directory.


Functionality
====

The docstrings of classes and functions should explain their usage. To explore
them you may use the `help` function in an interactive session:
```python
>>> import orgmin
>>> help(orgmin)
```
```
Help on package orgmin:

NAME
    orgmin

DESCRIPTION
    Package for keeping track of the results of numerical experiments with varying
    hyperparameters, and for storing the results of function minimization.

    Interface:

    - The **Parameters** class for keeping a catalogue of the results of different
      code runs (see README.md or run `help(orgmin.Parameters)`).
    - The **expand_registry** function to expand the registry managed by the
      Parameters class (see README.md or run `help(orgmin.expand_registry)`).
    - The **csv_to_html** function used internally to create simple HTML versions
      of CSV-files (run `help(orgmin.csv_to_html)` for information.
    - The **TargetWrapper** class is a wrapper around a function which is to be
      minimized. It will keep track of the number of function calls and the best
      values obtained during optimization in an instance of
      MinimizationHistory. (See README.md or run `help(orgmin.TargetWrapper)`).
    - The **MinimizationHistory** class is an object which contains the results
      obtained during minimization (see README.md or run
      `help(orgmin.MinimizationHistory)`).
```

The `Parameters` class
----

This is a (base) class for storing parameters for numerical calculations.

When calling the `catalogue` method, all attributes (both instance variables
and `@property`s) not starting with an underscore will be treated as model
parameters and saved to the registry. Callable methods will be ignored. This
allows for more flexible and complex behaviour than storing the results in a
simple container like a dictionary.

```python
>>> from orgmin import Parameters
>>> from pathlib import Path
...
>>> p = Parameters()
>>> p.first_setting = 1
>>> p.second_setting = False
>>> p._hidden_setting = 1.5
>>> p.list = [1, 2, 3]
...
>>> # Directory 'results' must exist beforehand.
>>> path = p.catalogue(Path('results'))
>>> path
PosixPath('results/10000')
...
>>> # run code and save the results in the directory specified by `path`
```
Assuming the directory `results` was empty before this is now its content:
```
.
└── results
    ├── 10000
    ├── registry.csv
    └── registry.html
```
Seeing as there was no registry in the specified folder, the new sample was
given an id of 10 000, and the registry files were created; a CSV file for easy
handling within code and a simple HTML version easily viewed in a web browser.

The `registry.csv` file now contains
```
Sample;Time;first_setting;list;second_setting
10000;2024-02-25-11:06:26;1;[1, 2, 3];False
```

Calling the `catalogue` method again with the same directory `results` is only
possible when the same parameters (instance attributes) are specified. Doing so
will generate a new id, in this case 10 001, create the directory within which
to save the corresponding results, and append the sample with the parameters to
the registry.  If you would to expand the registry with a new parameter not
previously saved use the `expand_registry` function:
```python
>>> from pathlib import Path
>>> from orgmin import expand_registry
...
>>> expand_registry(Path('results/registry.csv'), 'new_setting', '123')
```
This modifies the registry file to include the parameter `new_setting` with the
value `123` in all previously catalogued samples allowing you to log runs with
varying values of this parameter.

To load the parameters of a sample use the `load` method. This returns a
dictionary of strings to strings (improvements possible here).
```python
>>> from pathlib import Path
>>> from orgmin import expand_registry
...
>>> d = Parameters.load(Path('results'), 10000)
>>> d
{
    'Sample': '10000',
    'Time': '2024-02-25-11:06:26',
    'first_setting': '1',
    'list': '[1, 2, 3]',
    'new_setting': '123',
    'second_setting': 'False'
}
```


The `TargetWrapper` and `MinimizationHistory` classes
----

These classes are designed to keep track of the progress of a function
minimizer during its operation.
```python
>>> from pathlib import Path
>>> from orgmin import TargetWrapper, MinimizationHistory
...
>>> def rosenbrock(x):
...     """The Rosenbrock function, 2-dim"""
...     res = sum(100.0*(x[1:]-x[:-1]**2.0)**2.0 + (1-x[:-1])**2.0)
...     return res
...
>>> target = TargetWrapper(rosenbrock, dim=2)
>>> target.history.start_timing()   # if desirable
...
>>> # Do some complicated combination of different minimization algorithms.
... # The best function values along with their locations and the number of
... # function calls will be saved automatically.
...
>>> # Append the final count of function calls to the history to include
... # potential function calls since the last best function value.
>>> target.append_best_evaluation()
...
>>> target.history.stop_timing()            # if desirable
...
>>> # A boolean success flag may be set for later reference.
>>> if some_criterion:
...     target.history.success = True
...
>>> print(target)   # not the results of an actual calculation :)
Content of TargetWrapper: {
  Function evaluations: 14580
  Minimum value: 1e-15
  Minimum x: [ 6.890996e-02 -4.807991e-01]
  History: {
    Function evaluations: 14580
    Minimum value: 1e-15
    Minimum x: [ 6.890996e-02 -4.807991e-01]
    Success: True
    Elapsed time: 6.865109867000683
  }
}
...
>>> history: MinimizationHistory = target.history
>>> plot(history.evaluations, history.f_mins)
...
>>> # The history is easily saved
>>> history.save(Path('results/10001'))
...
>>> # ... and loaded.
>>> loaded_history: MinimizationHistory = MinimizationHistory.load(Path('results/10001'))
```


TODO
====

- [x] Lose the pandas dependency for `csv_to_html` through custom function.
- [x] Update the result of `help(orgmin)`.
- [ ] Expand TargetWrapper to be able to save all results, not only the current
best value upon each improvement.
- [ ] Results class with functionality for keeping a registry of the results.
