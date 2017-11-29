import os

script_dir = os.path.dirname(os.path.realpath(__file__))
script_dir_chop_up = script_dir.split(os.sep)

path_to_models = os.sep.join(script_dir_chop_up[:-1]) + os.sep + 'models'
path_to_my_models = path_to_models + os.sep + 'my_models'
path_to_destination = path_to_models + os.sep + 'image_dirs'

directories = os.listdir(path_to_my_models)

def make_new_directory(directory):
	if not os.path.exists(directory) :
		os.makedirs(directory)

count = 0

for model in directories :

	make_new_directory(path_to_destination + os.sep + model)
	os.system("cp " + path_to_my_models + os.sep + model + os.sep + "*.serp " + path_to_destination + os.sep + model + os.sep + "serpent_input.serp")
	os.system("cp " + path_to_my_models + os.sep + model + os.sep + "human* " + path_to_destination + os.sep + model + os.sep + "model_description.txt")
	count +=1
	print "copied serpent input and description for model", model, "(" + str(count) + "/" + str(len(directories)) + ")"

