#! /usr/bin/bash
echo "Hello World"

if [ $# -ne 2 ]
    then
        echo "Script requires 2 argument, closing"
        exit 0
fi

echo "Entered arg is $@"

for x in $@
do
    echo "Entered arg is $@"
done

scp -r eraguzin@silicon.inst.bnl.gov:/u/home/eraguzin/matlab/$1 ~/nextcloud/LuSEE/matlab_transfer
#mkdir -p ~/nextcloud/LuSEE/matlab_transfer/$1/libero_proj
/usr/local/microchip/Libero_SoC_v2022.2/Libero/bin64/libero script:libero_matlab_setup.tcl "script_args:$1 $2" logfile:make_libero.log

data_files=$(find ~/nextcloud/LuSEE/matlab_transfer/$1/codegen/$2/hdlsrc -type f -name "*.dat")
for file in $data_files
    do
        echo "Moving $file"
        mv $file ~/nextcloud/LuSEE/matlab_transfer/$1/libero_proj/simulation
    done

export LM_LICENSE_FILE=1702@iolicense2.inst.bnl.gov:7180@iolicense2.inst.bnl.gov:7184@iolicense2.inst.bnl.gov
/usr/local/microchip/Libero_SoC_v2022.2/Libero/bin/libero
