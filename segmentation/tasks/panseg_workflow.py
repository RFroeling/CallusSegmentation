"""Run PanSeg headless workflows from a YAML configuration.

This module provides a tiny wrapper used to invoke PanSeg in headless mode
from a YAML workflow definition. It exposes a single function, ``main``, that
delegates to PanSeg's :func:`Panseg.headless.headless.run_headless_workflow`.

Example:
    main(Path("workflow.yml"))
"""

def main(yaml_path):
    """Execute the PanSeg headless workflow defined in `yaml_path`.

    Args:
        yaml_path (str or pathlib.Path): Path to the PanSeg YAML configuration.
    """
    from panseg.headless.headless import run_headless_workflow
    
    run_headless_workflow(yaml_path)
