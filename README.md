# Distributable Access-Port Study
## Investigating the effect of access port placement on the tritium breeding ration in EU DEMO

Project worked carried out at Culham Centre for Fusion Energy Summer 2017 by James Bernardi. Full report in this directory.

Flowchart PDF explains full usage of scripts. This points out which parameters can be varied and where

All changes that can be made easily (eg parameters, folder names etc) are at the top of each script.

NB: current folder structure allows scripts to work with default values- each script uses the current folder structure as-is, so will need changing if you wish to change the structure/nomenclature.

Access-ports are made in make_models.py, and from there follow the flowchart to see how they are combined with the NOVA model and eventually simulated upon.

After these have been run, if surface area is required then see secondflow chart for obtaining surface area data.

Repository created by (and acknowledgments made to):
	James Bernardi
	University of Cambridge
	bernardi.james.h@gmail.com


### USAGE 
#### complete information is found in flowchart pdf files- this gives the most important scripts

This package has scripts to generate a serpent input file from a directory of stl-geometry files. Full details contained in flowchart file.

The scripts are designed to keep these scripts and files in directories as marked, but these can be changed at the top of the scripts.

#### material_database.py
	
This script contains a library of materials and related calculations necessary for creating the serpent input.

New materials should be added to this script in the format provided in the script by other materials in the dictionary.
