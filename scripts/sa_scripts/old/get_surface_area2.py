import os, sys, math
sys.path.append('/usr/lib/freecad-daily/lib/')
import FreeCAD, Part, Mesh
from FreeCAD import Base

#Takes arguments specifying directories (none defaults to all)
#Reads in the stl files, finds the front faces, then finds their surface area for each model
#Note the script finds front faces by specifying a normal to every face and seeing 
#which brings the endpoint of the projection of that normal by the 'd_radius' (see finding function)
#to within d_radius/2 of the plasma center (again see definition later) (also specify that it must be closer than the original com)

model_name = 'default'
blanket_prefixes = ['obr', 'obc', 'obl', 'ibl', 'ibr', 'ibc']
directory_form = 'model_'
model_dir_form = "default_cut_"
toroid_parameter_prefix = 'BSS' #see make_ports_from_file.py for more info

script_dir = os.path.dirname(os.path.realpath(__file__))
script_dir_chop_up = script_dir.split(os.sep)

path_to_my_models = '/media/sf_Ubuntu_Shared/my_models'
path_to_simulation_data = os.sep.join(script_dir_chop_up[:-2]) + os.sep + 'simulation_data'

directory_path_to_stl_files = os.sep.join(script_dir.split(os.sep)[:-2]) + os.sep  + 'models' + os.sep +  model_name

path_to_tbr_data = path_to_simulation_data + os.sep + 'raw_data.txt'
path_to_output = path_to_simulation_data + os.sep + 'SA_data.txt'

def magnitude(v) :
	sqrs = v.x**2 + v.y**2 + v.z**2
	return math.sqrt(sqrs)

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

def find_plasma_parameters(directory_path_to_stl_files) :
	
	"""Finds the toroidal radius, distance to the centre of the plasma and difference between the two (ie radius of the 'D') """

	print "\nChecking STL directory " +directory_path_to_stl_files + " for previous run-data on this model (previous_runs.txt)..."
	try :
		previous = open(directory_path_to_stl_files + os.sep + 'previous_runs.txt', 'r')
		print "Content found, reading-in:"
		previous_content = previous.readlines()
		tor_radius = float(previous_content[0].split(" ")[1].strip())
		plasma_radius = float(previous_content[1].split(" ")[1].strip())
		d_radius = float(previous_content[2].split(" ")[1].strip())
		print "tor_radius:", tor_radius, "\nplasma_radius:", plasma_radius, "\nd_radius:", d_radius, "\n"
	
	except :
		print "No previous runs found, finding from stl files..."
		previous = open(directory_path_to_stl_files + os.sep + 'previous_runs.txt', 'w')
		tor_radius = find_tor_radius_from_files(directory_path_to_stl_files, toroid_parameter_prefix)
		plasma_radius = find_plasma_radius_from_stl(directory_path_to_stl_files)
		d_radius = tor_radius - plasma_radius
	
		previous.write("tor_radius " + str(tor_radius) + "\nplasma_radius " + str(plasma_radius) + "\nd_radius " + str(d_radius))
		print "file 'previous_runs.txt' created in", directory_path_to_stl_files
		print "tor_radius:", tor_radius, "\nplasma_radius:", plasma_radius, "\nd_radius:", d_radius, "\n"

	previous.close()
	return tor_radius, plasma_radius, d_radius

def find_tor_radius_from_files(directory, prefix) :
	
	"""Finds the radius, i.e. distance from the origin to the closest point on any of the files with the given prefix, in the given directory."""
	
	print "reading files with prefix", prefix, "in directory", directory, "to find radius..." 
	
	current_max = 0.0
	origin = Base.Vector(0.0, 0.0, 0.0)
	counter = 0

	#go through every stl file with given prefix and find distance from origin
	for stl_file in os.listdir(directory) :
		if stl_file.endswith(".stl") and stl_file.lower().startswith(prefix.lower()) :		
			print "reading", stl_file		
			#return a shape:
			try :
				obj = Mesh.Mesh(os.path.join(directory, stl_file))
				shape = Part.Shape()
				shape.makeShapeFromMesh(obj.Topology, 0.05)
				#solid = Part.makeSolid(shape)
				try:
					for vertex in shape.Vertexes:
						dist = vertex.Point.x
						if dist > current_max :
							current_max = dist
				except: 
					print "failed to find vertex in shape. vertexes for", stl_file
				counter += 1
			except :
				print "failed to read file", os.path.join(directory, stl_file) + ". Continuing..."

	print counter, "files read. Tor radius read:", current_max
	return float(current_max)

