import os

local_script_dir = os.path.dirname(os.path.realpath(__file__))
local_script_dir_chop_up = local_script_dir.split(os.sep)
local_path_to_my_models = os.sep.join(local_script_dir_chop_up[:-1]) + os.sep + 'models' + os.sep + 'my_models'

remote_path_to_my_models = '~/models/my_models'

for directory in os.listdir(local_path_to_my_models) :
	for filename in os.local_script_dir(local_path_to_my_models + os.sep + directory) :
		if filename.endswith('submission_file.txt') :
			os.system('ssh jhbernar@login1.cumulus.hpc.l "llsubmit ' + remote_path_to_my_models + os.sep + directory + os.sep + filename +  '"' )
