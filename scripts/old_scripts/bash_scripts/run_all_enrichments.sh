#!/bin/sh
#Takes a single argument- blanket material- and runs for each enrichment

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo looking for make_model_description.py file in $DIR

for enrichment in $(seq 0.1 0.1 1.0) 
do
	echo enrichment is $enrichment, running serpent script:
	python $DIR/simulate.py "$1" $enrichment
done 
