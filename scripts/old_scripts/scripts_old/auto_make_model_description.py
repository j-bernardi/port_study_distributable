import os, sys, re, ast
#form: 'component_name eg bss':[Part_objects_with_this_component_name] ##
parts={}
""" USAGE:
    Run with either 0 arguments (operate on all directories in my_cuts)
    or specify directories in argument
    eg:
    python auto_make_model_description.py 1

    loads default_cut_model_1 from my_cuts
"""
#TODO: change so can add flags for enrichment arguments etc...

############################################################################
####### TO EDIT IF ANY OTHER PARTS ARE ADDED, MATERIALS CHANGED ETC ########
############################################################################
#default_blanket_material = 'Li4SiO4'
default_blanket_material = 'Pb84.2Li15.8'
default_enrichment = '0.6'

blanket_material = default_blanket_material
enrichment = default_enrichment

#set the materials dictionary for all prefixes existing in the stl_file directory
material_dict = {'bss': 'Eurofer' , 'coil': 'Homogenous_Magnet', 'div': 'Tungsten', \
                    'ibl': blanket_material, 'ibr': blanket_material\
                    , 'obc': blanket_material, 'obl': blanket_material, 'obr': blanket_material, \
                    'port': 'Eurofer', 'plasma': 'Plasma', \
                    
                    "l" : '0.6_SS-316L-IG_0.4_H2O',\
                    "iw" : 'SS-316L-IG', "cc" : 'H2O',\
                    "ow" : 'SS-316L-IG'
                }


tbr_tally_list = ['ibl', 'ibr', 'obc', 'obl', 'obr'] #list of items to set tally (and detectors) to
neutron_multiplication_tally_list = ['ibl', 'ibr', 'obc', 'obl', 'obr'] #list of items to set tally (and detectors) to
photon_heat_tally_list=['ibl', 'ibr', 'obc', 'obl', 'obr']
neutron_heat_tally_list=['ibl', 'ibr', 'obc', 'obl', 'obr']



#headers for the output file
headers = ['component_name', 'path_to_file', 'material', 'geometry_type', \
            'mc_code', 'tally', 'segment', 'source']

###########################################################################
########################### Script input/outputs ##########################
###########################################################################

path_to_my_models_suffix = 'models' + os.sep + 'my_models'

inner_directory_form = 'model_' # form of stl model directory from which to make description
inner_directory_prefix = 'default_cut_'

script_dir = os.path.dirname(os.path.realpath(__file__))
script_dir_chop_up = script_dir.split(os.sep)

path_to_my_models = os.sep.join(script_dir_chop_up[:-1])+os.sep+path_to_my_models_suffix


## all objects are initialised with below parameters. Use set-a function to change for exceptions below
default_geometry_type = 'STL'  #should match file extension, eg 'STL' -> .stl', 'TxT' -> '.txt' etc
default_segment = 'no'
default_tally = 'no'
default_mc_code = 'serpent'
default_source = 'no'

