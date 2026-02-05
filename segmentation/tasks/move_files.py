import pandas as pd
from pathlib import Path

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