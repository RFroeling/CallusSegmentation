"""Tiny launcher module that starts the interactive image reviewer GUI.

This module is intended for direct execution (``python -m segmentation.tasks.review``)
and simply constructs and runs :class:`segmentation.core.views.ImageReviewer`.
"""

from segmentation.core.views import ImageReviewer

if __name__ == '__main__':
    viewer = ImageReviewer()
    viewer.run()
