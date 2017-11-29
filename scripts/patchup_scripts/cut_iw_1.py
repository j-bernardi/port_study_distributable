#PROBLEM: WHEN NBPORT1 THIS EXISTS IN NBPORT11,12,13... etc. Finally cuts against the ports matching port 16!
"""
def fragment(key_list, port_dict, fused_object, port_number, outer_casing_prefix, q) :
	for port in key_list :
		if ("NBPort" + port_number) in port and not port.startswith(outer_casing_prefix) : 
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
"""

#FIX:


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
print cpu_global_count

	### Update these when specific bss identified ####
##########################################################
only_file_prefixes = ["bss_1", "bss_2", "bss_3", "bss_7", "bss_8", "bss_86", "bss_87", "bss_88"] #empty string defaults to all
##########################################################


#parameters for skipping when loading into the model dictionary for cuts etc 
ignore_file_prefixes = ['Plasma']#['NONE'] # 'NONE' defaults to no ignores

#prefixes to be skipped when cutting with the model. 
#This is necessary as we currently cut with the large, original outer box 
skip_prefixes = ['Plasma']


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
#q = Queue()

def magnitude(vect) :
	sqrs = vect.x ** 2 + vect.y ** 2 + vect.z ** 2
	return sqrs ** 0.5

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
			"""
			geofile_digits = 0
			for c in geofile :
				if c.isdigit() :
					geofile_digits += 1
			if geofile_digits == 1 :
			#if digits == 1 or digits == 2:
			"""
			if geofile.split(".")[0].lower() in only_file_prefixes :
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

def fragment(key_list, port_dict, fused_object, port_number, outer_casing_prefix, q) :
	for port in key_list :
		if ("NBPort" + port_number) in port and not port.startswith(outer_casing_prefix) : 
			
			digits = 0
			for c in port :
				if c.isdigit() :
					digits += 1
			
			#if True :
			if port_number == 1 and digits > 1 :
				#eg iw_NBPort12
				continue
			else :
			
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

def split_ports_remove_inner(port_dict, model_dict, first_wall_prefix, bounding_casing_prefix, outer_casing_prefix) :
	"""Perform boolean fragments with all the first wall structures in common in the model dict"""
	i = 0

	#first find all the first wall objects the port cuts
	for port in port_dict :
		print "considering", port
		port_number = ""
		for c in port :
			if c.isdigit():
				port_number += c
		
		digits = 0
		for c in port :
			if c.isdigit() :
				digits += 1

		if digits > 1 : 
		#if digits > 2 : 
			continue 
		else :

			print "\nSplitting outer port", port, "(" +str(i+1) + "/1)"
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
	for piece in key_list :
		if piece.lower().startswith(first_wall_prefix.lower()):
			if model_dict[piece].common(port_outer_component).Volume != 0 :
				q.put(model_dict[piece])

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


def save_files_to_output(solid_dict, directory) :

	cpu_count = cpu_global_count
	key_list_split = split_dict_to_key_parts(solid_dict)

	with ThreadPoolExecutor(max_workers = cpu_count) as executor :
		for lst in key_list_split :
			print "saving", lst
			executor.submit(parasave, lst, directory, solid_dict)

def parasave(key_list, directory, solid_dict) :
	for solid in key_list : 
		print "exporting", solid
		solid_dict[solid].exportStl(directory + os.sep + solid + ".stl")


directories = get_directories_from_args(path_to_my_models, directory_form)

print("Examining directories", directories)


#Just re-fixing models 4.2, 4.3 and 16.3
for model in directories :
	if True: #model.startswith("model_4.2") or model.startswith("model_4.3") or model.startswith("model_16.3") :
		model_number = ""
		for c in model:
			if c.isdigit() :
				model_number += c
	
	
		directory_path_to_current_ports = path_to_my_models + os.sep + model  + os.sep + port_std_name + model
		current_directory_path_to_output = path_to_my_models + os.sep + model + os.sep + model_name + '_' + output_suffix + model
		
		#Set output and input paths
		print("Working on model number " + str(model_number) + "...")
		
		print("Making iw port dict")
		iw_port_dict = get_port_dict("ow_NBPort1", True, directory_path_to_current_ports) 
		print("Making model dict (and copying)")
		bss_model_dict = get_model_dict(directory_path_to_stl_dir, ignore_file_prefixes = ignore_file_prefixes, only_file_prefixes = only_file_prefixes) #.copy()
		print iw_port_dict
		print bss_model_dict
	
		split_ports_remove_inner(iw_port_dict, bss_model_dict, first_wall_prefix, bounding_casing_prefix, bounding_box_prefix)
	
		print("Saving port files to " + current_directory_path_to_output + "...")
		
		#digits change iw back
		iw1_port_dict = {}
		iw1_port_dict['ow_NBPort1'] = iw_port_dict['ow_NBPort1']
		print iw1_port_dict
		save_files_to_output(iw1_port_dict, current_directory_path_to_output)