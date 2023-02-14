"""
Scrape a file hierarchy similar to

/mnt/ceph/users/lbrown/Labels3DMouse/GTSets/2022_Full

Usage:

$ python scraper.py FROM_PATH TO_PATH JSON_FILENAME.json
"""

# todo:
# - dump json manifest to correct file

import os
import glob
from subprocess import check_output
import numpy as np
from imageio import imsave, mimsave
from scipy.ndimage import gaussian_filter
import json
import shutil

# pseudocolor flag
PSEUDOCOLOR = False
ENHANCE = False

def run():
    import sys
    try:
        [from_path, to_path, json_filename] = sys.argv[1:]
        assert os.path.exists(from_path)
        assert json_filename.endswith(".json"), "must end in .json: " + repr(json_filename)
    except Exception:
        print(__doc__)
        raise
    print ("Scraping", from_path)
    print ("Generating", to_path)
    print ("JSON manifest", json_filename)
    return scrape(from_path, to_path, json_filename)

def scrape(from_path, to_path, json_filename):
    return scrape_all([from_path], to_path, json_filename)

def scrape_all(from_paths, to_path, json_filename):
    sequence = SeriesSequence(to_path, json_filename)
    for from_path in from_paths:
        print()
        print("SCRAPING", from_path)
        ts_folders = os.listdir(from_path)
        #sequence = SeriesSequence(to_path, json_filename)
        for ts_folder in ts_folders:
            ts_path = os.path.join(from_path, ts_folder)
            assert os.path.isdir(ts_path), "not a folder: " + ts_path
            [series_name, ts_str] = ts_folder.split("_")
            idx = int(ts_str)
            ts = sequence.get_timestamp(series_name, idx, ts_path)
            print("created", ts)
            labels = ts.labels_array()
            print("labels", labels.dtype, labels.shape)
            img = ts.img_array()
            print("img", img.dtype, img.shape)
    print()
    print("now populating")
    sequence.populate_to_path(json_filename)

class SeriesSequence:

    def __init__(self, to_path, json_filename):
        self.to_path = to_path
        self.json_filename = json_filename
        self.name_to_series = {}

    def populate_to_path(self, json_path):
        self.check_to_path()
        for (name, series) in sorted(self.name_to_series.items()):
            print("Populating Series", name)
            series.populate(self.source_path, self.web_path)
        json_manifest = self.json_manifest()
        #json_path = os.path.join(self.to_path, "manifest.json")
        f = open(json_path, "w")
        json.dump(json_manifest, f, indent=1)
        print("wrote manifest to", json_path)
        f.close()
        print("tarring source files")
        cmd = 'cd "%s"; tar -cvf source.tar source' % self.to_path
        print("::", cmd)
        os.system(cmd)

    def check_to_path(self):
        p = self.to_path
        check_folder(self.to_path)
        self.source_path = os.path.join(p, "source")
        check_folder(self.source_path)
        self.web_path = os.path.join(p, "web")
        check_folder(self.web_path)

    def get_series(self, name):
        n2s = self.name_to_series
        result = n2s[name] = n2s.get(name, Series(name))
        return result

    def get_timestamp(self, name, idx, folder):
        series = self.get_series(name)
        return series.get_timestamp(name, idx, folder)

    def json_manifest(self):
        n2s = self.name_to_series
        order = sorted(n2s.keys())
        detail = {name: series.json_manifest() for (name, series) in n2s.items()}
        return dict(
            path=self.to_path,
            source_path=self.source_path,
            web_path=self.web_path,
            series_order=order,
            series=detail,
        )

def check_folder(path):
    if not os.path.exists(path):
        os.mkdir(path)
    assert os.path.isdir(path)

class Series:

    def __init__(self, name):
        self.name = name
        self.index_to_timestamp = {}

    def populate(self, source_path, web_path):
        source_folder = os.path.join(source_path, self.name)
        check_folder(source_folder)
        web_folder = os.path.join(web_path, self.name)
        check_folder(web_folder)
        for (idx, ts) in sorted(self.index_to_timestamp.items()):
            print("   ", source_folder, web_folder, idx)
            ts.save_summary(source_folder, web_folder)

    def get_timestamp(self, series_name, idx, folder):
        i2s = self.index_to_timestamp
        result = i2s[idx] = i2s.get(idx, TimeStamp(series_name, idx, folder))
        return result

    def json_manifest(self):
        i2t = self.index_to_timestamp
        ts_list = sorted(i2t.keys())
        ts_map = {}
        for (idx, ts) in sorted(self.index_to_timestamp.items()):
            ts_map[str(idx)] = ts.json_manifest()
        return dict(
            name=self.name,
            timestamp_order=ts_list,
            timestamps=ts_map,
        )

