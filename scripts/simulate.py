"""
Created by:
	@author: James Bernardi
	University of Cambridge
	bernardi.james.h@gmail.com
	
	2017-09-01
"""

import sys
sys.path.append('/usr/lib/freecad-daily/lib/')
import math, string, FreeCAD, Part, os, multiprocessing, material_database, auto_make_model_description

from FreeCAD import Base
from auto_make_model_description import default_blanket_material, default_enrichment

#TODO: currently just selecting first density in list(ie points to first temperature) - in material cards - adjust so can specify a temp?

"""
USAGE:
    Finds mosel descriptions in models/my_models/model_x
    
    Can pass a list of space-delimited directories as an argument (eg 4.1 16.2.r1.. etc), or will default to iterate through ALL directories
    If specific enrichments and materials are required, pass flags -e (enrichment) -m (material) - although this is not implemented in auto_make_model..
    Else will default to the defaults passed in auto_make_model_description.py

OUTPUT:
If run = TRUE :
    signalling is to be run on a PC- optimises to run quickly and changes path to serpent data(see following section)
Else (if run = FALSE) :
    To be run on cumulus- no speed optimisation and must change the serpent data directory

If now = TRUE :
    Runs sss2 on the newly created input file from local machine
Else (if now = FALSE):
    Leaves the new file alone - ie to be scped over to a cluster or run later etc..


eg:
python simulate.py -e 0.6 -m LiPb 1 2 3... etc
python -e 0.6 2 (directory 2, enrichment specified)
python 1 2 3 (enrichment defaults, first 3 dirs selected)

"""
###################################### TO EDIT FOR FUNCTIONALITY #################################
#"model_description.txt" is produced by script 'auto_make_model_description.py'

#Set the serpent run parameters- 5e6 nps brings stat error to about 0.002 for TBR ~ 1.4
nps = 1000#000
batch_size = 50#00 #used to calculate number of batches below

batches = int(nps/batch_size) #used by serpent

run = True #If true, makes script PC optimised and path to serp data. If false, makes input to be scp'ed and run on cum. also only set opti if run (ie on local to conserve RAM)
now = False #if true, runs script after making file

#These are skipped on writing the file and simulating the result- eg if already done them or something.
skip_models_list = []#['model_16.1', 'model_16.1.no.opti', 'model_16.1.r1', 'model_16.1.r2', 'model_16.2', 'model_16.2.4.a', 'model_4.1.2', 'model_16.1.1', 'model_16.1.1.a', 'model_16.1.2', 'model_16.1.2.a', 'model_16.1.3', 'model_16.1.3.a', 'model_16.1.4', 'model_16.1.4.a', 'model_16.2.1', 'model_16.2.1.a', 'model_16.2.2', 'model_16.2.2.a', 'model_16.2.3', 'model_16.2.3.a', 'model_16.2.4', 'model_4.1.2.a', 'model_4.1.3', 'model_4.1.3.a', 'model_4.1.4', 'model_4.1.4.a', 'model_4.1.r1', 'model_4.1.r2', 'model_4.2', 'model_4.2.1', 'model_4.2.1.a', 'model_4.2.2', 'model_4.2.2.a', 'model_4.2.3', 'model_4.2.3.a', 'model_4.2.4', 'model_4.2.4.a', 'model_4.2.r1', 'model_4.2.r2', 'model_4.3', 'model_4.3.1', 'model_4.3.1.a', 'model_4.3.2', 'model_4.3.2.a', 'model_4.3.3', 'model_4.3.3.a', 'model_4.3.4']

#These are skipped on writing the serpent file material outputs (ie if any stl files are broken- recommended to leave these blank)
skip_prefixes = []#['bss_23', 'bss_27', 'bss_72', 'bss_68', 'obc4_14', 'obc5_14', 'obc6_14', 'obc8_5', 'obc9_5', 'obc10_5', 'obr5_15', 'obc7_6'] #empty list for none

