import os, sys

#DIRECTORY FINDING
script_dir = os.path.dirname(os.path.realpath(__file__))
script_dir_chop_up = script_dir.split(os.sep)

path_to_my_models = os.sep.join(script_dir_chop_up[:-2]) + os.sep + 'models' + os.sep + 'my_models' #'/media/sf_Ubuntu_Shared/my_models'
path_to_simulation_data = os.sep.join(script_dir_chop_up[:-2]) + os.sep + 'simulation_data'

model_name = 'default'
directory_path_to_stl_files = os.sep.join(script_dir.split(os.sep)[:-2]) + os.sep  + 'models' + os.sep +  model_name

path_to_tbr_data = path_to_simulation_data + os.sep + 'raw_data.txt'
path_to_sa = path_to_simulation_data + os.sep + 'SA_data.txt'
path_to_new_datafile = path_to_simulation_data + os.sep + 'combined_data.txt'

#form: (model: "macro_tbr stat_error" 
tbr_data, surface_area_data = {}, {}

with open(path_to_tbr_data) as tbr :
	content = tbr.readlines()
	for line in content :
		line_list = line.split(" ")
		
		#remove titles
		if line_list[0] == "model" :
			continue

		tbr_data[line_list[0].strip()] = line_list[-2].strip() + " " +  line_list[-1].strip()

with open(path_to_sa) as sa :
	cont = sa.readlines() 
	for line in cont :
		line_list = line.split(" ")
		
		#remove titles
		if line_list[0] == "model" :
			continue
		
		surface_area_data[line_list[0].strip()] = line_list[1].strip()


no_sa_data = []
lines = ["model    surface_area    macro_tbr    %error_tbr"]

#print "tbr data\n", tbr_data
#print "\n\nsa data", surface_area_data

for key in tbr_data :
	
	try :
		new_line = key + " " + surface_area_data[key]
	except :
		print "No surface area data found for", key
		continue

	try :
		new_line = new_line + " " + tbr_data[key]
	except :
		print "No tbr data found for", key, "- ommitting from new data file."
		continue

	lines.append(new_line)	

#print "lines:", lines

with open(path_to_new_datafile, 'a+') as n :
	for line in lines :
		n.write(line + "\n")
