"""
Created by:
	@author: James Bernardi
	University of Cambridge
	bernardi.james.h@gmail.com
	
	2017-09-01
"""

"""
USAGE: 
	Cuts the model specified by model_name with its ports, specified by the arguments

		No arguments - specifies all directories in my_ports (except model number 0- test)
		Arguments can be passed to list specific directories (eg python parallel_cut.py 4.1 4.2.2 16.1.r1 - for run on model_4.1, model_4.2.2, model_16.1.r1 only )
		Outputs the cut model into my_cuts specifying the model name and number from which it was evolved


NOTE: first_wall_prefix is used to cut the ends of the ports off- must be updated to the correct structure when known. 
	We require a solid structure (with no gaps) to adhere to the method of cutting used by this script. The structure must completely encase the reactor to ensure safe operation

NOTE: Should possibly do the cutting into the NOVA model with already fragmented ports ie to avoid overlap with things like plasma, inside, when port doesn't exist
	This can only be done when the first wall is known, though

NOTE: Submission is parallel- but I'm not sure that FreeCAD's functions run in parallel- work should be done to confirm this before submitting to Cumulus.

NOTE**: See function 'fragment' for untested part to remove false positives- originally made mistake of 'Port1' being 'in' Port10, Port11, etc, meaning Port1 failed to cut.
	script in patchup_scripts fixed the problem initially, BUT:

	Have implemented a fix un the untested part marked out by hashtags, but recommend checking this works before following.. 
"""

import sys, os

#sys.path.append('/usr/lib/freecad/lib/')
sys.path.append('/usr/lib/freecad-daily/lib/')
#sys.path.append(os.path.realpath(__file__))

import FreeCAD, Part, Mesh
import multiprocessing as mp
from BOPTools import SplitAPI
from concurrent.futures import ThreadPoolExecutor
from shutil import copyfile
from Queue import Queue
##############################################

cpu_global_count = mp.cpu_count()
print "CPU COUNT:", cpu_global_count

#parameters for skipping when loading into the model dictionary for cuts etc
ignore_file_prefixes = ['Plasma']#['NONE'] # 'NONE' defaults to no ignores- recommend leaving as 'Plasma'- no need to load this in at present

#the list of file prefixes to load in 
only_file_prefixes = [""]#["bss"] #empty string defaults to all
#only_file_prefixes = ["BSS_1.stl", "BSS_6.stl", "BSS_8.stl"] 

#prefixes to be skipped when cutting with the model. 
#This is necessary as we currently cut with the large, original outer box
skip_prefixes = ['Plasma']


#prefix that defines the first wall in order to perform boolean fragments with the ports- this must be a solid, encasing structure.
first_wall_prefix = 'BSS' #Note-this MUST completely encase/cut the ports (ie overhang around a non-solid structure will produce an error)
bounding_box_prefix = "OUTER" #prefix on stl files defining just an outer box where the port goes
bounding_casing_prefix = 'ow' #prefix on the stl files form "(bounding_casing_prefix)_NBPortx.stl" - eg the outer structure on the collection of port stl files. See 'auto_make_model_description.py'


models_folder = 'models'
my_models = 'my_models'
directory_form = 'model_'

model_name = 'default' # change if required- as the directory appears in models/
 
#port_folder = 'my_ports' - not required any more I believe
port_std_name = 'generated_ports_' 

output_suffix = 'cut_'

##############################################
script_dir = os.path.dirname(os.path.realpath(__file__))
script_dir_chop_up = script_dir.split(os.sep)

path_to_my_models = os.sep.join(script_dir_chop_up[:-1])+os.sep + models_folder + os.sep + my_models

directory_path_to_stl_dir = os.sep.join(script_dir_chop_up[:-1])+os.sep + models_folder + os.sep + model_name

##############################################
count = 0
#q = Queue()

def magnitude(vect) :
	sqrs = vect.x ** 2 + vect.y ** 2 + vect.z ** 2
	return sqrs ** 0.5

def lower_tuple(tup) :
	#turn whole tuple of strings to lower case
	result = []
	for i in range( len(tup) ) :
		result.append(tup[i].lower()) 
	return tuple(result)

def make_new_directory(directory):
	#make directory if one doesn't exist
	if not os.path.exists(directory) :
		print "Making new directory", directory
		os.makedirs(directory)
	else :
		print "Directory", directory, "found."

def split_dict_to_key_parts(dictionary) :
	"""Splits a dictionary's keys in to equal(ish) parts dep on cpu count
	Returns a list of lists of keys """
	cpu_count = cpu_global_count
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
	"""Splits a list in to equal(ish) parts dep on cpu count
	Returns a list of lists"""
	cpu_count = cpu_global_count
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
	q = Queue(maxsize = len(os.listdir(port_dir)))
	cpu_count = cpu_global_count
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
			executor.submit(make_solid, lst, port_dir, total, q)

	#form the dictionary from the queue
	port_dict = {}
	while not q.empty() :
		item = q.get()
		port_dict[item[0]] = item[1] 

	return port_dict

