"""
Module with functionality for keeping track of the parameters used for
different runs of numerical calculations. The outside interface consists of the
``Parameters`` class and the ``expand_registry`` and ``csv_to_html`` functions.
"""

from pathlib import Path
from datetime import datetime
from abc import ABC
import logging

logger = logging.getLogger('orgmin')


class Parameters(ABC):
    """Abstract base class for storing parameters for numerical calculations.

    When calling the ``catalogue`` method, all attributes
    (both instance variables and @property's)
    not starting with an underscore (_) will be treated as model parameters and
    saved to the registry. Callable methods will be ignored.
    """
    def catalogue(self, parent_dir: Path) -> Path:
        """Save the parameters passed as input to the registry file.

        args:
            parent_dir (pathlib.Path):
                The directory in which the parameters and results will be
                saved. This directory must exist beforehand and should contain
                no files created without the use of this class.

        returns:
            (pathlib.Path):
                Path to the directory in which results for this particular
                calculation should be saved.
        """
        assert parent_dir.is_dir()
        registry_file = parent_dir / 'registry.csv'
        if not registry_file.is_file():
            self._create_registry_files(parent_dir)

        self._verify_correct_directory(parent_dir)
        sample_dir = self._append_sample(parent_dir)
        full_path_to_sample_dir = parent_dir / sample_dir
        full_path_to_sample_dir.mkdir()
        return full_path_to_sample_dir

    def to_dict(self) -> dict:
        """Return a dictionary with all the parameters that are catalogued.

        returns:
            (dict):
                the parameters as a dictionary on the form
                {'parameter name': parameter_value}
        """
        attributes = [
            a for a in dir(self)
            if not a.startswith('_') and not callable(getattr(self, a))
        ]
        return {a: getattr(self, a) for a in sorted(attributes)}


    @staticmethod
    def load(parent_dir: Path, sample_id: int) -> dict:
        """Load parameters from the registry file.

        args:
            parent_dir (pathlib.Path):
                The directory in which the desired registry file exists.
            sample_id (int):
                The id of the sample whose parameters you would like to load
                from from the registry.

        returns:
            (subclass of Parameters):
                The loaded parameters.
        """
        # TODO: implement
        pass

    def _create_registry_files(self, path: Path) -> None:
        logger.info(
            'Creating registry files in direcory \'%s\'',
            path
        )
        fields = ['Sample', 'Time'] + list(self.to_dict().keys())
        file = path / 'registry.csv'
        with file.open('w', encoding='UTF-8') as f:
            f.write(','.join(fields) + '\n')
        csv_to_html(file, path / 'registry.html')

    def _verify_correct_directory(self, path: Path) -> None:
        file = path / 'registry.csv'
        with file.open('r', encoding='UTF-8') as f:
            expected_fields = f.readline().strip().split(',')

        observed = ['Sample', 'Time'] + list(self.to_dict().keys())
        msg = f'Expected fields that exist in the registry ({expected_fields}) ' \
            + f'do not match observed fields ({observed})'
        assert expected_fields == observed, msg

    def _append_sample(self, path: Path) -> str:
        """Create an id for the new sample and append it to the registry.

        The new id will be one number larger than the previous sample, even if
        there are intermittent samples missing. The first sample in a fresh
        registry is 10 000.

        args:
            path (Path):
                The path to the directory in which the registry and samples are
                stored.

        returns:
            (str): The id of the new sample.
        """
        registry_file = path / 'registry.csv'

        with registry_file.open('r', encoding='UTF-8') as f:
            last_line = [line.strip() for line in f.readlines()][-1]

        previous_sample = last_line.split(',')[0]
        if previous_sample == 'Sample':
            sample = str(10_000)
        else:
            sample = str(int(previous_sample) + 1)

        time = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')

        line = [sample, time] \
            + [str(a) for a in self.to_dict().values()]

        with registry_file.open('a', encoding='UTF-8') as f:
            f.write(','.join(line) + '\n')

        csv_to_html(registry_file, path / 'registry.html')

        return sample


def expand_registry(registry_file: Path, kw: str, val: str) -> None:
    """Expand an existing regitry to include a new parameter.

    args:
        registry_file (Path): the registry file to update
        kw (str): the keyword of the new parameter you wish to include
        val (str): the value to set for the new parameter in the already
            existing samples in the registry

    returns:
        None
    """
    assert registry_file.is_file()

    with registry_file.open('r', encoding='UTF-8') as f:
        fields = f.readline().strip().split(',')

        samples = []
        for line in f.readlines():
            values = line.strip().split(',')
            d = dict(zip(fields, values))
            if kw in d:
                raise ValueError(f'Keyword \'{kw}\' already exists in registry')
            d[kw] = val
            samples.append(d)

    new_fields = fields[:2] + sorted(fields[2:] + [kw])

    lines = [','.join(new_fields)]
    for s in samples:
        lines.append(','.join(s[f] for f in new_fields))

    with registry_file.open('w', encoding='UTF-8') as f:
        f.write('\n'.join(lines) + '\n')


def csv_to_html(csv_file: Path, html_file: Path):
    """Create an HTML copy of a CSV file.
    """
    assert csv_file.is_file(), f'File {csv_file.name} does not exist'
    html_lines = [
        '<table border="1" class="dataframe">',
        '  <thead>',
        '    <tr style="text-align: right;">',
        '      <th>Sample</th>',
        '      <th>Time</th>',
        '    </tr>',
        '  </thead>',
        '  <tbody>',
        '    <tr>',
        '      <td>10000</td>',
        '      <td>2023-12-13-11:37:31</td>',
        '      <td>50000000</td>',
        '      <td>True</td>',
        '      <td>1.000000e-11</td>',
        '    </tr>',
        '    <tr>',
        '      <td>10001</td>',
        '      <td>2023-12-13-11:38:00</td>',
        '      <td>50000000</td>',
        '      <td>True</td>',
        '      <td>1.000000e-11</td>',
        '    </tr>',
        '  </tbody>',
        '</table>',
    ]
    with csv_file.open('r', encoding='UTF-8') as f:
        headers = f.readline().split(',')


if __name__ == '__main__':
    reg = Path('/home/vegard/Documents/SIC-POVM/code/experimental_results/shgo/registry.csv')
    expand_registry(reg, 'sampling_method', 'simplicial')
