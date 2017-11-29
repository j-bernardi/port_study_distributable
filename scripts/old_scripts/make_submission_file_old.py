import os
from auto_make_model_description import inner_directory_form, path_to_my_models

max_cpu_count = ?

class FileInfo(object) :
	def __init__(self, directory_number, blanket_material, enrichment, )

def find_directories(path_to_my_models, inner_directory_form):
	"""returns a list of directories to generate submission files for based on listed arguments, else all present."""
	if len(sys.argv) > 1 :
	        directory_numbers = sys.argv[1:]
	        directories = []
	        for i in range(len(directory_numbers)):
	           directories.append(inner_directory_form + directory_numbers[i]) 
	    else :
	        directories = os.listdir(path_to_my_models)
	    print "models being considered:", directories
	    return directories

def find_description_file_list(directory):
	description_files = []
	for f in os.listdir(directory) :
    	if "description" in f :
    		description_files.append(f)
    return description_files

def get_parameter_object_list_from_files(description_files) :
	parameter_object_list = []
	for description_file in description_files :
    	
    	parameter_list = description_file.split('_')
    	parameter_object = FileInfo(parameter_list[1], parameter_list[3], parameter_list[4])
    	parameter_object_list.append(parameter_object)
    return parameter_object_list

def output_head() :
	lines = []
	lines.append("#!/bin/sh")
	lines.append("# @ jobtype = openmpi")
	lines.append("# @ input = /dev/null")
	return lines

def output_error_line(obj) :
	lines = ["# @ error = /common/scratch/jhbernar/my_models/serpent_error_" +\
		"_" + obj.enrichment + "_" + obj.blanket_material + "_model_" + obj.directory_number ".err"]
	return lines

def output_output_and_init(obj) :
	lines = []
	lines.append("# @ output = /common/scratch/jhbernar/my_models/serpent_output_" + obj.enrichment +\
			"_" + obj.blanket_material + "_model_" + obj.directory_number + ".terminal")
	lines.append("# @ initialdir= /common/scratch/jhbernar/my_models/model_" + obj.directory_number)
	return lines

def processor_info(cpu_count) :
	lines = []
	lines.append("# @ max_processors = " + str(max_cpu_count))
	lines.append("# @ min_processors = " + str(max_cpu_count/2))
	lines.appen("# @ queue")
	return lines

def command_output(obj) :
	lines = []
	lines.append("sss2 serpent_input_" + obj.enrichment + "_" + obj.blanket_material +\
		 "_model_" + obj.directory_number + ". serp")
	return lines

#find directories to operate on
directories = find_directories(path_to_my_models, inner_directory_form)

#form {"model_x" : [list_of_parameter_objects], .. }
parameter_dictionary = {}

#Load up the parameters found in each directory
for model in directories :

    directory_path_to_description = path_to_my_models + os.sep + model
    description_files = find_description_file_list(directory_path_to_description)
   	parameter_dictionary[model] = get_parameter_object_list_from_files(description_files)
   
for model in parameter_dictionary :
	for obj in parameter_dictionary[model] :

		#get the lines as a list of lines (return lines_for_file from functions)
		output_lines = []
		output_lines += output_head()
		output_lines += output_error_line(obj)
		output_lines += output_output_and_init(obj)
		output_lines += processor_info(max_cpu_count):
		output_lines += command_output(obj)
		#write to specific file
		with open(directory_path_to_description + os.sep + model + '_submission_file_' + obj.blanket_material + '_' + obj.enrichment + '.txt', 'w' ) as output :
			for x in output_lines :
				output.write(x + '\n')

"""
OUTPUTS:
#!/bin/sh

# @ jobtype = openmpi
# @ input = /dev/null
# @ error = /common/scratch/jshimwell/mcnp_inputs/nm_0.0756_lc_0.0224_Li4SiO4_0.64_1.0_Zr5Pb4_0.64_tbr_.err
# @ output = /common/scratch/jshimwell/mcnp_inputs/nm_0.0756_lc_0.0224_Li4SiO4_0.64_1.0_Zr5Pb4_0.64_tbr_.terminal
# @ initialdir= /common/scratch/jshimwell/mcnp_inputs
# @ max_processors = 1
# @ min_processors = 1
# @ queue

sss2 input.serp
"""

#	OTHER running methods:
#   mpirun -np 4 sss2 input.serp
#   sss2 input.serp
#   sss2 input.serp -omp 4
