"""
Created by:
	@author: James Bernardi
	University of Cambridge
	bernardi.james.h@gmail.com
	
	2017-09-01
"""

import os, sys
from auto_make_model_description import inner_directory_form, path_to_my_models

cumulus_path_to_my_models = "/home/jhbernar/models/my_models"
chunks = 8 # note chunks*threads < 1028 (physical machine limit for EVERYONE)
threads = 4 #ALWAYS LESS THAN 32 (this is number of threads per chunk) - but fewer means more chance of sneaking on a semi-used thread
mem = str(threads * 8 ) +"gb" #probably want 4g per core at least for serpent- is a hard limit anyway, doesn't actually allocate you more RAM
#eg chunksxthreads with mem

walltime = "03:30:00" #hard limit on time allowed to run for

#Read in the directories specified in args eg 4.1 -> model_4.1
if len(sys.argv) > 1 :
    all_flag = False
    starts_with_args = sys.argv[1:]
    for i in range(len(starts_with_args)) :
        starts_with_args[i] = "model_" + starts_with_args[i]
else :
    all_flag = True
    starts_with_args = ["model"]

class FileInfo(object) :
    #Create an object storing the model's info
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
    #find all description files in the directory
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

def output_head(model_number) :
    lines = []
    lines.append("#!/bin/bash")
    lines.append("#PBS -V")
    lines.append("#PBS -N s" + model_number)
    return lines

def processor_info(chunks, threads, mem, walltime) :
    lines = []
    #lines.append("#PBS -l nodes=" + str(nodes) + ":ppn=" + str(cores_per_node))
    lines.append("#PBS -l walltime=" + walltime)
    lines.append("#PBS -l select=" + str(chunks) + ":ncpus=" + str(threads) + ":mem=" + mem )
    return lines

def email_info():
	lines = []
	lines += ["#PBS -m abe"]
	lines += ["#PBS -M jhb57@cam.ac.uk"]
	return lines

def exporting_info(obj, output_directory) :
    lines = []
    lines.append("cd " + output_directory)
    #lines.append("export OMP_NUM_THREADS=" + str(nodes))
    return lines

def command_output(threads, directory) :
    lines = []
    lines.append("mpirun sss2 " + directory + os.sep + "serpent_input_" + obj.file_format + ".serp -omp " + str(threads))
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

    if not all_flag :
        if model in (starts_with_args) :
            for obj in parameter_dictionary[model] :
                model_number = model[6:]
                print "Creating file for", model +" (" + model_number + ")"
                directory = path_to_my_models + os.sep + model
                output_directory = cumulus_path_to_my_models + os.sep + model
            
                #get the lines as a list of lines (return lines_for_file from functions)
                output_lines = []
                output_lines += output_head(model_number)
                output_lines += processor_info(chunks, threads, mem, walltime)
                output_lines += email_info()
                output_lines += exporting_info(obj, output_directory)
                output_lines += command_output(threads, output_directory)
                #write to specific file
                print "Writing file..."
                with open(directory + os.sep + model + '_submission_file_' + obj.blanket_material + '_' + obj.enrichment + '.txt', 'w' ) as output :
                    for x in output_lines :
                        output.write(x + '\n')

    else :
        for obj in parameter_dictionary[model] :
            model_number = model[6:]
            print "Creating file for", model +" (" + model_number + ")"
            directory = path_to_my_models + os.sep + model
            output_directory = cumulus_path_to_my_models + os.sep + model
            
            #get the lines as a list of lines (return lines_for_file from functions)
            output_lines = []
            output_lines += output_head(model_number)
            output_lines += processor_info(chunks, threads, mem, walltime)
            output_lines += email_info()
            output_lines += exporting_info(obj, output_directory)
            output_lines += command_output(threads, output_directory)
            #write to specific file
            print "Writing file..."
            with open(directory + os.sep + model + '_submission_file_' + obj.blanket_material + '_' + obj.enrichment + '.txt', 'w' ) as output :
                for x in output_lines :
                    output.write(x + '\n')


print "Complete"