directory_form = 'model_'
output_data_directory = 'simulation_data'
output_data_filename = 'raw_data.txt'

    ############################    CHANGE ACCORDING TO USER ##################################
remote_acelib_location = "/home/jhbernar/serpent" #/serpent2/xsdir.serp (in call) or /serpent2/photon_data
local_acelib_location = "/opt"
    ############################################################################################

# directory finding 
script_dir = os.path.dirname(os.path.realpath(__file__))
script_dir_chop_up = script_dir.split(os.sep)

path_to_models = os.sep.join(script_dir_chop_up[:-1]) + os.sep + 'models'

#script currently uses 'path to my models'
path_to_my_models = path_to_models + os.sep + 'my_models'
path_to_destination = path_to_models + os.sep + 'image_dirs'

# if "" instead of path_to_my_models is used- gives relative path to stl files in the directory given, else use path_to_my_models as abs path to models (eg if using image dirs_)
def get_abs_path(model_name) :
    return path_to_my_models + os.sep + model_name
##################################################################################################

class Component(object) :
    #An object storing a component's data
    #requirement: arguments appear in same order as they do in the model description, otherwise malleable
    def __init__(self, component, CAD_file, material, geometry_type, mc_code, tally, segment, source):
        self.component = component
        self.CAD_file = CAD_file
        self.material = material
        self.geometry_type = geometry_type
        #ignore mc_code- serpent in this case.
        self.tally = tally
        self.segment = segment
        self.source = source

def lower_tuple(tup) :
    #lower a tuple of strings
    result = []
    for i in range( len(tup) ) :
        result.append(tup[i].lower()) 
    return tuple(result)

def read_in_parameter_file(filename):
    #componet_list , CAD_files_list,materials_list,geometry_type_list,tally_list,segment_list,source_list =[],[],[],[],[],[],[]
    #Read in the model directory and turn into Components for the serpent file
    parts = {}
    print 'Model description filename:', filename
    with open(filename) as f:
        content = f.readlines()

    content = [x.strip() for x in content]

    for linecounter in range(0,len(content)):

        line = content[linecounter].strip()

        if line.startswith('#')==False and len(line)>0:

            line_chopped_up = line.split(',')

            data_list = []
            for i in range(len(line_chopped_up)):
                data_list.append(line_chopped_up[i].strip())
            current_part = Component(*data_list) #componet_list, CAD_files_list,materials_list,geometry_type_list,mc_code,tally_list,segment_list,source_list

            #add to the dictionary of parts
            if data_list[0] in parts:
                parts[data_list[0]].append(current_part)
            else :
                parts[data_list[0]] = [current_part]

    return parts

#Not currently used
def open_stp_and_resave_geometry_as_seperate_stl_bodies(filenames):
    os.system('mkdir stl_files')
    for filename  in filenames:
        short_filename,extension =os.path.splitext(filename)
        model =Part.Shape()
        model.read(filename)

        module_counter=1
        remaining_solids=[]

        for solid in model.Solids :

            print(' looking at soild with a volume of '+str(solid.Volume))

            #if len(solid.Faces)==6:
              #common_solid = solid.common(slice)
            #if common_solid.Volume !=0 :
                    #common_solid.exportStep('stl_files/'+short_filename+'_'+str(module_counter)+'.stp')
                       #common_solid.exportSt('stl_files/'+short_filename+'_'+str(module_counter)+'.stl')
                    #module_counter=module_counter+1
                #remaining_solids.append(common_solid)

    #common_solid_compound = Part.makeCompound(remaining_solids)
    #common_solid_compound.exportStl('stl_modules/lithium-lead-all.stl')
    return list_of_stl_files_for_each_stp_file

