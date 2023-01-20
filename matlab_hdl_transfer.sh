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
#./matlab_hdl_transfer.sh --scp_source eraguzin@silicon.inst.bnl.gov:/u/home/eraguzin/matlab/LNspec/matlab --local_project ~/nextcloud/LuSEE/matlab_transfer --directory matlab_chain2_script --file weight_streamer --create --open

#If you need to tell the user how to use the command
PROGNAME=$0
usage() {
  cat << EOF >&2
Usage: $PROGNAME [-s <scp_source>] [-l <local_source>] [-d <directory>]

-s <scp_source>: Location of the Matlab folder that needs to be brought locally. Example: eraguzin@silicon.inst.bnl.gov:/u/home/eraguzin/matlab/
-l <local_project>: Location on this computer where you want to bring the Matlab folder. Example: ~/nextcloud/LuSEE/matlab_transfer
-d <directory>: If starting this without SCP mode, you need the local project location and a subdirectory where the specific project is (for example, we have "basic" and "matlab" in the LNspec folder)
-f <file>: Each Matlab project can have multiple modules that are generated. Name the one you want to make the Libero project out of. Example: sfft
-m <move>: Flag to SCP over the Matlab files
-c <create>: Flag to create a Libero project
-o <open>: Flag to open the Libero project at the end

So for example, with only the -m flag and -s and -l, you can simply SSH over everything. If the files already exist, with -l, -d, -f, and -c you can create the Libero project locally with no SCP connection. And use -o to open Libero at the end.
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

while getopts :-:s:l:d:f:cm x; do
  case $x in
    -)
            case "${OPTARG}" in
                scp_source)
                    #Has to manually get the next indexed argument
                    check_for_argument true ${!OPTIND} "scp_source"
                    scp_source="${!OPTIND}"
                    echo "SCP Source will be" $scp_source
                    #Need to manually shift after getting argument because of hacky way to have two dash arguments
                    shift 1
                    ;;

                local_project)
                    check_for_argument true ${!OPTIND} "local_project"
                    local_project="${!OPTIND}"
                    echo "Local Project location will be" $local_project
                    shift 1
                    ;;

                directory)
                    check_for_argument true ${!OPTIND} "directory"
                    directory="${!OPTIND}"
                    echo "Directory location will be" $directory
                    shift 1
                    ;;

                file) file="${!OPTIND}"
                    check_for_argument true ${!OPTIND} "file"
                    file="${!OPTIND}"
                    echo "Main Libero file name will be" $file
                    shift 1
                    ;;

                create)
                    check_for_argument false ${!OPTIND} "create"
                    echo "Will create libero project"
                    create=true
                    ;;

                move)
                    check_for_argument false ${!OPTIND} "move"
                    echo "Will SCP Matlab project"
                    move=true
                    ;;

                open)
                    check_for_argument false ${!OPTIND} "open"
                    echo "Will open Libero at end"
                    open=true
                    ;;
                *) usage
            esac;;

    s)
        check_for_argument true $OPTARG "scp_source"
        scp_source=$OPTARG
        echo "SCP Source will be" $scp_source
        ;;

    l)
        check_for_argument true $OPTARG "local_project"
        local_project=$OPTARG
        echo "Local Project will be" $local_project
        ;;

    d)
        check_for_argument true $OPTARG "directory"
        directory=$OPTARG
        echo "Directory location will be" $directory
        ;;

    f)
        check_for_argument true $OPTARG "file"
        file=$OPTARG
        echo "Main Libero file name will be" $file
        ;;

    c)
        echo "Will create libero project"
        create=true
        ;;

    m)
        echo "Will SCP Matlab project"
        move=true
        ;;

    o)
        echo "Will open Libero at the end"
        open=true
        ;;

    *) usage
  esac
done

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
#Set up directory structure
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------

if [ $directory != none ]
    then
        location_to_send=$local_project/$directory
    else
        if [ $scp_source != none ]
        then
            #https://unix.stackexchange.com/questions/247560/print-everything-after-a-slash
            #https://stackoverflow.com/questions/4651437/how-do-i-set-a-variable-to-the-output-of-a-command-in-bash
            directory=$(echo $scp_source | sed 's:.*/::')
            echo "Directory is now" $directory
            location_to_send=$local_project/$directory
        else
            location_to_send=$local_project
        fi
fi

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
#Do the scp if necessary
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------

if [ $move == true ]
then
    if  [ $scp_source != none ] && [ $local_project != none ]
    then
        echo "--------------------------------------------------------------------------------------------------------------"
        echo "SCP INITIALIZING"
        scp -pr $scp_source $location_to_send
        echo "SCP FINISHED"
        echo "--------------------------------------------------------------------------------------------------------------"
        echo "ZIPPING UP VHDL FILES"
        #https://stackoverflow.com/questions/75177035/gnu-linux-proper-use-of-the-zip-command-to-flatten-the-subdirectories/75180778#75180778
        (cd $local_project/$directory/codegen; zip -r - . -i '*.vhd') > $local_project/$directory/$directory.zip
        #zip -r $local_project/$directory . -i $directory/codegen/*/hdlsrc/*.vhd
        echo "ZIPPING FINISHED"
        echo "--------------------------------------------------------------------------------------------------------------"

    else
        echo "You need to specify a source and destination for the SCP to move files over"
    fi
fi

if [ $create == false ]
then
    echo "Finished"
    exit 0
else
    if [ $local_project == none ] || [ $file == none ];
    then
        echo "You need to specify a local project directory and file name"
        exit 0
    fi
fi

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
#Start the Libero project, run that TCL file
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
export LM_LICENSE_FILE=1702@iolicense2.inst.bnl.gov:7180@iolicense2.inst.bnl.gov:7184@iolicense2.inst.bnl.gov

echo "--------------------------------------------------------------------------------------------------------------"
echo "TCL SCRIPT INITIALIZING"

/usr/local/microchip/Libero_SoC_v2022.2/Libero/bin64/libero script:libero_matlab_setup.tcl "script_args:$location_to_send $file" logfile:make_libero.log

echo "TCL SCRIPT FINISHED"
echo "--------------------------------------------------------------------------------------------------------------"

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
#Start Libero
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
if [ $open == true ]
then
    echo "--------------------------------------------------------------------------------------------------------------"
    echo "STARTING LIBERO"

    /usr/local/microchip/Libero_SoC_v2022.2/Libero/bin/libero

    echo "LIBERO CLOSED"
    echo "--------------------------------------------------------------------------------------------------------------"
fi
