"""Run PanSeg headless workflows from a YAML configuration.

This module provides the PanSegRunner class to locate and execute the PanSeg
binary with a YAML configuration file. The PanSegRunner automatically discovers
the PanSeg executable from the environment, PATH, or common installation locations.

It exposes a ``main`` function that creates a PanSegRunner instance and executes
a headless workflow defined in a YAML configuration file.

Example:
    main("workflow.yaml")
    main(Path("workflow.yaml"))
"""

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional


class PanSegRunner:
    def __init__(self, panseg_bin: Optional[str] = None):
        self.panseg_bin = panseg_bin or self._find_panseg()

    # Locate PanSeg executable
    def _find_panseg(self) -> str:
        # 1. Environment override
        env_override = os.environ.get("PANSEG_BIN")
        if env_override and Path(env_override).exists():
            return env_override

        # 2. Check PATH
        panseg = shutil.which("panseg")
        if panseg:
            return panseg

        system = platform.system()
        exe = "panseg.exe" if system == "Windows" else "panseg"
        home = Path.home()

        candidates = [
            home / "panseg",
            home / "PanSeg",
            home / ".panseg",
        ]

        for root in candidates:
            paths = [
                # # Preferred: conda env binary
                # root / "envs/panseg" / ("Scripts" if system == "Windows" else "bin") / exe,

                # # Alternate layout
                # root / "env" / ("Scripts" if system == "Windows" else "bin") / exe,

                # Wrapper script
                root / ("Scripts" if system == "Windows" else "bin") / exe,
            ]

            for p in paths:
                if p.exists():
                    return str(p)

        raise FileNotFoundError(
            "Could not locate PanSeg executable. "
            "Set PANSEG_BIN or install PanSeg in ~/panseg."
        )

    # Run headless workflow
    def run_config(
        self,
        input_path: str,
        check: bool = True,
        capture_output: bool = False,
    ):
        cmd = [
            self.panseg_bin,
            "--config",
            input_path,
        ]

        result = subprocess.run(
            cmd,
            check=check,
            text=True,
            capture_output=capture_output,
        )

        return result


def main(yaml_path):
    """Execute the PanSeg headless workflow defined in `yaml_path`.

    Args:
        yaml_path (str or pathlib.Path): Path to the PanSeg YAML configuration.
    """
    runner = PanSegRunner()
    runner.run_config(yaml_path)

if __name__ == '__main__':
    main('test_general_workflow.yaml')