#! /usr/bin/bash

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
#Parse the input arguments
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------

#Example values
#scp_source=eraguzin@silicon.inst.bnl.gov:/u/home/eraguzin/matlab/
#local_project=~/nextcloud/LuSEE/matlab_transfer
#directory=matlab
#file=sfft
#create=true
#move=true

#Options parser
#https://unix.stackexchange.com/questions/321126/dash-arguments-to-shell-scripts

#Example input:
#./matlab_hdl_transfer.sh --scp_source eraguzin@silicon.inst.bnl.gov:/u/home/eraguzin/matlab/LNspec/matlab --local_project ~/nextcloud/LuSEE/matlab_transfer --directory matlab_chain2_script --file weight_streamer --move --create --open

#If you need to tell the user how to use the command
PROGNAME=$0
usage() {
  cat << EOF >&2
Usage: $PROGNAME [-i <input>] [-o <output>]

-i <input>: Location of the HDL source file that will be cleaned up and zipped
-o <output>: Location where the output file should be zipped to

EOF
  exit 1
}

#Checks that there is or isn't an argument as appropriate
check_for_argument() {
    if [ $1 == true ];
    then
        if [ "${2::1}" == "-" ];
        then
            echo "$3 command requires an argument!"
            usage
        fi
    else

        #If it's the last one then $3 will be empty. If it isn't, the next "argument" should be the next command
        if [ "${2::1}" != "-" ] && [ ! -z "$3" ];
        then
            echo "$3 command does not take any arguments!"
            usage
        fi
    fi
}

#Parse the arguments
scp_source=none
local_project=none
directory=none
file=none
create=false
move=false
open=false

#Parse with long arguments
#https://stackoverflow.com/a/7680682

while getopts :-:i:o: x; do
  case $x in
    -)
            case "${OPTARG}" in
                input)
                    #Has to manually get the next indexed argument
                    check_for_argument true ${!OPTIND} "input"
                    input="${!OPTIND}"
                    echo "Path to HDL source directory input will be" $input
                    #Need to manually shift after getting argument because of hacky way to have two dash arguments
                    shift 1
                    ;;

                output)
                    check_for_argument true ${!OPTIND} "output"
                    output="${!OPTIND}"
                    echo "Output zip file location will be" $output
                    shift 1
                    ;;
                *) usage
            esac;;

    i)
        check_for_argument true $OPTARG "input"
        input=$OPTARG
        echo "Path to HDL source directory input will be" $input
        ;;

    o)
        check_for_argument true $OPTARG "output"
        output=$OPTARG
        echo "Output zip file location will be" $output
        ;;
    *) usage
  esac
done

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
#Clean up the HDL Source directory
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
#Zip it up to the output
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
