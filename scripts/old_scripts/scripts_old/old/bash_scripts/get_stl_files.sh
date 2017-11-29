cd '~/Documents/CCFE_project_work'

echo 'Deleting original files from stl_files'

rm -r ~/Documents/CCFE_project_work/project_serpent/stl_files/*

cp Nova/Geometry/* ~/Documents/CCFE_project_work/project_serpent/stl_files/tf_coils
cp Nova/nova/Blankets/SN* ~/Documents/CCFE_project_work/project_serpent/stl_files/tf_coils

echo 'All files from Nova/Geometry and Nova/..../SN moved to stl_files'