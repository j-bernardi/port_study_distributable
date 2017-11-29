import sys, os, math, copy
#sys.path.append('/usr/lib/freecad/lib/')
sys.path.append('/usr/lib/freecad-daily/lib/')
import FreeCAD
import Part, Mesh, Draft
from FreeCAD import Base
from Draft import *
from math import pi, cos, sin, tan, sqrt

""" USAGE: 
Run this script from the directory into which you wish the generated ports to be placed.
See below for the run parameters, in terms of radial and lateral angles of each port.
The script finds parameters of the torus from the 'file finding parameters' section
Makes ports with the dimensions specified below.

The port object contains a list of component objects that describe a single port.
The component object contains a 'box' state that is the freecad solid (amongst other data).
The bounding box is found with port.outer_casing_component.box.

See the bottom of the script for outputs
"""

##################### DEFAULT RUN PARAMETERS ############################

port_length = 3000.0 #mm
radial_angles = [    0.0,     0.3,   2*pi/3, 5*pi/6, 4*pi/3, 6.11, 6.11] #rad
lateral_angles = [pi/4 + 0.1, 0.25,  0.47,   2*pi/5, 0.3, -0.2, 0.3] #rad
long_adjs = [0.0] * len(radial_angles) #rad
lat_adjs = [0.0] * len(radial_angles) #rad

#########################################################################
###################### FILE FINDING PARAMETERS ##########################

stl_file_directory = 'stl_files'
models_folder_name = 'models'
model_no = 'default'
port_parent_directory = 'my_ports'
port_directory = 'generated_ports_model_0' #default - change in make_ports_from_file
toroid_parameter_prefix = 'BSS' #component from which radiii are found.

script_dir = os.path.dirname(os.path.realpath(__file__))
directory_path_to_stl_parent = os.sep.join(script_dir.split(os.sep)[:-1]) + os.sep + stl_file_directory
directory_path_to_model_stl_files = directory_path_to_stl_parent + os.sep + models_folder_name + os.sep + model_no
directory_path_to_port_parent = directory_path_to_stl_parent + os.sep + port_parent_directory
output_directory = directory_path_to_stl_parent + os.sep + port_parent_directory + os.sep + port_directory

#########################################################################
###################### DEFAULT PORT PARAMETERS ##########################

#Port dimensions
outer_wall_thickness = 60.0 #SS316 (mm) 
coolant_channel_thickness = 80.0 #Water (mm)
inner_wall_thickness = 60.0 #SS316 (mm)
void_thickness = 30.0
liner_width_thickness = 370.0 #Steel:Water
liner_height_thickness = 530.0 #60:40
nb_height = 1060.0
nb_width = 550.0

def add_tuple(t1, t2) :
	#adds a number to every element in the first argument if t2 is tuple length 1
	#OR adds corresponding elements
	result = []
	if len(t2) == 1 :
		for i in range(len(t1)) :
			result.append( t1[i] + t2[0] )
	elif len(t1) == len(t2) :
		for i in range (len(t1)) :
			result.append( t1[i] + t2[i] )
	else :
		return "tuple length did not match in addition."
	return tuple(result)

nb_border = (nb_width, nb_height)
liner_border = add_tuple(nb_border, (liner_width_thickness, liner_height_thickness))
void_border = add_tuple(liner_border, tuple([void_thickness]) )
inner_wall_border = add_tuple(void_border, tuple([inner_wall_thickness]))
coolant_channel_border = add_tuple(inner_wall_border, tuple([coolant_channel_thickness]))
outer_wall_border = add_tuple(coolant_channel_border, tuple([outer_wall_thickness]))

total_width = outer_wall_border[0]
total_height = outer_wall_border[1]

#dictionary of components with their corresponding (widths, heights) tuples
outer_wall_name = "ow" # used to bound the port and 
components = {"nb" : nb_border, "l" : liner_border, "v" : void_border,\
				"iw" : inner_wall_border, "cc" : coolant_channel_border,\
				"ow" : outer_wall_border}

#########################################################################

