SEE FLOWCHART FOR FULL DESCRIPTION OF DIRECTORY'S FUNCTION

Keep the current folder structure to allow scripts to work with default values- each script uses the current folder structure as-is, so will need changing if you wish to change the structure/nomenclature.
All changes that can be made easily (eg parameters, folder names etc) are at the top of each script.

The models are made in make_models.py, and from there follow the flowchart to see how they are combined with the NOVA model and eventually simulated upon.
The flowchart points out what can be varied and where.

After these have been run, if surface area is required then see secondflow chart for obtaining surface area data.

Repository created by (and acknowledgments made to):
	James Bernardi
	University of Cambridge
	bernardi.james.h@gmail.com


USAGE (complete information is found in flowchart pdf files- this gives the most important scripts):

This package has scripts to generate a serpent input file from a directory of stl-geometry files. 
The scripts are designed to keep these scripts and files in directories as marked, but these can be changed at the top of the scripts.

script 1) make_model_description.py

	This script reads in the stl files and outputs a model description file to a directory specified in the script as.
	The model description uses stl file prefixes to group components, and specify their materials.

	*If materials are to be changed, do this within this script in the materials_dictionary*
	
	The output file is found in the directory 'data_files' with a name specified by the blanket material and enrichment used.
	The script takes 2, 1 or 0 arguments, delimited by a space.
	If 2 are passed, these are the blanket material and the enrichment.
	If one is passed, the script uses a default material in the script and the enrichment is the argument.
	If none are passed, it uses a default specified in the script for both variables.


script 2) simulate.py

	This script uses its arguments to find the datafile requested from the directory 'data_files' (can be changed within the script).
	The script takes 2, 1 or 0 arguments, delimited by a space.
	If 2 are passed, these are the blanket material and the enrichment.
	If one is passed, the script uses a default material in the script and the enrichment is the argument.
	If none are passed, it uses a default specified in the script for both variables.

	The script will output a serpent file in the directory 'serpent_files' and will then run this file from that directory.
	

script 3) material_database.py
	
	This script contains a library of materials and related calculations necessary for creating the serpent input.
	New materials should be added to this script in the format provided in the script by other materials in the dictionary.
