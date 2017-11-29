SEE FLOW CHART IN PARENT DIRECTORY FOR MORE INFO on the functionality of each script

The surface area flow chart explains usage of sa_scripts

"""
Created by:
	@author: James Bernardi
	University of Cambridge
	bernardi.james.h@gmail.com
	
	2017-09-01
"""

make_model_description.py 
	Works by reading in stl files from a given directory (see in the folder)
	Creates a mmodel description of materials and tally properties based on file prefixes (see within script)
	Reads properties from materials_database.py
	Outputs the description file to directory data_files

simulate.py 
	Reads in data files in the directory data_files, and creates (and runs) a serpent input to serpent_files
	In another directory (simulation_data), it outputs the tbr value and other data.

make_ports_from_file.py
	Reads in parameters from parameters.txt in parameter_files directory, then puts ports in stl_files/my_ports

parallel_cut_prefixes.py 
	Reads in a specified port model and NOVA model in order to output cut files to my_cuts
	This is a model ready to be read-in by simulate.p
