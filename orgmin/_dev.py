# Sketch of an expansion of MinimizationHistory.save_results which has the
# option to keep a registry of the results obtained during different runs.
class MinimizationHistory:
    def save_results(
        self,
        path: Path,
        result_registry: Optional[Path] = None
    ) -> None:
        """Save the results to file.

        args:
            path (pathlib.Path):
                The directory in which the results should be saved.
            result_registry (pathlib.Path, optional):
                If supplied then the highlights of the minimization history
                will be saved to the file supplied as argument. The file will
                be created if it does not already exist.
        """
        np.save(path / 'evaluations.npy', self.evaluations)
        np.save(path / 'f_mins.npy', self.f_mins)
        np.save(path / 'x_bests.npy', self.x_bests)

        file = path / 'time.txt'
        with file.open('w', encoding='UTF-8') as f:
            f.write(str(self.elapsed_time))

        file = path / 'solution_found.txt'
        with file.open('w', encoding='UTF-8') as f:
            f.write(str(self.solution_found))

        if result_registry is not None:
            self._update_result_registry(result_registry)

    def _update_result_registry(self, result_registry: Path):
        if not result_registry.is_file():
            fields = ['Sample', 'Elapsed time', 'Success', 'Evaluations', 'f-min']
            with result_registry.open('w', encoding='UTF-8') as f:
                f.write(','.join(fields) + '\n')

        fields = ['Sample', 'Elapsed time', 'Success', 'Evaluations', 'f-min']
        with result_registry.open('w', encoding='UTF-8') as f:
            f.write(','.join(fields) + '\n')

        csv_to_html(result_registry, result_registry.with_suffix('.html'))
