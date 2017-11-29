"""
Created by:
	@author: James Bernardi
	University of Cambridge
	bernardi.james.h@gmail.com
	
	2017-09-01
"""

import os, math
#directory_form = 'model_'

#Iterates through all directories in my_models and saves a line of data to the following location

#output location
output_data_directory = 'simulation_data'
output_data_filename = 'raw_data.txt'

script_dir = os.path.dirname(os.path.realpath(__file__))
script_dir_chop_up = script_dir.split(os.sep)

directory_path_to_simulation_data = os.sep.join(script_dir_chop_up[:-1]) + os.sep + output_data_directory + os.sep + output_data_filename 
path_to_my_models = os.sep.join(script_dir_chop_up[:-1]) + os.sep + 'models' + os.sep + 'my_models'

#Read a file and save to the output file
def print_output_to_simulation_datafile(directory_path_to_tbr, directory_path_to_simulation_data, model, enrichment, blanket_mat):
    try :
        with open(directory_path_to_tbr) as f:
            content=f.readlines()
    except :
        print "No file", directory_path_to_tbr, "was found."
        print "Was the serpent simulation run?"
        print "Has the _det0 file been output to the correct place?"
        return

    tbr_list = []
    error_list_sq = []
    macro_tbr_list, macro_error_list_sq = [], []

    for counter in range(0,len(content)):
        if content[counter].startswith('DETli6_mt205') or content[counter].startswith('DETli7_mt205'):
            counter= counter+1
            while content[counter].startswith('];')==False:
                #print(content[counter])
                tbr_list.append(float(content[counter].split()[-2]))
                error_list_sq.append(float(content[counter].split()[-1]))
                counter= counter+1
    
    for counter in range(0,len(content)):
        if content[counter].startswith('DETtbr'):
            counter= counter+1
            while content[counter].startswith('];')==False:
                #print(content[counter])
                macro_tbr_list.append(float(content[counter].split()[-2]))
                macro_error_list_sq.append(float(content[counter].split()[-1]))
                counter= counter+1


    tbr_total = 0
    error_total_sq =0
    macro_total = 0
    error_macro_total_sq = 0

    for i in range(len(tbr_list)):
        error_total_sq += error_list_sq[i] ** 2
        tbr_total += tbr_list[i]
    for i in range(len(macro_tbr_list)):
        macro_total += macro_tbr_list[i]
        error_macro_total_sq += error_list_sq[i] ** 2
    
    error_total = math.sqrt(error_total_sq)
    macro_error_total = math.sqrt(error_macro_total_sq)
    print "\nRESULT:"
    print "tbr total: ", tbr_total
    print "error total: ", error_total
    print "macro tbr total: ", macro_total
    print "macro error total: ", macro_error_total

    new_line = "\n" + model + " " + blanket_mat + " " + enrichment + " " + str(tbr_total) + " " + str(error_total) + " " +str(macro_total) + " " + str(macro_error_total)
    print "full simulated data: ", new_line.strip()

    already_exists_flag = False
    update_required = False
    line_counter = 1
    #write line to file
    with open(directory_path_to_simulation_data, 'a+') as sd :    
        data_as_lines = sd.readlines()
        #initialise if a new file
        if data_as_lines == [] :
            sd.write("model material enrichment tbr_value error macro_tbr_value macro_error")
        #check if the line already exists
        for data_line in data_as_lines :
            
            file_data_list = data_line.split(" ")

            if data_line.startswith(blanket_mat + " " + enrichment) :
          
                already_exists_flag = True
                #checking different cases - update if error is lower, else report no change
                tbr_dif = abs(float(file_data_list[-2].strip()) - tbr_total)
                error_dif = abs(float(file_data_list[-1].strip()) - error_total)
                
                if error_dif < 1e-10 and tbr_dif < 1e-10:
                    print "simulation produced no new results- error and tbr differences  < 1e-10 (or same) "
          
                elif error_dif < 1e-10 :
                    print "updating ", blanket_mat + " " + enrichment, " as error is same but tbr has changed."
                    data_as_lines[line_counter - 1] = new_line 
                    update_required = True
                
                elif float(file_data_list[-1].strip()) > error_total :
                    print "updating ", blanket_mat + " " + enrichment, " as error is lower for new simulated value"
                    print "( " + str(error_total) + " < " + file_data_list[-1].strip() + " )"
                    print "New tbr: ", str(tbr_total), ". Old tbr: ", str(file_data_list[-2]), ". Difference: ", tbr_dif
                    data_as_lines[line_counter - 1] = new_line
                    update_required = True
                
                else : 
                    print "entry already exists with lower error for ", blanket_mat + " " + enrichment, ". Not updating file."

                    "( " + str(error_total) + " > " + file_data_list[-1].strip() + " )"

                    print "New tbr: ", str(tbr_total), ". Old tbr: ", file_data_list[-2]
            line_counter += 1
    
    if not already_exists_flag :
        print "appending new data to " + directory_path_to_simulation_data + "..."
        with open(directory_path_to_simulation_data, 'a') as sd :
            sd.write(new_line)
    elif update_required :
        with open(directory_path_to_simulation_data, 'w') as sd :
            sd.writelines(data_as_lines)
    print '\n'

if __name__ == '__main__' :
    
    directories = os.listdir(path_to_my_models)
    print "directories:", directories

    serpent_output_filenames = []

    #do for each directory, every output file
    for directory in directories :
        for f in os.listdir(path_to_my_models + os.sep + directory) :
            if f.endswith('det0.m') :
                print "appending", f
                serpent_output_filenames.append(path_to_my_models + os.sep + directory + os.sep + f)

    serpent_output_filenames.sort()

    for serpent_output in serpent_output_filenames :
    
        chop_up = serpent_output.split(os.sep)
        file_name_split = chop_up[-1].split('_')
        enrichment = file_name_split[2]
        blanket_mat = file_name_split[3]
        directory = file_name_split[4] + '_' + file_name_split[5][:-5]

        print "file name -", file_name_split,  "- enrichment -", enrichment, "- mat -", blanket_mat

        print_output_to_simulation_datafile(serpent_output, directory_path_to_simulation_data, directory, enrichment, blanket_mat)
