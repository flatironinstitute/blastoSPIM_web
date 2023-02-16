# blastospim_web

Generate a web site supporting the Blastospim mouse embryo research project.

The web site is designed to be served as static files from the web server
with Javascript readable data files generated from source data in a preprocessing step.

<a href="https://users.flatironinstitute.org/~awatters/blastospim/html/">
The top level directory for the site is currently located at
https://users.flatironinstitute.org/~awatters/blastospim/html/ . </a>

# Development install

The repository supports runnning in experimental mode from a local workstation and includes
a small source test data collection for testing data preprocessing.

```bash
% git clone https://github.com/AaronWatters/blastospim_web.git
% cd blastospim_web
% pip install -e .
% cd ..
```

# The sample data

The following sample data is provided by the repository.  It must be processed by the preprocessor
before it is used by the test web site.

```bash
 $ find sample_data/
sample_data/
sample_data//F11_66
sample_data//F11_66/F11_66
sample_data//F11_66/F11_66/images
sample_data//F11_66/F11_66/images/F11_66_image_0001.npy
sample_data//F11_66/F11_66/F11_66_image_0001.npy
sample_data//F11_66/F11_66/masks
sample_data//F11_66/F11_66/masks/F11_66_masks_0001.npy
sample_data//F11_65
sample_data//F11_65/F11_65
sample_data//F11_65/F11_65/F11_65_image_0001.npy
sample_data//F11_65/F11_65/images
sample_data//F11_65/F11_65/images/F11_65_image_0001.npy
sample_data//F11_65/F11_65/masks
sample_data//F11_65/F11_65/masks/F11_65_masks_0001.npy
sample_data//M6_20
sample_data//M6_20/M6_20
sample_data//M6_20/M6_20/images
sample_data//M6_20/M6_20/images/M6_20_image_0001.npy
sample_data//M6_20/M6_20/masks
sample_data//M6_20/M6_20/masks/M6_20_masks_0001.npy
```

# Make the test site

The following command prepares the sample data for ingestion by the test web site.

```bash
$ cd blastospim_web
$ cd scripts
$ python make_test_site.py
```

This generates the following test data hierarchy

```bash
$ find test_site/data/
test_site/data/
test_site/data//F11
test_site/data//F11/66
test_site/data//F11/66/max_intensity_image.png
test_site/data//F11/66/extruded_colorized_labels.png
test_site/data//F11/66/image_and_labels.tgz.npz
test_site/data//F11/65
test_site/data//F11/65/max_intensity_image.png
test_site/data//F11/65/extruded_colorized_labels.png
test_site/data//F11/65/image_and_labels.tgz.npz
test_site/data//M6
test_site/data//M6/20
test_site/data//M6/20/max_intensity_image.png
test_site/data//M6/20/extruded_colorized_labels.png
test_site/data//M6/20/image_and_labels.tgz.npz
test_site/data//manifest.json
```

Then to view the test web site launch a simple web server like

```
$ python3 -m http.server
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
```

Then navigate to the website root at `http://localhost:8000/.../blastospim_web/template`.

For development purposes the web site `template` files may be editted and reloaded in place
without rerunning the preprocessor.  You only need to rerun the preprocessor if the data formats
change.

# Install the development site on `rusty`

The following command will preprocess all source data on `rusty` and install
the development website code.

```bash
$ srun -N1 --pty bash -i
$ cd blastospim_web
$ cd scripts
$ nohup python -u make_rusty_site.py &
```

```bash
$ module load slurm
$ module load disBatch
$ sbatch -n 1 --ntasks-per-node 1 --wrap "disBatch.py job.sh"
```

The data processing takes a while.

# Install just the HTML/CSS and Javascript in development

If you do not need to regenerate the preprocessed data the following will
copy only the "code" files and not the data from the repository to the
web site directories (to save time).

```bash
$ cd blastospim_web
$ cd scripts
$ python update_rusty_code.py
```
