"""
USAGE: 
Cuts the model specified by model_name with the ports specified by the arguments

No arguments specifies all directories in my_ports (except model number 0- test)
Arguments can be passed to list specific directories (eg python parallel_cut.py 1 2 5 - for models 1, 2, 5)
Outputs the cut model into my_cuts specifying the model name and number from which it was evolved

NOTE: first_wall_prefix must be updated to the correct structure when known. This structure must completely encase the reactor
"""

import sys, os, copy, math
#sys.path.append('/usr/lib/freecad/lib/')
sys.path.append('/usr/lib/freecad-daily/lib/')
import FreeCAD, Part, Draft, Mesh, BOPTools
from BOPTools import SplitAPI
import multiprocessing as mp 
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process, Manager
from shutil import copyfile
from Queue import Queue
##############################################

ignore_file_prefixes = ['NONE'] # 'NONE' defaults to no ignores
only_file_prefixes = [""]#["bss"] #empty string defaults to all
#only_file_prefixes = ["BSS_1.stl", "BSS_6.stl", "BSS_8.stl"] #empty string defaults to all - good for model 3

#prefix that defines the first wall in order to perform boolean fragments with the ports
first_wall_prefix = 'BSS' #Note-this MUST completely encase/cut the ports (ie overhang will produce an errr)
bounding_box_prefix = "OUTER" #prefix on stl files defining just a box where the port goes
bounding_casing_prefix = 'ow' #suffix on the stl files form "NBPortn_(bounding_casing_prefix).stl"

models_folder = 'models'
my_models = 'my_models'
directory_form = 'model_'

model_name = 'default' # change if required
 
port_folder = 'my_ports'
port_std_name = 'generated_ports_' 

output_suffix = 'cut_'

##############################################
script_dir = os.path.dirname(os.path.realpath(__file__))
script_dir_chop_up = script_dir.split(os.sep)

path_to_my_models = os.sep.join(script_dir_chop_up[:-1])+os.sep + models_folder + os.sep + my_models

directory_path_to_stl_dir = os.sep.join(script_dir_chop_up[:-1])+os.sep + models_folder + os.sep + model_name

##############################################
count = 0

def magnitude(vect) :
	sqrs = vect.x ** 2 + vect.y ** 2 + vect.z ** 2
	return math.sqrt(sqrs)

def lower_tuple(tup) :
	result = []
	for i in range( len(tup) ) :
		result.append(tup[i].lower()) 
	return tuple(result)

def make_new_directory(directory):
	if not os.path.exists(directory) :
		print "Making new directory", directory
		os.makedirs(directory)
	else :
		print "Directory", directory, "found."

def split_dict_to_key_parts(dictionary) :
	"""Splits a dictionary's keys in to equal(ish) parts dep on cpu count
	Returns a list of lists of keys """
	cpu_count = mp.cpu_count()
	part_list = []
	key_list = dictionary.keys()
	len_part = len(dictionary) / cpu_count

	if cpu_count >= len(dictionary) :
		for key in dictionary :
			part_list.append([key]) 
	else :
		for i in range(cpu_count - 1) :
			part_list.append(key_list[i*len_part : (i+1) * len_part] )
		part_list.append(key_list[(cpu_count -1) * len_part : ])

	return part_list

def split_list_to_parts(lst) :
	cpu_count = mp.cpu_count()
	part_list = []
	len_part = len(lst) / cpu_count

	#print "cpus", cpu_count
	#print "list len", len(lst)
	#print "partlen", len_part

	if cpu_count >= len(lst) :
		for item in lst :
			part_list.append([item])
	else :
		for i in range(cpu_count - 1) :
			#print "range", i*len_part, ":", (i+1)*len_part
			part_list.append(lst[i*len_part : (i+1) * len_part] )
		part_list.append(lst[(cpu_count -1)*len_part : ])

	return part_list

def get_port_dict(outer_casing_prefix, prefix_wanted_flag, port_dir) :
	"""returns a list of the port objects with (or without) the given prefix from the given directory"""
	""" Form : {port_name : solid_stl, ... } """
	manager = Manager()
	port_dict = manager.dict()
	cpu_count = mp.cpu_count()
	file_list = []

	if prefix_wanted_flag :
		for geofile in os.listdir(port_dir) :
			if geofile.endswith(".stl") and geofile.lower().startswith(outer_casing_prefix.lower()) :
				file_list.append(geofile)
	else :
		for geofile in os.listdir(port_dir) :
			if geofile.endswith(".stl") and not geofile.lower().startswith(outer_casing_prefix.lower()) :
				file_list.append(geofile)

	#print file_list
	total = len(file_list)
	file_list_split = split_list_to_parts(file_list)

	#print file_list_split
	global count
	count = 0
	with ThreadPoolExecutor(max_workers = cpu_count) as executor : 
		for lst in file_list_split :
			#print "passing", lst
			executor.submit(make_solid, lst, port_dir, port_dict, total)

	return port_dict

