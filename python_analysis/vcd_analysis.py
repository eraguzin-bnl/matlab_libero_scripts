import io
from vcd.reader import TokenKind, tokenize
import sys
import numpy as np
import matplotlib.pyplot as plt
import json

class LuSEE_VCD_Analyze:
    def __init__(self):

        with open("config.json", "r") as jsonfile:
            json_data = json.load(jsonfile)

        self.signals_of_interest = {}
        for num,i in enumerate(json_data["Signals"]):
            listing = {}
            listing['Signedness'] = json_data["Signals"][i]['Signedness']
            listing['Word Length'] = json_data["Signals"][i]['Word Length']
            listing['Fraction Length'] = json_data["Signals"][i]['Fraction Length']
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

    def header(self):
        for num,i in enumerate(self.tokens):
            #Still in the preamble. It's getting header data and signal definitions.
            if (i.kind is TokenKind.TIMESCALE):
                time_magnitude = i.timescale.magnitude.value
                timescale = i.timescale.unit.value

            elif (i.kind is TokenKind.SCOPE):
                top = i.scope.ident

            elif (i.kind is TokenKind.VAR):
                id_code = i.var.id_code
                reference = i.var.reference
                bit_index = i.var.bit_index
                #Want to create signals that keep the arrays together.
                if reference in self.signals_of_interest:
                    if reference not in self.pairs:
                        #First time a signal name is found. A key in the master list is made for it as a 1-bit value. And a spot in the value tracker array ismade too
                        key_in = {}
                        key_in[id_code] = bit_index
                        key_in['bits'] = 1
                        self.pairs[reference] = key_in

                        val_in = {}
                        val_in['values'] = []
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
            #TODO add an option for a time tick before the change with the previous value - smoothing
            #VCD files end with a time stamp, so this will be the last section read when analyzing a file
            if (i.kind is TokenKind.CHANGE_TIME):
                self.prev_time = self.time
                self.time = int(i.data)
                for j in self.pairs:
                    if (self.vals[j]['modified'] == True):
                        values = self.vals[j]['values']
                        lv = self.vals[j]['last_val']
                        signedness = self.signals_of_interest[j]['Signedness']
                        word_length = self.signals_of_interest[j]['Word Length']
                        fraction_length = self.signals_of_interest[j]['Fraction Length']
                        #print("{} Original value is {}".format(j, bin(lv)))
                        if (signedness == 'signed'):
                            if (((lv >> (word_length - 1)) & 0x1) == 1):
                                new_val = (lv - (1 << word_length)) /(2**fraction_length)
                                values.append([self.prev_time, new_val])
                                #print("New value1 is {}".format(new_val))
                            else:
                                new_val = (lv) /(2**fraction_length)
                                values.append([self.prev_time, new_val])
                                #print("New value2 is {}".format(new_val))
                        else:
                            new_val = (lv) /(2**fraction_length)
                            values.append([self.prev_time, new_val])

                        self.vals[j]['values'] = values
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

    def plot(self):
        #print(self.vals['w1']['values'])
        a = self.vals['w1']['values']
        x,y = zip(*a)
        #for num,i in enumerate(y):
        #    if (num < 500):
        #        print(i)
        plt.plot(x, y)
        plt.show()

#Called from command line
if __name__ == "__main__":
    x = LuSEE_VCD_Analyze()
    x.header()
    x.body()
    x.plot()
