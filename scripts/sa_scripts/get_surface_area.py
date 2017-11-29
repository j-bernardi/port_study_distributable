import os, sys, math
sys.path.append('/usr/lib/freecad-daily/lib/')
import FreeCAD, Part, Mesh
from FreeCAD import Base

#Takes arguments specifying directories (none defaults to all)
#Reads in the stl files, finds the front faces, then finds their surface area for each model

#Note the script finds front faces by:
#1) specifying a normal to every face.
#2)finding the vector from the plasma center at that radial angle to a face's COM
#3) keeping only those faces with DPs that are close to -1 

#Note this is done by finding which face COM has the max (-ive) dot product with the normal
#Then finding all those faces that are within (1-cut_off)*100% of the max cut_off
#0.9 appears to work for model_0 
#0.85 gives same result for model_0
#0.8 was too large (some inner blankets detected too many faces)
cut_off = 0.85
#eg only do those models missing from the file specified below as output.. If false, will just append to file
only_do_missing = True 

model_name = 'default'
blanket_prefixes = ['obr', 'obc', 'obl', 'ibl', 'ibr', 'ibc']
#see make_ports_from_file.py for more info - defines tor_radius and plasma_center:
toroid_parameter_prefix = 'BSS' 


#DIRECTORY FINDING STUFF - CHANGE IF MODEL FOLDER NAME CHANGES
directory_form = 'model_'
model_dir_form = "default_cut_"

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
	#converts a list of strings for blanket parts to a list of (string, solid) parts found in 3rd arg directory.
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

		print "\nFINDING FRONT FACES FOR BLANKET", blanket_name, " (" + str(cnt) + "/" + str(ln) + ")"

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
			
			e0, e1, e2 = edges[0], edges[1], edges[2]
			
			#Find points defining edges
			e0p0 = Base.Vector(e0.Vertexes[0].X, e0.Vertexes[0].Y, e0.Vertexes[0].Z)
			e0p1 = Base.Vector(e0.Vertexes[1].X, e0.Vertexes[1].Y, e0.Vertexes[1].Z)
			e1p0 = Base.Vector(e1.Vertexes[0].X, e1.Vertexes[0].Y, e1.Vertexes[0].Z)
			e1p1 = Base.Vector(e1.Vertexes[1].X, e1.Vertexes[1].Y, e1.Vertexes[1].Z)
			
			#vectors parallel to 2 edges
			v1 = e0p1.sub(e0p0)
			v2 = e1p1.sub(e1p0)

			#find normal to the face
			normal = v1.cross(v2)
			normal = normal.multiply(1.0/magnitude(normal))

			#if the distance from shape_COM to face_COM decreases when normal is added, then normal is pointing towards centre of the shape so flip
			if magnitude(blanket.CenterOfMass.sub(face.CenterOfMass)) > magnitude(blanket.CenterOfMass.sub(face.CenterOfMass.add(normal))) :
				normal = normal.multiply(-1.0)

			#save the info for this face in form (face_solid, face_centre_point, outward_normal)
			info = (face, face.CenterOfMass, normal)
			info_list.append(info)
			
		#Now have info about all faces in this blanket.
		#Now distinguish which normal projections (eg from COM of its face by dradius) get closer to plasma centre
		#find direction of blanket from O, make unit, multiply by plasma radius.
		flat_blanket_position = Base.Vector(blanket.CenterOfMass.x, blanket.CenterOfMass.y, 0.0)
		unit_direction_vector = flat_blanket_position.multiply(1.0/magnitude(flat_blanket_position))
		plasma_center = unit_direction_vector.multiply(plasma_radius)
		
		#RECALCULATE THE D RADIUS AS DIFFERENCE BETWEEN BLANKET AND PLASMA CENTER

		front_faces, front_faces_temp = [], []
		back_faces_temp, back_faces = [], []
		
		#create adaptive d_radius
		d_radius = magnitude(blanket.CenterOfMass.sub(plasma_center))
		
		#Iterate through every face in the blanket, find front faces (see explanation at top)
		
		for face_tuple in info_list :
			
			solid, com, normal = face_tuple[0], face_tuple[1], face_tuple[2]
			
			#find normal to the face surface (and check mag is 1)
			normal = normal.multiply(1.0/magnitude(normal))
			if magnitude(normal) > 1.01 or magnitude(normal) < 0.99:
				print "mag normal = " + str(magnitude(normal)) + " - not 1.0 "	
				sys.exit()
			
			#Find the distance to the plasma center after adding the normal and without
			normal_added = magnitude( (com.sub(plasma_center)) .add(normal.multiply(d_radius)))
			without = magnitude(com.sub(plasma_center))

			#vector between plasma center and face center of mass 
			norm_com = com.sub(plasma_center)
			norm_com = norm_com.multiply(1.0/magnitude(norm_com))
			normal = normal.multiply(1.0/magnitude(normal))

			#find dot product between face com from plasma center and normal to the surface
			dot_prod = normal.dot(norm_com)
			#print "normal (to face) dotted with vector between face and plasma center", dot_prod
			
			#First find the dots < -0.5 -candidates for front faces 
			if normal_added < without and normal_added < d_radius and normal.dot(norm_com) < - 0.5:
				#print "ADDED"
				front_faces_temp.append((solid, dot_prod))
			#also stor back faces for diagnostics/verification
			elif normal_added > without and normal_added > d_radius and normal.dot(norm_com) > 0.5:
				back_faces_temp.append((solid, dot_prod))
			else:
				pass
				#print "NOT ADDED"

			#print "Front_faces_temp: ", front_faces_temp
			#print ""

		#Have now got a list of all potential front faces
		#iterate through shortlist to find max dot prod
		maxi = front_faces_temp[0]
		for front_face in front_faces_temp :
			if abs(front_face[1]) > abs(maxi[1]) :
				maxi = front_face
		#(and back faces for verification if desired)
		maxa = back_faces_temp[0]
		for back_face in back_faces_temp :
			if abs(back_face[1]) > abs(maxa[1]) :
				maxa = back_face
		
		#print "Front_faces_temp: ", front_faces_temp

		#now iterate to find those that are within cut_off of max
		for front_face in front_faces_temp :
			if abs(front_face[1]) > cut_off * abs(maxi[1]) :
				front_faces.append(front_face[0])
		#and for back faces
		for back_face in back_faces_temp :
			if abs(back_face[1]) > cut_off * abs(maxa[1]) :
				back_faces.append(back_face[0])

		#print "FRONT FACES:", front_faces

		#This is a useful verificaiton *FOR NOVA*- most blankets have 12 faces originally, and if detected correctly only 2 will be added to fron face
		if len(info_list) == 12 and len(front_faces) != 2 :
			print "12 FACES FOUND, ", str(len(front_faces)), " FRONT FACES FOUNT. PROBABLY SHOULD HAVE 2 FRONT FACES."
			print "EXITING- DOUBLE CHECK CODE"
			sys.exit()

		#append the faces of this blanket module to the overall list for this model
		faces_list += (front_faces)
		#print some info
		print "Appended " + str(len(front_faces)) + "/" + str(len(faces)) + " (front/all) faces for this blanket module."
		print str(len(back_faces)) + " back faces found."
		rem = len(faces) - len(front_faces) - len(back_faces)
		print "(leaves: " + str(rem) + " identified as side faces)"
		
		"""
		#THESE CHECKS ONLY WORK FOR MODEL 0- BUT VERYIFIES THAT CODE IS FINDING FRONT FACES
		#The potential number of faces on a side face (counted in FreeCAD)
		rem1 = rem % 34
		rem2 = rem %36
		rem3 = rem %38
		p = False
		rem_list = [rem1, rem2, rem3]
		
		for r in rem_list :
			if rem == 8 :
				p = True
				break
			if r == 2 or r == 4 or r == 6 : #number of side faces left after complex one
				p = True
				break
		
		if not p :
			print "************* CHECK - REMAINDER SHOULD BE 2, 4 or 6? ****************"
			print "total rem:", rem
			for k in range(len(rem_list)) :
				print "rem" + str(k+1) + ": " + str(rem_list[k])
			print "These are the box geometries observed.."
			sys.exit()
		"""

	print "all blanket modules for the model completed. (" + str(len(faces_list)) + "faces found)" 
	return faces_list

def get_surface_area_of_faces(faces) :
	#Take a list of faces and return their surface area
	print "Finding total area"
	total_area = 0.0
	for face in faces :
		total_area += face.Area
	return total_area

def append_line(model, surface_area, output_location) :
	#take the model as the first column, s_a as the second column, append to file specified by 3rd arg
	if not os.path.exists(output_location) :
		with open(output_location, 'w') as sd :
			sd.write("model    surface_area_of_model")
	
	with open(output_location, 'a+') as sd :
		sd.write("\n" + model + " " + str(surface_area))


tor_radius, plasma_radius, d_radius_fixed = find_plasma_parameters(directory_path_to_stl_files)

directories_temp = get_directories_from_args(path_to_my_models, directory_form)

skip_models, directories = [], []

if only_do_missing :
	
	with open(path_to_output) as op :
		lines = op.readlines()
		
	#0th line is titles
	for l in range (1, len(lines)) :
		model = lines[l].split(" ")
		skip_models.append(model[0])

	for directory in directories_temp :
		if directory not in skip_models :
			directories.append(directory)

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