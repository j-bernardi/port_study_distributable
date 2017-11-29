#An install script for Serpent 2 (dependent on having files found ~10 lines down)

sudo apt-get install libgd2-noxpm-dev -f
sudo apt-get install build-essential -f
sudo apt-get install dos2unix -f

sudo mkdir /opt/serpent2
sudo mkdir /opt/serpent2/src

#these two files should have been previously downloaded
sudo tar -xzf Serpent2.tar.gz -C /opt/serpent2/src
sudo tar -xzf sssup2.1.29.tar.gz -C /opt/serpent2/src

cd /opt/serpent2/src 
sudo wget -O usersrc.c https://s3-us-west-2.amazonaws.com/shimwellstorage/ssh/usersrc.c
sudo make
sudo cp sss2 /bin
cd /opt/serpent2


#nuclear data download unzip
sudo wget https://www-nds.iaea.org/fendl/data/neutron/fendl31b-neutron-ace.zip
sudo mkdir /opt/serpent2/FENDL3.1b
sudo wget https://www.oecd-nea.org/dbforms/data/eva/evatapes/jeff_32/Processed/JEFF32-ACE-293K.tar.gz
sudo mkdir /opt/serpent2/FENDL3.1b
sudo mkdir /opt/serpent2/JEFF32-ACE-293K
sudo unzip fendl31b-neutron-ace.zip -d /opt/serpent2/FENDL3.1b
sudo tar -xzf JEFF32-ACE-293K.tar.gz -C /opt/serpent2/JEFF32-ACE-293K
cd /opt/serpent2/FENDL3.1b
sudo dos2unix *
cd /opt/serpent2/JEFF32-ACE-293K
sudo dos2unix *



cd /opt/serpent2
# downloads nuclear transmutation data from https://www.oecd-nea.org/dbdata/data/nds_eval_libs.htm
sudo mkdir /opt/serpent2/xs
cd /opt/serpent2/xs
sudo wget https://www.oecd-nea.org/dbforms/data/eva/evatapes/jeff_31/JEFF31/JEFF31RDD.ASC
sudo wget https://www.oecd-nea.org/dbforms/data/eva/evatapes/jeff_31/JEFF31/JEFF31NFY.ASC
sudo wget https://www.oecd-nea.org/dbforms/data/eva/evatapes/jeff_31/JEFF31/JEFF31SFY.ASC
sudo wget https://www.oecd-nea.org/dbforms/data/eva/evatapes/jeff_31/JEFF31/JEFF31A.ASC
cd /opt/serpent2

sudo wget -O xsdir.serp https://s3-us-west-2.amazonaws.com/shimwellstorage/ssh/xsdir.serp