def find_plasma_radius_from_stl(directory) :
	"""Reads in the 'Plasma_params' text file in the given (NOVA-II - Simon McIntosh, Samuel Ha and Samuel Merriman Model) directory and returns the parameters for source info"""
	current_key = ""
	current_value = ""
	speech_count = 0
	value_count = 0

	with open(os.path.join(directory, "Plasma_params.txt"), 'r') as f:
		content = f.read()
	#read in plasma params as dictionary
	plasma_params = {}
	for c in content:
		if c == '{' :
			pass
		elif c == '"' and speech_count % 2 == 0 :
			speech_count += 1
		elif speech_count % 2 == 1 and c != '"':
			current_key += c
		elif c == '"' :
				speech_count +=1
		elif speech_count % 2 == 0 and c==':' :
				value_count +=1
		elif value_count % 2 == 1 and c == ',' or c == '}':
				plasma_params[current_key.strip()] = current_value.strip()
				current_key = ""
				current_value = ""
				value_count += 1
		elif value_count % 2 == 1 :
				current_value += c
	#convert to mm
	return float(plasma_params["R"]) * 1000

def load_blankets(path_to_my_models, blanket_prefixes, directory) :
	#Returns a pair of model, blanket_part_list, model specified by directory
	
	model = directory.split(os.sep)[-2]

	#Load up the blanket parts if they exist
	print "Loading blanket model pairs from", model, "(STL FILES ONLY)"
	try :
		all_parts = os.listdir(directory)
		print model + " directory found."
	except :
		print model + ' failed- model directory not found'
		return "FAILED", []
	
	blanket_parts = []
	
	for part in all_parts :
		if part.lower().startswith(tuple(blanket_prefixes)) and part.lower().endswith(".stl"):
			blanket_parts.append(part)

	print "ADDING", str(len(blanket_parts)), "BLANKET PARTS TO DICT"
	#model_blanket_dict[model] = blanket_parts
		
	return model, blanket_parts

def str_to_part(blanket_string_list, file_location) :
	#converts a list of strings for blanket parts to a list of (string, solid) parts.
	print "Converting strings, read to stl files..."
	stl_parts = []
	counter = 1
	tota = len(blanket_string_list)

	print "CONVERTING MODEL", directory.split(os.sep)[-2], "(1/1)"
	
	for string in blanket_string_list :
		print "READING", string, str(counter) + "/" + str(tota)
		counter += 1
		obj = Mesh.Mesh(os.path.join(file_location, string))
		shape = Part.Shape()
		shape.makeShapeFromMesh(obj.Topology, 0.05)
		solid = Part.makeSolid(shape)
			
		stl_parts.append( (string, solid) )
		
	return stl_parts

