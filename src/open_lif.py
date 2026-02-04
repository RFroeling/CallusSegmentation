from pathlib import Path

from bioio import BioImage
import bioio_lif

lif_path = Path(".data/00_raw/250925_LowResSegmentation.lif")
ome_path = Path(".data/00_raw/250925_LowResSegmentation.ome.tiff")
out_dir = Path(".data/testtif")


def read_lif(filename: Path) -> BioImage:
    return BioImage(filename, reader=bioio_lif.Reader)


def save_scenes_as_ome_tiff(bioimg: BioImage, output_dir: Path) -> None:
    for scene in bioimg.scenes:
        path = output_dir / f'{scene}.ome.tiff'
        print(f"Current scene type: {type(scene)}, value: {repr(scene)}")
        bioimg.save(path, select_scenes=[scene])


bioimg = read_lif(lif_path)
save_scenes_as_ome_tiff(bioimg, out_dir)