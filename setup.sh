sudo apt-get install wget
sudo apt-get install unzip
wget https://bootstrap.pypa.io/get-pip.py
sudo python3 get-pip.py

curl https://raw.githubusercontent.com/GoogleCloudPlatform/compute-gpu-installation/main/linux/install_gpu_driver.py --output install_gpu_driver.py
sudo python3 install_gpu_driver.py