#!/usr/bin/env bash

if [ ! -f annuaire_mois_en_cours.txt ]; then
    echo Converting pdf to text...
    pdftotext annuaire_mois_en_cours.pdf -layout
else
    echo phonebook found...
fi

file="annuaire_mois_en_cours.txt"

# Include all lines containing a Dr or Prof
pattern="^.*(\bDr|Dre|Prof\b)\.?[ \t]+([a-zA-Z’ \.-]+).*$"
replacement="\1 \2"

s="$(sed -n -E "s/$pattern/$replacement/p" $file | grep -vE "Mme|liste garde|Gastro-oesophage|Proctologie"|awk '{$1=$1};1' | sort -u | tail -n +2 | awk  '$3!=""')"

# Exclude lines containing  or "Mme"



echo "$s" > parsed_phonebook.txt