class TimeStamp:

    def __init__(self, series_name, idx, folder):
        self.series_name = series_name
        self.idx = idx
        self.folder = folder
        self.save_folder = None

    def __repr__(self):
        return "TS" + repr((self.series_name, self.idx, self.folder))

    def save_summary(self, source_folder, web_folder):
        ts_folder = os.path.join(web_folder, str(self.idx))
        self.save_folder = ts_folder
        print("      ", ts_folder)
        if os.path.exists(ts_folder):
            shutil.rmtree(ts_folder)
        os.mkdir(ts_folder)
        # save data arrays
        labels = self.labels_array()
        img = self.img_array()
        #self.data_shape = img.shape
        fn = "%s_%s" % (self.series_name, self.idx)
        fpath = os.path.join(source_folder, fn)
        np.savez(fpath, img=img, labels=labels)
        self.data_path = fn
        # make extruded labels image
        slicing = positive_slicing(labels)
        slabels = slice3(labels, slicing)
        self.data_shape = slabels.shape
        (extruded, evolume) = extrude_labels(slabels)
        colorized = colorize_array(extruded)
        lfn = os.path.join(ts_folder, "extruded_colorized_labels.png")
        imsave(lfn, colorized)
        self.labels_image_path = lfn
        # make max intensity image
        simg = slice3(img, slicing)
        # apply blur before calculating max intensity...
        bsimg = blur(simg)
        #(mint, mvolume) = max_intensity(simg)
        (mint, mvolume) = max_intensity(bsimg)
        #bint = blur(mint)
        bint = mint
        #mint256 = scale256(bint)
        if ENHANCE:
            mint256 = enhance_contrast(bint)
        else:
            mint256 = scale256(bint)
        ifn = os.path.join(ts_folder, "max_intensity_image.png")
        if not PSEUDOCOLOR:
            imsave(ifn, mint256)
        else:
            pint256 = pseudo_colorize(mint256)
            imsave(ifn, pint256)
        self.max_intensity_path = ifn
        # save extruded volume binary
        colorized = colorize_array(evolume)
        evfn = os.path.join(ts_folder, "extruded_volume.bin")
        save_binary(colorized, evfn)
        self.extruded_volume = evfn
        # save max intensity volume
        #bvol = blur(mvolume)
        mvfn = os.path.join(ts_folder, "max_intensity_volume.bin")
        #mvol256 = scale256(mvolume)
        # enhance contrast for each layer of mvolume independently
        if ENHANCE:
            mvol256 = np.zeros(mvolume.shape, dtype=np.ubyte)
            for i in range(len(mvolume)):
                mvol256[i] = enhance_contrast(mvolume[i])
        else:
            mvol256 = np.zeros(mvolume.shape, dtype=np.ubyte)
            for i in range(len(mvolume)):
                mvol256[i] = scale256(mvolume[i])
        if not PSEUDOCOLOR:
            save_binary(mvol256, mvfn)
        else:
            pvol256 = pseudo_colorize(mvol256)
            save_binary(pvol256, mvfn)
        self.max_intensity_volume = mvfn

    def json_manifest(self):
        assert self.save_folder is not None, "materialize manifest only after save."
        return dict(
            series=self.series_name,
            idx=self.idx,
            source_folder=self.folder,
            save_folder=self.save_folder,
            data_path=self.data_path,
            labels_path=self.labels_image_path,
            max_intensity_path=self.max_intensity_path,
            shape=self.data_shape,
            extruded_volume=self.extruded_volume,
            max_intensity_volume=self.max_intensity_volume
        )

    def labels_array(self):
        pname = "%s_%s" % (self.series_name, self.idx)
        glob_pattern = "%s/%s/masks/*_masks_*.npy" % (self.folder, pname,)
        files = glob.glob(glob_pattern)
        assert len(files) == 1, "should have one file: " + repr((glob_pattern, files, self))
        [fn] = files
        labels = np.load(fn, allow_pickle=True)
        return labels

    def img_array(self):
        pname = "%s_%s" % (self.series_name, self.idx)
        glob_pattern = "%s/%s/images/*_image_*.npy" % (self.folder, pname,)
        files = glob.glob(glob_pattern)
        assert len(files) == 1, "should have one file: " + repr((glob_pattern, files, self))
        [fn] = files
        img = np.load(fn, allow_pickle=True)
        return img

