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
from multiprocessing import Process, Manager
##############################################

limit = 0 # 0 defaults to no limit (ie all)
ignore_file_prefixes = ['NONE'] # 'NONE' defaults to no ignores
only_file_prefixes = ["bss"] #empty string defaults to all
#only_file_prefixes = ["BSS_1.stl", "BSS_6.stl", "BSS_8.stl"] #empty string defaults to all - good for model 3

#prefix that defines the first wall in order to perform boolean fragments with the ports
first_wall_prefix = 'BSS' #Note-this MUST completely encase/cut the ports (ie overhang will produce an errr)
bounding_box_prefix = "OUTER" #prefix on stl files defining just a box where the port goes
bounding_casing_prefix = 'ow' #suffix on the stl files form "NBPortn_(bounding_casing_prefix).stl"


output_folder = 'my_cuts'
models_folder = 'models'
stl_file_folder_name = 'stl_files' 
model_name = 'default' # change if required
 
port_folder = 'my_ports'
port_std_name = 'generated_ports_model_' 

output_suffix = 'cut_model_'

##############################################
script_dir = os.path.dirname(os.path.realpath(__file__))
script_dir_chop_up = script_dir.split(os.sep)

directory_path_to_stl_dir = os.sep.join(script_dir_chop_up[:-1])+os.sep+stl_file_folder_name+ os.sep + models_folder + os.sep + model_name
directory_path_to_ports_dir = os.sep.join(script_dir_chop_up[:-1])+os.sep+stl_file_folder_name+os.sep+port_folder
directory_path_to_output = os.sep.join(script_dir_chop_up[:-1])+os.sep+stl_file_folder_name+os.sep + output_folder + os.sep + model_name + '_' + output_suffix
##############################################

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
#DONE
def get_port_dict(outer_casing_prefix, prefix_wanted_flag, port_dir) :
	"""returns a list of the port objects with (or without) the given prefix from the given directory"""
	""" Form : {port_name : solid_stl, ... } """
	manager =Manager()
	port_dict = manager.dict()

	if prefix_wanted_flag :
		print("Fetching " + outer_casing_prefix +" ports from " + port_dir + "...")
		for geofile in os.listdir(port_dir) :
			if geofile.endswith(".stl") and geofile.lower().startswith(outer_casing_prefix.lower()) :
				p = Process(target = make_solid, args = (geofile, port_dir, port_dict))
				p.start()
				p.join()
	else :
		print ("Fetching ports from " + port_dir + "...") 
		for geofile in os.listdir(port_dir) :
			if geofile.endswith(".stl") and not geofile.lower().startswith(outer_casing_prefix.lower()) :
				p = Process(target = make_solid, args = (geofile, port_dir, port_dict))
				p.start()
				p.join()

	return port_dict

def make_solid(geofile, directory, dicti):
	"""Takes a file to read in, the directory in which it is found, and the dictionary into which to put it"""
	print "*** Reading file:", geofile
	obj = Mesh.Mesh(os.path.join(directory, geofile))
	shape = Part.Shape()
	shape.makeShapeFromMesh(obj.Topology, 0.05)
	solid = Part.makeSolid(shape)
	
	dicti[("").join(geofile.split(".")[:-1])] = solid

def cut_model(component, model_dict, port_dict, cut_components, counter) :
	print("Copying " + component + " to be cut..")
	cut_component = copy.deepcopy(model_dict[component])
	print("Cutting part " + component+ " " + str(counter+1) + "/" + str(len(model_dict)) )
	for port in port_dict :
		cut_component = cut_component.cut(port_dict[port])
	cut_components[component] = cut_component
		
def get_model_dict(model_dir, limit = 0, ignore_file_prefixes = ["NONE"], only_file_prefixes = [""]) :
	"""returns a dict of the model objects from the given directory"""
	""" Form : {port_name : solid_stl, ... } """

	print "File prefixes being read (if blank, all):", only_file_prefixes
	print "Ignored file prefixes:", ignore_file_prefixes

	stl_counter = 0
	for geofile in os.listdir(model_dir) :
		if geofile.endswith(".stl") and (not geofile.lower().startswith(lower_tuple(tuple(ignore_file_prefixes))) and geofile.lower().startswith(lower_tuple(tuple(only_file_prefixes))) ) :
			stl_counter += 1
	if limit == 0 :
		limit = stl_counter

	manager =Manager()
	model_dict = manager.dict()

	print("Fetching " + str(limit) + " model components from " + model_dir + " out of " + str(stl_counter) + "...")

	counter = 0

	for geofile in os.listdir(model_dir) :
		if geofile.endswith(".stl") and ( not geofile.lower().startswith(lower_tuple(tuple(ignore_file_prefixes))) and geofile.lower().startswith(lower_tuple(tuple(only_file_prefixes))) ):
			if counter < limit :
				print("Creating solid from file: " + geofile +". " + str(counter+1) + "/" + str(limit))
				counter += 1
				p = Process(target = make_solid, args = (geofile, model_dir, model_dict))
				p.start()
				p.join()
			else :
				break
	return model_dict

