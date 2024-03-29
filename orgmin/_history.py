"""
Module with wrappers for target functions to save the results obtained
throughout the entire minimization process.
"""

from typing import Callable, Optional
import time
from pathlib import Path
import logging
import traceback

import numpy as np

logger = logging.getLogger('orgmin')


class TargetWrapper:
    """
    Class with `__call__` method to be called by optimizer.
    State variables like number of function calls, best values obtained etc.
    are instance variables.

    The class keeps track of the number of instances created, and issues a
    warning to the "orgmin" logger if more than one instance is created. If an
    instance is copied inadvertently during optimization, e.g.  because of
    multiprocessing, then the instance variables counting the function
    evaluations will no longer work as intended. If this warning arises as a
    result of purposefully creating several instances of the class, then the
    warning can of course be ignored.
    """
    _number_of_instances: int = 0

    def __new__(cls, *args, **kwargs) -> 'TargetWrapper':
        cls._number_of_instances += 1
        if cls._number_of_instances > 1:
            logger.warning(
                'There have been created %d instances of the class\n'
                '`orgmin.TargetWrapper`.\n'
                'If this is intentional, this message can be ignored.\n'
                'Stack trace:\n%s',
                cls._number_of_instances,
                ''.join(traceback.format_stack()[:-1])
            )
        return super(TargetWrapper, cls).__new__(cls)

    def __init__(self, target_function: Callable, dim: int) -> None:
        """
        args:
            target_function (Callable):
                The function to minimize, should take one array_like input
                argument `x` of length `dim`.
            dim (int):
                The number of elements in `x`, the input argument to the
                function to be minimized.
        """
        self._target_function: Callable = target_function
        self._number_of_evaluations: int = 0
        self._current_f_min: float = float('inf')
        self._x_best = None
        self._history = MinimizationHistory(dim)

    def __call__(self, x):
        """Evaluate the target function, and save the results.

        args:
            x (array_like):
                Argument to be passed on to the target function, should be of
                length `dim` (see ``__init__``).

        returns:
            The result from evaluating the target function.
        """
        result = self._target_function(x)
        self._number_of_evaluations += 1

        if result < self._current_f_min:
            self._current_f_min = result
            self._x_best = x
            self.append_best_evaluation()

        return result

    @property
    def number_of_evaluations(self):
        return self._number_of_evaluations

    def append_best_evaluation(self):
        """Append the current values of the properties to the history.
        """
        self._history.append_evaluation(
            self._number_of_evaluations, self._current_f_min, self._x_best
        )

    @property
    def history(self):
        return self._history

    @property
    def x_best(self):
        if isinstance(self._x_best, np.ndarray):
            return self._x_best.copy()
        return self._x_best

    @property
    def current_f_min(self):
        return self._current_f_min

    def content(self) -> str:
        lines = [
            '{',
            f'Function evaluations: {self._number_of_evaluations}',
            f'Minimum value: {self._current_f_min}',
            f'Minimum x: {self._x_best}',
            f'History: {self._history.content(indent=4)}',
        ]
        return ('\n' + ' '*2).join(lines) + '\n}'

    def __str__(self):
        return 'Content of TargetWrapper: ' + self.content()


