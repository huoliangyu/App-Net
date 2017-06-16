trap "exit" INT

# number of runs (same client start times)
num_runs_inner=1
# number of runs (different client start times)
num_runs_outer=5
# parameter for EWMA
alpha=0.8
# bandwidth configured at the router
bw=1440
# timeinterval beteween network probes
sleep_time=1.0

for big_run in `eval echo {1..$num_runs_outer}`;do

        folder_outer='baseline/run_'$big_run

	#############################################################################################

	#set the bandwidth value in network control
	einh='kbit'
	value=$bw$einh
	echo $value
	var="GW_bandwidth = {\"GW1\" : \"$value\"}"
	echo $var
	sed -i "26s/.*/$var/" ../trash/tcPRIOHTBConfig.py

        for small_run in `eval echo {1..$num_runs_inner}`;do
                echo "Performing baseline"
                folder_inner='baseline/bw_'$bw
                complete_folder=$folder_outer/$folder_inner
		mkdir -p $complete_folder
		sudo -S xterm -e "timeout 600s python networkControl.py"&
		sleep 5
		xterm -hold -e "timeout 600s python networkEntity.py "$complete_folder" "$sleep_time" "$alpha&
                echo $complete_folder
                (sleep 600;killall xterm)
		sleep 5

		sleep 10
        done

	#############################################################################################
	
done
