# Microsemi Tcl Script
# libero
# Date: Wed Nov 23 15:33:55 2022
# Will start up libero with the exported Matlab files

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
#Get all directory values
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------

puts "Welcome to Eric's Matlab Libero Setup TCL script!"
set directory_path [lindex $argv 0]
set module [lindex $argv 1]
puts "Directory Path is $directory_path"
set project_name "libero_proj_$module"
set location "$directory_path/$project_name"
puts "Location is $location"
set hdl_location "$directory_path/codegen/$module/hdlsrc/"
puts "HDL location is $hdl_location"
#Matlab keeps double underscores for directories, but not for files
#So when we use $module for files, eliminate the double underscore
set module [string map {__ _} $module]
#Also, having a trailing underscore complicates file name, so remove it
set module [string trimright $module _]
puts "File name is $module"
set root "$module\_fixpt"
puts "Root is $root"
set tb_name "$module\_fixpt_tb"
puts "Testbench name is $tb_name"

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
#Get all files with certain extensions
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------

#Get all files with .dat extension. Needed for simulation
#set dat_files [glob -dir $hdl_location *.dat]
#puts "dat_files are $dat_files"


if {[catch {glob -dir $hdl_location *.dat} errmsg]} {
    puts "There are no .dat files"
    set dat_files []
} else {
    puts "There are .dat files"
    set dat_files [glob -dir $hdl_location *.dat]
}

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

if {[file exists $location]} then {
    puts "Deleting the existing $location"
    file delete -force -- $location
} else {
    puts "Creating new directory"
}

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
#Libero operations, create the project
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------

new_project -location $location -name $project_name -project_description {} -block_mode 0 -standalone_peripheral_initialization 0 -instantiate_in_smartdesign 1 -ondemand_build_dh 1 -use_relative_path 0 -linked_files_root_dir_env {} -hdl {VHDL} -family {PolarFire} -die {MPF500TS} -package {FCG1152} -speed {-1} -die_voltage {1.0} -part_range {IND} -adv_options {IO_DEFT_STD:LVCMOS 1.8V} -adv_options {RESTRICTPROBEPINS:1} -adv_options {RESTRICTSPIPINS:0} -adv_options {TEMPR:IND} -adv_options {UNUSED_MSS_IO_RESISTOR_PULL:None} -adv_options {VCCI_1.2_VOLTR:IND} -adv_options {VCCI_1.5_VOLTR:IND} -adv_options {VCCI_1.8_VOLTR:IND} -adv_options {VCCI_2.5_VOLTR:IND} -adv_options {VCCI_3.3_VOLTR:IND} -adv_options {VOLTR:IND}

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

#.dat files are necessary in the simulation folder for ModelSim to pull seed values and compare to expected values
foreach dat_file $dat_files {
    file copy $dat_file "$location/simulation"
}
#Run specific tools
run_tool -name {SIM_PRESYNTH}
#run_tool -name {SYNTHESIZE}
#save_project

#https://wiki.tcl-lang.org/page/How+do+I+read+and+write+files+in+Tcl

#Now that the simulation has run once, Libero auto-generated a run.do file. There's a lot in there that I didn't want to do programmatically, so Libero auto-generating it is the easiest
#But there are a few lines that sometimes get added, like telling it to exit after simulation, or after a break or error, or logging the wrong signals
#So I open up the run.do file and write each line to a new file, taking out some of them, and then adding others at the end.
set fp [open "$location/simulation/run.do" r]
set file_data [read $fp]
close $fp
set data [split $file_data "\n"]

#New edited file
set filename "$location/simulation/run_edit.do"
set fileId [open $filename "w"]

foreach line $data {
        #Don't include lines with these commands
     if {([string match "*exit*" $line] == 0) &&
        ([string match "*onbreak*" $line] == 0) &&
        ([string match "*onerror*" $line] == 0) &&
        ([string match "log*" $line] == 0)} {
            puts $fileId $line
     }
        #After the vsim command, I want to put these, so they run in the ModelSim environment, but before it actually runs
     if {[string match "*vsim*" $line] != 0} {
        for {set i 1} {$i < 18} {incr i} {
            #Gives fixed point (signed and unsigned) radixes when looking at signal values. ModelSim doesn't do this themselves, but our project is all about fixed point numbers with different values
            #You can go up to 17 fractional digits in ModelSim, so I have all the options up til that point
            puts $fileId "radix define fp_${i} -fixed -fraction ${i} -base decimal"
            puts $fileId "radix define sfp_${i} -fixed -signed -fraction ${i} -base decimal"
        }
        #So that the top level signals are already recorded during the simulation
        puts $fileId "add wave /$tb_name/*"
        #Track all signals for VCD output dump
        puts $fileId "vcd file $module\_waveform.vcd"
        #puts $fileId "vcd add -r /$tb_name/*"
        puts $fileId "vcd add /$tb_name/*"

     }
}
#Flush VCD after the "run" command
puts $fileId "vcd flush"
close $fileId

#Tells Libero that by default, next time you start a ModelSim simulation, don't auto-generate a DO file, use this custom one we just made
set_modelsim_options -use_automatic_do_file 0
set_modelsim_options -user_do_file "$location/simulation/run_edit.do"
save_project

#close_project -save 1
#puts "Project closed"
#open_project -file "$location/$project_name\.prjx"
#puts "Project open"
#Run again to get VCD output (this hangs the script)
#run_tool -name {SIM_PRESYNTH}
