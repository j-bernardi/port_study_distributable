#!/bin/sh
#make and run for the default material

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo making model displays
bash make_all_enrichments.sh
echo running scripts
bash run_all_enrichments.sh
