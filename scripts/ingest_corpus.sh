#!/bin/bash
# Ingestion script for Agatha Christie Standard Ebooks Corpus

mkdir raw_data
cd raw_data

echo "Cloning repositories..."
git clone git@github.com:standardebooks/agatha-christie_the-murder-at-the-vicarage.git
git clone git@github.com:standardebooks/agatha-christie_giants-bread.git
git clone git@github.com:standardebooks/agatha-christie_the-secret-adversary.git
git clone git@github.com:standardebooks/agatha-christie_the-murder-on-the-links.git
git clone git@github.com:standardebooks/agatha-christie_the-man-in-the-brown-suit.git
git clone git@github.com:standardebooks/agatha-christie_the-big-four.git
git clone git@github.com:standardebooks/agatha-christie_poirot-investigates.git
git clone git@github.com:standardebooks/agatha-christie_the-mysterious-affair-at-styles.git
git clone git@github.com:standardebooks/agatha-christie_the-secret-of-chimneys.git
git clone git@github.com:standardebooks/agatha-christie_the-seven-dials-mystery.git
git clone git@github.com:standardebooks/agatha-christie_the-murder-of-roger-ackroyd.git
git clone git@github.com:standardebooks/agatha-christie_the-mystery-of-the-blue-train.git

echo "Ingestion complete."