def get_model_dict(model_dir, ignore_file_prefixes = ["NONE"], only_file_prefixes = [""]) :
	"""returns a dict of the model objects from the given directory"""
	""" Form : {port_name : solid_stl, ... } """

	print "File prefixes being read (if blank, all):", only_file_prefixes
	print "Ignored file prefixes:", ignore_file_prefixes

	cpu_count = mp.cpu_count()
	file_list = []
	for geofile in os.listdir(model_dir) :
		if geofile.endswith(".stl") and (not geofile.lower().startswith(lower_tuple(tuple(ignore_file_prefixes))) and geofile.lower().startswith(lower_tuple(tuple(only_file_prefixes))) ) :
			file_list.append(geofile)
	
	total_files_found = len(file_list)
	file_list_split = split_list_to_parts(file_list)

	#print file_list_split

	manager = Manager()
	model_dict = manager.dict()

	print("Fetching " + str(total_files_found) + " model components from " + model_dir + " out of " + str(total_files_found) + "...")
	global count
	count = 0
	with ThreadPoolExecutor(max_workers = cpu_count) as executor : 
		for lst in file_list_split :
			executor.submit(make_solid, lst, model_dir, model_dict, total_files_found)

	return model_dict

def make_solid(geofile_list, directory, dicti, total):
	"""Takes a file to read in, the directory in which it is found, and the dictionary into which to put it"""
	global count
	for geofile in geofile_list :
		print "*** Creating solid from file: " + geofile + " (" + str(count + 1) + "/" + str(total) + ") ***"
		count += 1
		obj = Mesh.Mesh(os.path.join(directory, geofile))
		shape = Part.Shape()
		shape.makeShapeFromMesh(obj.Topology, 0.05)
		solid = Part.makeSolid(shape)
	
		dicti[("").join(geofile.split(".")[:-1])] = solid

def split_ports_remove_inner(port_dict, model_dict, first_wall_prefix, bounding_casing_prefix, outer_casing_prefix) :
	"""Perform boolean fragments with all the first wall structures in common in the model dict"""
	i = 0
	#first find all the first wall objects the port cuts
	for port in port_dict :
		if port.lower().startswith(bounding_casing_prefix.lower()) :

			port_number = ""
			for c in port :
				if c.isdigit():
					port_number += c

			print "\nSplitting outer port", port, "(" +str(i+1) + "/" + str(len(outer_port_dict)) + ")"
			i += 1

			common_list = find_fw_components_in_common(first_wall_prefix, port_dict[port], model_dict)
			fused_object = fuse_object_list(common_list)

			print "Performing fragmentation..."

			#fragment each port with its fused object and update the port object
			key_list_split = split_dict_to_key_parts(port_dict)
			global count
			count = 0
			cpu_count = mp.cpu_count()
			
			with ThreadPoolExecutor(max_workers = cpu_count) as executor :
				for key_list in key_list_split :
					executor.submit(fragment, key_list, port_dict, fused_object, port_number, outer_casing_prefix)

			print "completed\n"

def find_fw_components_in_common(first_wall_prefix, port_outer_component, model_dict):
	print "Finding", first_wall_prefix, "objects in common with port..."
	common_list = []

	key_list_split = split_dict_to_key_parts(model_dict) 
	global count
	count = 0 
	cpu_count = mp.cpu_count()
	common_dict = {}
	with ThreadPoolExecutor(max_workers = cpu_count) as executor :
		for key_list in key_list_split :
			executor.submit(iterate_common, key_list, model_dict, first_wall_prefix, port_outer_component, common_dict)

	common_list = []
	for key in common_dict :
		common_list.append(common_dict[key])
	return common_list

	"""
	OLD
	for piece in model_dict :
		if piece.lower().startswith(first_wall_prefix.lower()):
			if model_dict[piece].common(port_outer_component).Volume != 0 :
				common_list.append(model_dict[piece])
	return common_list
	"""

def iterate_common(key_list, model_dict, first_wall_prefix, port_outer_component, common_dict) :
	for piece in key_list :
		if piece.lower().startswith(first_wall_prefix.lower()):
			if model_dict[piece].common(port_outer_component).Volume != 0 :
				common_dict[piece] = model_dict[piece]

def fuse_object_list(common_list) :
	print "Fusing...",
	if len(common_list) == 0 :
		print "No fw structures found in common with this port!"
		return
	new_obj = common_list[0]
	if len(common_list) > 1 :
		for i in range(1, len(common_list)) :
			new_obj = new_obj.fuse(common_list[i])
	print "Success"
	return new_obj

