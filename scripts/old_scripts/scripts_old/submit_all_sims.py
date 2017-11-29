import os, sys

local_script_dir = os.path.dirname(os.path.realpath(__file__))
local_script_dir_chop_up = local_script_dir.split(os.sep)
local_path_to_my_models = os.sep.join(local_script_dir_chop_up[:-1]) + os.sep + 'models' + os.sep + 'my_models'

remote_path_to_my_models = '/home/jhbernar/models/my_models'

if len(sys.argv) > 1 :
    all_flag = False
    starts_with_args = sys.argv[1:]
    for i in range(len(starts_with_args)) :
        starts_with_args[i] = "model_" + starts_with_args[i]
else :
    all_flag = True
    starts_with_args = "model"

for directory in os.listdir(local_path_to_my_models) :
	if not all_flag :
		if directory in (starts_with_args) :
			for filename in os.listdir(local_path_to_my_models + os.sep + directory) :
				if filename.endswith('.txt') and filename.startswith(directory) and "submission_file" in filename and "generation" not in filename:
					print "submitting", remote_path_to_my_models + os.sep + directory + os.sep + filename
					os.system('ssh jhbernar@login1.cumulus.hpc.l "qsub ' + remote_path_to_my_models + os.sep + directory + os.sep + filename +  '"' )
	else :
		for filename in os.listdir(local_path_to_my_models + os.sep + directory) :
				if filename.endswith('.txt') and filename.startswith(directory) and "submission_file" in filename and "generation" not in filename:
					print "submitting", remote_path_to_my_models + os.sep + directory + os.sep + filename
					os.system('ssh jhbernar@login1.cumulus.hpc.l "qsub ' + remote_path_to_my_models + os.sep + directory + os.sep + filename +  '"' )			