class Component(object) :

	global tor_radius, d_radius, plasma_radius

	def __init__(self, port_name, component_name, width, height, length, radial_angle, lateral_angle, long_adj, lat_adj) :

		#identity
		self.port_name = port_name #the corresponding port to which the component belongs
		self.component_name = component_name #the name of this component
		#parmeters
		self.length = length
		self.width = width
		self.height = height
		self.radial_angle = radial_angle
		self.lateral_angle = lateral_angle
		self.long_adj = long_adj
		self.lat_adj = lat_adj

		#the solid object
		self.box = self.make_box(length, width, height, radial_angle, lateral_angle, long_adj, lat_adj)

	def make_box(self, length, width, height, radial_angle, lateral_angle, long_adj, lat_adj) :

		box_centre_point = self.find_centre_point(radial_angle, lateral_angle)
		
		#print "\ncentre point", box_centre_point
		
		plasma_centre = self.find_plasma_centre(radial_angle)
		
		#print "plasma centre", plasma_centre
		#print self.magnitude(plasma_centre)
		
		norm_vector_from_plasma = box_centre_point.sub(plasma_centre)
		norm_vector_from_plasma.multiply(1.0/self.magnitude(norm_vector_from_plasma))
		
		subtraction = norm_vector_from_plasma
		subtraction.multiply(length/2.0)

		front_face_centre = box_centre_point.sub(subtraction)

		#print "normal from plasma", norm_vector_from_plasma
		
		o_x, o_y, o_z = norm_vector_from_plasma.x, norm_vector_from_plasma.y, norm_vector_from_plasma.z

		#treat divide-by-0 cases
		if o_x == 0 :
			y = 0.0
			if o_y > 0 :
				x = - 1.0
			else :
				x = 1.0
		elif o_y == 0 :
			x = 0.0
			if o_x > 0 :
				y = 1.0
			else :
				y = -1.0
		#normal case
		else :
			grad = o_y/o_x
			recip = -1.0/grad
			theta = math.atan(recip)
			x = cos(theta)
			y = sin(theta)
		
		perp_horizontal = Base.Vector(x, y, 0.0)
		perp_horizontal.multiply(1.0/self.magnitude(perp_horizontal))

		#print "horizontal vector perp to norm", perp_horizontal
		#print "dot of horizontal vector with normal", norm_vector_from_plasma.dot(perp_horizontal)

		width_vector = perp_horizontal
		width_vector.multiply(width/2.0)

		#print "width_vector", width_vector, "magnitude", self.magnitude(width_vector)

		height_vector = norm_vector_from_plasma.cross(perp_horizontal)
		height_vector.multiply(1.0/self.magnitude(height_vector))
		height_vector.multiply(height/2.0)

		#print "height vector", height_vector, "magnitude", self.magnitude(height_vector)
		
		if height_vector.z < 0 :
			height_vector.multiply(-1.0)

		#print "dot of height vector with width vector", height_vector.dot(perp_horizontal)
		#print "dot of height vector with normal vector", norm_vector_from_plasma.dot(height_vector)

		#Follow the perp vector forward and backward to find the widths
		#Then go up and down the line (find the angle)

		#Fix so edge 1 in clockwise dir from centre, edge 2 anticlockwise
		#currently if y > 0 width vector is ac, y<0 width vector is cw?
		#changed from box centre to fron face centre
		
		if o_y <= 0 :
			edge1_centre = front_face_centre.add(width_vector)
			edge2_centre = front_face_centre.sub(width_vector)
		else :
			edge1_centre = front_face_centre.sub(width_vector)
			edge2_centre = front_face_centre.add(width_vector)
		
		point1 = FreeCAD.Vector(edge1_centre.sub(height_vector))
		point2 = FreeCAD.Vector(edge1_centre.add(height_vector))
		point3 = FreeCAD.Vector(edge2_centre.add(height_vector))
		point4 = FreeCAD.Vector(edge2_centre.sub(height_vector))

		point_list = [point1, point2, point3, point4, point1]
		
		#print point_list
		
		wire_frame = Part.makePolygon(point_list)
		wire_face = Part.Face(wire_frame)

		# now adjust for long and lat adjust
		
		extrusion_vector = FreeCAD.Vector(norm_vector_from_plasma.x, norm_vector_from_plasma.y, norm_vector_from_plasma.z)
		extrusion_vector.multiply(1.0/self.magnitude(extrusion_vector))
		extrusion_vector.multiply(length)
		
		new_obj = wire_face.extrude(extrusion_vector)

		#print "magnitude extrusion", self.magnitude(extrusion_vector)

		return new_obj
		#return Part.makeBox(1000,1000,1000, Base.Vector(box_centre_point))
		
	def find_centre_point(self, radial_angle, lateral_angle) :
		
		x_ratio = cos(radial_angle)
		y_ratio = sin(radial_angle)

		x = plasma_radius*cos(radial_angle) + x_ratio * d_radius * cos(lateral_angle)
		y = plasma_radius*sin(radial_angle) + y_ratio * d_radius * cos(lateral_angle)
		z = d_radius * sin(lateral_angle)

		centre_point = (x, y, z)

		return Base.Vector(centre_point)

	def find_plasma_centre(self, radial_angle) :

		return Base.Vector(plasma_radius*cos(radial_angle), plasma_radius*sin(radial_angle), 0.0)

	def magnitude(self, vector) :

		return sqrt(vector.dot(vector))

