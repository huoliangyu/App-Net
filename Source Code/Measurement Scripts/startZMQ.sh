logger "logger1"

folder=/home/client2/Master-Praktikum/Praktikum-Code/Experiment/$1
echo "folder is" $folder&
mkdir -p $folder&

xterm -hold -e "python messageBroker.py "$folder



