import matplotlib.pyplot as plt 
import numpy as np 
import os

script_dir = os.path.dirname(os.path.realpath(__file__))
script_dir_chop_up = script_dir.split(os.sep)

path_to_data = os.sep.join(script_dir_chop_up[:-1]) + os.sep + 'simulation_data'
data_file = 'raw_data.txt'


def read_in_file(direct, filename) :
	with open(direct + os.sep + filename) as f:
		content = f.readlines()

	for l in range(len(content)):
		content[l] = content[l].split(" ")

	#content is now a list of lists- content [i][j] is a single cell in the table
	return content


#content[i] = [model, material, enrichment, tbr_value, error, macro_tbr_value, macro_error]