def find_front_faces(blanket_tuple_list, model, plasma_radius) :
	#takes a list of blankets with their names and returns a dictionary of their front faces
	print "\nFINDING FRONT FACEs FOR", model
	faces_list = []
	cnt = 1
	ln = len(blanket_tuple_list)

	for blanket_tuple in blanket_tuple_list :
		
		num_faces_dict = {}

		blanket_name = blanket_tuple[0]
		blanket = blanket_tuple[1]

		print "\n******* FINDING FRONT FACES FOR BLANKET", blanket_name, " (" + str(cnt) + "/" + str(ln) + ") *********"

		cnt += 1

		faces = blanket.Faces

		# a list of info for the faces of this blanket module
		info_list = []

		"""
		print "exporting", blanket, " to ~/Downloads" + os.sep + model + "_test.stl"
		blanket.exportStl("/home/james/Downloads" + os.sep + model + "_test.stl")
		
		num_faces_dict[blanket_name] = len(faces) 
		append_line(blanket_name, len(faces), script_dir + os.sep + 'FACES.txt')
		"""
		print str(len(faces)) + " detected." 

		#find the two closest faces for this blanket
		#print "Edges for faces:"
		for face in faces:

			edges = face.Edges
		
			#print len(edges), ", ",
			
			"""
			print ""
			print "EXAMINING FACE", face
			print "EDGES: ", edges
			"""
			e0, e1, e2 = edges[0], edges[1], edges[2]
			
			#Find points defining edges
			e0p0 = Base.Vector(e0.Vertexes[0].X, e0.Vertexes[0].Y, e0.Vertexes[0].Z)
			e0p1 = Base.Vector(e0.Vertexes[1].X, e0.Vertexes[1].Y, e0.Vertexes[1].Z)
			e1p0 = Base.Vector(e1.Vertexes[0].X, e1.Vertexes[0].Y, e1.Vertexes[0].Z)
			e1p1 = Base.Vector(e1.Vertexes[1].X, e1.Vertexes[1].Y, e1.Vertexes[1].Z)
			
			#vectors parallel to 2 edges
			v1 = e0p1.sub(e0p0)
			v2 = e1p1.sub(e1p0)
			
			"""
			print "e0p0 ", e0p0
			print "e0p1 ", e0p1
			print "e1p0 ", e1p0
			print "e1p1 ", e1p1

			print "V1: ", v1
			print "V2: ", v2
			"""

			#find normal to the face
			normal = v1.cross(v2)
			normal = normal.multiply(1.0/magnitude(normal))

			"""
			print "SHAPE COM: ", blanket.CenterOfMass
			com_mag = magnitude(blanket.CenterOfMass)
			print "COM MAG", com_mag
			print "FACE COM:", face.CenterOfMass
			print "NORMAL TO FACE: ", normal
			print ""
			"""

			#if the distance from shape_COM to face_COM decreases when normal is added, then normal is pointing towards centre of the shape so flip
			if magnitude(blanket.CenterOfMass.sub(face.CenterOfMass)) > magnitude(blanket.CenterOfMass.sub(face.CenterOfMass.add(normal))) :
				normal = normal.multiply(-1.0)

			#save the info for this face in form (face_solid, face_centre_point, outward_normal)
			info = (face, face.CenterOfMass, normal)
			info_list.append(info)
			
		#Now distinguish which normal projections (eg from COM of its face by dradius) get closer to plasma centre
		
		#find direction of blanket from O, make unit, multiply by plasma radius.
		flat_blanket_position = Base.Vector(blanket.CenterOfMass.x, blanket.CenterOfMass.y, 0.0)
		unit_direction_vector = flat_blanket_position.multiply(1.0/magnitude(flat_blanket_position))
		plasma_center = unit_direction_vector.multiply(plasma_radius)
		
		#RECALCULATE THE D RADIUS AS DIFFERENCE BETWEEN BLANKET AND PLASMA CENTER

		front_faces = []
		#create adaptive d_radius
		d_radius = magnitude(blanket.CenterOfMass.sub(plasma_center))
		
		#Iterate through every face in the blanket
		#if moving from the face COM along the normal by the d_radius brings it closer to the plasma center, the face is front-facing.
		#also specify must be less than d_radius/2.0
		c1_fail, c1_success, c2_success = 0, 0, 0
		
		for face_tuple in info_list :
			solid, com, normal = face_tuple[0], face_tuple[1], face_tuple[2]
			if magnitude(normal) > 1.01 or magnitude(normal) < 0.99:
				print "mag normal = " + str(magnitude(normal)) + " - not 1.0 "
				sys.exit()
			#eg if the vector between com of face and plasma com gets smaller when you go along the normal, it was front-facing
			#First check if shape is properly front-facing
			if magnitude((com.sub(plasma_center)).add(normal.multiply(d_radius))) < 0.5 * d_radius :
				#reset normal, check got closer
				normal = normal.multiply(1.0/magnitude(normal))
				if magnitude( (com.sub(plasma_center)).add(normal.multiply(d_radius))) < magnitude( com.sub(plasma_center)) :
					c1_success +=1 
					front_faces.append(solid)
				else :
					print "Was within 0.5 but did NOT get closer."

			#second check if not within 0.5- assume only those that get closer are front facing- rest go wrong way
			else :
				print "CHECK 2 ENTERED:"
				c1_fail +=1
				normal = normal.multiply(1.0/magnitude(normal))
				
				if magnitude(normal) > 1.01 or magnitude(normal) < 0.99:
					print "mag normal = " + str(magnitude(normal)) + " - not 1.0 "	
					sys.exit()
				
				normal_added = magnitude( (com.sub(plasma_center)) .add(normal.multiply(d_radius)))
				without = magnitude(com.sub(plasma_center))
				
				#diagnostics
				print "Face area: ", solid.Area
				#print "mag adding normal: ", normal_added
				#print "mag without add: ", without
				#print "d_radius", d_radius
				
				print "plasma center", plasma_center
				print "face com", com
				print "endpoint mag from pc", normal_added

				#vector between plasma center and face center of mass - should be opposite to face normal
				norm_com = com.sub(plasma_center)
				norm_com = norm_com.multiply(1.0/magnitude(norm_com))

				normal = normal.multiply(1.0/magnitude(normal))

				#print "mag norm", magnitude(normal)
				#print "mag norm_com", magnitude(norm_com)
				print "normal (to face) dotted with vector between face and plasma center", normal.dot(norm_com)

				#WAS and magnitude(com.sub(plasma_center)) < magnitude(blanket.CenterOfMass.sub(plasma_center))
				#eg must get closer and get MORE close than CHECK THE CPM/BLANKET COM ONE
				#inner normal are parallel to the plasma center vector, outer anti parallel
				
				#CHANGE so if within 10% of the max -ive?
				if normal_added < without and normal_added < d_radius and normal.dot(norm_com) < - 0.5:
					print "ADDED"
					front_faces.append(solid)
					c2_success += 1
				else :
					print "NOT ADDED"

				print ""
		
		print "Check one failed", c1_fail, "times."
		print "Check one succeeded", c1_success, "times."
		print "Check two succeeded", c2_success, "times."
		print "Check two failed", str(len(info_list) - c1_success - c1_success - c2_success), "times."
		
		if len(info_list) == 12 and len(front_faces) != 2 :
			print "12 FACES FOUND, ", str(len(front_faces)), " FRONT FACES FOUNT. PROBABLY SHOULD HAVE 2 FRONT FACES."
			print "EXITING- DOUBLE CHECK CODE"
			sys.exit()

		faces_list += (front_faces)
		print "Appended " + str(len(front_faces)) + " (front) faces for this blanket module."

	print "all blanket modules for the model completed. (" + str(len(faces_list)) + "faces found)" 
	return faces_list

