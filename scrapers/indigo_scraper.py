# TODO: EDIT THIS TO MAKE WORK FOR INDIGO GIRLS
"""
indigo_scraper.py
-----------------
Scrapes the Indigo Girls discography from lifeblood.net and builds
an OHCO-structured corpus at the token level.
 
OHCO hierarchy:
    album_title > song_title > stanza_num > line_num > token_num
 
Usage:
    python indigo_scraper.py
"""

import os
import time

import pandas as pd
import json
import requests
from bs4 import BeautifulSoup


# ======= Constants =======

BASE_URL = 'https://jonimitchell.com'
DISCOGRAPHY_URL = f'{BASE_URL}/music/index.cfm'
USER_AGENT = f'BeanBot/2.2 (bhj3vc@virginia.edu) python-requests/{requests.__version__}'
HEADERS = {
    'User-Agent': USER_AGENT,
    'From': 'bhj3vc@virginia.edu'
}

# ======= Scraping Functions =======

def get_album_urls(discography_url, headers, base_url='https://jonimitchell.com'):
    """
    Scrapes discography index and returns a list of dictionaries,
    each containing the album's URL, title, and release date.
    """

    # get discography page
    print(f"Pinging {discography_url} for album index...")
    r = requests.get(discography_url, headers=headers)

    # check if request was successful
    if r.status_code != 200:
        print(f"Warning: Received status code {r.status_code}.")
        return []

    # parse the html with BeautifulSoup
    soup = BeautifulSoup(r.text, 'html.parser')

    # target the div that contains all the info for a single album
    gallery_items = soup.find_all('div', class_='gallery-item')

    albums = []

    for item in gallery_items:
        # extract the URL
        a_tag = item.find('a', href=True)
        if not a_tag or 'album.cfm' not in a_tag['href']:
            continue # skip item if it doesn't have a valid album link
        
        full_url = base_url + a_tag['href']

        # extract title
        title_tag = item.find('span', class_='albumtitle')
        title = title_tag.text.strip() if title_tag else 'Unknown Title'
        
        # extract release date
        date_tag = item.find('span', class_='released')
        if date_tag:
            # remove the word "Released' so you just have Month Day Year
            release_date = date_tag.text.replace('Released ', '').strip()
        else:
            release_date = 'Unknown Date'
        # bind the info together into a single record
        album_record = {
            'album_url': full_url,
            'album_title': title,
            'release_date': release_date
        }

        albums.append(album_record)

    return albums


def get_album_tracks(album_record, headers, base_url='https://jonimitchell.com/music/'):
    """
    Takes a single album dictionary, visits its page, and returns a list of
    dictionaries representing the individual songs on that album.
    """

    album_url = album_record['album_url']
    print(f"  -> Digging into album: {album_record['album_title']}...")

    r = requests.get(album_url, headers=headers)
    time.sleep(3) # be polite to server and wait a few seconds before the next request
    
    if r.status_code != 200:
        print(f"  Warning: Received status code {r.status_code} for album page.")
        return []

    soup = BeautifulSoup(r.text, 'html.parser')

    # find the div that contains the track listing
    tracklist_ul = soup.find('ul', class_='tracklist') # ul in html means unordered list

    if not tracklist_ul:
        print("  Warning: No tracklist found on this page.")
        return []

    # extract links within the tracklist
    song_links = tracklist_ul.find_all('a', href=True)

    songs = []

    for link in song_links:
        href = link['href']

        # make sure its a song link
        if 'song.cfm?id=' not in href:
            continue # skip if it's not a valid song link

        # extract songs within tracklist
        song_title = link.contents[0].strip()

        # make sure the song title is not empty
        if not song_title:
            continue # skip if song title is empty

        # get url and title for each song and carry down album metadata
        song_record = {
            'song_url': base_url + href,
            'song_title': song_title,
            'album_title': album_record['album_title'], # preserving ohco hierarchy
            'release_date': album_record['release_date'] # preserving ohco hierarchy
        }

        songs.append(song_record)

    # remove duplicates
    # sometimes tracklists link the same song twice (clicking number v title for ex)
    unique_songs = {song['song_url']: song for song in songs}.values()

    return list(unique_songs)


def get_song_lyrics(song_record, headers):
    """
    Visits a specific song page, extracts the author, lyrics, and copyright,
    and returns a complete, finalized dictionary for the corpus.
    """

    song_url = song_record['song_url']
    print(f"    -> Fetching lyrics for song: {song_record['song_title']}")

    r = requests.get(song_url, headers=headers)
    time.sleep(2) # be polite to server and wait a few seconds

    if r.status_code != 200:
        print(f"    Warning: Received status code {r.status_code} for song page.")
        song_record.update({'author': None, 'copyright': None, 'lyrics': None})
        return song_record

    soup = BeautifulSoup(r.text, 'html.parser')

    # extract the author
    # note the author tag is outside of the lyrics div, so we have to look for it separately by searching the whole soup
    author_tag = soup.find('p', class_='author')
    if author_tag:
        author_text = author_tag.text.strip()
        # clean the data: remove "by" if it exists at start of string and strip whitespace
        if author_text.lower().startswith('by '):
            author_text = author_text[3:].strip()
        song_record['author'] = author_text
    else:
        song_record['author'] = "Unknown"

    # target the lyrics container
    lyrics_div = soup.find('div', class_='songlyrics')

    if not lyrics_div:
        print("    Warning: No lyrics found on this page.")
        song_record.update({'copyright': None, 'lyrics': None})
        return song_record

    # extract copyright metadata
    copyright_tag = lyrics_div.find('p', class_='lyricscopyright')
    if copyright_tag:
        song_record['copyright'] = copyright_tag.text.replace('© ', '').strip()
    else:
        song_record['copyright'] = "Unknown"

    # extract OHCO-ready lyrics text
    lyrics_paragraphs = lyrics_div.find_all('p', class_=lambda x: x != 'lyricscopyright') # get all paragraphs except the copyright one
    
    raw_lyrics = []
    for p in lyrics_paragraphs:
        # get_text(separator='\n') will replace all <br> tags with actual line breaks
        raw_lyrics.append(p.get_text(separator='\n').strip())
    
    song_record['lyrics'] = '\n\n'.join(raw_lyrics)

    return song_record


