import sys, os

script_dir = os.path.dirname(os.path.realpath(__file__))
script_dir_chop_up = script_dir.split(os.sep)

path_to_my_models = os.sep.join(script_dir_chop_up[:-1]) + os.sep + 'models' + os.sep + 'my_models'
path_to_default_model = os.sep.join(script_dir_chop_up[:-1]) + os.sep + 'models' + os.sep + 'default'

for directory in os.listdir(path_to_my_models) :
	for stl_file in os.listdir(path_to_default_model) :
		if stl_file.lower().startswith('div') and stl_file.endswith('stl') :
			#copy the file from default/div_x to model_n for all x and then all n
			print "copying", stl_file, "to", directory,
			os.system("cp " + path_to_default_model + os.sep + stl_file +\
							" " + path_to_my_models + os.sep + directory + os.sep + 'default_cut_' + directory)

	print ""