import os, sys
from auto_make_model_description import inner_directory_form, path_to_my_models

cumulus_path_to_my_models = "/home/jhbernar/models/my_models"
nodes = 1 #up to 16?
cores_per_node = 16 #ALWAYS LESS THAN 32
walltime = "05:00:00"


#TODO: increase cores 
#TODO: change walltime to fit job in

class FileInfo(object) :
	def __init__(self, directory_number, blanket_material, enrichment) :
		self.directory_number = directory_number
		self.blanket_material = blanket_material
		self.enrichment = enrichment

		self.file_format = enrichment + "_" + blanket_material + "_model_" + directory_number

def find_directories(path_to_my_models, inner_directory_form):
    """returns a list of directories to generate submission files for based on listed arguments, else all present."""
    if len(sys.argv) > 1 :
            directory_numbers = sys.argv[1:]
            directories = []
            for i in range(len(directory_numbers)):
               directories.append(inner_directory_form + directory_numbers[i]) 
    else :
        directories = os.listdir(path_to_my_models)
    print "Models being considered:", directories
    return directories

def find_description_file_list(directory):
    description_files = []
    for f in os.listdir(directory) :
        if "description" in f and "human" not in f:
            description_files.append(f)
    return description_files

def get_parameter_object_list_from_files(description_files) :
    parameter_object_list = []
    for description_file in description_files :
        
        parameter_list = description_file.split('_')
        
        for i in range(len(parameter_list)) :
            parameter_list[i] = parameter_list[i].replace('.txt', "")

        parameter_object = FileInfo(parameter_list[1], parameter_list[3], parameter_list[4])
        parameter_object_list.append(parameter_object)
    return parameter_object_list

def output_head() :
    lines = []
    lines.append("#!/bin/bash")
    lines.append("#PBS -V")
    lines.append("#PBS -N serpent")
    return lines

def processor_info(nodes, cores_per_node, walltime) :
    lines = []
    lines.append("#PBS -l nodes=" + str(nodes) + ":ppn=" + str(cores_per_node))
    lines.append("#PBS -l walltime=" + walltime)
    return lines

def email_info():
	lines = []
	lines += ["#PBS -m abe"]
	lines += ["#PBS -M jhb57@cam.ac.uk"]
	return lines

def exporting_info(obj, output_directory) :
    lines = []
    lines.append("cd " + output_directory)
    lines.append("export OMP_NUM_THREADS=" + str(nodes))
    return lines

def command_output(nodes, cores_per_node, obj, directory) :
    lines = []
    lines.append("mpirun -np " + str(cores_per_node*nodes) + " sss2 " + directory + os.sep + "serpent_input_" + obj.file_format + ".serp")
    return lines

#find directories to operate on
directories = find_directories(path_to_my_models, inner_directory_form)

#form {"model_x" : [list_of_parameter_objects], .. }
parameter_dictionary = {}

#Load up the parameters found in each directory
print "Creating parameter objects from:"
for model in directories :
    print model + ",",
    directory_path_to_description = path_to_my_models + os.sep + model
    description_files = find_description_file_list(directory_path_to_description)
    parameter_dictionary[model] = get_parameter_object_list_from_files(description_files)
print ""
   
for model in parameter_dictionary :
    for obj in parameter_dictionary[model] :
        print "Creating file for", model
        directory = path_to_my_models + os.sep + model
        output_directory = cumulus_path_to_my_models + os.sep + model
    
        #get the lines as a list of lines (return lines_for_file from functions)
        output_lines = []
        output_lines += output_head()
        output_lines += processor_info(nodes, cores_per_node,walltime)
        output_lines += email_info()
        output_lines += exporting_info(obj, output_directory)
        output_lines += command_output(nodes, cores_per_node, obj, output_directory)
        #write to specific file
        print "Writing file..."
        with open(directory + os.sep + model + '_submission_file_' + obj.blanket_material + '_' + obj.enrichment + '.txt', 'w' ) as output :
            for x in output_lines :
                output.write(x + '\n')
print "Complete"

