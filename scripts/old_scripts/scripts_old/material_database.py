#!/usr/bin/python


import re, os, sys

script_dir = os.path.dirname(os.path.realpath(__file__))

def find_mass_in_kg_enriched_lc(name,packing_fraction,theoretical_density,enrichment_fraction, script_dir):
  list =[a for a in re.split(r'([A-Z][a-z]*)', name) if a]
  #print(list)
  list_elements=[]
  list_fraction=[]
  list_abundance=[]
  for counter in range(0,len(list)):
    if list[counter].isdigit():
      pass
    else:
      list_elements.append(list[counter])
      try:
        if list[counter+1].isdigit():
          list_fraction.append(list[counter+1])
        else:
          list_fraction.append('1')
      except:
          list_fraction.append('1')
  #print(list_elements)
  #print(list_fraction)
  #print('')
  with open(script_dir + os.sep + 'nist_data_exstended.txt') as f:
    content = f.readlines()
  cumlative_molar_mass=0
  for x in range(0,len(content)):
    line=content[x]
    chop_up=line.split()
    try:
      if chop_up[1] in list_elements:
        index= list_elements.index(chop_up[1])
        #print('index number ='+str(index))
        protons=chop_up[0]
        element=chop_up[1]
        #print(content[x])
        while content[x].startswith('___________')==False:   
          #print('   '+content[x])
          subchop_up =content[x].split()
          neutrons = str(int(subchop_up[-3])-int(protons))
          if element=='Li':
            if neutrons=='3':
              abundance =enrichment_fraction
              #print(protons+element+neutrons+' ='+str(abundance))
            elif neutrons=='4':
              abundance =1.0-enrichment_fraction
              #print(protons+element+neutrons+' ='+str(abundance))
          else:
            abundance = float(subchop_up[-1]) 
          atomic_mass= float(subchop_up[-2])
          running_molar_mass=float(list_fraction[index])*atomic_mass*abundance
          #print(str(list_fraction[index])+'*'+str(atomic_mass)+'*'+str(abundance)+'=' +str(running_molar_mass) )
          cumlative_molar_mass=cumlative_molar_mass+running_molar_mass
          atomic_number=str(int(protons) +int(neutrons))
          if len(atomic_number)==2:
            #print('little one found')
            atomic_number='0'+atomic_number
          if len(atomic_number)==1:
            atomic_number='00'+atomic_number
          #print('        '+protons +' '+neutrons+ ' ' + str(abundance) + ' '+ str(list_fraction[index]))
          if len(protons)==2:
            #print('little one found')
            protons='0'+protons
          if len(protons)==1:
            protons='00'+protons
          #print()
          #output.write('        '+protons+atomic_number+ ' ' + str((abundance) * (list_fraction[index]))+'\n')
          x=x+1
          if content[x].startswith('___________')==True:
            pass#print('escaping loop')
    except:
      pass
      #print('elment not found')
  #print('cumlative_molar_mass = '+str(cumlative_molar_mass))
  #output.close()
  #print('    '+ name+' molar mass = '+ str(cumlative_molar_mass))
  mass_in_grams=cumlative_molar_mass*1.66054e-24
  #print('    '+ name+' mass in grams='+str(mass_in_grams))
  mass_in_grams=mass_in_grams*packing_fraction
  mass_in_grams=mass_in_grams*theoretical_density
  return mass_in_grams/1000


