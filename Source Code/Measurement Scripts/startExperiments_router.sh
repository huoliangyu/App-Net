trap "exit" INT

source config

while getopts b:m:i:h:l:g:a option
do
 case "${option}"
 in
 b) bandwidth_pattern=${OPTARG};;
 m) mechanism=${OPTARG};;
 i) exp_id=${OPTARG};;
 h) high=${OPTARG};;
 l) low=${OPTARG};;
 g) granularity=${OPTARG};;
 a) alpha=${OPTARG};;
 esac
done

if [ -z "$alpha" ];
then 
        alpha=0.8
fi

#all strings to non-capital letters
mechanism=$(echo "$mechanism" | tr '[:upper:]' '[:lower:]')
bandwidth_pattern=$(echo "$bandwidth_pattern" | tr '[:upper:]' '[:lower:]')
exp_id=$(echo "$exp_id" | tr '[:upper:]' '[:lower:]')


for run in `eval echo {1..$num_runs}`;do

	n_folder='Experiments/'$exp_id'/'$mechanism'/'$bandwidth_pattern'/run_'$run
	

	#set the bandwidth value
	einh='kbit'
	value=$high$einh
	echo $value
	var="GW_bandwidth = {\"GW1\" : \"$value\"}"
	echo $var
        
   	#replace the line in trash-config which indicates the bandwidth limit
	sed -i "26s/.*/$var/" ../trash/tcPRIOHTBConfig.py
        
        mkdir -p $n_folder
				
        xterm -hold -e "timeout 600s python networkControl.py" "$bandwidth_pattern" "$high" "$low" "$mechanism"
                
	sleep 5
	sudo -X xterm -e "timeout 600s python networkMonitoring.py" "$n_folder" "$granularity" "$alpha" "$mechanism" 
        (sleep 450;killall xterm)
	sleep 5


	sleep 10



done