def return_serpent_file_head():
    #Standard output for head
    lines_for_file=[]
    lines_for_file.append('% File automatically generated by AutoSerpent')
    lines_for_file.append('% AutoSerpent is a python script written by Jonathan Shimwell and James Bernardi and Xiaoying Tang to find neutronics metrics of fusion reactors')
    lines_for_file.append('% run this file using one of the following three commands')
    lines_for_file.append('%     sss2 tbr_calc3.txt -tracks 100 ')
    lines_for_file.append('%     sss2 tbr_calc3.txt -omp 2 ')
    lines_for_file.append('%     sss2 tbr_calc3.txt ')
    lines_for_file.append(' ')
    lines_for_file.append(' ')
    lines_for_file.append('% nova model as STL files')
    lines_for_file.append('surf 999  sph 0 0 0 2000 %base units are cm')
    lines_for_file.append('surf 998  sph 0 0 0 2001')
    lines_for_file.append('\n\n% CSG cells')
    lines_for_file.append('cell 1000  0 fill sector -999 %sphere fill with universe sector')
    lines_for_file.append('cell 1999  0 outside 999')
    lines_for_file.append('\n\n%background universe cell = void')
    lines_for_file.append('cell 2000  bg_for_stl void -998 % background universe number 2')
    lines_for_file.append('\n\n')
    lines_for_file.append('\n\n% ------  STL cells in universe 1 ------\n% background is universe 2 which is just void')
    lines_for_file.append('solid 2  sector bg_for_stl   %solid 2 is STL.  <uni> <bg uni>')
    lines_for_file.append('100 3 10 5 5     %adaptive search mesh parameters')
    lines_for_file.append('%<max cells under mesh before split> <n levels> <size 1> < size 2> < size n>')
    lines_for_file.append('% here initial search mesh is 10x10x10, any mesh with > 5 cells under it is split into a 5x5x5 mesh.')
    lines_for_file.append('1 0.0000001   %1=fast, 2=safe tracking mode.  verticies snap tolerence.')
    lines_for_file.append('% these made no difference to error')


    return lines_for_file

def return_serpent_file_run_params():

    lines_for_file=[]
    lines_for_file.append('  ')
    lines_for_file.append('  ')
    lines_for_file.append('% ---- RUN ----')
    lines_for_file.append('set outp 1000')
    lines_for_file.append('set srcrate 1.0')
    if run :
        lines_for_file.append('set acelib "'+ local_acelib_location + '/serpent2/xsdir.serp"')
    else :
        lines_for_file.append('set acelib "'+ remote_acelib_location + '/serpent2/xsdir.serp"')
    lines_for_file.append('\n\n')
    return lines_for_file

#Change if different plots are required
def return_serpent_file_plot_params():
    lines_for_file=['\n\n% ------ PLOT PARAMS -------']

    lines_for_file.append('set nps '+str(nps) +' '+ str(batches) +'% neutron population, bunch count')
    lines_for_file.append('set outp '+str(batches+1)+' %only prints output after batchs +1, ie at the end')
    lines_for_file.append('plot 1 1030 1030 -2  -2000 2000 -2000 2000')
    lines_for_file.append('plot 2 1030 1030 -2  -2000 2000 -2000 2000 %plot py pixels pixels origin')
    lines_for_file.append('plot 3 1030 1030 -2  -2000 2000 -2000 2000')
    lines_for_file.append('\n\n')
    return lines_for_file