def get_model_dict(model_dir, ignore_file_prefixes = ["NONE"], only_file_prefixes = [""]) :
	"""returns a dict of the model objects from the given directory"""
	""" Form : {port_name : solid_stl, ... } """

	print "File prefixes being read (if blank, all):", only_file_prefixes
	print "Ignored file prefixes:", ignore_file_prefixes

	cpu_count = cpu_global_count
	file_list = []
	q = Queue(maxsize = len(os.listdir(model_dir)))

	#find the files for loading
	for geofile in os.listdir(model_dir) :
		if geofile.endswith(".stl") and (not geofile.lower().startswith(lower_tuple(tuple(ignore_file_prefixes))) and geofile.lower().startswith(lower_tuple(tuple(only_file_prefixes))) ) :
			file_list.append(geofile)
	
	total_files_found = len(file_list)
	file_list_split = split_list_to_parts(file_list)

	for i in range(len(file_list_split)) :
		file_list_split[i].sort()

	#print file_list_split

	print("Fetching " + str(total_files_found) + " model components from " + model_dir + " out of " + str(total_files_found) + "...")
	global count
	count = 0
	with ThreadPoolExecutor(max_workers = cpu_count) as executor : 
		for lst in file_list_split :
			executor.submit(make_solid, lst, model_dir, total_files_found, q)

	model_dict = {}
	#form the dictionary from the queue
	while not q.empty() :
		item = q.get()
		model_dict[item[0]] = item[1] 

	return model_dict

def make_solid(geofile_list, directory, total, q):
	"""Takes a file to read in, the directory in which it is found, and the dictionary into which to put it"""
	global count
	for geofile in geofile_list :
		print "*** Creating solid from file: " + geofile + " (" + str(count + 1) + "/" + str(total) + ") ***"
		count += 1
		obj = Mesh.Mesh(os.path.join(directory, geofile))
		shape = Part.Shape()
		shape.makeShapeFromMesh(obj.Topology, 0.05)
		solid = Part.makeSolid(shape)

		q.put( (("").join(geofile.split(".")[:-1]) , solid) )

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

			print "Performing fragmentation on port", port_number,"..."
			#print "common list:", common_list
			#print "fused object to cut:", fused_object
			#fragment each port with its fused object and update the port object
			key_list_split = split_dict_to_key_parts(port_dict)
			#print "key_list_split", key_list_split
			global count
			count = 0
			cpu_count = cpu_global_count
			q = Queue(maxsize = len(port_dict))

			with ThreadPoolExecutor(max_workers = cpu_count) as executor :
				for key_list in key_list_split :
					#print "submitting list", key_list
					executor.submit(fragment, key_list, port_dict, fused_object, port_number, outer_casing_prefix, q)

			#replace the port in port_dict with the new port
			print "Updating dictionary..."
			while not q.empty() :
				item = q.get()
				port_dict[item[0]] = item[1]

			print "completed\n"

def find_fw_components_in_common(first_wall_prefix, port_outer_component, model_dict):
	"""Finds all the first wall components (with f_w_prefix) in common with the port_outer_component. Returns a list."""

	print "Finding", first_wall_prefix, "objects in common with port..."
	common_list = []
	cpu_count = cpu_global_count
	q = Queue()

	key_list_split = split_dict_to_key_parts(model_dict) 
	
	global count
	count = 0 

	#parallelise
	with ThreadPoolExecutor(max_workers = cpu_count) as executor :
		for key_list in key_list_split :
			executor.submit(iterate_common, key_list, model_dict, first_wall_prefix, port_outer_component, q)

	#Retreive the list from the queue
	common_list = []
	while not q.empty() :
		common_list.append(q.get())

	return common_list

def iterate_common(key_list, model_dict, first_wall_prefix, port_outer_component, q) :
	"""Iterative way to find the common objects, return to a queue"""
	for piece in key_list :
		if piece.lower().startswith(first_wall_prefix.lower()):
			if model_dict[piece].common(port_outer_component).Volume != 0 :
				q.put(model_dict[piece])

def fuse_object_list(common_list) :
	"""Takes a list of objects and fuses them to return a new fused-object"""
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

def fragment(key_list, port_dict, fused_object, port_number, outer_casing_prefix, q) :
	"""Fragments a port into parts: outside fused_object, in common with the fused_object and inside the fused_object. 
	Discards the inside part (ie the part that would intersect with plasma)
	Puts the new port structures in a queue for removal by its caller"""

	for port in key_list :
		#PROBLEM: NBPort1 is in NBPort10,11,12 ... 
		if ("NBPort" + port_number) in port and not port.startswith(outer_casing_prefix) : 


			####### UNTESTED PART BEGINS ###########
			#REMOVE FALSE POSITIVES ie NBPort1 is IN NBPort12, NBPort16 etc..
			port_digits = 0
			for c in port :
				if c.isdigit() :
					port_digits += 1
			port_number_digits = len(port_number)
						
			if port_number_digits != port_digits :
				#eg iw_NBPort12 and iw_NBPort1
				#eg iw_NBPort10 and iw_NBPort106
				continue
			#else: we have found a correct match

			######### UNTESTED PART ENDS ###########

			#print "found", port, "for cutting"
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
			
			q.put( (port, new_port) )

