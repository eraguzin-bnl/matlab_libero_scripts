# Microsemi Tcl Script
# libero
# Date: Wed Nov 23 15:33:55 2022
# Will start up libero with the exported Matlab files

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
#Get all directory values
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------

puts "Welcome to Eric's Matlab Setup TCL script"
set directory_path [lindex $argv 0]
set module [lindex $argv 1]
puts "Directory Path is $directory_path"
set project_name "libero_proj_$module"
set location "$directory_path/$project_name"
puts "Location is $location"
set hdl_location "$directory_path/codegen/$module/hdlsrc/"
puts "File name is $module"
set root "$module\_fixpt"
puts "Root is $root"
set tb_name "$module\_fixpt_tb"
puts "Testbench name is $tb_name"

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
#Get all files with certain extensions
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------

#Get all files with .dat extension. Needed for simulation
set dat_files [list]
lappend dat_files {*}[glob -dir $hdl_location *.dat]
#puts "dat_files are $dat_files"

#Get all files with _tb text. Needed for simulation
set tb_pkg_file [glob -dir $hdl_location *_tb_pkg.vhd]
set tb_file [glob -dir $hdl_location *_tb.vhd]
#puts "tb_files are $tb_file"
#puts "tb_pkg files are $tb_pkg_file"

#Get all VHDL files
set vhdl_files [list]
lappend vhdl_files {*}[glob -dir $hdl_location *.vhd]

#Remove the test bench files from the list of VHDL files
set idx [lsearch $vhdl_files $tb_pkg_file]
set vhdl_files [lreplace $vhdl_files $idx $idx]

set idx [lsearch $vhdl_files $tb_file]
set vhdl_files [lreplace $vhdl_files $idx $idx]

set tb_pkg_project_file "$location/stimulus/$module\_fixpt_tb_pkg.vhd"
puts "File location is $tb_pkg_project_file"
set tb_project_file "$location/stimulus/$module\_fixpt_tb.vhd"
puts "File location is $tb_project_file"

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
#Libero operations, create the project
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------

new_project -location $location -name $project_name -project_description {} -block_mode 0 -standalone_peripheral_initialization 0 -instantiate_in_smartdesign 1 -ondemand_build_dh 1 -use_relative_path 0 -linked_files_root_dir_env {} -hdl {VHDL} -family {PolarFire} -die {MPF300T} -package {FCG1152} -speed {-1} -die_voltage {1.0} -part_range {EXT} -adv_options {IO_DEFT_STD:LVCMOS 1.8V} -adv_options {RESTRICTPROBEPINS:1} -adv_options {RESTRICTSPIPINS:0} -adv_options {SYSTEM_CONTROLLER_SUSPEND_MODE:0} -adv_options {TEMPR:EXT} -adv_options {VCCI_1.2_VOLTR:EXT} -adv_options {VCCI_1.5_VOLTR:EXT} -adv_options {VCCI_1.8_VOLTR:EXT} -adv_options {VCCI_2.5_VOLTR:EXT} -adv_options {VCCI_3.3_VOLTR:EXT} -adv_options {VOLTR:EXT}
set_device -family {PolarFire} -die {MPF300T} -package {FCG1152} -speed {-1} -die_voltage {1.0} -part_range {EXT} -adv_options {IO_DEFT_STD:LVCMOS 1.8V} -adv_options {RESTRICTPROBEPINS:1} -adv_options {RESTRICTSPIPINS:0} -adv_options {SYSTEM_CONTROLLER_SUSPEND_MODE:0} -adv_options {TEMPR:EXT} -adv_options {VCCI_1.2_VOLTR:EXT} -adv_options {VCCI_1.5_VOLTR:EXT} -adv_options {VCCI_1.8_VOLTR:EXT} -adv_options {VCCI_2.5_VOLTR:EXT} -adv_options {VCCI_3.3_VOLTR:EXT} -adv_options {VOLTR:EXT} 

#Add each VHDL file
foreach vhdl_file $vhdl_files {
    import_files \
         -convert_EDN_to_HDL 0 \
         -library {work} \
         -hdl_source $vhdl_file
}

#Add simulation files as stimulus
import_files \
         -convert_EDN_to_HDL 0 \
         -library {work} \
         -stimulus $tb_pkg_file

import_files \
         -convert_EDN_to_HDL 0 \
         -library {work} \
         -stimulus $tb_file

#Necessary because Libero is in project mode. Equivalent to pressing "Build Heirarchy" button in GUI and selecting top level
build_design_hierarchy
set_root -module $root\::work

#pkg files must come first or else ModelSim doesn't know where to get the library specified in the test bench file
organize_tool_files -tool {SIM_PRESYNTH} -file $tb_pkg_project_file -file $tb_project_file -module $root\::work -input_type {stimulus}
organize_tool_files -tool {SIM_POSTSYNTH} -file $tb_pkg_project_file -file $tb_project_file -module $root\::work -input_type {stimulus}
organize_tool_files -tool {SIM_POSTLAYOUT} -file $tb_pkg_project_file -file $tb_project_file -module $root\::work -input_type {stimulus}

#Equivalent of going to Project Options and changing DO file area. Testbench will have a different name then default, so it needs to know
set_modelsim_options -tb_module_name $tb_name
save_project

foreach dat_file $dat_files {
    file copy $dat_file "$location/simulation"
}
#Run specific tools
run_tool -name {SIM_PRESYNTH}
#run_tool -name {SYNTHESIZE}
#save_project

#https://wiki.tcl-lang.org/page/How+do+I+read+and+write+files+in+Tcl

set fp [open "$location/simulation/run.do" r]
set file_data [read $fp]
close $fp
set data [split $file_data "\n"]

set filename "$location/simulation/run_edit.do"
set fileId [open $filename "w"]

foreach line $data {
     if {([string match "*exit*" $line] == 0) &&
        ([string match "*onbreak*" $line] == 0) &&
        ([string match "*onerror*" $line] == 0) &&
        ([string match "log*" $line] == 0)} {
            puts $fileId $line
     }
     if {[string match "*vsim*" $line] != 0} {
        for {set i 1} {$i < 18} {incr i} {
            puts $fileId "radix define fp_${i} -fixed -fraction 1 -base decimal"
        }
        puts $fileId "add wave /$tb_name/*"
     }
}
close $fileId

set_modelsim_options -use_automatic_do_file 0
set_modelsim_options -user_do_file "$location/simulation/run_edit.do"
