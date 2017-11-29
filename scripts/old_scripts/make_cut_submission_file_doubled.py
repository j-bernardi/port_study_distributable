import os, sys
from auto_make_model_description import inner_directory_form, path_to_my_models

cumulus_path_to_my_models = "/home/jbernar/my_models"
nodes = 1 #KEEP AS 1 
cores_per_node = 8 #ALWAYS LESS THAN 32
walltime = "00:15:00"


#TODO: increase cores 
#TODO: change walltime to fit job in

class FileInfo(object) :
	def __init__(self, directory_number) :

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

def output_head() :
    lines = []
    lines.append("#!/bin/sh")
    lines.append("#PBS -V")
    lines.append("#PBS -N python")
    return lines

def processor_info(nodes, cores_per_node, walltime) :
    lines = []
    lines.append("#PBS -l nodes=" + str(nodes) + ":ppn=" + str(cores_per_node))
    lines.append("#PBS walltime=" + walltime)
    return lines

def email_info():
	lines = []
	lines += ["#PBS -m abe"]
	lines += ["#PBS -M jhb57@cam.ac.uk"]
	return lines

def exporting_info(nodes, output_directory) :
    lines = []
    lines.append("cd $" + output_directory)
    lines.append("export OMP_NUM_THREADS=" + str(nodes))
    return lines

def command_output(directory) :
    lines = []
    lines.append("python " + directory + os.sep + 'parallel_cut_prefixes.py ' + " ".join(sys.argv[1:]))
    return lines

#find directories to operate on
directories = find_directories(path_to_my_models, inner_directory_form)

#List of stl file directories
stl_directories = []

#Load up the parameters found in each directory
for model in directories :
    for f in os.listdir(path_to_my_models + os.sep + model) :
        if "cut" in f and os.path.isdir(path_to_my_models + os.sep + model + os.sep + f):
            stl_directories.append(path_to_my_models + os.sep + model + os.sep + f)

for model_dir in stl_directories :

    print "Making submission file for", model_dir
    output_directory = os.sep.join(model_dir.split(os.sep)[:-1])
    
    #get the lines as a list of lines (return lines_for_file from functions)
    output_lines = []
    output_lines += output_head()
    output_lines += processor_info(nodes, cores_per_node,walltime)
    output_lines += email_info()
    output_lines += exporting_info(nodes, output_directory)
    output_lines += command_output(path_to_my_models + '/../../scripts')
    
    #write to specific file
    filename = model_dir.split(os.sep)[-1]
    print "Writing to", output_directory + os.sep + filename+ 'generation_submission_file.txt'
    with open(output_directory + os.sep + filename+ '_generation_submission_file.txt', 'w' ) as output :
        for x in output_lines :
            output.write(x + '\n')
print "Complete"

