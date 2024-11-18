from typing import Dict, List, Tuple
from pathlib import Path
import json

import numpy as np


class ComputeDB:
    _accepted_types: List[type] = [int, float, bool, str]
    _storage_sep = '|'

    def __init__(self, path: Path) -> None:
        assert path.is_dir(), f'Database {path} does not exist.'
        self._db_dir = path
        self._name = path.name
        self._verify_file_structure()
        self._load_configuration()
        self._load_data()

    def _load_configuration(self) -> None:
        config = ComputeDB._load_dict(self._db_dir / 'configuration.json')
        self._parameters: Dict[str, type] = {
            p: ComputeDB._str_to_type(t) for p, t in config['parameters'].items()
        }
        self._targets: Dict[str, type] = {
            t: ComputeDB._str_to_type(tp) for t, tp in config['targets'].items()
        }
        self._float_precision: int = config['float_precision']
        self._max_string_length: int = config['max_string_length']

    def _load_data(self) -> None:
        d = self._load_dict(self._db_dir / 'data.json')
        self._data = {
            tuple(k.split(self._storage_sep)): v
            for k, v in d.items()
        }

    def _verify_file_structure(self):
        for fname in ['description.txt', 'configuration.json', 'data.json']:
            file = self._db_dir / fname
            msg = 'Database file structure check failed.\n' \
                f'File {fname} does not exist.'
            assert file.is_file(), msg

    def print_configuration(self) -> None:
        print(f'Configuration of ComputeDB {self._name}:')
        print(f'  Parameters:\n    {self._parameters}')
        print(f'  Targets:\n    {self._targets}')
        print(f'  Float precision: {self._float_precision}')
        print(f'  Max string length: {self._max_string_length}')

    def save_data(self) -> None:
        d = {self._storage_sep.join(k): v for k, v in self._data.items()}
        ComputeDB._save_dict(self._db_dir / 'data.json', d)

    def add(self, parameters: Dict, targets: Dict, save: bool = True) -> None:
        msg = f'Parameters {parameters.keys()} do not match {self._parameters.keys()}'
        assert parameters.keys() == self._parameters.keys(), msg
        for p, v in parameters.items():
            assert isinstance(v, self._parameters[p])

        msg = f'Targets {targets.keys()} do not match {self._targets.keys()}'
        assert targets.keys() == self._targets.keys(), msg
        for t, v in targets.items():
            assert isinstance(v, self._targets[t])

        d = self._data
        key = self._create_tuple(list(parameters[k] for k in self._parameters.keys()))
        value = self._create_tuple(list(targets[k] for k in self._targets.keys()))
        d[key] = value

        if save:
            self.save_data()

    def _create_tuple(self, values: List) -> Tuple:
        """
        Create a tuple of str to serve either as key of value in the dict that
        serves as the databse.

        args:
            values: a list of values
        """
        return tuple(self._format_entry(v) for v in values)

    def _format_entry(self, v) -> str:
        if isinstance(v, float):
            return ('{:.' + str(self._float_precision) + 'e}').format(v)
        if isinstance(v, str):
            assert self._storage_sep not in v
            l = max(len(v), self._max_string_length)
            return v[:l]
        return str(v)

    def __getitem__(self, parameters: Dict) -> Dict:
        msg = f'Parameters {parameters.keys()} do not match {self._parameters.keys()}'
        assert parameters.keys() == self._parameters.keys(), msg
        for p, v in parameters.items():
            assert isinstance(v, self._parameters[p])
        key = self._create_tuple(list(parameters[k] for k in self._parameters.keys()))
        result = self._data[key]
        return {name: t(v) for (name, t), v in zip(self._targets.items(), result)}

    @staticmethod
    def initialize(
        path: Path,
        name: str,
        parameters: Dict[str, type],
        targets: Dict[str, type],
        description: str,
        float_precision: int = 12,
        max_string_length: int = 8,
    ) -> None:
        """

        args:
            float_precision: floats are stored in standard form with this
                number of decimals
            max_string_length: strings will be truncated to this length
        """
        msg = 'Dir. in which to initialize DB does not exist. Aborting.'
        assert path.is_dir(), msg
        db_dir = path / name
        msg = 'Database already exists. Aborting.'
        assert not db_dir.is_dir(),msg

        if not ComputeDB._types_are_valid(parameters):
            raise TypeError(
                'Parameters contain invalid types.\n'
                f'Valid types are {ComputeDB._accepted_types}.'
            )
        if not ComputeDB._types_are_valid(targets):
            raise TypeError(
                'Targets contain invalid types.\n'
                f'Valid types are {ComputeDB._accepted_types}.'
            )

        db_dir.mkdir()
        description_file = db_dir / 'description.txt'
        with description_file.open('w', encoding='UTF-8') as f:
            f.write(description)

        configuration = {
            'parameters': {
                p: ComputeDB._type_to_str(t) for p, t in parameters.items()
            },
            'targets': {
                t: ComputeDB._type_to_str(tp) for t, tp in targets.items()
            },
            'float_precision': float_precision,
            'max_string_length': max_string_length,
        }
        ComputeDB._save_dict(db_dir / 'configuration.json', configuration)

        # save empty data dict to (empty) file data.json
        ComputeDB._save_dict(db_dir / 'data.json', {})

    @staticmethod
    def _type_to_str(t: type) -> str:
        return {
            int: 'int',
            float: 'float',
            bool: 'bool',
            str: 'str',
        }[t]

    @staticmethod
    def _str_to_type(s: str) -> type:
        return {
            'int': int,
            'float': float,
            'bool': bool,
            'str': str,
        }[s]

    @staticmethod
    def _types_are_valid(d: Dict[str, type]) -> bool:
        for dtype in d.values():
            if dtype not in ComputeDB._accepted_types:
                return False
        return True

    @staticmethod
    def _save_dict(file: Path, d: Dict) -> None:
        with file.open('w', encoding='UTF-8') as f:
            json.dump(d, f, indent=2, sort_keys=True)

    @staticmethod
    def _load_dict(file: Path) -> Dict:
        with file.open('r', encoding='UTF-8') as f:
            return json.load(f)


def _test_initialize():
    ComputeDB.initialize(
        Path('/home/vegard/Desktop'),
        'Test',
        {'omega': float, 't': int, 'oscillator_size': int},
        {'F': float, 'v': float},
        description='This is a test.\nBlaBla\nBlaBlaBla.'
    )


def _test_load():
    db = ComputeDB(Path('/home/vegard/Desktop/Test'))
    db.print_configuration()
    print(db._data)
    print(db[{'omega': 1.0, 't': 2, 'oscillator_size': 3}])


def _test_add():
    db = ComputeDB(Path('/home/vegard/Desktop/Test'))
    db.add(
        {'omega': 1.0, 't': 2, 'oscillator_size': 3},
        {'v': -1.0, 'F': np.pi}
    )


def _main():
    def f():
        return 1, 2

    x = f()
    print(x)


if __name__ == '__main__':
    # _test_initialize()
    _test_load()
    # _test_add()
    # _main()
