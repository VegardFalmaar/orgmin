"""
Package for keeping track of the results of numerical experiments with varying
hyperparameters, and for storing the results of function minimization.

Interface:

- The ``Parameters`` class for keeping a catalogue of the results of different
  code runs (see README.md or run `help(orgmin.Parameters)`).
- The ``expand_registry`` function to expand the registry managed by the
  ``Parameters`` class (see README.md or run `help(orgmin.expand_registry)`).
- The ``csv_to_html`` function used internally to create simple HTML versions
  of CSV-files (run `help(orgmin.csv_to_html)` for information.
- The ``TargetWrapper`` class is a wrapper around a function which is to be
  minimized. It will keep track of the number of function calls and the best
  values obtained during optimization in an instance of
  ``MinimizationHistory``. (See README.md or run `help(orgmin.TargetWrapper)`).
- The ``MinimizationHistory`` class is an object which contains the results
  obtained during minimization (see README.md or run
  `help(orgmin.MinimizationHistory)`).
"""
from ._catalogue import Parameters, expand_registry, csv_to_html
from ._history import TargetWrapper, MinimizationHistory