def find_volume_in_m3(name):
    units=''
    if name=='Li4SiO4':
        vol=1.1543 #http://materials.springer.com/isp/crystallographic/docs/sd_1404772
        units='nm3'
        molecules_per_unit_cell=14.0
    if name=='Li2SiO3':
        vol=0.23632 #http://materials.springer.com/isp/crystallographic/docs/sd_1703282
        units='nm3'
        molecules_per_unit_cell=4.0
    if name=='Li2ZrO3':
        vol=0.24479 #http://materials.springer.com/isp/crystallographic/docs/sd_1520554
        units='nm3'
        molecules_per_unit_cell=4.0        
    if name=='Li2TiO3':
        vol=0.42701 #http://materials.springer.com/isp/crystallographic/docs/sd_1716489
        units='nm3'
        molecules_per_unit_cell=8.0          
    if name=='Be':
        vol=0.01622 #http://materials.springer.com/isp/crystallographic/docs/sd_0261739
        units='nm3'
        molecules_per_unit_cell=2.0
    if name=='Be12Ti':
        vol=0.22724 #http://materials.springer.com/isp/crystallographic/docs/sd_0528340
        molecules_per_unit_cell=2.0 
        units='nm3'
    if name=='Ba5Pb3':
        vol=1.37583 #http://materials.springer.com/isp/crystallographic/docs/sd_0528381
        molecules_per_unit_cell=4.0 
        units='nm3'
    if name=='Nd5Pb4':
        vol=1.06090 #http://materials.springer.com/isp/crystallographic/docs/sd_0252125
        molecules_per_unit_cell=4.0 
        units='nm3'  
    if name=='Zr5Pb3':
        vol= 0.36925 #http://materials.springer.com/isp/crystallographic/docs/sd_0307360
        molecules_per_unit_cell=2.0 
        units='nm3'  
    if name=='Zr5Pb4':
        vol=  0.40435 #http://materials.springer.com/isp/crystallographic/docs/sd_0451962
        molecules_per_unit_cell=2.0 
        units='nm3'            
    #print('unit cell volume ='+str(vol)+' '+units)
    #if units=='nm3':
     #   vol=(vol*1.0e-21)/molecules_per_unit_cell
        #convert nm3 to cm3
    if units=='nm3':
        vol=(vol*1.0e-27)/molecules_per_unit_cell
    return vol

def mass_fraction_from_equation(script_dir, chemical_equation,Li6_enrichment_fraction=0.0759):
  if Li6_enrichment_fraction>1:
      return "Enrichmentfraction for lithium can't be greater than 1"    
      sys.exit()
  list =[a for a in re.split(r'([A-Z][a-z]*)', chemical_equation) if a]
  list_elements=[]
  list_fraction=[]
  for counter in range(0,len(list)):
    try:
      float(list[counter])
    except:
      list_elements.append(list[counter])
      try:
        float(list[counter+1])
        list_fraction.append(list[counter+1])
      except:
          list_fraction.append('1')
  return_abundances_list=[] 
  with open(script_dir + os.sep + 'nist_data_exstended.txt') as f:
    content = f.readlines()
  for x in range(0,len(content)):
    chop_up=content[x].split()
    if len(chop_up)>1:
      if chop_up[1] in list_elements:
        index= list_elements.index(chop_up[1])
        protons=chop_up[0]
        element=chop_up[1]
        while content[x].startswith('___________')==False:
          subchop_up =content[x].split()
          neutrons = str(int(subchop_up[-3])-int(protons))
          abundance = float(subchop_up[-1])
          atomic_number=str(int(protons) +int(neutrons))
          if len(atomic_number)==2:
            #print('little one found')
            atomic_number='0'+atomic_number
          if len(atomic_number)==1:
            atomic_number='00'+atomic_number
          if (protons+atomic_number) =='3006':
            if Li6_enrichment_fraction!=0:
              return_abundances_list.append((Li6_enrichment_fraction) * float(list_fraction[index]))
          elif (protons+atomic_number) =='3007':
            if 1.0-Li6_enrichment_fraction!=0:
              return_abundances_list.append((1-Li6_enrichment_fraction) * float(list_fraction[index]))
          else:
            return_abundances_list.append((abundance) * float(list_fraction[index]))
          x=x+1
  norm_return_abundances_list = [i/sum(return_abundances_list) for i in return_abundances_list ]
  return  norm_return_abundances_list 

