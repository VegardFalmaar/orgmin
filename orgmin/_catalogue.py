"""
Module with functionality for keeping track of the parameters used for
different runs of numerical calculations. The outside interface consists of the
``Parameters`` class and the ``expand_registry`` and ``csv_to_html`` functions.
"""

from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger('orgmin')

CSV_DELIMITER = ';'


class Parameters:
    """(Base) class for storing parameters for numerical calculations.

    When calling the ``catalogue`` method, all attributes
    (both instance variables and ``@property``s)
    not starting with an underscore (_) will be treated as model parameters and
    saved to the registry. Callable methods will be ignored.
    """
    def catalogue(self, parent_dir: Path) -> Path:
        """Save the parameters passed as input to the registry file.

        args:
            parent_dir (pathlib.Path):
                The directory in which the parameters and results will be
                saved. This directory must exist beforehand and should contain
                no files created without the use of this class. A separate
                subdirectory will be created for each sample.

        returns:
            (pathlib.Path):
                Path to the subdirectory in which results for this particular
                calculation should be saved.
        """
        msg = f'Directory \'{parent_dir}\' does not exist'
        assert parent_dir.is_dir(), msg

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
                The parameters as a dictionary on the form
                {'parameter name': parameter_value}.
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
            (dict):
                The loaded parameters as a dictionary on the form
                {'parameter name': parameter_value}.
        """
        registry_file = parent_dir / 'registry.csv'
        with registry_file.open('r', encoding='UTF-8') as f:
            headers = f.readline().strip().split(CSV_DELIMITER)
            for line in f:
                fields = line.strip().split(CSV_DELIMITER)
                if fields[0] == str(sample_id):
                    return dict(zip(headers, fields))
        raise ValueError(
            f'Sample {sample_id} not found in the registry in {parent_dir}'
        )

    def _create_registry_files(self, path: Path) -> None:
        logger.info(
            'Creating registry files in direcory \'%s\'',
            path
        )
        fields = ['Sample', 'Time'] + list(self.to_dict().keys())
        file = path / 'registry.csv'
        with file.open('w', encoding='UTF-8') as f:
            f.write(CSV_DELIMITER.join(fields) + '\n')
        csv_to_html(file, path / 'registry.html', delimiter=CSV_DELIMITER)

    def _verify_correct_directory(self, path: Path) -> None:
        file = path / 'registry.csv'
        with file.open('r', encoding='UTF-8') as f:
            expected_fields = f.readline().strip().split(CSV_DELIMITER)

        observed = ['Sample', 'Time'] + list(self.to_dict().keys())
        if not expected_fields == observed:
            raise AttributeError(
                f'Expected fields that exist in the registry '
                f'({expected_fields}) do not match the received fields '
                f'({observed}). To introduce a new parameter to the registry '
                'use the ``expand_registry`` function.'
            )

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
            (str):
                The id of the new sample.
        """
        registry_file = path / 'registry.csv'

        with registry_file.open('r', encoding='UTF-8') as f:
            last_line = [line.strip() for line in f.readlines()][-1]

        previous_sample = last_line.split(CSV_DELIMITER)[0]
        if previous_sample == 'Sample':
            sample = str(10_000)
        else:
            sample = str(int(previous_sample) + 1)

        time = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')

        line = [sample, time] \
            + [str(a) for a in self.to_dict().values()]

        with registry_file.open('a', encoding='UTF-8') as f:
            f.write(CSV_DELIMITER.join(line) + '\n')

        csv_to_html(
            registry_file,
            path / 'registry.html',
            delimiter=CSV_DELIMITER
        )

        return sample


def expand_registry(registry_file: Path, kw: str, val: str) -> None:
    """Expand an existing registry to include a new parameter.

    This is useful if you have run the code multiple times with a set of
    parameters and you would like to vary a new parameter which has not been
    catalogued in the previous runs.

    args:
        registry_file (Path):
            The registry file to update.
        kw (str):
            The keyword of the new parameter you wish to include.
        val (str):
            The value to set for the new parameter in the existing samples in
            the registry.

    returns:
        None
    """
    if not registry_file.is_file():
        raise FileNotFoundError(f'File \'{registry_file}\' does not exist')
    if not isinstance(kw, str):
        raise TypeError(f'kw {kw} should be of type str not {type(kw)}')
    if not isinstance(val, str):
        raise TypeError(f'val {val} should be of type str not {type(val)}')

    with registry_file.open('r', encoding='UTF-8') as f:
        fields = f.readline().strip().split(CSV_DELIMITER)

        samples = []
        for line in f.readlines():
            values = line.strip().split(CSV_DELIMITER)
            d = dict(zip(fields, values))
            if kw in d:
                raise ValueError(f'Keyword \'{kw}\' already exists in registry')
            d[kw] = val
            samples.append(d)

    new_fields = fields[:2] + sorted(fields[2:] + [kw])

    lines = [CSV_DELIMITER.join(new_fields)]
    for s in samples:
        lines.append(CSV_DELIMITER.join(s[f] for f in new_fields))

    with registry_file.open('w', encoding='UTF-8') as f:
        f.write('\n'.join(lines) + '\n')


def csv_to_html(csv_file: Path, html_file: Path, delimiter: str = ',') -> None:
    """Create an HTML copy of a CSV file.

    args:
        csv_file (pathlib.Path):
            Path to the CSV file.
        html_file (pathlib.Path):
            Desired path to the HTML file.
        delimiter (str):
            Delimiter used in the CSV file. Default is ','.

    Returns:
        None
    """
    assert csv_file.is_file(), f'File {csv_file.name} does not exist'
    with csv_file.open('r', encoding='UTF-8') as f:
        headers = f.readline().strip().split(delimiter)
        samples = [line.strip().split(delimiter) for line in f]
    html_lines = [
        '<table border="1" class="dataframe">',
        '  <thead>',
        '    <tr style="text-align: right;">',
    ]
    html_lines += [f'      <th>{header}</th>' for header in headers]
    html_lines += [
        '    </tr>',
        '  </thead>',
        '  <tbody>',
    ]
    for sample in samples:
        html_lines.append('    <tr>')
        for field in sample:
            html_lines.append(f'      <td>{field}</td>')
        html_lines.append('    </tr>')
    html_lines.append('  </tbody>')
    html_lines.append('</table>')

    with html_file.open('w', encoding='UTF-8') as f:
        f.write('\n'.join(html_lines))


def _main():
    path = Path('/home/vegard/Desktop')
    csv_to_html(path / 'registry.csv', path / 'registry_test.html')
    # reg = Path('/home/vegard/Documents/SIC-POVM/code/experimental_results/shgo/registry.csv')
    # expand_registry(reg, 'sampling_method', 'simplicial')


if __name__ == '__main__':
    _main()
