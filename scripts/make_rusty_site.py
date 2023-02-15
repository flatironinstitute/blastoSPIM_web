
from blastospim_web.scraper import scrape_all
import os
import shutil

# old folder
from_folders = [
    "/mnt/ceph/users/lbrown/Labels3DMouse/GTSets/2022_Full",
]
# new folder
from_folders = [
    "/mnt/ceph/users/hnunley/Labels3DMouse/GTSets/2023_Full'",
]
to_folder = "/mnt/ceph/users/awatters/blastospim/website"

def make_test_site(from_folders=from_folders, to_folder=to_folder):
    data_path = os.path.join(to_folder, "data")
    if not os.path.isdir(to_folder):
        os.makedirs(to_folder)
    # install the data files
    json_filename = os.path.join(data_path, "manifest.json")
    scrape_all(from_folders, data_path, json_filename)
    print ("PLEASE INSTALL model.tar.gz MANUALLY.")
    install_web_infrastructure()

def install_web_infrastructure(from_folder=from_folder, to_folder=to_folder):
    src = "../template"
    dst_folder = "html"
    dst_path = os.path.join(to_folder, dst_folder)
    if os.path.exists(dst_path):
        shutil.rmtree(dst_path)
    shutil.copytree(src, dst_path)
    # patch javascript
    js_path = os.path.join(dst_path, "series.js")
    with open(js_path) as f:
        js_text = f.read()
    edit_text = js_text.replace('var WEB_ROOT = "../test_site/";', 'var WEB_ROOT = "../";')
    with open(js_path, "w") as f:
        f.write(edit_text)
    print ("wrote", js_path)

if __name__=="__main__":
    make_test_site()
