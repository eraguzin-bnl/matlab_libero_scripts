# Microsemi Tcl Script
# libero
# Date: Wed Nov 23 15:33:55 2022
# Will start up libero with the exported Matlab files
puts "Welcome to Eric's Matlab TCL script"
set folder_name [lindex $argv 0]
puts "Folder name is $folder_name"
set location "/home/eraguzin/nextcloud/LuSEE/matlab_transfer/$folder_name/libero_proj"
puts "Location is $location"

puts "Number is $argc"

set file_name [lindex $argv 1]
puts "File name is $file_name"
set file1 "/home/eraguzin/nextcloud/LuSEE/matlab_transfer/$folder_name/codegen/$file_name/hdlsrc/$file_name\_fixpt.vhd"
puts "File location is $file1"
set file2 "/home/eraguzin/nextcloud/LuSEE/matlab_transfer/$folder_name/codegen/$file_name/hdlsrc/$file_name\_fixpt_pkg.vhd"
puts "File location is $file2"
set file3 "/home/eraguzin/nextcloud/LuSEE/matlab_transfer/$folder_name/codegen/$file_name/hdlsrc/$file_name\_fixpt_tb.vhd"
puts "File location is $file3"
set file4 "/home/eraguzin/nextcloud/LuSEE/matlab_transfer/$folder_name/codegen/$file_name/hdlsrc/$file_name\_fixpt_tb_pkg.vhd"
puts "File location is $file4"
set root "$file_name\_fixpt"
puts "Root is $root"
set file5 "/home/eraguzin/nextcloud/LuSEE/matlab_transfer/$folder_name/libero_proj/stimulus/$file_name\_fixpt_tb.vhd"
puts "File location is $file5"
set file6 "/home/eraguzin/nextcloud/LuSEE/matlab_transfer/$folder_name/libero_proj/stimulus/$file_name\_fixpt_tb_pkg.vhd"
puts "File location is $file6"
set tb_name "$file_name\_fixpt_tb"
puts "Testbench name is $tb_name"

new_project -location $location -name {libero_proj} -project_description {} -block_mode 0 -standalone_peripheral_initialization 0 -instantiate_in_smartdesign 1 -ondemand_build_dh 1 -use_relative_path 0 -linked_files_root_dir_env {} -hdl {VHDL} -family {PolarFire} -die {MPF300T} -package {FCG1152} -speed {-1} -die_voltage {1.0} -part_range {EXT} -adv_options {IO_DEFT_STD:LVCMOS 1.8V} -adv_options {RESTRICTPROBEPINS:1} -adv_options {RESTRICTSPIPINS:0} -adv_options {SYSTEM_CONTROLLER_SUSPEND_MODE:0} -adv_options {TEMPR:EXT} -adv_options {VCCI_1.2_VOLTR:EXT} -adv_options {VCCI_1.5_VOLTR:EXT} -adv_options {VCCI_1.8_VOLTR:EXT} -adv_options {VCCI_2.5_VOLTR:EXT} -adv_options {VCCI_3.3_VOLTR:EXT} -adv_options {VOLTR:EXT}
set_device -family {PolarFire} -die {MPF300T} -package {FCG1152} -speed {-1} -die_voltage {1.0} -part_range {EXT} -adv_options {IO_DEFT_STD:LVCMOS 1.8V} -adv_options {RESTRICTPROBEPINS:1} -adv_options {RESTRICTSPIPINS:0} -adv_options {SYSTEM_CONTROLLER_SUSPEND_MODE:0} -adv_options {TEMPR:EXT} -adv_options {VCCI_1.2_VOLTR:EXT} -adv_options {VCCI_1.5_VOLTR:EXT} -adv_options {VCCI_1.8_VOLTR:EXT} -adv_options {VCCI_2.5_VOLTR:EXT} -adv_options {VCCI_3.3_VOLTR:EXT} -adv_options {VOLTR:EXT} 
import_files \
         -convert_EDN_to_HDL 0 \
         -library {work} \
         -hdl_source $file1

import_files \
         -convert_EDN_to_HDL 0 \
         -library {work} \
         -hdl_source $file2

import_files \
         -convert_EDN_to_HDL 0 \
         -library {work} \
         -stimulus $file3

import_files \
         -convert_EDN_to_HDL 0 \
         -library {work} \
         -stimulus $file4

build_design_hierarchy
set_root -module $root\::work
organize_tool_files -tool {SIM_PRESYNTH} -file $file6 -file $file5 -module $root\::work -input_type {stimulus}
organize_tool_files -tool {SIM_POSTSYNTH} -file $file6 -file $file5 -module $root\::work -input_type {stimulus}
organize_tool_files -tool {SIM_POSTLAYOUT} -file $file6 -file $file5 -module $root\::work -input_type {stimulus}
set_modelsim_options -tb_module_name $tb_name
save_project
#run_tool -name {SIM_PRESYNTH}
#run_tool -name {SYNTHESIZE}
#save_project