# ======= Corpus Builder =======

def build_joni_corpus(discography_url, headers):
    """
    Orchestrates the 3-level extraction pipeline and transforms the
    resulting data into an OHCO-formatted pandas DataFrame.
    """
    print("Starting corpus build process...\n")
    final_corpus = []

    # skip scraping and go straight to OHCO transformation if raw JSON data already exists
    raw_path = 'data/raw/joni_mitchell_raw.json'
    if os.path.exists(raw_path):
        print("Raw JSON found, skipping scraping...")
        with open(raw_path, 'r') as f:
            final_corpus = json.load(f)

    else:
        # level 1: get album urls
        albums = get_album_urls(discography_url, headers)
        total_albums = len(albums)

        # to test on a subset, replace albums with albums[:2] or however many you want to test on
        for i, album in enumerate(albums, start=1):
            print(f"\nAlbum {i} of {total_albums}:")
            # level 2: get song urls by iterating through albums
            songs = get_album_tracks(album, headers)

            for song in songs:
                # level 3: get lyrics and metadata for each song
                complete_record = get_song_lyrics(song, headers)
                final_corpus.append(complete_record)

        print("\nExtraction complete!")

        # save the raw extracted corpus as JSON for posterity
        os.makedirs("data/raw", exist_ok=True)
        with open('data/raw/joni_mitchell_raw.json', 'w') as f:
            json.dump(final_corpus, f, indent=2)

        print("Raw corpus saved to data/raw/joni_mitchell_raw.json")

    print("\nStarting OHCO transformation...")

    # OHCO transformation
    df = pd.DataFrame(final_corpus)
    
    # get rid of tracks with no lyrics (instrumentals, etc)
    df = df.dropna(subset=['lyrics'])

    # split into stanzas by double line break
    df_stanzas = df.set_index(['album_title', 'release_date', 'song_title', 'author', 'copyright', 'song_url'])['lyrics']\
        .str.split('\n\n', expand=True)\
        .stack()\
        .to_frame('stanza_text')
    
    df_stanzas.index.names = ['album_title', 'release_date', 'song_title', 'author', 'copyright', 'song_url', 'stanza_num']

    # split into lines
    df_lines = df_stanzas['stanza_text'].str.split('\n', expand=True)\
        .stack()\
        .to_frame('line_text')
    
    df_lines.index.names = ['album_title', 'release_date', 'song_title', 'author', 'copyright', 'song_url', 'stanza_num', 'line_num']
    df_lines['line_text'] = df_lines['line_text'].str.strip() # clean up whitespace

    # split lines into individual words
    # using whitespace and punctuation as delimiters for now
    # TO BE UPDATED USING NLTK OR OTHER METHODS FROM NOTES
    # using a regular expression (\W+ splits on any non-word character)
    df_tokens = df_lines['line_text'].str.split(r'\W+', expand=True)\
        .stack()\
        .to_frame('token_str')
    
    # name the deepest index level 'token_num'
    # dynamically grab existing index names from df_lines and add our new one
    df_tokens.index.names = list(df_lines.index.names) + ['token_num']

    # clean artifacts
    # lowercase all tokens
    df_tokens['token_str'] = df_tokens['token_str'].str.lower()

    # drop any empty strings that may have been created during regex split
    df_tokens = df_tokens[df_tokens['token_str'].notna() & (df_tokens['token_str'] != '')]

    print("Token-level OHCO built successfully.")

    # return the line-level and token-level dataframes
    return df_lines, df_tokens


# ======= Main =======

if __name__ == "__main__":
    # ensure a directory exists for the outputs
    os.makedirs('data/processed', exist_ok=True)

    # run pipeline
    CORPUS, TOKENS = build_joni_corpus(DISCOGRAPHY_URL, HEADERS)
    
    # LIB table (unique metadata per album)
    LIB = (
        CORPUS.index.to_frame()
        .reset_index(drop=True)[['album_title', 'release_date']]
        .drop_duplicates()
        .set_index('album_title')
    )

    print("\n--- LIB (album library) ---")
    print(LIB)
    print(f"\n--- CORPUS: {len(CORPUS):,} lines ---")
    print(f"--- TOKENS: {len(TOKENS):,} tokens ---")


    # Save outputs
    LIB.to_csv('data/processed/joni_mitchell_LIB.csv')
    CORPUS.to_csv('data/processed/joni_mitchell_CORPUS.csv')
    TOKENS.to_csv('data/processed/joni_mitchell_TOKENS.csv')

    print("\nSaved: joni_mitchell_LIB.csv, joni_mitchell_CORPUS.csv, joni_mitchell_TOKENS.csv")

    print("\nScript complete!")