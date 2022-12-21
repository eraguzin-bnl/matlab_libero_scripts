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

        self.time_for_ready = 5000
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
                print (self.pairs)
                print (self.vals)
                print (self.sensitivity_list)
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

    def plot_spectrometer(self, signal, division=1):
        x = self.vals['ready_expected']['x']
        y = self.vals['ready_expected']['y']
        print(x)
        print(y)

        chk_x = self.vals['ready_chkdata']['x']
        chk_y = self.vals['ready_chkdata']['y']

        ready_high1 = y.index(1)
        print(ready_high1)
        ready_high2 = y.index(1, ready_high1+1)
        print(ready_high2)

        time1 = x[ready_high1]
        time2 = x[ready_high2]

        print(time1)
        print(time2)
        t_d = time2 - time1
        print(t_d)
        #Turn into a while loop with a static t that is increasing and being checked against
        if (t_d > self.time_for_ready):
            print("enough")
            enable = next(x for x in chk_x if x > time1)
            enable_index =chk_x.index(enable)
            print(enable)
            print(enable_index)
            enable_high = chk_y.index(1, enable_index+1)
            print(enable_high)
            enable_high_x = chk_x[enable_high]
            print(enable_high_x)
        else:
            print("Not enough time passed for the ready signal")

#Called from command line
if __name__ == "__main__":
    x = LuSEE_VCD_Analyze("config_peaks.json")
    x.header()
    x.body()
    x.plot_spectrometer(['pks_ref_0', 'pks_ref_1', 'pks_ref_2', 'pks_ref_3', 'ready_chkdata', 'ready_expected'], 1e9)
