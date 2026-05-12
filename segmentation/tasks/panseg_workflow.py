import logging
import platform
import shutil
import subprocess
from pathlib import Path

logger = logging.basicConfig(level="DEBUG")

def find_panseg_executable(
    executable_path: str | Path | None = None,
) -> Path:
    """
    Locate the panseg executable.

    Search order:
    1. Explicit executable path
    2. PATH
    3. Common standalone install layouts
    """

    system = platform.system()

    executable_name = "panseg.exe" if system == "Windows" else "panseg"

    # 1. Explicit path
    if executable_path is not None:
        path = Path(executable_path).expanduser().resolve()

        if path.is_file():
            return path

        raise FileNotFoundError(
            f"PanSeg executable not found at: {path}"
        )

    # 2. Search PATH
    found = shutil.which("executable_name")

    if found:
        logging.debug(f"Found on PATH: {found} ")
        return Path(found).resolve()

    # 3. Search common standalone install layouts
    candidate_dirs: list[Path] = []

    home = Path.home()
    logging.debug(f"Home: {home}")

    if system == "Windows":
        candidate_dirs.extend(
            [
                home / "AppData" / "Local" / "panseg" / "Scripts",
                home / "panseg" / "Scripts",
                Path("C:/panseg/Scripts"),
                Path("C:/Program Files/panseg/Scripts"),
            ]
        )

    else:
        candidate_dirs.extend(
            [
                home / "panseg" / "bin",
                Path("/opt/panseg/bin"),
                Path("/usr/local/panseg/bin"),
            ]
        )

    for directory in candidate_dirs:
        candidate = directory / executable_name
        logging.debug(f"Searching for PanSeg executable in: {candidate}")

        if candidate.is_file():
            return candidate.resolve()

    raise FileNotFoundError(
        "Could not locate the PanSeg executable."
    )


def run_panseg(
    config_path: str | Path,
    executable_path: str | Path | None = None,
) -> None:
    """
    Run a PanSeg job synchronously.

    Parameters
    ----------
    config_path:
        Path to YAML config file.

    executable_path:
        Optional explicit path to panseg executable.

    Returns
    -------
    int
        Process return code.

    Raises
    ------
    FileNotFoundError
        If the executable cannot be located.

    subprocess.CalledProcessError
        If PanSeg exits with a non-zero return code.
    """

    config_path = Path(config_path).expanduser().resolve()

    if not config_path.is_file():
        raise FileNotFoundError(
            f"Config file does not exist: {config_path}"
        )

    executable = find_panseg_executable(executable_path)
    logging.debug(f'Attempting to run PanSeg from: {executable}')

    command = [
        str(executable),
        "--config",
        str(config_path),
    ]

    logging.debug(f'Command: {command}')

    process = subprocess.run(
        command,
        check=True,
    )

if __name__ == "__main__":
    run_panseg(config_path=".data2/test_general_workflow.yaml")