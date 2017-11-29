import sys, os, copy
#sys.path.append('/usr/lib/freecad/lib/')
sys.path.append('/usr/lib/freecad-daily/lib/')
import FreeCAD, Part, Mesh
##############################################

limit = 0 # 0 defaults to no limit (ie all)
ignore_file_prefixes = 'NONE' # NONE defaults to no ignores
only_file_prefixes = "BSS" #empty defaults to all

stl_file_folder_name = 'stl_files'
model_name = 'default' # change if required
port_setup_name = 'my_ports' + os.sep + 'generated_ports' # default - set by argument if exists
bounding_casing_prefix = "OUTER"
output_prefix = 'cut'

#read in the port geometry file from the arguments, if provided
if len(sys.argv) == 2 :
	port_setup_name = sys.argv[1]
elif len(sys.argv) != 1 :
	"Please run with only the port geometry folder name as argument or none."

##############################################

script_dir = os.path.dirname(os.path.realpath(__file__))
script_dir_chop_up = script_dir.split(os.sep)

directory_path_to_stl_dir = os.sep.join(script_dir_chop_up[:-1])+os.sep+stl_file_folder_name+os.sep+model_name
directory_path_to_ports_dir = os.sep.join(script_dir_chop_up[:-1])+os.sep+stl_file_folder_name+os.sep+port_setup_name
directory_path_to_output = directory_path_to_stl_dir + '_' + output_prefix


##############################################

def find_casings_from_directory(directory, bounding_casing_prefix) :
	
	outer_casing_list = []
	for f in os.listdir(directory) :
		if f.lower().startswith(bounding_casing_prefix.lower()) :
			outer_casing_list.append(f)
	return outer_casing_list

def make_new_directory(directory):
	if not os.path.exists(directory) :
		os.makedirs(directory)

def get_port_dict(outer_casing_prefix, prefix_wanted_flag, port_dir) :
	"""returns a list of the port objects with (or without) the given prefix from the given directory"""
	""" Form : {port_name : solid_stl, ... } """
	port_list = {}

	if prefix_wanted_flag :
		print("Fetching " + outer_casing_prefix +" ports from " + port_dir + "...")
		for geofile in os.listdir(port_dir) :
			if geofile.endswith(".stl") and geofile.lower().startswith(outer_casing_prefix.lower()) :
				port_list[("").join(geofile.split(".")[:-1])] = make_solid(geofile, port_dir)
	else :
		print ("Fetching ports from " + port_dir + "...") 
		for geofile in os.listdir(port_dir) :
			if geofile.endswith(".stl") and not geofile.lower().startswith(outer_casing_prefix.lower()) :
				port_list[("").join(geofile.split(".")[:-1])] = make_solid(geofile, port_dir)

	return port_list

def make_solid(geofile, port_dir):
	print "reading file:", geofile
	obj = Mesh.Mesh(os.path.join(port_dir, geofile))
	shape = Part.Shape()
	shape.makeShapeFromMesh(obj.Topology, 0.05)
	solid = Part.makeSolid(shape)
	
	return solid

def get_model_dict(model_dir, limit = 0, ignore_file_prefixes = "NONE", only_file_prefixes = "") :

	"""returns a dict of the model objects from the given directory"""
	""" Form : {port_name : solid_stl, ... } """

	print only_file_prefixes, " - file prefixes"

	stl_counter = 0
	for geofile in os.listdir(model_dir) :
		if geofile.endswith(".stl") and (not geofile.lower().startswith(ignore_file_prefixes.lower()) and geofile.lower().startswith(only_file_prefixes.lower()) ) :
			stl_counter += 1
	if limit == 0 :
		limit = stl_counter

	model_list = {}

	print("Fetching " + str(limit) + " model components from " + model_dir + " out of " + str(stl_counter) + "...")

	counter = 0

	for geofile in os.listdir(model_dir) :
		if geofile.endswith(".stl") and ( not geofile.lower().startswith(ignore_file_prefixes.lower()) and geofile.lower().startswith(only_file_prefixes.lower()) ):
			if counter < limit :
				print("Creating solid from file: " + geofile +". " + str(counter+1) + "/" + str(limit))
				counter += 1

				obj = Mesh.Mesh(os.path.join(model_dir, geofile))
				shape = Part.Shape()
				shape.makeShapeFromMesh(obj.Topology, 0.05)
				solid = Part.makeSolid(shape)
				model_list[("").join(geofile.split(".")[:-1])] = solid
			else :
				break
	return model_list

def cut_holes_in_model(port_dict, model_dict) :

	print("Cutting the port components out of the model")
	print 'number of cuts to make', len(model_dict)
	counter = 0
	cut_components = {}
	
	for component in model_dict:
		cut_component = copy.deepcopy(model_dict[component])
		print("Cutting part " + str(counter+1) + "/" + str(len(model_dict)) )
		counter += 1
		for port in port_dict :
			cut_component = cut_component.cut(port_dict[port])
		cut_components[component] = cut_component

	return cut_components

#DONT THINK THIS IS NEEDED IF LIMITING MODEL DICT ALREADY
def cut_holes_in_model_limits(port_dict, model_dict, limit = 0) :

	if limit == 0 :
		limit = len(model_dict)

	print("Cutting the port components out of the model")
	print('number of cuts to make', limit, ". Total model components:", len(model_dict))
	counter = 0
	cut_components = {}
	
	while counter < limit :
		for component in model_dict:
			cut_component = model_dict[component]
			print("Cutting part " + str(counter) + "/" + str(limit))
			counter += 1
			for port in port_dict :
				cut_component = cut_component.cut(port_dict[port])
			cut_components[component] = cut_component

	return cut_components

def save_files_to_output(solid_dict, directory) :

	for solid in solid_dict :
		solid_dict[solid].exportStl(directory + os.sep + solid + ".stl")


#make the new output directory if one is required
make_new_directory(directory_path_to_output)

#list of files describing outer casings
outer_casing_dict = find_casings_from_directory(directory_path_to_ports_dir, bounding_casing_prefix)

outer_port_dict = get_port_dict(bounding_casing_prefix, True, directory_path_to_ports_dir)

model_dict = get_model_dict(directory_path_to_stl_dir, limit = limit, ignore_file_prefixes = ignore_file_prefixes, only_file_prefixes = only_file_prefixes)

cut_model_dict = cut_holes_in_model(outer_port_dict, model_dict)

port_dict = get_port_dict(bounding_casing_prefix, False, directory_path_to_ports_dir)

print("Saving model files to "+ directory_path_to_output + "...")
save_files_to_output(cut_model_dict, directory_path_to_output)

print("Saving port files to " + directory_path_to_output + "...")
save_files_to_output(port_dict, directory_path_to_output)