def extrude_labels(labels_array):
    volume = labels_array.copy()
    extruded = labels_array[0].copy()
    for (i, labelsi) in enumerate(labels_array):
        nz = (labelsi > 0)
        extruded = np.choose(nz, [extruded, labelsi])
        volume[i] = extruded
    return (extruded, volume)

def max_intensity(imgs_array):
    volume = imgs_array.copy()
    m = imgs_array[0]
    for (i,m2) in enumerate(imgs_array):
        m = np.maximum(m, m2)
        volume[i] = m
    return (m, volume)

def save_binary(array, to_fn):
    f = open(to_fn, "wb")
    array.ravel().tofile(f)
    f.close()

def blur(img, sigma=2):
    return gaussian_filter(img, sigma=sigma)

def enhance_contrast(img, cutoff=0.1):
    (unique, count) = np.unique(img, return_counts=True)
    size = img.size
    def breakpoint(delta):
        stop = delta * size
        total = 0
        for (i, c) in enumerate(count):
            total += c
            if total > stop:
                return i
        return len(count)
    low_index = breakpoint(cutoff)
    high_index = breakpoint(1.0 - cutoff)
    length = max(unique) + 1
    mapping = np.zeros((length,), dtype=np.ubyte)
    low = unique[low_index]
    high = unique[high_index]
    # print("low", low, "high", high)
    if low < high:
        delta = 255.0 / (high - low)
    else:
        delta = 255.0
    for i in range(length):
        if i < low:
            v = 0
        elif i > high:
            v = 255
        else:
            v = int(delta * (i - low))
        mapping[i] = v
    result = mapping[img]
    return result

def scale256(img, epsilon=1e-11):
    img = np.array(img, dtype=np.float)
    m = img.min()
    M = img.max()
    D = M - m 
    if D < epsilon:
        D = epsilon
    scaled = (255.0 * (img - m)) / D
    return scaled.astype(np.ubyte)

def colorize_array(a, color_mapping_array=None):
    from . import color_list
    if color_mapping_array is None:
        maxlabel = a.max()
        color_choices = [(0,0,0)] + color_list.get_colors(maxlabel)
        color_mapping_array = np.array(color_choices, dtype=np.ubyte)
    shape = a.shape
    colors = color_mapping_array[a.flatten()]
    colorized_array = colors.reshape(shape + (3,))
    return colorized_array

def positive_slicing(M):
    """
    for 3d matrix M determine I,J,K (start, end) slicing of minimal volume containing all positive M[i,j,k]
    """
    slices = np.zeros((3, 2), dtype=np.int)
    Itest = M.max(axis=2).max(axis=1)
    (inz,) = np.nonzero(Itest > 0)
    slices[0] = (inz.min(), inz.max()+1)
    Jtest = M.max(axis=2).max(axis=0)
    (jnz,) = np.nonzero(Jtest > 0)
    slices[1] = (jnz.min(), jnz.max()+1)
    Ktest = M.max(axis=1).max(axis=0)
    (knz,) = np.nonzero(Ktest > 0)
    slices[2] = (knz.min(), knz.max()+1)
    return slices

def slice3(M, s):
    "Slice M by array generated by positive_slicing."
    # xxx not neeeded?  For completeness
    im, iM = s[0]
    jm, jM = s[1]
    km, kM = s[2]
    return M[im:iM, jm:jM, km:kM]

# pseudocolor support
h = 255
white = [h, h, h]
yellow = [h, h, 0]
magenta = [h, 0, h]
magenta = [h, h//2, h] # lighter magenta to avoid blue streak
red = [h, 0, 0]
cyan = [0, h, h]
green = [0, h, 0]
blue = [0, 0, h]
black = [0, 0, 0]

interpolator = np.array([
    black,
    blue,
    green,
    cyan,
    magenta,
    red,
    yellow,
    white,
])

def interpolate255(i, interpolator=interpolator):
    assert i >= 0 and i <= 255
    nint = len(interpolator)
    lam = i * 1.0/255.0
    if lam == 1:
        return interpolator[-1].astype(np.int)
    ir = (nint - 1) * lam
    i0 = int(ir)
    i1 = i0 + 1
    if i1 >= nint:
        return interpolator[-1].astype(np.int)
    delta = ir - i0
    e0 = interpolator[i0]
    e1 = interpolator[i1]
    cr = (1 - delta) * e0 + delta * e1
    return cr.astype(np.int)

pseudo_color_mapping = np.array([interpolate255(i) for i in range(256)]).astype(np.ubyte)

def pseudo_colorize(a):
    return colorize_array(a, pseudo_color_mapping)

if __name__=="__main__":
    run()