def return_serpent_file_source(parts):
    #Return info about the (plasma) source
    source_list = []
    for key in parts :
        for part in parts[key] :
            source_list.append(part.source)

    for entry in source_list:
        #print(entry)
        if entry != 'no':
            #print('source found',entry)
            idums_rdums= entry.split()
            #print(idums_rdums)
            #print(len(idums_rdums))
            try:
                idum1,idum2,idum3,rdum1,rdum2,rdum3,rdum4,rdum5,rdum6,rdum7,rdum8,rdum9,rdum10,rdum11 =idums_rdums
            except:
                print('There is something wrong with your source term')
                if len(idums_rdums)!=14:
                    print('There should be 14 terms in the source, you have got '+str(len(idums_rdums)))
                    sys.exit()
            break

    lines_for_file=[]
    lines_for_file.append('% --------------------- SOURCE SPECIFICATION ---------------------')
    lines_for_file.append('% MUIR GAUSSIAN FUSION ENERGY SPECTRUM IN USER DEFINED SUBROUTINE')
    lines_for_file.append('% PARAMETERS TO DESCRIBE THE PLASMA:')
    lines_for_file.append('src 1 si 16')
    lines_for_file.append('3 11')
    lines_for_file.append(idum1+' % IDUM(1) = ???')
    lines_for_file.append(idum2+' % IDUM(2) = number of valid cell numbers to follow')
    lines_for_file.append(idum3+' % IDUM(3) to IDUM(IDUM(2)+1) = valid source cells')
    lines_for_file.append(rdum1+' % RDUM(1) = Reaction selector 1=DD otherwise DT')
    lines_for_file.append(rdum2+' % RDUM(2) = TEMPERATURE OF PLASMA IN KEV')
    lines_for_file.append(str(float(rdum3)*100)+' % RDUM(3) = RM  = MAJOR RADIUS')
    lines_for_file.append(str(float(rdum4)*100)+' % RDUM(4) = AP  = MINOR RADIUS')
    lines_for_file.append(rdum5+' % RDUM(5) = E   = ELONGATION')
    lines_for_file.append(rdum6+' % RDUM(6) = CP  = TRIANGUARITY')
    lines_for_file.append(rdum7+' % RDUM(7) = ESH = PLASMA SHIFT')
    lines_for_file.append(rdum8+' % RDUM(8) = EPK = PLASMA PEAKING')
    lines_for_file.append(rdum9+' % RDUM(9) = DELTAZ = PLASMA VERTICAL SHIFT (+=UP)')
    lines_for_file.append(rdum10+' % RDUM(10) = Start of angular extent')
    lines_for_file.append(rdum11+'% RDUM(11) = Range of angular extent')
    lines_for_file.append('\n\n')

    return lines_for_file

def return_serpent_file_material_cards(parts, script_dir, skip_prefixes = []):
    #find the material information from material_database.py and associate that with the STL files read from the model decsription.

    line_for_file = ['\n\n']
    line_for_file.append("%----------- MATERIAL INPUT ------------")
    unique_materials=[]
    for key in parts :
        for part in parts[key]:
            if part.material not in unique_materials :# and part.material.lower() != 'plasma' :
                unique_materials.append(part.material)


    line_for_file.append("\n\n")

    #treat the other materials

    #print('unique_materials ',unique_materials)
    for material in unique_materials:
        chop_up = material.split()
        #print "CHOP UP", chop_up
        if len(chop_up) == 1:
            result = material_database.find_material_properties(script_dir, chop_up[0])
        else:
            result = material_database.find_material_properties(script_dir, chop_up[0], float(chop_up[1]))
        try:
            density_g_per_cm3 = float(result["density"][0])*0.001
            line_for_file.append("mat " + result["name"].lower() + " -" + str(density_g_per_cm3) )

        except:
            print 'No density found for ' + result["name"] + ", trying atom_density:",
            try :
                density_at_barn = float(result["atom_density"][0])
                line_for_file.append("mat " + result["name"].lower() + " " + str(density_at_barn) )
                print "Success"
            except :
                 print 'Failed for material name: ' + result["name"]

        for isotope in result["isotopes"] :
            #line_for_file.append(str(isotope) + ".31c  " + str(result["mass_fractions"][result["isotopes"].index(isotope)]))
            
            if str(isotope).startswith('1603'):
                line_for_file.append(str(isotope) + ".03c  " + str(result["mass_fractions"][result["isotopes"].index(isotope)]))
            else:
                line_for_file.append(str(isotope) + ".31c  " + str(result["mass_fractions"][result["isotopes"].index(isotope)]))
            
        line_for_file.append('\n')
    line_for_file.append('%adding dummy materials')
    line_for_file.append('mat li-6 1')
    line_for_file.append('  3006.31c  1')
    line_for_file.append('mat li-7 1')
    line_for_file.append('  3007.31c  1')
    line_for_file.append('\n\n')
    return line_for_file