def isotopes_from_equation(script_dir, chemical_equation,Li6_enrichment_fraction=0.0759):
  if Li6_enrichment_fraction>1:
      print("enrichmentfraction for lithium can't be greater than 1")
      sys.exit()
  list =[a for a in re.split(r'([A-Z][a-z]*)', chemical_equation) if a]
  list_elements=[]
  list_fraction=[]
  for counter in range(0,len(list)):
    if list[counter].isdigit():
      pass
    else:
      list_elements.append(list[counter])
      try:
        if list[counter+1].isdigit():
          list_fraction.append(list[counter+1])
        else:
          list_fraction.append('1')
      except:
          list_fraction.append('1')
  return_isotopes_list=[]
  with open(script_dir + os.sep + 'nist_data_exstended.txt') as f:
    content = f.readlines()
  for x in range(0,len(content)):
    chop_up=content[x].split()
    if len(chop_up)>1:
      if chop_up[1] in list_elements:
        index= list_elements.index(chop_up[1])
        protons=chop_up[0]
        element=chop_up[1]
        while content[x].startswith('___________')==False:
          subchop_up =content[x].split()
          neutrons = str(int(subchop_up[-3])-int(protons))
          abundance = float(subchop_up[-1])
          atomic_number=str(int(protons) +int(neutrons))
          if len(atomic_number)==2:
            #print('little one found')
            atomic_number='0'+atomic_number
          if len(atomic_number)==1:
            atomic_number='00'+atomic_number
          if (protons+atomic_number) =='3006':
            if Li6_enrichment_fraction!=0:
              return_isotopes_list.append(int(protons+atomic_number))
          elif (protons+atomic_number) =='3007':
            if 1.0-Li6_enrichment_fraction!=0:
              return_isotopes_list.append(int(protons+atomic_number))
          else:
            return_isotopes_list.append(int(protons+atomic_number))
          x=x+1
  return   return_isotopes_list
  

def calculate_density_of_material(script_dir, name,packing_fraction,theoretical_density, enrichment_fraction=0.0759):
    return find_mass_in_kg_enriched_lc(name,packing_fraction,theoretical_density,enrichment_fraction, script_dir)/find_volume_in_m3(name)

def return_zaid(protons,neutrons):
  protons_str=str(protons)
  neutrons_str=str(neutrons)
  if len(neutrons_str)==1:
    neutrons_str='00'+neutrons_str 
  if len(neutrons_str)==2:
    neutrons_str='0'+neutrons_str
  #print(protons_str,neutrons_str)
  return int(protons_str+neutrons_str)
       

def return_molar_mass_of_isotope(isotope_zaid, script_dir):
  with open(script_dir + os.sep + 'nist_data_simple.txt') as f:
    content = f.readlines()
  for x in range(0,len(content)):
    line=content[x]
    if line.startswith('_____')==False:
        chop_up=line.split()
        if return_zaid(chop_up[0],chop_up[2]) == isotope_zaid:
          return   float(chop_up[3])

def return_atoms_per_unit_volume(script_dir, list_of_isotopes,list_of_fractions,density):
  list_of_mass_fractions=[]
  list_of_molar_masses=[]
  for isotope, fraction in zip(list_of_isotopes,list_of_fractions):
    molar_mass_of_isotope = return_molar_mass_of_isotope(isotope, script_dir)
    list_of_molar_masses.append(molar_mass_of_isotope)
    list_of_mass_fractions.append(molar_mass_of_isotope*fraction)
  #print('list_of_fractions',list_of_fractions)
  #print('list_of_molar_masses',list_of_molar_masses)
  #print('list_of_mass_fractions',list_of_mass_fractions)
  total_mass_fraction = sum(list_of_mass_fractions)
  list_of_normalised_mass_fractions=[]
  for fraction in  list_of_mass_fractions:
    list_of_normalised_mass_fractions.append(fraction/total_mass_fraction)
  list_of_grams_per_cm3 = []
  for fraction in list_of_normalised_mass_fractions:
    list_of_grams_per_cm3.append(density*fraction/1000)#density is in kg
  #print('list_of_normalised_mass_fractions',list_of_normalised_mass_fractions)
  #print('list_of_grams_per_cm3',list_of_grams_per_cm3)
  list_of_dv_values=[]
  for molar_mass, grams_per_cm3 in zip(list_of_molar_masses,list_of_grams_per_cm3):
    list_of_dv_values.append((1/((6.022E23*grams_per_cm3)/molar_mass))/1e-24)
  return list_of_dv_values 




