"""Run PlantSeg headless workflows from a YAML configuration.

This module provides a tiny wrapper used to invoke PlantSeg in headless mode
from a YAML workflow definition. It exposes a single function, ``main``, that
delegates to PlantSeg's :func:`plantseg.headless.headless.run_headless_workflow`.

Example:
    main(Path("workflow.yml"))
"""

from plantseg.headless.headless import run_headless_workflow


def main(yaml_path):
    """Execute the PlantSeg headless workflow defined in `yaml_path`.

    Args:
        yaml_path (str or pathlib.Path): Path to the PlantSeg YAML configuration.
    """
    run_headless_workflow(yaml_path)
