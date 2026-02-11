"""Ad-hoc script to move accepted files into a curated directory.

This small helper reads a review CSV produced by the reviewer GUI and moves
all files with decision "accepted" into a `curated_labels` directory.

The script is environment-specific in this repository and uses absolute
paths; it is kept as a convenience script and is not intended as a
reusable library function.
"""

from pathlib import Path

import pandas as pd

from segmentation.core.io import move_h5

src_path = Path("W:\\AFSG\\Groups\\BIC\\Bulk\\Rik\\Experiments\\251201_CallusSegmentation\\stellaris\\plantseg_labels\\comparison_plots")
dest_path = src_path.parents[1] / 'curated_labels'
dest_path.mkdir(parents=True, exist_ok=True)
log_path = src_path.parent / '_logs' / 'review_log.csv'

df = pd.read_csv(log_path)

accepted_files = df.loc[df['Decision'] == 'accepted', 'FileName'].tolist()

for file in accepted_files:
    file = file.replace('comparison_', "")
    file = file.replace('.png', '.h5')
    file_path = src_path.parent / file
    move_h5(file_path, dest_path)

print('Done')