#This was found to be more useful- detects all mult and tritium breeding
def return_serpent_macroscopic_detectors(detector_name, mtnumber, particletype, tally_list):
    blanket_material = auto_make_model_description.blanket_material
    
    #change this to blanket multiplier material
    detector_cell_string = ""
    for cell in tally_list :
        if tally_list.index(cell) != len(tally_list)-1 :
            detector_cell_string +="\tdc " + cell + "-c\n"
        else :
            detector_cell_string +="\tdc " + cell + "-c"

    result = []
    result.append('\n\n')
    result.append('% ------------ DETECTOR INPUT (macroscopic) ---------------')
    result.append('det '+detector_name+ ' '+particletype)
    result.append(detector_cell_string)
    if particletype == 'p' :
        result.append('\tdr '+mtnumber+'  void')
    else :
       result.append('\tdr '+mtnumber+'  '+blanket_material.split()[0].lower())

    return result

#Useful for plotting, perhaps..
def return_serpent_microscopic_detectors(enrichment):

    tally_list = auto_make_model_description.tbr_tally_list
    material_dict = auto_make_model_description.material_dict
    blanket_material = auto_make_model_description.blanket_material + ' ' + enrichment

    chop_up = blanket_material.split()
    print(chop_up)
    
    if len(chop_up) == 1:
        result = material_database.find_material_properties(script_dir, chop_up[0])
    else:
        result = material_database.find_material_properties(script_dir, chop_up[0], float(chop_up[1]))

    #print "result", result

    dv_list = result["tally_multiplier"]
    counter=0
    for isotope in result["isotopes"] :

        if isotope==3006:
             dv_li6=str(dv_list[counter])
        if isotope==3007:
            dv_li7=str(dv_list[counter])
        counter=counter+1

    #print('result["isotopes"]',result["isotopes"])
    #print('dv_list',dv_list)
    #print('dv_li6',dv_li6)
    #print('dv_li7',dv_li7)

    detector_cell_string = ""
    for cell in tally_list :
        if tally_list.index(cell) != len(tally_list)-1 :
            detector_cell_string +="\tdc " + cell + "-c\n"
        else :
            detector_cell_string +="\tdc " + cell + "-c"


    result = []
    result.append('\n\n')
    result.append('% ------------ DETECTOR INPUT (microscopic) ---------------')
    if float(enrichment) > 0 :
        result.append("det li6_mt205 n %tritium production")
        result.append(detector_cell_string)
        result.append("\tdr 205 li-6 % tritium production")
        result.append("\tdm "+chop_up[0].lower()+" % material to score in")
        result.append("\tdv "+dv_li6+" % multiplication by atomic density (this is the reciprocal)")
        result.append('\n')
    if float(enrichment) < 1.0 :
        result.append('det li7_mt205 n %tritium production for li7 isotope')
        result.append(detector_cell_string + '\n\tdr 205 li-7 \n\tdm '+chop_up[0].lower()+'\n\tdv '+dv_li7+'\n')

    #result.append('det tbr_in_mesh\n\tdx -2000 2000 100\n\tdy -2000 2000 100\n\tdz -2000 2000 100')
    #result.append(detector_cell_string + '\n\tdr 205 li-7 \n\tdm '+blanket_material.lower()+'\n\tdv 1941.2')
    result.append('\n\n')

    return result

