# import libraries
import pandas as pd
import glob
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from bs4 import BeautifulSoup


# helper functions for if a field is missing in the content.opf file, return None instead of throwing an error
def get_metadata(root, property_val, NS):
    el = root.find(f'opf:metadata/opf:meta[@property="{property_val}"]', NS)
    return el.text if el is not None else None

def get_dc(root, tag, NS):
    el = root.find(f'opf:metadata/dc:{tag}', NS)
    return el.text if el is not None else None