def get_surface_area_of_faces(faces) :
	print "Finding total area"
	total_area = 0.0
	for face in faces :
		total_area += face.Area
	return total_area

#NOT USED
def print_dict(output_location, sa_dict) :

	with open(output_location, 'a+') as sd :
		for model in sa_dict :
			sd.write("\n" + model + " " + str(sa_dict[model]))

def append_line(model, surface_area, output_location) :

	if not os.path.exists(output_location) :
		with open(output_location, 'w') as sd :
			sd.write("model    surface_area_of_model")
	
	with open(output_location, 'a+') as sd :
		sd.write("\n" + model + " " + str(surface_area))


tor_radius, plasma_radius, d_radius_fixed = find_plasma_parameters(directory_path_to_stl_files)

directories = get_directories_from_args(path_to_my_models, directory_form)

sa_dict = {}
success_list, failed_list = [], []
cnt = 1
tot = len(directories)

for model in directories :

	print ""
	print "**** COMMENCING SURFACE AREA FINDER FOR MODEL", model, str(cnt) + "/" + str(tot), "****"
	cnt +=1 
	print ""

	#specify the directory in which to find the parts 
	directory = path_to_my_models + os.sep + model + os.sep + model_dir_form + model
	#load up just the blanket parts into a list
	model_name_returned, blanket_string_list = load_blankets(path_to_my_models, blanket_prefixes, directory)

	#Check whether the directory existed
	if model_name_returned == "FAILED" :
		print "Directory was not found for " + directory + " continuing to next model."
		failed_list.append(model)
		continue

	#gives format [(string, solid), ... ]) list of tuples
	blanket_tuple_list = str_to_part(blanket_string_list, directory)

	success_list.append(model)
	print "Finding front faces..."
	front_faces = find_front_faces(blanket_tuple_list, model, plasma_radius)

	print "Finding Surface Area"
	surface_area = get_surface_area_of_faces(front_faces)
	sa_dict[model] = surface_area

	append_line(model, surface_area, path_to_output)

	print "Appended sa_dict[" + model + "] = " + str(surface_area) + " to file successfully."

print "Dictionary produced and printed to ", path_to_output, ":\n", sa_dict
print "\nAll models in directories completed."


#Go through every face in 'blankets- produce a line normal to every face
#Find which FOUR go closest to the plasma center (look at make_ports)
#(EG Each face is made from 2 triangles, and front and back will be indistinguishable)
#select the two of the four

#subtract from model 0 surface area (in another script?)