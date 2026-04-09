import os
import glob
from lxml import etree
import pandas as pd

# Namespaces used in SE's OPF files
NS = {
    'opf':  'http://www.idpf.org/2007/opf',
    'dc':   'http://purl.org/dc/elements/1.1/',
    'rdf':  'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
}

def parse_opf(opf_path):
    tree = etree.parse(opf_path)
    root = tree.getroot()

    def get(xpath):
        result = root.find(xpath, NS)
        return result.text.strip() if result is not None and result.text else None

    def get_all(xpath):
        return [el.text.strip() for el in root.findall(xpath, NS) if el.text]

    def get_meta(prop):
        el = root.find(f'.//opf:meta[@property="{prop}"]', NS)
        return el.text.strip() if el is not None and el.text else None

    # series: belongs-to-collection is a direct meta property
    series_el = root.find('.//opf:meta[@property="belongs-to-collection"]', NS)
    series = series_el.text.strip() if series_el is not None else None

    # group-position refines the collection element's id, not a standalone property
    series_pos = None
    if series_el is not None:
        coll_id = series_el.get('id')
        if coll_id:
            pos_el = root.find(f'.//opf:meta[@property="group-position"][@refines="#{coll_id}"]', NS)
            series_pos = pos_el.text.strip() if pos_el is not None else None

    # pub year: regex from long-description prose (fragile but workable)
    import re
    long_desc = get_meta('se:long-description')
    pub_year = None
    if long_desc:
        m = re.search(r'[Pp]ublished in (\d{4})', long_desc)
        if m:
            pub_year = int(m.group(1))

    repo_slug = opf_path.split(os.sep)[1]

    return {
        'book_id':        repo_slug,
        'title':          get('opf:metadata/dc:title'),
        'author':         get('opf:metadata/dc:creator'),
        'se_date':        get('opf:metadata/dc:date'),        # SE edition date
        'pub_year':       pub_year,                           # original, regex-extracted — verify manually
        'word_count':     get_meta('se:word-count'),
        'flesch_ease':    get_meta('se:reading-ease.flesch'),
        'language':       get('opf:metadata/dc:language'),
        'description':    get('opf:metadata/dc:description'),
        'subjects':       '|'.join(get_all('opf:metadata/dc:subject')),
        'se_subjects':    '|'.join([el.text.strip() for el in root.findall('.//opf:meta[@property="se:subject"]', NS) if el.text]),
        'series':         series,
        'series_pos':     series_pos,
        'wikipedia_url':  get_meta('se:url.encyclopedia.wikipedia'),
        'se_url':         get_meta('se:url.vcs.github'),
        'n_chapters':     len(glob.glob(os.path.join(os.path.dirname(opf_path), 'text', 'chapter-*.xhtml'))),
    }

opf_paths = glob.glob('raw_data/*/src/epub/content.opf')
records = [parse_opf(p) for p in sorted(opf_paths)]

LIB = pd.DataFrame(records)
LIB.index.name = 'book_num'

print(LIB[['title', 'pub_date', 'series', 'n_chapters']].to_string())
LIB.to_csv('LIB.csv', sep='|', index=True)