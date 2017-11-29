#!/usr/bin/pvpython

import os
from paraview.simple import *

######################## PATH TO THE DATAFILES TO BE LOADED ##########################
file_dir = '/home/james/Documents/CCFE_project_work/Nova/nova/Blankets/SN/'
######################################################################################

def LoadFiles(file_dir):

	print_options()
	FilePrefix = raw_input("input a prefix ('none' for all)")
	if FilePrefix != 'none' :
		LoadMultipleFiles(file_dir, FilePrefix)
	else:
		LoadAllFiles(file_dir)



def print_options() :
	print ("options are as follows")
	unique_options = []
	for file_name in os.listdir(file_dir):
		option = ""		
		for c in file_name :
			if c.isdigit() or c == '_' or c == '.':
				break
			else :
				option += c
		if option in unique_options :
			pass
		else :
			unique_options.append(option)

	print unique_options




def LoadAllFiles(file_dir):
	
	os.chdir(file_dir)
	for file_name in os.listdir(file_dir):
		try:
			if file_name.endswith(".stl"):
				reader = OpenDataFile(file_name)
				Show(reader)
		except : 
			print 'failed to load: ' + file_name
	Render()

def LoadMultipleFiles(file_dir, FilePrefix):

	os.chdir(file_dir)
	for file_name in os.listdir(file_dir):
		try:
			if file_name.startswith(FilePrefix) and file_name.endswith(".stl"):
				reader = OpenDataFile(file_name)
				Show(reader)
		except : 
			print 'failed to load: ' + file_name
	Render()


LoadFiles(file_dir)

