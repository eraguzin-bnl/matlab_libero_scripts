import io, sys, os, json
from vcd.reader import TokenKind, tokenize
import numpy as np
import matplotlib.pyplot as plt

class LuSEE_VCD_Analyze:
    def __init__(self, config_file):

        with open(config_file, "r") as jsonfile:
            json_data = json.load(jsonfile)

        self.signals_of_interest = {}
        for num,i in enumerate(json_data["Signals"]):
            listing = {}
            listing['Title'] = json_data["Signals"][i]['Title']
            listing['Y-axis'] = json_data["Signals"][i]['Y-axis']
            listing['Signedness'] = json_data["Signals"][i]['Signedness']
            listing['Word Length'] = json_data["Signals"][i]['Word Length']
            listing['Fraction Length'] = json_data["Signals"][i]['Fraction Length']
            listing['Smoothing'] = json_data["Signals"][i]['Smoothing']
            self.signals_of_interest[i] = listing

        self.axis_font = json_data["Plot"]["axis_font"]
        self.title_font = json_data["Plot"]["title_font"]
        self.x_lim_low = json_data["Plot"]["x_lim_low"]
        self.x_lim_high = json_data["Plot"]["x_lim_high"]
        self.freq_adjust = json_data["Plot"]["freq_adjust"]

        self.time_high = json_data["time_high"]
        self.bins = json_data["bins"]
        self.loop = json_data["loop"]

        #Example dicts:
        #{'w1': {'I': 13, 'bits': 14, 'J': 12, 'K': 11, 'L': 10, 'M': 9, 'N': 8, 'O': 7, 'P': 6, 'Q': 5, 'R': 4, 'S': 3, 'T': 2, 'U': 1, 'V': 0}}
        #{'w1': {'values': [], 'last_val': 0, 'modified': False}}
        #{'I': 'w1', 'J': 'w1', 'K': 'w1', 'L': 'w1', 'M': 'w1', 'N': 'w1', 'O': 'w1', 'P': 'w1', 'Q': 'w1', 'R': 'w1', 'S': 'w1', 'T': 'w1', 'U': 'w1', 'V': 'w1'}

        self.sensitivity_list = {}
        self.pairs = {}
        self.vals = {}
        f = open(json_data["File Name"], "rb")
        self.tokens = tokenize(f)
        self.top = None
        self.time = 0
        self.prev_time = 0
        self.plot_num = 0

    def header(self):
        for num,i in enumerate(self.tokens):
            #Still in the preamble. It's getting header data and signal definitions.
            if (i.kind is TokenKind.TIMESCALE):
                self.time_magnitude = i.timescale.magnitude.value
                self.timescale = i.timescale.unit.value

            elif (i.kind is TokenKind.SCOPE):
                self.top = i.scope.ident

            elif (i.kind is TokenKind.VAR):
                id_code = i.var.id_code
                reference = i.var.reference
                bit_index = i.var.bit_index
                array_type = type(bit_index)
                #This means it's an array of an array, so like $var wire 1 " pks_ref [0][12] $end
                #This correction assumes you can only have double nested arrays. It will have to be fixed if you can have triple or higher
                if array_type is tuple:
                    reference = f"{reference}_{bit_index[0]}"
                    bit_index = bit_index[1]
                #Want to create signals that keep the arrays together.
                if reference in self.signals_of_interest:
                    if reference not in self.pairs:
                        #First time a signal name is found. A key in the master list is made for it as a 1-bit value
                        #And a spot in the value tracker array ismade too
                        key_in = {}
                        key_in[id_code] = bit_index
                        key_in['bits'] = 1
                        self.pairs[reference] = key_in

                        val_in = {}
                        val_in['x'] = []
                        val_in['y'] = []
                        val_in['last_val'] = 0
                        val_in['modified'] = False
                        self.vals[reference] = val_in

                    else:
                        #This means this key is part of an array, the extra bit and indicator is added to the master list
                        key_in = {}
                        key_in[id_code]=bit_index
                        key_in['bits'] = self.pairs[reference]['bits'] + 1
                        self.pairs[reference].update(key_in)

                    new_sensitive_var = {}
                    new_sensitive_var[id_code] = reference
                    self.sensitivity_list.update(new_sensitive_var)

            #The last line of the preamble/header
            elif (i.kind is TokenKind.ENDDEFINITIONS):
                #print (self.pairs)
                #print (self.vals)
                #print (self.sensitivity_list)
                break
            
    def body(self):
        for num,i in enumerate(self.tokens):
            #Unfortunately the only way to check these files is line by line as far as I can tell
            #If the time has changed, check for any values that may have changed in the previous time interval
            #If there is an array, we want the final value to be recorded after all bits of the array have been registered as changed.
            #VCD files end with a time stamp, so this will be the last section read when analyzing a file
            if (i.kind is TokenKind.CHANGE_TIME):
                self.prev_time = self.time
                self.time = int(i.data)
                for j in self.pairs:
                    if (self.vals[j]['modified'] == True):
                        x = self.vals[j]['x']
                        y = self.vals[j]['y']
                        lv = self.vals[j]['last_val']
                        signedness = self.signals_of_interest[j]['Signedness']
                        word_length = self.signals_of_interest[j]['Word Length']
                        fraction_length = self.signals_of_interest[j]['Fraction Length']

                        #Because VHDL signals aren't report until they change, you might get weird interpolation
                        #This makes sure that the plotted line before this most recent change is at the right value
                        if (self.signals_of_interest[j]['Smoothing'] == "true"):
                            if (len(y) > 0):
                                x.append(self.prev_time - self.time_magnitude)
                                y.append(self.vals[j]['y'][-1])

                        if (signedness == 'signed'):
                            if (((lv >> (word_length - 1)) & 0x1) == 1):
                                new_val = (lv - (1 << word_length)) /(2**fraction_length)
                                x.append(self.prev_time)
                                y.append(new_val)
                            else:
                                new_val = (lv) /(2**fraction_length)
                                x.append(self.prev_time)
                                y.append(new_val)
                        else:
                            new_val = (lv) /(2**fraction_length)
                            x.append(self.prev_time)
                            y.append(new_val)

                        self.vals[j]['x'] = x
                        self.vals[j]['y'] = y
                        self.vals[j]['modified'] = False

            #Each line after the time indicates a changed value. See if the changed value is one that is tracked
            #If it's an
            elif (i.kind is TokenKind.CHANGE_SCALAR):
                id_code = i.scalar_change.id_code
                if id_code in self.sensitivity_list:
                    signal = self.sensitivity_list[id_code]
                    sublist = self.pairs[signal]
                    previous_val = self.vals[signal]['last_val']
                    bit = sublist[id_code]
                    value = i.scalar_change.value
                    #Update most recent value of that array for that bit with the specified value
                    if (value == 'x' or value == '0'):  #Is there a better way to deal with don't cares?
                        val = 0
                        if (bit == None):
                            previous_val = val
                        else:
                            #To change a single bit to a 0, need to AND with a mask of 1s with a 0 in the desired bit location
                            inverse_mask = 1 << bit
                            mask = ~inverse_mask
                            previous_val = previous_val & mask
                    else:
                        val = 1
                        if (bit == None):
                            previous_val = val
                        else:
                            #To add a 1, simple to use OR
                            previous_val = previous_val | (val << bit)

                    #Keep this value in case the next line has the next bit of the array
                    #Mark it so that this value gets saved at the end of the time tick
                    self.vals[signal]['last_val'] = previous_val
                    self.vals[signal]['modified'] = True

        #After the file is done, add the last value as the final time tick
        #It helps with analysis later
        for i in self.vals:
            self.vals[i]['x'].append(self.time)
            self.vals[i]['y'].append(self.vals[i]['last_val'])

    def plot(self, signal, division=1):
        x = np.divide(self.vals[signal]['x'], division)
        y = self.vals[signal]['y']

        fig, ax = plt.subplots()

        title = self.signals_of_interest[signal]["Title"]
        fig.suptitle(title, fontsize = 24)
        yaxis = self.signals_of_interest[signal]["Y-axis"]
        ax.set_ylabel(yaxis, fontsize=14)


        ax.set_xlabel('Time (ns)', fontsize=14)
        ax.ticklabel_format(style='plain', useOffset=False, axis='x')

        ax.plot(x, y)

        plot_path = os.path.join(os.getcwd(), "plots")
        if not (os.path.exists(plot_path)):
            os.makedirs(plot_path)

        fig.savefig (os.path.join(plot_path, f"plot{self.plot_num}.jpg"))
        np.save(os.path.join(plot_path, f"data{self.plot_num}"), x, y)
        self.plot_num = self.plot_num + 1
        plt.show()

    #Takes the value to look for in binary, the x and y coordinates
    #the length of time in picoseconds to consider fully changing
    #and a global time limit, if the search goes past that time, it's over

    #It find the beginning and ending time when the y signal hits the value
    #and it stays for the given amount of time
    #Will only find a change in time, not if it's already at the desired value
    def find_next_time(self, value, x, y, length, time_limit = None):
        time = self.time

        #Go from the global time to the next time tick for this given signal
        next_time = next(i for i in x if i > time)
        if (time_limit != None):
            if (next_time > time_limit):
                print("Next change occurs after time limit")
                return None, None
        #Get the actual index of that time, so that you can match with Y values
        next_time_index = x.index(next_time)

        while (True):
            #Find the next time the signal is the desired value
            try:
                next_val = y.index(value, next_time_index)
                end_val = y[next_val+1]
            except ValueError:
                print(f"Started checking from {time}, but signal does not reach {value}")
                return None
            except IndexError:
                print(f"Started checking from {time}, but signal does not reach {value}")
                return None

            #Get the time of this tick hitting the value
            time1 = x[next_val]

            #Find the next time the signal changes back, starting at the time that it was found for this value
            try:
                next_change = y.index(end_val, next_val + 1)
            except ValueError:
                #It doesn't change back
                #So the the "end time" is the last time in the signal array
                next_change = len(x) -1

            #Turn the index into actual time
            time2 = x[next_change]

            #Check that it was long enough and return if so
            #Or else, start with the latest time and continue the loop
            if (time2 - time1 > length):
                #print(f"Signal changes to {value} at {time1} until {time2}, which is {(time2-time1)/1e3} ns")
                return time1, time2
            else:
                print(f"Signal changes to {value} at {time1} but changes back at {time2}, before {length} time has passed")
                next_time_index = next_change

    def plot_spectrometer(self,loop=None, return_data=False):
        self.time = 0
        #Get all relevant values
        bin_x = self.vals['outbin']['x']
        bin_y = self.vals['outbin']['y']

        pks0_x = self.vals['pks_0']['x']
        pks0_y = self.vals['pks_0']['y']

        pks1_x = self.vals['pks_1']['x']
        pks1_y = self.vals['pks_1']['y']

        pks2_x = self.vals['pks_2']['x']
        pks2_y = self.vals['pks_2']['y']

        pks3_x = self.vals['pks_3']['x']
        pks3_y = self.vals['pks_3']['y']

        i = 0
        pk_values0 = []
        pk_values1 = []
        pk_values2 = []
        pk_values3 = []


        if loop is None:
            loop = self.loop
        #Searches for a certain iteration of the ready signal going high
        for i in range(loop+1):
            #Find first index where ready goes high
            time_ready_high_start, time_ready_high_end = self.find_next_time(0x7ff, bin_x, bin_y, self.time_high)
            print(f"Time that outbin starts going for at least {self.time_high/1e3} ns is {time_ready_high_start/1e3} ns, until {time_ready_high_end/1e3} ns")
            self.time = time_ready_high_start # start from where you ended, so you find next one

        # step back a little
        self.time = time_ready_high_start - 1
        i = 0
        for i in range(self.bins-1, 3, -1):  ## we skip last bin due to some weird edge issue
            print(i)
            time_ready_high_start, time_ready_high_end = self.find_next_time(i, bin_x, bin_y, self.time_high)
            #print(f"Time that outpeak goes to {i} for at least 1 ns is {time_ready_high_start/1e3} ns, until {time_ready_high_end/1e3} ns")
            self.time = time_ready_high_start

            #We know the time that "check data" goes high
            #Convert that to the pk time domain to find a transition time after that
            pk_time = next(i for i in pks0_x if i > time_ready_high_start)
            pk_time_index = pks0_x.index(pk_time)
            #Find the value at the change before this time
            #That's the actual value at the check data time
            pk_value = pks0_y[pk_time_index-1]
            pk_values0.append(pk_value)
            #print(f"pk0 is {hex(int(pk_value))}")

            #Repeat for the rest of the pks coming out of spectrometer.m
            pk_time = next(i for i in pks1_x if i > time_ready_high_start)
            pk_time_index = pks1_x.index(pk_time)
            pk_value = pks1_y[pk_time_index-1]
            pk_values1.append(pk_value)
            #print(f"pk1 is {hex(int(pk_value))}")

        # throw away last one
        pk_values0.append(0)
        pk_values1.append(0)
        
        freq_reversed = np.flip(np.arange(1,self.bins-2))
        freq = self.freq_adjust/self.bins * freq_reversed

        if return_data:
            return freq, np.array(pk_values0), np.array(pk_values1)
        
        fig, ax = plt.subplots()
        ax.plot(freq,pk_values0)
        ax.set_yscale('log')
        ax.plot(freq,pk_values1)
        ax.set_yscale('log')
        ax.set_xlim([self.x_lim_low, self.x_lim_high])

        title = "PFB output of 1MHz and 6 MHz sine waves"
        fig.suptitle(title, fontsize = self.title_font)
        yaxis = "power"
        ax.set_ylabel(yaxis, fontsize=self.axis_font)


        ax.set_xlabel('freq [MHz]', fontsize=self.axis_font)
        #ax.ticklabel_format(style='plain', useOffset=False, axis='x')

        plot_path = os.path.join(os.getcwd(), "plots")
        if not (os.path.exists(plot_path)):
            os.makedirs(plot_path)

        fig.savefig (os.path.join(plot_path, f"plot{self.plot_num}.jpg"))
        #np.save(os.path.join(plot_path, f"data{self.plot_num}"), x, y)
        self.plot_num = self.plot_num + 1

        plt.show()


#Called from command line
if __name__ == "__main__":
    x = LuSEE_VCD_Analyze(sys.argv[1])
    x.header()
    x.body()
    x.plot_spectrometer()
