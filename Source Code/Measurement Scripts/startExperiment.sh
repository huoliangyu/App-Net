trap "exit" INT

while getopts b:m:i: option
do
 case "${option}"
 in
 b) bandwidth_pattern=${OPTARG};;
 m) mechanism=${OPTARG};;
 i) exp_id=${OPTARG};;
 esac
done

echo $bandwidth_pattern
echo $mechanism
echo $exp_id

source config

#all strings to non-capital letters
mechanism=$(echo "$mechanism" | tr '[:upper:]' '[:lower:]')
bandwidth_pattern=$(echo "$bandwidth_pattern" | tr '[:upper:]' '[:lower:]')
exp_id=$(echo "$exp_id" | tr '[:upper:]' '[:lower:]')

for big_run in `eval echo {1..$num_runs_outer}`;do
	folder_outer='Experiments/'$exp_id'/'$mechanism'/'$bandwidth_pattern'/run_'$big_run
	mkdir -p $folder_outer


	#test='Comparison_Experiments/Experiment1/baseline/fixed_bw/run_'$big_run'/config'
	#test='mumu/fixed_bw/nm_network_only/run_'$big_run'/config'

	#var=$(<$test)
	#arr=($var)
	#echo "the config is "$test

	#compute the starting time points for each of the clients
	for value in {1..6};do
		#starttime[$value]=${arr[`expr $value - 1`]}
		starttime[$value]=$(( $RANDOM % ($MAX + 1 - $MIN) + $MIN ))
		zmqPort[$value]=$(($INITPORT + $value))
		echo ${starttime[$value]}
		echo ${zmqPort[$value]}
	done

	start_time_HQ1=${starttime[1]}
	start_time_HQ2=${starttime[2]}
	start_time_MQ1=${starttime[3]}
	start_time_MQ2=${starttime[4]}
	start_time_LQ1=${starttime[5]}
	start_time_LQ2=${starttime[6]}

	zmq_port_HQ1=${zmqPort[1]}
	zmq_port_HQ2=${zmqPort[2]}
	zmq_port_MQ1=${zmqPort[3]}
	zmq_port_MQ2=${zmqPort[4]}
	zmq_port_LQ1=${zmqPort[5]}
	zmq_port_LQ2=${zmqPort[6]}

	
	echo ${starttime[*]}
	echo "${starttime[*]}" > "$folder_outer/config"

	########################################################################################################

	for small_run in `eval echo {1..$num_runs_inner}`;do
		sleep 5
		echo "Performing "$mechanism
		folder_inner='bw_'$bw
		complete_folder=$folder_outer/$folder_inner
		echo "Logging to folder:" $complete_folder
	
		if [ "$mechanism" == "baseline" ]
		then 
			timeout 450s bash baselineExperiment.bash ${starttime[*]} $complete_folder 
		elif [ "$mechanisms" == "nade" ]
		then 
			timeout 450s bash nadeExperiment.bash ${starttime[*]} ${zmqPort[*]} $complete_folder $bw $bw_usage $complete_folder

		elif [ "$mechanism" == "qoeff" ]
		then
			timeout 450s bash qoeffExperiment.bash ${starttime[*]} ${zmqPort[*]} $complete_folder $bw $bw_usage  $complete_folder
 		elif [ "$mechanism" == "spm" ]
		then 
			timeout 450s bash spmExperiment.bash ${starttime[*]} ${zmqPort[*]} $complete_folder $dt_margin $bw 
		
		else 
			echo "Mechanism unknown!"
			break 
		fi		
		sleep 5

        done
	echo "done"

	sleep 10


done