def return_serpent_file_stl_parts(parts, model_name):
    #Returns the list of stl files to be simulated in serpent

    material_dict = auto_make_model_description.material_dict

    component_list, CAD_files_list, source_list = [], [], []
    source_CAD_file = ""

    for key in parts :
        for part in parts[key] :
            component_list.append(part.component)
            CAD_files_list.append(part.CAD_file)
            source_list.append(part.source)
            if part.source != 'no' :
                source_CAD_file = part.CAD_file


    scaling_factor =0.1
    lines_for_file=[]
    lines_for_file.append("\n\n% -------------- STL FILE INPUT ---------------")
    unique_componets=[]

    #leave source out of components
    for component , source in zip(component_list,source_list):
        if component not in unique_componets and source == "no":
            unique_componets.append(component)
        elif source !='no':
            component_name_of_source = component


    #print('unique_componets',unique_componets)
    try :
        print'Component name of source:', component_name_of_source
    except:
        print('*** WARNING ***')
        print('No component name of source was found (ie all source tallys set to "no")')
        print('Exiting- can move dependencies to allow this within script but would expect a source.') 

    lines_for_file.append('\n\n')
    lines_for_file.append('body '+component_name_of_source+'-b 67 '+component_name_of_source)
    lines_for_file.append('file '+component_name_of_source+'-b "'+ get_abs_path(model_name) + os.sep + source_CAD_file+'" 0.1 0 0 0  ' )
    lines_for_file.append('\n\n')

    for component in unique_componets:

        try:
            if component != component_name_of_source:
                if len(material_dict[component].split())==1:
                    lines_for_file.append('body '+component+'-b '+component+'-c ' +material_dict[component].lower())
                else:
                    lines_for_file.append('body '+component+'-b '+component+'-c ' +material_dict[component].split()[0].lower())

            for CAD_file, sub_component in zip(CAD_files_list, component_list):
                
                if skip_prefixes != [] and CAD_file.split(os.sep)[-1].split(".")[0].lower() in [c.lower() for c in skip_prefixes] :
                    print "Skipping", CAD_file
                    continue

                if sub_component == component and component != component_name_of_source:
                    lines_for_file.append('file '+component+'-b "'+ get_abs_path(model_name) + os.sep + CAD_file+'" 0.1 0 0 0  ' )
        except:
            pass

    #for CAD_file, component, source in zip(CAD_files_list, componet_list, source_list):
     #   print(CAD_file,component,source)


    return lines_for_file

def return_serpent_file_mesh(detector_name):
    result = []
    result.append('\n\n% '+detector_name+' mesh plot:')
    result.append("mesh 8 4 "+detector_name+" 3 1680 1050 0  -3200 3200 -2000 2000\n"+\
    "mesh 8 4 "+detector_name+" 2 1280 1024 0 -2500 2500 -3200 3200\n"+\
    "mesh 8 4 "+detector_name+" 1 1280 1024 0 -2500 2500 -3200 3200")
    return result

