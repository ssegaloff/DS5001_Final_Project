# WORK IN PROGRESS, MAY TRASH THIS


# Lyrics are not static data points; they are socially constructed artifacts that change depending on the architectural constraints of the database housing them.

import json
import difflib
import pandas as pd

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_text_divergence(lifeblood_text, genius_text):
    """
    Uses the Ratcliff/Obershelp algorithm to calculate a similarity ratio 
    between two text strings. 1.0 means identical, 0.0 means completely different.
    """
    # Standardize casing to focus on content, not formatting
    lb_clean = lifeblood_text.lower().strip()
    gen_clean = genius_text.lower().strip()
    
    # Calculate similarity
    similarity = difflib.SequenceMatcher(None, lb_clean, gen_clean).ratio()
    
    # Calculate structural differences
    lb_words = len(lb_clean.split())
    gen_words = len(gen_clean.split())
    
    return {
        "similarity_score": round(similarity * 100, 2),
        "lifeblood_word_count": lb_words,
        "genius_word_count": gen_words,
        "word_delta": gen_words - lb_words
    }

def run_comparative_ethnography(lifeblood_file, genius_file):
    print("Loading archives...")
    lifeblood_data = load_json(lifeblood_file) # Assuming a dict of {song_title: lyrics}
    genius_data = load_json(genius_file)       # Assuming the raw Genius JSON dump
    
    # Extract just the songs/lyrics from the Genius artifact
    genius_songs = {song['title'].lower(): song['lyrics'] for song in genius_data['songs']}
    
    comparison_results = []
    
    # Find the overlapping songs present in both archives
    for lb_title, lb_lyrics in lifeblood_data.items():
        search_title = lb_title.lower()
        
        if search_title in genius_songs:
            gen_lyrics = genius_songs[search_title]
            
            stats = calculate_text_divergence(lb_lyrics, gen_lyrics)
            stats['song_title'] = lb_title
            
            comparison_results.append(stats)
            
    # Convert to a DataFrame for easy viewing
    df = pd.DataFrame(comparison_results)
    
    # Sort by the most divergent texts
    df = df.sort_values(by="similarity_score")
    
    return df

if __name__ == "__main__":
    # Example usage:
    # df_comparison = run_comparative_ethnography('raw_data/lifeblood.json', 'raw_data/indigo_girls_genius.json')
    # print("Top 5 Most Divergent Transcriptions:")
    # print(df_comparison.head())
    # df_comparison.to_csv('processed_data/archive_divergence_metrics.csv', index=False)
    pass