"""
Created by:
	@author: James Bernardi
	University of Cambridge
	bernardi.james.h@gmail.com
	
	2017-09-01
"""

import os, sys

local_script_dir = os.path.dirname(os.path.realpath(__file__))
local_script_dir_chop_up = local_script_dir.split(os.sep)
local_path_to_my_models = os.sep.join(local_script_dir_chop_up[:-1]) + os.sep + 'models' + os.sep + 'my_models'

remote_path_to_my_models = '~/models/my_models'

zip_list, scp_list, unzip_list, local_del_list, remote_del_list = [], [], [], [], []

#Read in directory arguments
if len(sys.argv) > 1 :
    all_flag = False
    starts_with_args = sys.argv[1:]
    for i in range(len(starts_with_args)) :
        starts_with_args[i] = "model_" + starts_with_args[i]
else :
    all_flag = True
    starts_with_args = "model"
    
for directory in os.listdir(local_path_to_my_models) :

	if not all_flag :
		if directory in (starts_with_args):
			print "Directory", directory, "in:", starts_with_args
			target = remote_path_to_my_models + os.sep + directory
			destination = local_path_to_my_models + os.sep + directory
		
			os.chdir(destination)
			#Just move the serpent input
			print "SCPing serpent file:"
			try:
				os.system('scp jhbernar@login1.cumulus.hpc.l:' + target + '/serp* ' + destination) #was serp*
			except:
				print "error"
				scp_list.append(directory)
		else :
			pass
	else :
		print "Directory", directory, "in:", starts_with_args
		target = remote_path_to_my_models + os.sep + directory
		destination = local_path_to_my_models + os.sep + directory
	
		os.chdir(destination)
		#Just move the serpent input
		print "SCPing serpent file:"
		try:
			os.system('scp jhbernar@login1.cumulus.hpc.l:' + target + '/serp* ' + destination) #was serp*
		except:
			print "error"
			scp_list.append(directory)

print "ERRORS:"
print "scp errors:", scp_list