##########################################################################
##### TO EDIT TO CHANGE PARAMETERS THAT ARE EXCEPTIONS TO THE DEFAULT ####
###### ALSO UPDATE PLASMA PARAMS IF NOVA CAN OUTPUT MORE IN FUTURE #######
##########################################################################
def set_parameters(parts, directory_path_to_stl_files) :
    global tbr_tally_list
    global neutron_multiplication_tally_list
    #get the plasma parameters from the file
    with open(os.path.join(directory_path_to_stl_files, "Plasma_params.txt"), 'r') as f:
        content = f.read()

    ################ PLASMA PARAMETER READ-IN FROM FILE ##################
    plasma_params = {}
    current_key = ""
    current_value = ""
    speech_count = 0
    value_count = 0
    ## read into dictionary
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

    print 'plasma parameters read as dictionary: '
    for i in plasma_params :
        print i, plasma_params[i]

    ## set parameters
    for key in parts:
        for part in parts[key]:
            tally_string=''
            if key in neutron_multiplication_tally_list :
                tally_string=tally_string+' n_mt-16'
            if key in tbr_tally_list :
                tally_string=tally_string+' n_mt205'
                tally_string=tally_string+' n_mt-55'
            if key in photon_heat_tally_list:
                tally_string=tally_string+' p_mt-12'
            if key in neutron_heat_tally_list:
                tally_string=tally_string+' n_mt-4'

            part.set_tally(tally_string.strip())
            if key == 'plasma' :
                idum1 = "1 "
                number_of_cells_to_follow = "1 "
                valid_source_cells = "67 " #random?
                reactopm_selector = "2.0 " #DT, =1 for DD else is DT
                t_in_kev = "15.4 " # can't get a better fix on this with NOVA yet
                major_rad = plasma_params["R"] + " "
                minor_rad = plasma_params["a"] + " "
                elongation = plasma_params["kappa"] + " "
                triangularity = str(( float(plasma_params["del_l"]) + float(plasma_params["del_u"]) )/ 2) + " "#average of upper and lower

                plasma_shift = "0.0 " #probably fix this - maybe should vary
                plasma_peaking = "1.7 " #SHould vary but can't be extracted from nova yet
                plasma_vertical_shift = "0.0 " #FIX
                ang_extent = "0 360.0" # FIX
                part.set_source(idum1 + number_of_cells_to_follow + valid_source_cells + reactopm_selector + t_in_kev\
                    +major_rad + minor_rad + elongation + triangularity + plasma_shift + plasma_peaking + plasma_vertical_shift\
                    + ang_extent)
    ######################################################################
##########################################################################
########### REST OF FUNCTIONALITY SHOULD REMAIN UNALTERED ################
##### (unless changing format of data file, then change class below) #####
##########################################################################

class Part(object):
    #Each part is its own object
    #set default- can be changed with 'set-a's below
    source = default_source
    tally = default_tally
    segment = default_segment
    geometry_type = default_geometry_type
    mc_code = default_mc_code
    member_list = []

    def __init__(self, component_name, path_to_file, material):
        self.component_name = component_name
        self.material = material
        self.path_to_file = path_to_file

        j=0
        for c in path_to_file :
            if c == '/' :
                j+=1 #j is the index of the final '/' character- want everything after this
            if j != len(path_to_file) -1 :
                 self.filename = path_to_file[(j+1):]
            else :
                 self.filename = path_to_file
    def set_source(self, source) :
        self.source = source

    def set_segment(self, segment):
        self.segment = segment

    def set_tally(self, tally):
        self.tally = tally
    def set_geometry_type(self, geometry_type):
        self.geometry_type = geometry_type

    def set_mc_code(self, mc_code):
        self.mc_code = mc_code

    def init_list(self) :
        #outputs an object's member variables as a list in form seen in 'headers'
        self.member_list = [self.component_name,self.path_to_file,self.material,self.geometry_type,self.mc_code,self.tally,self.segment,self.source]

def get_objects_from_file(directory_path, relative_path_to_stl_dir, filetype, material_dict, enrichment = 0.0):
    #takes a path to a directory with the geometry file and a .filetype (eg ".stl")
    #returns a dictionary of parts {'component_name_1':[corresponding Part objects], c_n_2:[],... etc }

    print "Getting", filetype, "objects from", directory_path

    parts = {}
    all_files = os.listdir(directory_path)
    files_found=[]

    for file_name in all_files :
        if file_name.endswith(filetype) :
            files_found.append(file_name)

    #files_found is a list of all files with correct suffix

    #split into prefixes
    for prefix in material_dict:
        for file in files_found:
            if bool(re.match(prefix, file, re.I)):
                #print "prefix =", prefix.lower(), "b_m =", blanket_material.lower()
                if material_dict[prefix].lower() == blanket_material.lower() :
                    new_part = Part(prefix, relative_path_to_stl_dir + os.sep + file, material_dict[prefix.lower()] + ' ' + enrichment)
                else :
                    new_part = Part(prefix, relative_path_to_stl_dir + os.sep + file, material_dict[prefix.lower()])
                if prefix in parts:
                    parts[prefix].append(new_part)
                else :
                    parts[prefix] = [new_part]
    return parts