def cut_holes_in_model(outer_port_dict, model_dict, skip_prefixes = ['NONE']) :
	"""Takes a dictionary of port outer-casings"""
	"""Perform a cut on every model part with the outer port dictionaries"""
	print("Cutting the port components out of the model")
	print 'number of cuts to make', len(model_dict)
	global counter
	counter = 0
	cpu_count = cpu_global_count

	key_list_split = split_dict_to_key_parts(model_dict)

	for key_list in key_list_split :
		for key in key_list :
			if key.startswith(tuple(skip_prefixes)) :
				key_list.remove(key)

	for lst in key_list_split :
		lst.sort()

	q = Queue(maxsize = len(model_dict))

	with ThreadPoolExecutor(max_workers = cpu_count) as executor :
		for lst in key_list_split :
			executor.submit(cut_model, lst, model_dict, outer_port_dict, q)

	#retrieve parts from the queue
	cut_parts = {}
	while not q.empty() :
		item = q.get()
		cut_parts[item[0]] = item[1]

	return cut_parts

def cut_model(component_list, model_dict, port_dict, q) :
	"""The function that iterates through model components and cuts them according to the port dictionary passed. Called by cut_holes"""
	global counter 
	for component in component_list :
		#USED TO COPY THE DICT COMPONENT BELOW- TEST
		cut_component = model_dict[component]

		print("Cutting part " + component+ " " + str(counter+1) + "/" + str(len(model_dict)) )
		counter +=1
		for port in port_dict :
			cut_component = cut_component.cut(port_dict[port])
		q.put( (component, cut_component) ) 

def save_files_to_output(solid_dict, directory) :
	"""Saves the files in the dictionary to the directory"""
	cpu_count = cpu_global_count
	key_list_split = split_dict_to_key_parts(solid_dict)

	with ThreadPoolExecutor(max_workers = cpu_count) as executor :
		for lst in key_list_split :
			executor.submit(parasave, lst, directory, solid_dict)

def parasave(key_list, directory, solid_dict) :
	"""Iterative- called by save_files"""
	for solid in key_list : 
		solid_dict[solid].exportStl(directory + os.sep + solid + ".stl")

def get_directories_from_args(path_to_my_models, directory_form) :
	"""Convert the arguments to a directory number"""
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
	"""Copy across plasma parameters and stl without having to load in (ie no operations are required to be made on these)"""
	print "copying Plasma_params.txt and Plasma.stl from", path_to_original_model, "to", path_to_cut_model
	copyfile(path_to_original_model + os.sep + 'Plasma_params.txt', path_to_cut_model + os.sep + 'Plasma_params.txt')
	copyfile(path_to_original_model + os.sep + 'Plasma.stl', path_to_cut_model + os.sep + 'Plasma.stl')
	

directories = get_directories_from_args(path_to_my_models, directory_form)

print("Examining directories", directories)

"""Perform cut on every model"""
for model in directories :

	#This doesn't account for full-stops (eg 4.1.1 -> 411)- will need to be changed for visual output but doesn't make a difference for operation
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
	
	print("Making outer port dict")
	outer_port_dict = get_port_dict(bounding_box_prefix, True, directory_path_to_current_ports) #.copy() - was when using manager objects
	print("Making port dict")
	port_dict = get_port_dict(bounding_box_prefix, False, directory_path_to_current_ports) #.copy()
	print("Making model dict")
	model_dict = get_model_dict(directory_path_to_stl_dir, ignore_file_prefixes = ignore_file_prefixes, only_file_prefixes = only_file_prefixes) #.copy()

	"""Fragment the ports and remove overhang to inner tokamak"""
	split_ports_remove_inner(port_dict, model_dict, first_wall_prefix, bounding_casing_prefix, bounding_box_prefix)
	
	#Cut the model to get the new parts out
	cut_model_dict = cut_holes_in_model(outer_port_dict, model_dict, skip_prefixes) #.copy()

	#add the plasma parameters to the new directory
	add_plasma_params(current_directory_path_to_output, directory_path_to_stl_dir)

	#Save the files
	print("Saving model files to "+ current_directory_path_to_output + "...")
	save_files_to_output(cut_model_dict, current_directory_path_to_output)

	print("Saving port files to " + current_directory_path_to_output + "...")
	save_files_to_output(port_dict, current_directory_path_to_output)

	print("\n\n******* MODEL " + model_number + " COMPLETE *********\n\n")
