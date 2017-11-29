import os 
from auto_make_model_description import default_enrichment as enrichment
from auto_make_model_description import default_blanket_material as blanket_mat

script_dir = os.path.dirname(os.path.realpath(__file__))
script_dir_chop_up = script_dir.split(os.sep)

path_to_my_models = os.sep.join(script_dir_chop_up[:-1]) + os.sep + 'models' + os.sep + 'my_models'

directories = os.listdir(path_to_my_models)

success_list, failed_list = [], []

for model in directories :

    model_dir = path_to_my_models + os.sep + model
    serpent_input_filename = 'serpent_input_' + enrichment + '_' + blanket_mat + '_' + model
    directory_path_to_serpent_output = model_dir + os.sep + serpent_input_filename + '.serp'

    if os.path.isfile(directory_path_to_serpent_output + "_det0.m") :
        success_list.append(model)
    else :
        failed_list.append(model)

print "DET_0.M FILES EXIST FOR:\n", success_list
print "(" + str(len(success_list)) + "/" + str(len(directories)) + ")"

print "\n\nThese directores exist but have no DET_0.M files:\n", failed_list
print "(" + str(len(failed_list)) + "/" + str(len(directories)) + ")"