class MinimizationHistory:
    def __init__(self, dim: int):
        self._capacity: int = int(1024)
        self._len: int = 0
        self._dim: int = dim
        self._evaluations: np.ndarray = np.zeros(self._capacity, dtype=int)
        self._f_mins: np.ndarray = np.zeros(self._capacity)
        self._x_bests: np.ndarray = np.zeros((self._capacity, dim))
        self._start_time: float | None = None
        self._elapsed_time: float | None = None
        self.success: bool = False

    @property
    def dim(self) -> int:
        return self._dim

    def start_timing(self) -> None:
        if not self._start_time is None:
            logger.warning('Timing already started, statement ignored.')
            return
        self._start_time = time.perf_counter()

    def stop_timing(self) -> None:
        if self._start_time is None:
            logger.warning('Timing not started, timing will not be saved')
            return
        if self._elapsed_time is not None:
            logger.warning('Timing already stopped, statement ignored')
            return
        self._elapsed_time = time.perf_counter() - self._start_time

    @property
    def elapsed_time(self) -> Optional[float]:
        return self._elapsed_time

    def append_evaluation(
        self,
        number_of_evaluations: int,
        f_min: float,
        x_best
    ) -> None:
        """Append the input values to the history.

        args:
            number_of_evaluations (int):
                The current number of evaluations.
            f_min (float):
                The current minimum value of the target function.
            x_best (array_like):
                The coordinates for the current minimum, should be of length
                `dim` (see ``__init__``)
        """
        if self._len >= self._capacity:
            self._expand()
        self._evaluations[self._len] = number_of_evaluations
        self._f_mins[self._len] = f_min
        self._x_bests[self._len] = x_best
        self._len += 1

    def _expand(self) -> None:
        self._capacity *= 2
        if self._capacity >= int(1e7):
            logger.warning(
                'Capacity of orgmin.MinimizationHistory increased to %d',
                self._capacity
            )

        new = np.zeros(self._capacity, dtype=int)
        new[:self._len] = self._evaluations
        self._evaluations = new

        new = np.zeros(self._capacity)
        new[:self._len] = self._f_mins
        self._f_mins = new

        new = np.zeros((self._capacity, self._dim))
        new[:self._len] = self._x_bests
        self._x_bests = new

    @property
    def evaluations(self):
        """
        returns:
            (np.1darray of int):
                The number of function evaluations at each point an evaluation
                was saved. This is a copy of the array used internally.
        """
        return self._evaluations[:self._len].copy()

    @property
    def f_mins(self):
        """
        returns:
            (np.1darray of float):
                The function values at each point an evaluation was saved. This
                is a copy of the array used internally.
        """
        return self._f_mins[:self._len].copy()

    @property
    def x_bests(self):
        """
        returns:
            (np.2darray of shape (number_of_saved_evaluations, dim) of float):
                The function arguemtns at each point an evaluation was saved.
                This is a copy of the array used internally.
        """
        return self._x_bests[:self._len].copy()

    def save(self, path: Path) -> None:
        """Save the results to file.

        args:
            path (pathlib.Path):
                The directory in which the results should be saved. Several
                files will be created.
        """
        np.save(path / 'evaluations.npy', self.evaluations)
        np.save(path / 'f_mins.npy', self.f_mins)
        np.save(path / 'x_bests.npy', self.x_bests)

        file = path / 'time.txt'
        with file.open('w', encoding='UTF-8') as f:
            f.write(str(self.elapsed_time))

        file = path / 'success.txt'
        with file.open('w', encoding='UTF-8') as f:
            f.write(str(self.success))

    @classmethod
    def load(cls, path: Path) -> 'MinimizationHistory':
        """Factory method to create an object from saved files.

        args:
            path (pathlib.Path):
                The path to the directory containing the files saved by the
                ``save_results`` method.

        returns:
            (MinimizationHistory):
                The loaded results.
        """
        evaluations = np.load(path / 'evaluations.npy')
        f_mins = np.load(path / 'f_mins.npy')
        x_bests = np.load(path / 'x_bests.npy')

        dim = x_bests.shape[1]
        result = cls(dim)

        result._capacity = len(evaluations)
        result._len = result._capacity
        result._evaluations = evaluations
        result._f_mins = f_mins
        result._x_bests = x_bests
        result._elapsed_time = MinimizationHistory._read_elapsed_time(path)
        result.success = MinimizationHistory._read_success_file(path)
        return result

    @staticmethod
    def _read_elapsed_time(path: Path) -> float:
        file = path / 'time.txt'
        with file.open('r', encoding='UTF-8') as f:
            text = f.read()
        return float(text)

    @staticmethod
    def _read_success_file(path: Path) -> bool:
        file = path / 'success.txt'
        with file.open('r', encoding='UTF-8') as f:
            text = f.read()
        if text == 'True':
            return True
        if text == 'False':
            return False
        raise ValueError(f'Unexpected text \'{text}\' found.')

    def content(self, indent: int = 2) -> str:
        assert indent >= 2
        lines = [
            '{',
            f'Function evaluations: {self._evaluations[self._len - 1]}',
            f'Minimum value: {self._f_mins[self._len - 1]}',
            f'Minimum x: {self._x_bests[self._len - 1]}',
            f'Success: {self.success}',
            f'Elapsed time: {self.elapsed_time}',
        ]
        return ('\n' + ' '*indent).join(lines) + '\n' + ' '*(indent - 2) + '}'

    def __str__(self):
        return 'Content of MinimizationHistory: ' + self.content()