#Was used to append simulated data to the output file straight away- but now this data is collected by script gather_results.py all together.
#Not used
def print_output_to_simulation_datafile(directory_path_to_tbr, directory_path_to_simulation_data, model, enrichment, blanket_mat):
    try :
        with open(directory_path_to_tbr) as f:
            content=f.readlines()
    except :
        print "No file", directory_path_to_tbr, "was found."
        print "Was the serpent simulation run?"
        print "Has the _det0 file been output to the correct place?"
        return

    tbr_list = []
    error_list_sq = []
    macro_tbr_list, macro_error_list_sq = [], []

    for counter in range(0,len(content)):
        if content[counter].startswith('DETli6_mt205') or content[counter].startswith('DETli7_mt205'):
            counter= counter+1
            while content[counter].startswith('];')==False:
                #print(content[counter])
                tbr_list.append(float(content[counter].split()[-2]))
                error_list_sq.append(float(content[counter].split()[-1]))
                counter= counter+1
    
    for counter in range(0,len(content)):
        if content[counter].startswith('DETtbr'):
            counter= counter+1
            while content[counter].startswith('];')==False:
                #print(content[counter])
                macro_tbr_list.append(float(content[counter].split()[-2]))
                macro_error_list_sq.append(float(content[counter].split()[-1]))
                counter= counter+1


    tbr_total = 0
    error_total_sq =0
    macro_total = 0
    error_macro_total_sq = 0

    for i in range(len(tbr_list)):
        error_total_sq += error_list_sq[i] ** 2
        tbr_total += tbr_list[i]
    for i in range(len(macro_tbr_list)):
        macro_total += macro_tbr_list[i]
        error_macro_total_sq += error_list_sq[i] ** 2
    
    error_total = math.sqrt(error_total_sq)
    macro_error_total = math.sqrt(error_macro_total_sq)
    print "\nRESULT:"
    print "tbr total: ", tbr_total
    print "error total: ", error_total
    print "macro tbr total: ", macro_total
    print "macro error total: ", macro_error_total

    new_line = "\n" + model + " " + blanket_mat + " " + enrichment + " " + str(tbr_total) + " " + str(error_total) + " " +str(macro_total) + " " + str(macro_error_total)
    print "full simulated data: ", new_line.strip()

    already_exists_flag = False
    update_required = False
    line_counter = 1
    #write line to file
    with open(directory_path_to_simulation_data, 'a+') as sd :    
        data_as_lines = sd.readlines()
        #initialise if a new file
        if data_as_lines == [] :
            sd.write("model material enrichment tbr_value error macro_tbr_value macro_error")
        #check if the line already exists
        for data_line in data_as_lines :
            
            file_data_list = data_line.split(" ")

            if data_line.startswith(blanket_mat + " " + enrichment) :
          
                already_exists_flag = True
                #checking different cases - update if error is lower, else report no change
                tbr_dif = abs(float(file_data_list[-2].strip()) - tbr_total)
                error_dif = abs(float(file_data_list[-1].strip()) - error_total)
                
                if error_dif < 1e-10 and tbr_dif < 1e-10:
                    print "simulation produced no new results- error and tbr differences  < 1e-10 (or same) "
          
                elif error_dif < 1e-10 :
                    print "updating ", blanket_mat + " " + enrichment, " as error is same but tbr has changed."
                    data_as_lines[line_counter - 1] = new_line 
                    update_required = True
                
                elif float(file_data_list[-1].strip()) > error_total :
                    print "updating ", blanket_mat + " " + enrichment, " as error is lower for new simulated value"
                    print "( " + str(error_total) + " < " + file_data_list[-1].strip() + " )"
                    print "New tbr: ", str(tbr_total), ". Old tbr: ", str(file_data_list[-2]), ". Difference: ", tbr_dif
                    data_as_lines[line_counter - 1] = new_line
                    update_required = True
                
                else : 
                    print "entry already exists with lower error for ", blanket_mat + " " + enrichment, ". Not updating file."

                    "( " + str(error_total) + " > " + file_data_list[-1].strip() + " )"

                    print "New tbr: ", str(tbr_total), ". Old tbr: ", file_data_list[-2]
            line_counter += 1
    
    if not already_exists_flag :
        print "appending new data to " + directory_path_to_simulation_data + "..."
        with open(directory_path_to_simulation_data, 'a') as sd :
            sd.write(new_line)
    elif update_required :
        with open(directory_path_to_simulation_data, 'w') as sd :
            sd.writelines(data_as_lines)
    print '\n'

