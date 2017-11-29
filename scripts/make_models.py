"""
Created by:
	@author: James Bernardi
	University of Cambridge
	bernardi.james.h@gmail.com
	
	2017-09-01
"""

"""
USAGE: 
	Start with base-models (specifying radial angles- see script commencing under function definitions) 
	Then use the functions given (or make one's own) to maniuplate lateral angles in a controlled way.
	Calling print_models_to_file on a given list will append the models generated to variable relative_parameter_location

	Running script will write models (specified by functions below) to text file specified in relative_parameter_location

POSSIBLE ADDITIONS:
	Implement lateral adjustments and longitudinal adjustments in make_ports_from_file.py so that ports can enter the tokamak at an angle
		eg need to read in the last 2 lists in the model description and maniupulate the cad model to implement these.
"""

from __future__ import division
from random import randint
import os, math
from math import pi

script_dir = os.path.dirname(os.path.realpath(__file__))
script_dir_chop_up = script_dir.split(os.sep)

relative_parameter_location = "parameter_files/auto_parameters.txt"
path_to_parameters = os.sep.join(script_dir_chop_up[:-1])+os.sep+ relative_parameter_location

#An object that stores the parameters and has a method of 
class Model(object) :
	def __init__(self, model_number, port_length, radial_angles, lateral_angles, long_adjs, lat_adjs) :
		self.model_number = model_number
		self.port_length = port_length
		self.radial_angles = radial_angles
		self.lateral_angles = lateral_angles
		self.long_adjs = long_adjs
		self.lat_adjs = lat_adjs

	def append_to_file(self, path_to_parameters) :
		lines = []
		lines.append(str(self.model_number) )
		lines.append("port_length " + str(self.port_length) )
		lines.append("radial_angles " + (" ").join(str(a) for a in self.radial_angles) )
		lines.append("lateral_angles " + (" ").join(str(a) for a in self.lateral_angles) ) 
		lines.append("long_adjs " + (" ").join(str(a) for a in self.long_adjs) )
		lines.append("lat_adjs " + (" ").join(str(a) for a in self.lat_adjs) )
		
		with open(path_to_parameters, 'a') as f :
			for x in lines :
				f.write(x + '\n')

def uniform_lateral_split(model_obj, min_lat, max_lat, num_models) :
	"""Takes a model with given radial angles and separates them uniformly"""
	"""Returns a list of models regardless of initial lateral angles"""
	"""Appends a suffix to the model number to show its derivative model"""

	increment = (max_lat - min_lat) / num_models
	m = model_obj
	model_list = [] 

	for i in range(num_models + 1) :
		angle = min_lat + i * increment		

		model_list.append( Model( str(m.model_number)+"."+str(i+1), m.port_length, m.radial_angles, \
											[angle] * len(m.lateral_angles), m.long_adjs, m.lat_adjs ) )

	return model_list

def alternate_lateral_angle(model_obj, lateral_angle) :
	"""Takes a model number and a lateral angle, and returns a model with alternating +/- lateral angle"""
	"""Best passing a 1.x model and using that model's original lateral angle, for labelling"""
	m = model_obj

	angles = [lateral_angle] * len(model_obj.lateral_angles) 
	for i in range(len(angles)) :
		if i % 2 == 1 :
			angles[i] = angles[i]*(-1)
	return Model(m.model_number + ".a", m.port_length, m.radial_angles, angles, m.long_adjs, m.lat_adjs )

def increment_lateral_angle(model_obj, min_lat, max_lat) :
	pass

def generate_random_lateral_angle_model(model_obj, min_lat, max_lat, random_model_number) :
	"""Generates random lateral angles for a model with given radial angles."""
	"""Best to pass a vanilla model_1 etc to this, for labelling"""
	m = model_obj
	angles = []

	min_int_deg = 100*min_lat*180
	max_int_deg = 100*max_lat*180

	for i in range(len(m.lateral_angles)) :
		angle = randint( min_int_deg, max_int_deg )
		angle = angle/(100.0 * pi)
		angle = (math.pi/180.0) * angle
		angles.append(angle)
	print "Random angles for model", str(m.model_number) + ".r" + str(random_model_number),":", angles
	new_model = Model(str(m.model_number) + ".r" + str(random_model_number), m.port_length, m.radial_angles, angles, m.long_adjs, m.lat_adjs )
	return new_model

def print_models_to_file(model_list, path_to_models) :
	"""Takes a list of models and appends them to the model file specified above"""
	for model in model_list :
		print "Appending model", model.model_number, "to file", path_to_models, "..."
		model.append_to_file(path_to_models)


#min radial separation used for bunched ports
sep = 0.5
#number of increments to make
incs = 3 
rands_per_model = 2
opposite_models = 4
min_lat, max_lat = -1.0, 1.0 #currently must be an integer on multiplcation by 100 for random number gen in generate_random_lateral_angle_model- could adjust this as required

