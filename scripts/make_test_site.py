
from blastospim_web.scraper import scrape
import os

def make_test_site(from_folder="../sample_data", to_folder="../test_site"):
    data_path = os.path.join(to_folder, "data")
    if not os.path.isdir(to_folder):
        os.makedirs(to_folder)
    # install the data files
    json_filename = os.path.join(data_path, "manifest.json")
    scrape(from_folder, data_path, json_filename)
    # now install web infrastructure ...

if __name__=="__main__":
    make_test_site()
