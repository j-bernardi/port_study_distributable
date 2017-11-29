#!/bin/sh
#Takes no arguments- and runs for each enrichment for the default specified in the make script

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo looking for make_model_description.py file in $DIR

for enrichment in $(seq 0.1 0.1 1.0)
do
	echo enrichment is $enrichment, running serpent script:
	python $DIR/simulate.py $enrichment
done 