#uniform
model1 = Model(4.1, 5000.0, [0, pi/2, pi, 3*pi/2], [0] * 4, [0] * 4, [0] * 4)
#bunched
model2 = Model(4.2, 5000.0, [-pi/8, pi/8, 7*pi/8, 9*pi/8], [0] * 4, [0] * 4, [0] * 4)
#non-symmetric
model3 = Model(4.3, 5000.0, [-pi/8, 0, pi/8, pi], [0] * 4, [0] * 4, [0] * 4)

a = pi/16
#uniform
l = range(16)
model4 = Model(16.1, 5000.0, [x * pi/8 for x in l], [0] * 16, [0] * 16, [0] * 16)

model5 = Model(16.2, 5000.0, [a, 2*a, pi/2-2*a, pi/2-a, pi/2+a, pi/2+2*a, pi-2*a, pi-a,pi+a, pi+2*a, 3*pi/2 -2*a, 3*pi/2-a, 3*pi/2+a, 3*pi/2+2*a, 2*pi-2*a, 2*pi-a ], [0]*16, [0]*16, [0]*16)
k = range(13)
model6 = Model(16.3, 5000.0, [-a, 0.0, a ] + [pi - (13*pi/16)/2 + i*a for i in k ] , [0]*16, [0]*16, [0]*16)

#model1 - uniform base-case
#model1 = Model(1, 5000.0, [0, pi/4, pi/2, 3*pi/4, pi, 5*pi/4, 3*pi/2, 7*pi/4], [0] * 8, [0] * 8, [0] * 8)
#model2 - all bunched
#model2 = Model(2, 5000.0, [sep, pi/2-sep, pi/2+sep, pi-sep, pi+sep, 3*pi/2-sep, 3*pi/2+sep, 2*pi-sep], [0] * 8, [0] * 8, [0] * 8)
#model3 - bunched and big gap 
#model3 = Model(3, 5000.0, [sep, pi/4, 3*pi/4, pi-sep, pi+sep, 5*pi/4, 7*pi/4, 2*pi-sep], [0] * 8, [0] * 8, [0] * 8)
#model4 - bunched and uniform
#model4 = Model(4, 5000.0, [sep, pi/3, 2*pi/3, pi-sep, pi+sep, 4*pi/3, 5*pi/3, 2*pi-sep], [0] * 8, [0] * 8, [0] * 8)

#A list of base models
#base_models = [model1, model2, model3, model4]
base_models = [model1, model2, model3, model4, model5, model6]

#For each model, try uniformly changing lateral positions
model_uniform_list = [] # becomes a list of lists
for model in base_models :
	model_uniform_list.append(uniform_lateral_split(model, min_lat , max_lat, incs))

#create #opposite_models of non-symmetric alternating groups models
model3_opposite_list, model6_opposite_list = [], []
for i in range(opposite_models + 1) :
	angle_increment = (max_lat - min_lat) / opposite_models
	angle = min_lat + i * angle_increment
	model3_opposite_list.append( Model("4.3.o" + str(i+1), 5000.0, [-pi/8, 0, pi/8, pi], [angle,angle,angle, -angle] , [0] * 4, [0] * 4 ) )
	model6_opposite_list.append(Model("16.3.o" + str(i+1), 5000.0, [-a, 0.0, a ] +  [pi - (11*pi/16)/2 + i*a for i in k ], [angle, angle, angle] + [-angle]*13, [0]*16, [0]*16 ))

print "Finished making uniform lateral models"

#For each uniform model generated, try alternating each port
model_alternate_list = []
for i in range(len(model_uniform_list)) :
	model_alternate_list.append([])
	for model in model_uniform_list[i] :
		model_alternate_list[i].append(alternate_lateral_angle(model, model.lateral_angles[0]))

print "Finished making alternating lateral models"

#Generate a few random models for good measure
random_model_list = []
num = 0
for model in base_models :
	for k in range(1, rands_per_model+ 1) :
		random_model_list.append(generate_random_lateral_angle_model(model, min_lat, max_lat, k))


#Add each model to the file
print_models_to_file(base_models, path_to_parameters)

uniform_count = 0
for model_list in model_uniform_list :
	print_models_to_file(model_list, path_to_parameters)
	uniform_count += len(model_list)

alternate_count = 0
for model_list in model_alternate_list :
	print_models_to_file(model_list, path_to_parameters)
	alternate_count += len(model_list)

print_models_to_file(model3_opposite_list, path_to_parameters)

print_models_to_file(model6_opposite_list, path_to_parameters)

print_models_to_file(random_model_list, path_to_parameters)

print "Total models generated:", str( len(base_models) + uniform_count + alternate_count + len(model3_opposite_list) + len(model6_opposite_list) + len(random_model_list) )
