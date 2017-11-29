"""
Created by:
	@author: James Bernardi
	University of Cambridge
	bernardi.james.h@gmail.com
	
	2017-09-01
"""

import os, multiprocessing, sys

fix_cores = False
fixed_number_cores = 1

directory_form = 'model_'

script_dir = os.path.dirname(os.path.realpath(__file__))
script_dir_chop_up = script_dir.split(os.sep)

path_to_models = os.sep.join(script_dir_chop_up[:-1]) + os.sep + 'models'

#script currently uses 'path to my models'
path_to_my_models = path_to_models + os.sep + 'my_models'
path_to_destination = path_to_models + os.sep + 'image_dirs'

skip_models_list = []

if len(sys.argv) == 1 :
        directories = os.listdir(path_to_my_models)
else :
    directories.append(directory_form + sys.argv[j])

failed_list, success_list, skipped = [], [], 0

for model_dir in directories :

    found = 0
    for f in os.listdir(path_to_destination + os.sep + model_dir) :  
        if f.endswith(".serp") :
            found += 1
            print "For simulation, found", f, "in", path_to_destination + os.sep + model_dir
            serp_file = f
        
    if found != 1 :
        print "CAUTION:", found, "input files were found in", model_dir

    directory_path_to_serpent_output = path_to_destination + os.sep + model_dir + os.sep + serp_file
    
    if fix_cores :
        cpu_cores = fixed_number_cores
    else :
        cpu_cores = multiprocessing.cpu_count()
    
    print 'Cpu cores found for simulation:', cpu_cores
    
    os.chdir(path_to_destination + os.sep +  model_dir)
    
    if cpu_cores > 1:
        os.system('sss2 '+directory_path_to_serpent_output+ ' -omp '+str(cpu_cores))
    else:
        os.system('sss2 '+directory_path_to_serpent_output)
    #Finally print the output to an output data file, appending or replacing
    
    print "Run has been completed (or exited)"
    #print_output_to_simulation_datafile(directory_path_to_tbr, directory_path_to_simulation_data, model, enrichment, blanket_mat)
            
    if os.path.isfile(directory_path_to_serpent_output + "_det0.m") :
        success_list.append(model_dir)
    else :
        failed_list.append(model_dir)
    
    print ""
    print "COMPLETED SO FAR:", failed_list + success_list
    print "\n"
    print str(len(failed_list + success_list) + skipped) + "/" + str(len(directories))
    print "\n"
    print "FAILED:", failed_list
    print "\n"
    print "SUCCESS:", success_list
    print "\n"
