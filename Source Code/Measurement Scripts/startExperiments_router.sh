trap "exit" INT

MIN=0
MAX=60
INITPORT=9000
num_runs_inner=40
num_runs_outer=15
alpha=0.8
bw=1440

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


for big_run in `eval echo {1..$num_runs_outer}`;do

	folder_outer='Experiments/'$exp_id'/'$mechanism'/'$bandwidth_pattern'/run_'$big_run
	

	#############################################################################################

	
	sleep_time=1.0
	sleep_time1=2.0
	sleep_time2=6.0

	#set the bandwidth value
	einh='kbit'
	value=$bw$einh
	echo $value
	var="GW_bandwidth = {\"GW1\" : \"$value\"}"
	echo $var
        
        #replace the line in trash-config which indicates the bandwidth limit
	sed -i "26s/.*/$var/" ../trash/tcPRIOHTBConfig.py

        for small_run in `eval echo {1..$num_runs_inner}`;do
                
                folder_inner='bw_'$bw
                complete_folder=$folder_outer/$folder_inner
                
		if [ "$mechanism" == "baseline" ]
                then
                        echo "Performing baseline"
                        sudo -S xterm -e "timeout 600s python networkControl.py"& 
                        sleep 5
                        xterm -hold -e "timeout 600s python networkEntity.py "$complete_folder" "$granularity" "$alpha&
                
                elif [ "$mechanism" == "nade" ] 
                then
                        echo "Performing NADE"
                        xterm -hold -e "timeout 450s python networkControl_nade.py $complete_folder $bw"&
                        sleep 5
                        xterm -hold -e "timeout 450s python networkEntity_nade.py "$complete_folder" "$sleep_time" "$alpha&
                        xterm -hold -e "timeout 450s python networkEntity2_nade.py "$complete_folder" "$sleep_time_fix" "$alpha&
                
                
                elif [ "$mechanism" == "qoeff" ]
                then 
                        echo "Performing QoE-FF"
                        xterm -hold -e "timeout 450s python networkControl_mumu.py $complete_folder"&
                        xterm -hold -e "timeout 450s python networkEntity.py "$complete_folder" "$sleep_time_fix" "$alpha&
                fi
                
                elif [ "$mechanism" == "spm" ]
                then
                        echo "Performing SPM"
                        xterm -hold -e "timeout 450s python networkControl_petrangeli.py $complete_folder"&"
                        xterm -hold -e "timeout 450s python networkEntity.py "$complete_folder" "$sleep_time_fix" "$alpha&
                fi
                sleep 450;killall xterm
                sleep 5
                        
                echo "Performing baseline"
                folder_inner='bw_'$bw
                complete_folder=$folder_outer/$folder_inner
                mkdir -p $complete_folder
		sleep 5
                xterm -hold -e "timeout 450s python networkEntity_petrangeli.py "$complete_folder" "$sleep_time1" "$alpha&
	        echo $complete_folder
                (sleep 450;killall xterm)
		sleep 5
        done

	sleep 10



done