if __name__ == "__main__":

    #Read in args, get enrich and material parameters from flag and selected directories (see USAGE)
    blanket_mat, enrichment = default_blanket_material, default_enrichment
    i = 1
    directories = []

    #Read in model directories passed
    while i < (len(sys.argv)) :
        if sys.argv[i] == "-e" :
            enrichment = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == "-m" :
            blanket_mat = sys.argv[i+1]
            i += 2
        else :
            #end of flags found
            break 
    #start from end of flags:
    
    if i == len(sys.argv) :
        directories = os.listdir(path_to_my_models)
    else :
        for j in range(i,len(sys.argv)) :
            directories.append(directory_form + sys.argv[j])
    
    print "\nRead enrichment:", enrichment
    print "Read material:", blanket_mat
    print "Read directories:", directories, "\n"

    success_list, failed_list = [],[]
    skipped = 0

    #Do for each model
    for model in directories :
        
        if model in skip_models_list :
            print "Skipping", model
            skipped += 1
            continue

        model_dir = path_to_my_models + os.sep + model
        serpent_input_filename = 'serpent_input_' + enrichment + '_' + blanket_mat + '_' + model

        directory_path_to_parameter_file = path_to_my_models + os.sep + model + os.sep + model + '_description_' + blanket_mat + '_' + enrichment +'.txt'
        directory_path_to_serpent_output = model_dir + os.sep + serpent_input_filename + '.serp'
        directory_path_to_tbr = directory_path_to_serpent_output +'_det0.m'

        directory_path_to_simulation_data = os.sep.join(script_dir_chop_up[:-1])+os.sep+ output_data_directory +os.sep+ output_data_filename

        input_filename = 'model_description_' + blanket_mat + '_' + enrichment + '.txt'
    
        parts={}
        try :
            parts =read_in_parameter_file(directory_path_to_parameter_file)
        except :
            print "No file", directory_path_to_parameter_file, "found. Continuing..."
            continue
    
    
        #list_of_stl_files_for_each_stp_file = open_stp_and_resave_geometry_as_seperate_stl_bodies(CAD_files_list)
        #print(componet_list)
        #print('CAD_files_list',CAD_files_list)
        #print('source_list',source_list)
    
        serpent_file=[]
        serpent_file += return_serpent_file_head()
        serpent_file += return_serpent_file_stl_parts(parts, model)
        serpent_file += return_serpent_file_run_params()
        serpent_file += return_serpent_file_material_cards(parts, script_dir, skip_prefixes)
        serpent_file += ["set gcu -1"]
        if run :
            serpent_file += ["set opti 1"]
        #serpent_file += ["set ngamma 1"]
        if run :
            pass
            #serpent_file += ['set pdatadir "' + local_acelib_location + '/serpent2/photon_data"']
        else :
            pass
            #serpent_file += ['set pdatadir "' + remote_acelib_location + '/serpent2/photon_data"']
        serpent_file += return_serpent_file_source(parts)
        serpent_file += return_serpent_file_plot_params()

        serpent_file += return_serpent_microscopic_detectors(enrichment)
        serpent_file += return_serpent_macroscopic_detectors('neutron_multiplication','-16','n',auto_make_model_description.neutron_multiplication_tally_list)
        serpent_file += return_serpent_macroscopic_detectors('neutron_heating','-4','n',auto_make_model_description.neutron_heat_tally_list)
        #serpent_file += return_serpent_macroscopic_detectors('photon_heating','-12','p',auto_make_model_description.photon_heat_tally_list)
        serpent_file += return_serpent_macroscopic_detectors('tbr','-55','n', auto_make_model_description.tbr_tally_list)

        serpent_file += return_serpent_file_mesh('li6_mt205')
        serpent_file += return_serpent_file_mesh('li7_mt205')
        serpent_file += return_serpent_file_mesh('neutron_multiplication')
    
        with open(directory_path_to_serpent_output, 'w') as s_i :
            for x in serpent_file:
                s_i.write(x + '\n')
    
        #os.system('sss2 '+directory_path_to_serpent_output) # NO MULTITHREADING
        #Implementing multithreading :
     
        if now :
            
            cpu_cores = multiprocessing.cpu_count()
            print 'Cpu cores found for simulation:', cpu_cores
            os.chdir(model_dir)
            
            if cpu_cores > 1:
                os.system('sss2 '+directory_path_to_serpent_output+ ' -omp '+str(cpu_cores))
            else:
                os.system('sss2 '+directory_path_to_serpent_output)
            #Finally print the output to an output data file, appending or replacing
        
        	print "Run has been completed (or exited)"
        #print_output_to_simulation_datafile(directory_path_to_tbr, directory_path_to_simulation_data, model, enrichment, blanket_mat)
        
            if os.path.isfile(directory_path_to_serpent_output + "_det0.m") :
                success_list.append(model)
            else :
                failed_list.append(model)
    
            print ""
            print "COMPLETED SO FAR:", failed_list + success_list
            print "\n"
            print str(len(failed_list + success_list) + skipped) + "/" + str(len(directories))
            print "\n"
            print "FAILED:", failed_list
            print "\n"
            print "SUCCESS:", success_list
            print "\n"