def find_material_properties(script_dir, search,Li6_fraction=0.0759):
    materials_dictionary = [
        {"name":"Tungsten", #tungsten pure KINH SDC-IC v3
                          "density":[19298,19291,19279,19267,19254,19242,19229,19217,19204,19191,19178,19165,19152,19139,19125,19112,19098,19084,19070,19056,19042,19014,18985,18956,18926,18895],#checked # mcnp model used 19250
                          "density_temperature":[293.15 ,323.15 ,373.15 ,423.15 ,473.15 ,523.15 ,573.15 ,623.15 ,673.15 ,723.15 ,773.15 ,823.15 ,873.15 ,923.15 ,973.15 ,1023.15,1073.15,1123.15,1173.15,1223.1,1273.15,1373.15,1473.15,1573.15,1673.15,1773.15],#checked
                          "isotopes":[74182,74183,74184,74186],#checked
                          "mass_fractions":[1.6733E-02,9.0295E-03,1.9322E-02,1.7933E-02],#checked
                          "conductivity":[172.8,169.7,164.8,155.5,147.2,139.8,133.1,127.2,122.1, 117.6, 113.7, 110.5, 107.7, 105.4, 103.6, 102.2, 101.1, 100.3, 99.7, 99.4, 99.2, 99.1, 99.1, 99.1, 99, 98.9],                
                          "conductivity_temperatures":[293.15 ,323.15 ,373.15 ,473.15 ,573.15 ,673.15 ,773.15 ,873.15 ,973.15 ,1073.15,1173.15,1273.15,1373.15,1473.15,1573.15,1673.15,1773.15,1873.15,1973.15,2073.15,2173.15,2273.15,2373.15,2473.15,2573.15,2673.15],
                          "youngs_modulus":[397800000000,397700000000,397400000000,396400000000,394800000000,392600000000,390000000000,386700000000,383000000000, 378700000000, 373800000000, 368400000000, 362500000000, 356000000000, 349000000000, 341400000000, 333300000000, 324700000000, 315500000000, 305700000000, 295500000000, 284600000000, 273300000000, 261400000000, 248900000000, 235900000000],
                          "youngs_modulus_temperatures":[293.15 ,323.15 ,373.15 ,473.15 ,573.15 ,673.15 ,773.15 ,873.15 ,973.15 ,1073.15,1173.15,1273.15,1373.15,1473.15,1573.15,1673.15,1773.15,1873.15,1973.15,2073.15,2173.15,2273.15,2373.15,2473.15,2573.15,2673.15],      
                          "coefficient_of_thermal_expansion":[4.5E-06,4.5E-06,4.53E-06,4.58E-06,4.63E-06,4.68E-06,4.72E-06,4.76E-06, 4.81E-06, 4.85E-06, 4.89E-06, 4.98E-06, 5.08E-06, 5.18E-06, 5.3E-06, 5.43E-06, 5.57E-06, 5.74E-06, 5.93E-06, 6.15E-06, 6.4E-06],
                          "coefficient_of_thermal_expansion_temperatures":[293.15 ,373.15 ,473.15 ,573.15 ,673.15 ,773.15 ,873.15 ,973.15 ,1073.15,1173.15,1273.15,1473.15,1673.15,1873.15,2073.15,2273.15,2473.15,2673.15,2873.15,3073.15,3273.15],
                          "poissons_ratio":[0.29],
                          "poissons_ratio_temperature":[24],
                          "specific_heat_capacity":[129,129.9,131.6,134.7,137.8,140.9,143.9,146.8,149.6, 152.4, 155.1, 157.7, 160.3, 162.8, 165.2, 167.5, 169.8, 172.1, 174.2, 176.3, 178.3, 180.3, 182.1, 184, 185.7, 187.4, 189, 190.5, 192, 193.4, 194.7, 196],
                          "specific_heat_capacity_temperatures":[293.15 ,323.15 ,373.15 ,473.15 ,573.15 ,673.15 ,773.15 ,873.15 ,973.15 ,1073.15,1173.15,1273.15,1373.15,1473.15,1573.15,1673.15,1773.15,1873.15,1973.15,2073.15,2173.15,2273.15,2373.15,2473.15,2573.15,2673.15,2773.15,2873.15,2973.15,3073.15,3173.15,3273.15]
       },
       {"name":"Eurofer", #from eurofer ansys xml file
                          "density":[7750,7728,7699,7666,7633,7596,7558],
                          "density_temperature":[293.15 ,373.15 ,473.15 ,573.15 ,673.15 ,773.15 ,873.15 ],
                          "isotopes":[26054,26056,26057,26058,5010,5011,6012,7014,7015,8016,13027,14028,14029,14030,15031,16032,16033,16034,16036,22046,22047,22048,22049,22050,23050,23051,24050,24052,24053,24054,25055,27059,28058,28060,28061,28062,28064,29063,29065,41093,42092,42094,42095,42096,42097,42098,42100,73181,74182,74183,74184,74186],
                          "mass_fractions":[4.56563E-03,6.91110E-02,1.56807E-03,2.05084E-04,9.43123E-07,3.45108E-06,4.14310E-04,1.34911E-04,4.65085E-07,2.95487E-06,7.02121E-06,4.05884E-05,1.98991E-06,1.26804E-06,3.05762E-06,4.21784E-06,3.27443E-08,1.79397E-07,7.89886E-10,8.49986E-08,7.50223E-08,7.27880E-07,5.23259E-08,4.90993E-08,4.651675e-8,0.00001856018,3.70662E-04,6.87292E-03,7.64630E-04,1.86808E-04,4.73931E-04,4.01637E-06,5.56272E-06,2.07132E-06,8.85630E-08,2.77823E-07,6.85423E-08,1.56104E-06,6.74368E-07,2.54802E-06,2.29342E-07,1.39911E-07,2.38263E-07,2.47037E-07,1.39981E-07,3.50081E-07,1.36919E-07,3.14209E-05,7.59071E-05,4.07659E-05,8.68119E-05,7.96842E-05],
                          "conductivity":[28.34,29.2,30.67,30.2,29.33,29.45,31.17],
                          "conductivity_temperatures":[293.15 ,373.15 ,473.15 ,573.15 ,673.15 ,773.15 ,873.15],
                          "youngs_modulus":[217000000000,212000000000,207000000000,203000000000,197000000000,189000000000,178000000000],
                          "youngs_modulus_temperatures":[293.15 ,373.15 ,473.15 ,573.15 ,673.15 ,773.15 ,873.15 ],
                          "coefficient_of_thermal_expansion":[9.09E-06,1.07E-05,1.1E-05,1.12E-05,1.17E-05,1.2E-05,1.23E-05],
                          "coefficient_of_thermal_expansion_temperatures":[293.15 ,373.15 ,473.15 ,573.15 ,673.15 ,773.15 ,873.15],
                          "poissons_ratio":[0.3],
                          "poissons_ratio_temperature":[24],                          
                          "specific_heat_capacity":[448,486,522,551,584,655,801],
                          "specific_heat_capacity_temperatures":[293.15 ,373.15 ,473.15 ,573.15 ,673.15 ,773.15 ,873.15 ]                          
        },
        {"name":"Li4SiO4",
                          "density":[calculate_density_of_material(script_dir, 'Li4SiO4',0.64,0.98,Li6_fraction)],
                          "isotopes":isotopes_from_equation(script_dir, 'Li4SiO4',Li6_fraction),
                          "mass_fractions":mass_fraction_from_equation(script_dir, 'Li4SiO4',Li6_fraction),
                          "tally_multiplier":return_atoms_per_unit_volume(script_dir, isotopes_from_equation(script_dir, 'Li4SiO4',Li6_fraction),mass_fraction_from_equation(script_dir, 'Li4SiO4',Li6_fraction),calculate_density_of_material(script_dir, 'Li4SiO4',0.64,0.98,Li6_fraction))
                         },
        {"name":"Li2TiO3",
                         "density":[calculate_density_of_material(script_dir, 'Li2TiO3',0.64,0.98,Li6_fraction)],
                         "isotopes":isotopes_from_equation(script_dir, 'Li2TiO3',Li6_fraction),
                         "mass_fractions":mass_fraction_from_equation(script_dir, 'Li2TiO3',Li6_fraction),  
                         "tally_multiplier":return_atoms_per_unit_volume(script_dir, isotopes_from_equation(script_dir, 'Li2TiO3',Li6_fraction),mass_fraction_from_equation(script_dir, 'Li2TiO3',Li6_fraction),calculate_density_of_material(script_dir, 'Li2TiO3',0.64,0.98,Li6_fraction))
                         },
        {"name":"Be",
                         #"density":[calculate_density_of_material('Be',0.64,0.98,Li6_fraction)],
                         "density":[i * 0.64 for i in [5,10]],
                         "density_temperature":[5,10],                         
                         "isotopes":isotopes_from_equation(script_dir, 'Be',Li6_fraction),
                         "mass_fractions":mass_fraction_from_equation(script_dir, 'Be',Li6_fraction),
                          "conductivity":[],
                          "conductivity_temperatures":[],
                          "youngs_modulus":[],
                          "youngs_modulus_temperatures":[],
                          "coefficient_of_thermal_expansion":[],
                          "coefficient_of_thermal_expansion_temperatures":[],
                          "poissons_ratio":[],
                          "poissons_ratio_temperature":[24],                          
                          "specific_heat_capacity":[390,393,398,402,407,412,417,422,427,432,437,442,447,452,458],
                          "specific_heat_capacity_temperatures":[0,50,100,150,200,250,300,350,400,450,500,550,600,650,700]   
                         },
        {"name": "Pb84.2Li15.8", #84.2Pb15.8Li    taken from ansys file, conductivity has been increased 10 x to mimick natural convection in stagnabt liquid
                         "density":[10172,9839,9779,9720,9661,9601,9542,9482,9423,9363],
                         "density_temperature":[293.15 ,573.15 ,623.15 ,673.15 ,723.15 ,773.15 ,823.15 ,873.15 ,923.15 ,973.15 ],
                         "isotopes":isotopes_from_equation(script_dir, 'Pb84.2Li15.8',Li6_fraction),
                         "mass_fractions":mass_fraction_from_equation(script_dir, 'Pb84.2Li15.8',Li6_fraction),
                          "conductivity":[7.69 ,13.18, 14.16, 15.14, 16.12, 17.10, 18.08, 19.06, 20.04, 21.02],
                          "conductivity_temperatures":[293.15 ,573.15 ,623.15 ,673.15 ,723.15 ,773.15 ,823.15 ,873.15 ,923.15 ,973.15],
                          "youngs_modulus":[1],
                          "youngs_modulus_temperatures":[24],
                          "coefficient_of_thermal_expansion":[0.0001168,0.000121,0.0001218,0.0001225,0.0001233,0.000124,0.0001248,0.0001255,0.0001263,0.000127],
                          "coefficient_of_thermal_expansion_temperatures":[293.15 ,573.15 ,623.15 ,673.15 ,723.15 ,773.15 ,823.15 ,873.15 ,923.15 ,973.15 ],
                          "poissons_ratio":[0.49999],
                          "poissons_ratio_temperature":[24],                          
                          "specific_heat_capacity":[192,190,186],
                          "specific_heat_capacity_temperatures":[293.15 ,573.15 ,973.15 ],   
                          "tally_multiplier": return_atoms_per_unit_volume(script_dir, isotopes_from_equation(script_dir, 'Pb84.2Li15.8',Li6_fraction),mass_fraction_from_equation(script_dir, 'Pb84.2Li15.8',Li6_fraction),9542)                      
                 } ,     
        {"name": "Homogenous_Magnet",
                         "atom_density":[7.194e-02],
                         "isotopes":[1001,6012,7014,8016,12024,12025,12026,13027,14028,14029,14030,16032,16033,16034,16036,29063,29065,41093,50112,50114,50115,50116,50117,50118,50119,50120,50122,50124,2004,5010,5011,6012,7014,8016,13027,14028,15031,16032,16033,16034,16036,19039,19040,19041,22046,22047,22048,22049,22050,23050,23051,24050,24052,24053,24054,25055,26054,26056,26057,26058,27059,28058,28060,28061,28062,28064,29063,29065,40090,40091,40092,40094,40096,41093,42092,42094,42095,42096,42097,42098,42100,50112,50114,50115,50116,50117,50118,50119,50120,50122,50124,73181,74182,74183,74184,74186,82206,82207,82208,83209,29063,29065,50112,50114,50115,50116,50117,50118,50119,50120,50122,50124],
                         "mass_fractions":[3.89340E-03,3.40560E-03,3.70800E-04,4.87080E-03,1.69197E-04,2.14200E-05,2.35834E-05,7.07400E-04,1.32800E-03,6.72000E-05,4.46000E-03,8.71457E-05,6.97680E-07,3.93822E-06,1.83600E-08,6.83585E-03,3.05684E-03,1.18439E-03,3.82953E-06,2.60566E-06,1.34231E-06,5.74035E-05,3.03204E-05,9.56198E-05,3.39131E-05,1.28625E-04,1.82791E-05,2.28587E-05,3.08888E-03,4.06294E-07,1.48738E-06,1.70203E-04,2.77382E-04,2.55621E-06,2.27302E-04,7.27891E-05,1.65004E-05,8.47338E-07,6.78371E-09,3.82922E-08,1.78519E-10,2.43807E-07,3.05877E-11,1.75950E-08,1.40904E-06,1.27070E-06,1.259086E-05,9.23990E-07,8.84708E-07,4.013075e-9,0.00000160121,3.03427E-04,5.67045E-03,6.34294E-04,1.55150E-04,5.58169E-04,1.46579E-03,2.21899E-02,5.16004E-04,7.24415E-05,1.73444E-05,2.89354E-03,1.07976E-03,5.07463E-05,1.46193E-04,4.48851E-05,2.24477E-05,9.72920E-06,2.30510E-07,5.02686E-08,7.68366E-08,7.78671E-08,1.25448E-08,1.21022E-05,6.32488E-05,3.94240E-05,6.78518E-05,7.10910E-05,4.24074E-05,1.02843E-04,4.10435E-05,3.34089E-09,2.27319E-09,1.17103E-09,5.00790E-08,2.64516E-08,8.34190E-08,2.95859E-08,1.12213E-07,1.59467E-08,1.99420E-08,5.64891E-08,2.96623E-08,1.60908E-08,3.40070E-08,3.12220E-08,1.78732E-08,1.78578E-08,4.19446E-08,7.82589E-08,3.38912E-03,1.51554E-03,2.54666E-06,1.73278E-06,8.92643E-07,3.81736E-05,2.01632E-05,6.35877E-05,2.25524E-05,8.55362E-05,1.21557E-05,1.52012E-0]
                 },
        {"name": "Plasma", 
                          "atom_density":[1e-20],
                          "isotopes":[1002, 1003],
                          "mass_fractions": [0.5, 0.5]
                 },
        {"name": "Li-6",
                          "atom_density":[1],
                          "isotopes":[3006],
                          "mass_fractions":[1]},
        {"name": "Li-7",
                          "atom_density":[1],
                          "isotopes":[3007],
                          "mass_fractions":[1]},

        {"name": "SS-316L-IG",
                         "atom_density":[8.58301E-02],
                         "density":[7930],
                         "isotopes":[26054,26056,26057,26058, 6012,25055,14028,14029,14030,15031,16032,16033,16034,16036,24050,24052,24053,24054,28058,28060,28061,28062,28064,42092,42094,42095,42096,42097,42098,42100, 7014, 7015, 5010, 5011,29063,29065,27059,41093,22046,22047,22048,22049,22050,73181],
                         "mass_fractions":[3.29181E-03,4.98289E-02,1.13058E-03,1.47865E-04,1.19277E-04,1.73653E-03,7.86496E-04,3.85593E-05,2.45713E-05,3.85117E-05,1.41667E-05,1.09980E-07,6.02549E-07,2.65303E-09,7.46975E-04,1.38506E-02,1.54092E-03,3.76464E-04,7.00641E-03,2.60890E-03,1.11548E-04,3.49927E-04,8.63311E-05,2.07981E-04,1.26880E-04,2.16071E-04,2.24028E-04,1.26943E-04,3.17475E-04,1.24166E-04,2.71878E-04,9.37261E-07,9.50314E-07,3.47739E-06,1.57294E-04,6.79509E-05,4.04699E-05,5.13489E-06,8.56466E-06,7.55943E-06,7.33429E-05,5.27248E-06,4.94736E-06,2.63837E-06]
                 },

        {"name": "0.6_SS-316L-IG_0.4_H2O",
                         "atom_density":[9.16106E-02],
                         "density":[5158],
                         "isotopes":[26054,26056,26057,26058, 6012,25055,14028,14029,14030,15031,16032,16033,16034,16036,24050,24052,24053,24054,28058,28060,28061,28062,28064,42092,42094,42095,42096,42097,42098,42100, 7014, 7015, 5010, 5011,29063,29065,27059,41093,22046,22047,22048,22049,22050,73181, 1001, 1002, 8016],
                         "mass_fractions":[1.97509E-03,2.98973E-02,6.78346E-04,8.87190E-05,7.15661E-05,1.04192E-03,4.71898E-04,2.31355E-05,1.47428E-05,2.31070E-05,8.49999E-06,6.59880E-08,3.61529E-07,1.59182E-09,4.48185E-04,8.31039E-03,9.24551E-04,2.25879E-04,4.20385E-03,1.56534E-03,6.69286E-05,2.09956E-04,5.17987E-05,1.24789E-04,7.61277E-05,1.29643E-04,1.34417E-04,7.61659E-05,1.90485E-04,7.44998E-05,1.63127E-04,5.62356E-07,5.70188E-07,2.08644E-06,9.43765E-05,4.07706E-05,2.42819E-05,3.08093E-06,5.13879E-06,4.53566E-06,4.40057E-05,3.16349E-06,2.96842E-06,1.58302E-06,2.67614E-02,1.53896E-06,1.33497E-02]
                 },
        {"name": "H2O",
                          "density" : [1000],
                          "isotopes": [1001, 1002, 8016],
                          "mass_fractions": [2.67614E-02,1.53896E-06,1.33497E-02]
                  }
    ]
    if not any(d['name'] == search for d in materials_dictionary):
        return  {"name":search,"density":'Material not found in database',"isotopes":['Material not found in database'],"mass_fractions":['Material not found in database'],"conductivity":['Material not found in database'],"conductivity_temperatures":['Material not found in database'],"specific_heat_capacity":['Material not found in database'],"specific_heat_capacity_temperatures":['Material not found in database']}
    for l in materials_dictionary:
        if l['name'] == search:
            match = l
            break
        else:
            match = None
    return match
    

if __name__ == "__main__":
    name = 'Pb84.2Li15.8'
    result = find_material_properties(script_dir, name,0.9)
    property= "isotopes"
    #print(property,result[property])  
    property= "mass_fractions"   
    #print(property,result[property]) 
    property= "density"
    #print(property,result[property]) 
    property= "tally_multiplier"
    #print(property,result[property])

    print()

    #name = 'Li4SiO4'
    #result = find_material_properties(name,0.6)
    #property= "isotopes"
    #print(property,result[property])  
    #property= "mass_fractions"   
    #print(property,result[property]) 
    #property= "density"
    #print(property,result[property]) 
    #property= "tally_multiplier"
    #print(property,result[property])    
    
    #print()
#
    name = 'Tungsten'
    result = find_material_properties(script_dir, name)
    property= "isotopes"
    #print(property,result[property])  
    property= "mass_fractions"   
    #print(property,result[property]) 
    property= "density"
    #print(property,result[property]) 

    name = 'Eurofer'
    result = find_material_properties(script_dir, name)
    property= "isotopes"
    #print(property,result[property])  
    property= "mass_fractions"   
    #print(property,result[property]) 
    property= "density"
    #print(property,result[property]) 
    
    #