def fragment(key_list, port_dict, fused_object, port_number, outer_casing_prefix) :
	for port in key_list :
		if ("NBPort" + port_number) in port and not port.startswith(outer_casing_prefix) : 

			pieces = SplitAPI.booleanFragments([fused_object, port_dict[port]], "Standard")
			downgraded_pieces = pieces.Solids
			
			for solid in downgraded_pieces :
				if solid.common(port_dict[port]).Volume == 0 :
					downgraded_pieces.remove(solid)
			
			#find the order of the remaining 3
			positions = {magnitude(downgraded_pieces[0].CenterOfMass) : downgraded_pieces[0], \
						magnitude(downgraded_pieces[1].CenterOfMass) : downgraded_pieces[1], \
						magnitude(downgraded_pieces[2].CenterOfMass) : downgraded_pieces[2] }
			
			mini = magnitude(downgraded_pieces[0].CenterOfMass)
			for val in positions :
				if val < mini :
					mini = val
			del positions[mini]

			remaining_list = []
			for val in positions :
				remaining_list.append(positions[val])

			if len(remaining_list) != 2 :
				print "********** WARNING in" + port + " ************"
				print "Expected 2 items remaining after removing minimum fragment"
				print "Recieved", len(remaining_list)

			new_port = Part.makeSolid(remaining_list[0].fuse(remaining_list[1]))
			print port, "completed"
			port_dict[port] = new_port

def cut_holes_in_model(outer_port_dict, model_dict) :
	"""Takes a dictionary of port outer-casings"""
	"""Perform a cut on every model part with the outer port dictionaries"""
	print("Cutting the port components out of the model")
	print 'number of cuts to make', len(model_dict)
	global counter
	counter = 0
	manager = Manager()
	cut_parts = manager.dict()
	cpu_count = mp.cpu_count()

	key_list_split = split_dict_to_key_parts(model_dict)

	with ThreadPoolExecutor(max_workers = cpu_count) as executor :
		for lst in key_list_split :
			executor.submit(cut_model, lst, model_dict, outer_port_dict, cut_parts)

	return cut_parts

def cut_model(component_list, model_dict, port_dict, cut_components) :
	global counter 
	for component in component_list :
		print("Copying " + component + " to be cut..")
		cut_component = copy.deepcopy(model_dict[component])
		print("Cutting part " + component+ " " + str(counter+1) + "/" + str(len(model_dict)) )
		counter +=1
		for port in port_dict :
			cut_component = cut_component.cut(port_dict[port])
		cut_components[component] = cut_component

def save_files_to_output(solid_dict, directory) :

	cpu_count = mp.cpu_count()
	key_list_split = split_dict_to_key_parts(solid_dict)
	with ThreadPoolExecutor(max_workers = cpu_count) as executor :
		for lst in key_list_split :
			executor.submit(parasave, lst, directory, solid_dict)

def parasave(key_list, directory, solid_dict) :
	for solid in key_list : 
		solid_dict[solid].exportStl(directory + os.sep + solid + ".stl")

def get_directories_from_args(path_to_my_models, directory_form) :

	directories = []
	if len(sys.argv) == 1 :
		"""consider all but directory 0 (hence the range(1, number))"""
		directories = os.listdir(path_to_my_models)
	else :
		directory_nums = sys.argv[1:]
		for num in directory_nums :
			directories.append(directory_form + num)
	return directories

def add_plasma_params(path_to_cut_model, path_to_original_model) :
	if not os.path.exists(path_to_cut_model + os.sep + 'Plasma_params.txt') :
		print "copying Plasma_params.txt from", path_to_original_model, "to", path_to_cut_model
		copyfile(path_to_original_model + os.sep + 'Plasma_params.txt', path_to_cut_model + os.sep + 'Plasma_params.txt')
	else :
		print "Plasma_params.txt found in", path_to_cut_model, ". Continuing..."

directories = get_directories_from_args(path_to_my_models, directory_form)

print("Examining directories", directories)

for model in directories :

	model_number = ""
	for c in model:
		if c.isdigit() :
			model_number += c


	directory_path_to_current_ports = path_to_my_models + os.sep + model  + os.sep + port_std_name + model
	current_directory_path_to_output = path_to_my_models + os.sep + model + os.sep + model_name + '_' + output_suffix + model
	
	#Set output and input paths
	print("Working on model number " + str(model_number) + "...")
	
	#make the new output directory if one is required
	make_new_directory(current_directory_path_to_output)
	
	print("Making outer port dict (and copying)")
	outer_port_dict = get_port_dict(bounding_box_prefix, True, directory_path_to_current_ports).copy()
	print("Making port dict (and copying)")
	port_dict = get_port_dict(bounding_box_prefix, False, directory_path_to_current_ports).copy()
	print("Making model dict (and copying)")
	model_dict = get_model_dict(directory_path_to_stl_dir, ignore_file_prefixes = ignore_file_prefixes, only_file_prefixes = only_file_prefixes).copy()

	split_ports_remove_inner(port_dict, model_dict, first_wall_prefix, bounding_casing_prefix, bounding_box_prefix)

	cut_model_dict = cut_holes_in_model(outer_port_dict, model_dict).copy()

	add_plasma_params(current_directory_path_to_output, directory_path_to_stl_dir)

	print("Saving model files to "+ current_directory_path_to_output + "...")
	save_files_to_output(cut_model_dict, current_directory_path_to_output)

	print("Saving port files to " + current_directory_path_to_output + "...")
	save_files_to_output(port_dict, current_directory_path_to_output)

	print("\n\n******* MODEL " + model_number + " COMPLETE *********\n\n")