class Port(object) :
	#contains a port name and a list of Component objects that make up that port
	
	global components, outer_wall_name # the component name with its border width
	#define- this is set in make_components
	outer_casing_component = None

	def __init__(self, port_name, component_list) :
		
		self.port_name = port_name
		self.component_list = component_list
		"""
		for component in component_list :
			if component.component_name == outer_wall_name :
				self.outer_casing_component = copy.deepcopy(component)
		"""

		self.component_names_ordered_desc_border_width = self.find_descending_component_names()

		new_components = []
		component_list_as_dict = {}
		for component in component_list :
			component_list_as_dict[component.component_name] = component

		#for component in self.component_names_ordered_desc_border_width :
			#print component

		for i in range(len(self.component_names_ordered_desc_border_width) - 1 ) :
			new_box = component_list_as_dict[self.component_names_ordered_desc_border_width[i]].box.cut(component_list_as_dict[self.component_names_ordered_desc_border_width[i+1]].box)
			new_component_name = component_list_as_dict[self.component_names_ordered_desc_border_width[i]].component_name
			
			#print "changing the box of", new_component_name
			component_list_as_dict[new_component_name].box = new_box


		#self.component_list = new_components

	def find_descending_component_names(self):

		component_list_manip = components.copy()
		component_names_ordered_desc_border_width = []

		while component_list_manip != {} :
			border_width = 0.0
			current_max = 0.0
			next_component = ""
			#iterate through names remaining
			for component in component_list_manip :
				#find the max border width
				border_width = components[component][0]
				if border_width > current_max :
					current_max = border_width
					next_component = component
			
			#add in descending order then delete from the remaining components
			component_names_ordered_desc_border_width.append(next_component)
			del component_list_manip[next_component]

		return component_names_ordered_desc_border_width

	def export_stl(self) :
		print("Exporting " + self.port_name + " as stl files...")
		for item in self.component_list :
			item.box.exportStl("NB" + self.port_name + "_" + item.component_name + ".stl")

	def export_step(self) :
		print("Exporting " + self.port_name + " as step files...")
		for item in self.box_list :
			item.box.exportStep("NB" + self.port_name + "_" + item.component_name + ".stp")

	def export_outer_casing_stl(self) :
		print("Exporting " + "OUTER_NB"+ self.port_name + ".stl" + " outer casing as an stl file...")
		self.outer_casing_component.box.exportStl("OUTER_NB"+ self.port_name + ".stl")

	def export_outer_casing_step(self) :
		print("Exporting " + "OUTER_NB"+ self.port_name + ".stp" + " outer casing as a step file...")
		self.outer_casing_component.box.exportStep("OUTER_NB"+ self.port_name + ".stp")

def make_components(port_number, port_length, component_dict, radial_angle, lateral_angle, long_adj, lat_adj) :
	"""
	Takes a list of components that define a single port structure, create a Component for each component with correct/passed positioning
	Returns a Port object that contains a list of boxes that make up a single port
	"""
	global outer_wall_name

	print ("*** Making Port%s ***") % port_number
	print ("making components: "),
	component_list = []
	for component in component_dict :
		print(component),
		new_component = Component("Port" + str(port_number), component,\
		 component_dict[component][0], component_dict[component][1], \
		 port_length, radial_angle, lateral_angle, long_adj, lat_adj)

		component_list.append( new_component )
		#save the outer casing component for later use in cutting with the model
		if component == outer_wall_name :
			outer_wall_box = copy.deepcopy(new_component)
	print("")

	new_port = Port("Port" + str(port_number), component_list)
	#add the outer casing
	new_port.outer_casing_component = outer_wall_box

	return new_port

def make_n_ports(port_length, component_dict, radial_angles, lateral_angles, long_adjs, lat_adjs) :
	"""
	call make_boxes then make a port for every angle in the lists (after checking all same length)
	return a list of port objects
	"""
	failed = False
	port_list = []

	if len(radial_angles) != len(lateral_angles) :
		failed = True
		message = "lateral angles"
	elif len(radial_angles) != len(long_adjs) :
		failed = True
		message = "longitudinal adjustments"
	elif len(radial_angles) != len(lat_adjs) :
		failed = True
		message = "latitudinal adjustments"
	if failed :
		print("Stopping: length of [radial angles] did not match length of [%s]") % message
	else :
		for i in range(len(radial_angles)) :
			port_list.append(make_components(i+1, port_length, component_dict, radial_angles[i], lateral_angles[i], long_adjs[i], lat_adjs[i]))

	return port_list

def find_plasma_radius_from_stl(directory) :
	
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

	return float(plasma_params["R"]) * 1000

def find_tor_radius_from_files(directory, prefix) :
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

def check_port_overlap(port_list, directory) :
	pass

def find_plasma_parameters(directory_path_to_stl_files) :
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

def make_new_directory(directory):
	if not os.path.exists(directory) :
		os.makedirs(directory)

tor_radius, plasma_radius, d_radius = find_plasma_parameters(directory_path_to_model_stl_files)

port_list = make_n_ports(port_length, components, radial_angles, lateral_angles, long_adjs, lat_adjs)

for i in range(len(port_list)) :
		
	"""
	DIAGNOSTICS
	print "looking at", port_list[i].port_name
	print "this port is encased by", port_list[i].outer_casing_component.component_name
	for component in port_list[i].component_list :
		print(component.component_name),
	print ""
	"""
	cwd = os.getcwd()
	os.chdir(output_directory)
	#exports the port components
	port_list[i].export_stl()
	#exports a casing that bounds the port (for cutting later)
	port_list[i].export_outer_casing_stl()
	os.chdir(cwd)