def output_header(parts, headers, filename, directory_path_to_output_dir):
    
    print "Outputting headers to", filename
    #outputs the headers for the parts object, spaced to fit all info

    spaces = [3] * len(headers) #number of spaces to follow each header
    len_list = [0] * len(headers)
    #finding max length of data string for each header
    for key in parts:
        for part in parts[key] :
            part.init_list()
            member_list = part.member_list #list with components in same split as the columns
            for i in range(len(member_list)):
                    if len(member_list[i]) > len_list[i]:
                        len_list[i]=len(member_list[i])
    for i in range(len(headers)) :
        if int(len(headers[i])) < len_list[i] :
            spaces[i] = len_list[i] -len(headers[i]) + 3
        else :
            spaces[i]=3

    with open(os.path.join(directory_path_to_output_dir, filename),'w') as f :
        f.write("#\n")
        f.write("# Example parameterfile for an auto Serpent simulation\n")
        f.write("#\n")
        f.write("# lines starting with # are treated as comments and ignored by the code\n")
        f.write("#\n")
        f.write("#".rstrip('\n'))

        for i in range(len(headers)) :
            space = " " * spaces[i]
            if i == len(headers) -1:
                f.write(headers[i]+'\n')
            else :
                f.write((headers[i]+space + ', ').rstrip('\n'))

def output_file_info(parts, headers, filename, directory_path_to_output_dir):
  
    print "Outputting file info to", filename
    spaces = [3] * len(headers) #number of spaces to follow each header
    len_list = [0] * len(headers)
    #finding max length of data string for each header
    for key in parts:
        for part in parts[key] :
            part.init_list()
            member_list = part.member_list
            for i in range(len(member_list)):
                if len(member_list[i]) > len_list[i]:
                    len_list[i]=len(member_list[i])

    with open(os.path.join(directory_path_to_output_dir, filename),'a') as f :
        for key in parts:
            for part in parts[key]:

                part.init_list()
                part_info = part.member_list
                for i in range(len(part_info)):

                    if int(len(headers[i])) < len_list[i] : #data is longest
                        spaces[i] = ((len_list[i]) - len(part_info[i])) + 3
                    else : #header is longest, fill space after data with spaces
                        spaces[i] = len(headers[i]) + 3 - len(part_info[i])

                    space = " " * spaces[i]
                    if i == 0:
                        f.write('\n' + part_info[i] + space + ' , ')
                    elif i == len(headers) - 1:
                        f.write((part_info[i]).rstrip('\n'))
                    else :
                        f.write((part_info[i] + space + ', ').rstrip('\n'))

if __name__ == "__main__" :

    if len(sys.argv) > 1 :
        directory_numbers = sys.argv[1:]
        directories = []
        for i in range(len(directory_numbers)):
           directories.append(inner_directory_form + directory_numbers[i]) 
    else :
        directories = os.listdir(path_to_my_models)
    print "models being considered:", directories

    for model in directories :
        
        directory_path_to_stl_files = path_to_my_models + os.sep + model + os.sep + inner_directory_prefix + model
        directory_path_to_output_dir = path_to_my_models + os.sep + model
        
        relative_path_to_stl_dir = inner_directory_prefix + model
        print "Relative path to stl files from model file:", relative_path_to_stl_dir

        output_file_name = model + '_description_' + blanket_material + '_' + enrichment + '.txt'

        print "Reading stl files from", directory_path_to_stl_files

        #set the input fule suffix, get the parts
        file_suffix =  '.' + default_geometry_type.lower()
        
        parts = get_objects_from_file(directory_path_to_stl_files, relative_path_to_stl_dir, file_suffix, material_dict, enrichment)
        #set plasma parameters from file
        set_parameters(parts, directory_path_to_stl_files)

        #output the model description
        output_header(parts, headers, output_file_name, directory_path_to_output_dir)
        output_file_info(parts, headers, output_file_name, directory_path_to_output_dir)

        print "Output model", model, "to", directory_path_to_output_dir
