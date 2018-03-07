#!/usr/bin/env bash

# ENCODES THE PHONEBOOK AS: SEX/PROFESSOR/NAME/INITIALS/1ST INITIAL

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

# parse phonebook into a partially sanitized list
list="$(sed -n -E "s/$pattern/$replacement/p" $file | grep -vE "Mme|liste garde|Gastro-oesophage|Proctologie" | unaccent UTF-8 | sort | awk -F '[ ]' '{gsub(/\./, ""); gsub(/\s*$/, "") $3!=""};1' | tail -n +2 | uniq)"
echo "$list" > parsed_phonebook.txt

# remove lines not containing an all caps word
table="$(sed -n -E '/\b[A-Z-]{2,}\b/p' parsed_phonebook.txt)"
echo "$table" > parsed_phonebook.txt

# underscores between parts of family name
table1="$(sed -E "s/(\b[A-Z]+\b)( )/\1_/g" parsed_phonebook.txt)"
echo "$table1" > parsed_phonebook.txt

# remove underscores between name and surname
table2="$(sed -E "s/(_)([A-Z][a-z-]+|[A-Z]$|[a-z]+)/ \2/g" parsed_phonebook.txt)"
echo "$table2" > parsed_phonebook.txt

# remove underscores between name and lone caps (surname initial)
table3="$(sed -E "s/(_)([A-Z] [A-Z][a-z-]+)/ \2/g" parsed_phonebook.txt)"
echo "$table3" > parsed_phonebook.txt

# dash between surname parts
table4="$(sed -E "s/( [A-Z][a-z-]+)( )/\1-/g" parsed_phonebook.txt)"
echo "$table4" > parsed_phonebook.txt
table4a="$(sed -E "s/( [A-Z][a-z]+-[A-Z][a-z]+)( )/\1-/g" parsed_phonebook.txt)"
echo "$table4a" > parsed_phonebook.txt


# dash between intial and surname
table5="$(sed -E "s/(\b[A-Z])( )([A-Z][a-z-]+\b)/\1-\3/g" parsed_phonebook.txt)"
echo "$table5" > parsed_phonebook.txt

# remove lines not containing a caps+normal or caps alone word
table6="$(sed -n -E '/( [A-Z][a-z-]+| [A-Z])\b/p' parsed_phonebook.txt)"
echo "$table6" > parsed_phonebook.txt

# replace  Dr(e) and Prof: 'F'=female 'M'=male 'D'=Dr 'P'=Prof
table7="$(sed -E 's/^Dre\b/F D/' parsed_phonebook.txt)"
echo "$table7" > parsed_phonebook.txt
table8="$(sed -E 's/^Dr\b/M D/' parsed_phonebook.txt)"
echo "$table8" > parsed_phonebook.txt
table9="$(sed -E 's/^Prof\b/I P/' parsed_phonebook.txt)"
echo "$table9" > parsed_phonebook.txt

#replace surnames by initials
table10="$(sed -E 's/\b([A-Z])[a-z]+/\1/g' parsed_phonebook.txt)"
echo "$table10" > parsed_phonebook.txt
table11="$(sed -E 's/\b([A-Z])[a-z]+-([A-Z])$/\1\2/' parsed_phonebook.txt)"
echo "$table11" > parsed_phonebook.txt

# replace spaces by commas and underscores by spaces, then decompose initials
table12="$(sed -E 's/ /\,/g' parsed_phonebook.txt)"
echo "$table12" > parsed_phonebook.txt
table13="$(sed -E 's/_/ /g' parsed_phonebook.txt)"
echo "$table13" > parsed_phonebook.txt
table14="$(awk -F ',' '{gsub(/-/,"", $4); gsub(/KP D/,"K", $4); print}' OFS=',' parsed_phonebook.txt)"
echo "$table14" > parsed_phonebook.txt
#table15="$(sed -E 's/(,[A-Z])$/\1\1/g' parsed_phonebook.txt)"
#echo "$table15" > parsed_phonebook.txt
#table16="$(sed -E 's/([A-Z])([A-Z])$/\1\2\,\1/g' parsed_phonebook.txt)"
#echo "$table16" > parsed_phonebook.txt

echo -e ".mode csv\ncreate table subjects(sex CHAR, status CHAR, name TEXT, initials TEXT);\n.import parsed_phonebook.txt subjects" | sqlite3 phonebook.db

echo "The above error is due to a malformed record. The info is correct, only the dropped extra is malformed."
echo "Done."
