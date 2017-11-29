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

for directory in os.listdir(local_path_to_my_models) :

	os.chdir(local_path_to_my_models)
	print "Zipping", directory, ":"
	try :
		os.system('zip -rq compressed_directory.zip ' + directory)
	except:
		print "error"
		zip_list.append(directory)

	print "SCPing zip folder:"
	try:
		os.system('scp compressed_directory.zip jhbernar@login1.cumulus.hpc.l:' + remote_path_to_my_models)
	except:
		print "error"
		scp_list.append(directory)

	print "Unzipping:"
	try :
		os.system('ssh jhbernar@login1.cumulus.hpc.l "unzip -q ' + remote_path_to_my_models + os.sep + 'compressed_directory.zip -d ' + remote_path_to_my_models + '"' )
	except:
		print "error"
		unzip_list.append(directory)

	print "Deleting used folders:"
	try :
		os.system('ssh jhbernar@login1.cumulus.hpc.l "rm ' + remote_path_to_my_models + os.sep + '*.zip"' )
	except :
		print "error"
		remote_del_list.append(directory)
	
	try :
		os.system('rm *.zip')
	except :
		print "error"
		local_del_list.append(directory)
"""
print "ERRORS:"
print "zipping errors:", zip_list
print "scp errors:", scp_list
print "unzip errors:", unzip_list
print "local deletion errors", local_del_list
print "remote deletion errors", remote_del_list 
"""