def cut_holes_in_model(outer_port_dict, model_dict) :
	"""Takes a dictionary of port outer-casings"""
	"""Perform a cut on every model part with the outer port dictionaries"""
	print("Cutting the port components out of the model")
	print 'number of cuts to make', len(model_dict)
	counter = 0
	manager = Manager()
	cut_parts = manager.dict()
	
	#print "PORT DICT:", outer_port_dict
	#print "MODEL DICT:", model_dict
	
	for part in model_dict:
		print "part:", part
		p = Process(target = cut_model, args = (part, model_dict, outer_port_dict, cut_parts, counter))
		p.start()
		p.join()
		counter += 1

	return cut_parts

def fuse_object_parallel(first_wall_prefix, port_outer_component, model_dict) :
	print "Finding", first_wall_prefix, "objects in common with port..."
	common_list = []
	for piece in model_dict :
		if piece.lower().startswith(first_wall_prefix.lower()):
			if model_dict[piece].common(port_outer_component).Volume != 0 :
				common_list.append(model_dict[piece])
	print "Fusing..."
	
	if len(common_list) == 0 :
		print "*** WARNING ***"
		print "No fw structures found in common with this port!"
		return

	new_obj = common_list[0]
	if len(common_list) > 1 :
		for i in range(1, len(common_list)) :
			new_obj = new_obj.fuse(common_list[i])
	print "Success"
	return new_obj

def split_ports_remove_inner(port_dict, model_dict, first_wall_prefix, bounding_casing_prefix, bounding_box_prefix) :
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

			#lparallelise?
			common_list = find_fw_components_in_common(first_wall_prefix, port_dict[port], model_dict)
			#parallelise?
			fused_object = fuse_object_list(common_list)
			#fused_object = fuse_object_parallel(first_wall_prefix, port_outer_component, model_dict)?

			print "Performing fragmentation..."
			
			"""
			PARALLELISATION:
			manager = Manager()
			new_port_dict = manager.dict()
			"""

			for port in port_dict :
				if ("NBPort" + port_number) in port and not port.startswith(bounding_box_prefix):
					#Find boolean fragments with fused_onject and update port_dict[port] = the two outer parts only:
					print "fragmenting", port 

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
						print "********** WARNING ************"
						print "Expected 2 items remaining after removing minimum fragment"
						print "Recieved", len(remaining_list)

					new_port = Part.makeSolid(remaining_list[0].fuse(remaining_list[1]))

					port_dict[port] = new_port

			print "completed\n"

def find_fw_components_in_common(first_wall_prefix, port_outer_component, model_dict):
	print "Finding", first_wall_prefix, "objects in common with port..."
	common_list = []
	for piece in model_dict :
		if piece.lower().startswith(first_wall_prefix.lower()):
			if model_dict[piece].common(port_outer_component).Volume != 0 :
				common_list.append(model_dict[piece])
	return common_list

def fuse_object_list(common_list) :
	print "Fusing..."
	if len(common_list) == 0 :
		print "No fw structures found in common with this port!"
		return
	new_obj = common_list[0]
	if len(common_list) > 1 :
		for i in range(1, len(common_list)) :
			new_obj = new_obj.fuse(common_list[i])
	print "Success"
	return new_obj

def save_files_to_output(solid_dict, directory) :

	for solid in solid_dict :
		p = Process(target = parasave, args = (directory, solid_dict, solid))
		p.start()
		p.join()

def parasave(directory, solid_dict, solid) :
	
	solid_dict[solid].exportStl(directory + os.sep + solid + ".stl")


def get_directories_from_args() :

	if len(sys.argv) == 1 :
		"""consider all but directory 0 (hence the range(1, number))"""
		number = 0
		for item in os.listdir(directory_path_to_ports_dir):
			print "considering item", item
			if os.path.isdir(directory_path_to_ports_dir + os.sep + item) :
				number +=1 
		directories = range(1, number)
		for i in range(len(directories)):
			directories[i] = str(directories[i])
	else :
		directories = sys.argv[1:]
	return directories

directories = get_directories_from_args()

print("Examining directories", directories)

for model_number in directories :
	#Set output and input paths
	print("Working on model number " + str(model_number) + "...")
	directory_path_to_current_ports = directory_path_to_ports_dir + os.sep + port_std_name + model_number
	current_directory_path_to_output = directory_path_to_output + model_number
	#make the new output directory if one is required
	make_new_directory(current_directory_path_to_output)
	
	print("Making outer port dict (and copying)")
	outer_port_dict = get_port_dict(bounding_box_prefix, True, directory_path_to_current_ports).copy()
	print("Making port dict (and copying)")
	port_dict = get_port_dict(bounding_box_prefix, False, directory_path_to_current_ports).copy()
	print("Making model dict (and copying)")
	model_dict = get_model_dict(directory_path_to_stl_dir, limit = limit, ignore_file_prefixes = ignore_file_prefixes, only_file_prefixes = only_file_prefixes).copy()

	split_ports_remove_inner(port_dict, model_dict, first_wall_prefix, bounding_casing_prefix, bounding_box_prefix)

	cut_model_dict = cut_holes_in_model(outer_port_dict, model_dict).copy()

	print("Saving model files to "+ current_directory_path_to_output + "...")
	save_files_to_output(cut_model_dict, current_directory_path_to_output)

	print("Saving port files to " + current_directory_path_to_output + "...")
	save_files_to_output(port_dict, current_directory_path_to_output)