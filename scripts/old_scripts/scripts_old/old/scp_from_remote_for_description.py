import os, sys

local_script_dir = os.path.dirname(os.path.realpath(__file__))
local_script_dir_chop_up = local_script_dir.split(os.sep)
local_path_to_my_models = os.sep.join(local_script_dir_chop_up[:-1]) + os.sep + 'models' + os.sep + 'my_models'

remote_path_to_my_models = '~/models/my_models'

zip_list, scp_list, unzip_list, local_del_list, remote_del_list = [], [], [], [], []

for directory in os.listdir(local_path_to_my_models) :
	
	target = remote_path_to_my_models + os.sep + directory
	destination = local_path_to_my_models + os.sep + directory
	os.chdir(destination)

	print "Zipping", directory, ":", 
	os.system('ssh jhbernar@login1.cumulus.hpc.l "zip -jrq ' + target + os.sep + 'compressed_directory.zip ' + target + os.sep + 'default_cut_' + directory + '"')
	print "success."
	#except:
	#	print "error"
	#	zip_list.append(directory)

	print "SCPing zip folder:",
	try:
		os.system('scp jhbernar@login1.cumulus.hpc.l:'+ target + os.sep + 'compressed_directory.zip ' + destination)
		print "success."
	except:
		print "error"
		scp_list.append(directory)

	print "Unzipping:",
	try :
		os.system('unzip -jq compressed_directory.zip -d default_cut_' + directory )
		print "success."
	except:
		print "error"
		unzip_list.append(directory)

	print "Deleting used folders:",
	try :
		os.system('ssh jhbernar@login1.cumulus.hpc.l "rm ' + target + os.sep + 'compressed_directory.zip"' )
	except :
		print "error"
		remote_del_list.append(directory)
	
	try :
		os.system('rm compressed_directory.zip')
		print "success."
	except :
		print "error"
		local_del_list.append(directory)


print "ERRORS:"
print "zipping errors:", zip_list
print "scp errors:", scp_list
print "unzip errors:", unzip_list
print "local deletion errors", local_del_list
print "remote deletion errors", remote_del_list 
