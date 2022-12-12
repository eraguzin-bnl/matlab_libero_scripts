import io
from vcd.reader import TokenKind, tokenize
import sys
import numpy as np
import matplotlib.pyplot as plt
signals_of_interest = ["w1",
                       "w1_done",
                       "w2"]

#Example status: {'w1_done': {'B': None, 'bits': 1, 'last_val': 0}, 'w1': {'I': 13, 'bits': 14, 'last_val': 0, 'J': 12, 'K': 11, 'L': 10, 'M': 9, 'N': 8, 'O': 7, 'P': 6, 'Q': 5, 'R': 4, 'S': 3, 'T': 2, 'U': 1, 'V': 0}, 'w2': {'W': 13, 'bits': 14, 'last_val': 0, 'X': 12, 'Y': 11, 'Z': 10, '[': 9, '\\': 8, ']': 7, '^': 6, '_': 5, '`': 4, 'a': 3, 'b': 2, 'c': 1, 'd': 0}}

pairs = {}
vals = {}
f = open("weight_streamer_waveform.vcd", "rb")
tokens = tokenize(f)
top = None
time = 0
prev_time = 0
state = "get_signals"
for num,i in enumerate(tokens):
    if (state == "get_signals"):
        if (i.kind is TokenKind.TIMESCALE):
            time_magnitude = i.timescale.magnitude.value
            timescale = i.timescale.unit.value

        elif (i.kind is TokenKind.SCOPE):
            top = i.scope.ident

        elif (i.kind is TokenKind.VAR):
            id_code = i.var.id_code
            reference = i.var.reference
            bit_index = i.var.bit_index

            if reference in signals_of_interest:
                if reference in pairs:
                    key_in = {}
                    key_in[id_code]=bit_index
                    key_in['bits'] = pairs[reference]['bits'] + 1
                    pairs[reference].update(key_in)
                else:
                    key_in = {}
                    key_in[id_code] = bit_index
                    key_in['bits'] = 1
                    key_in['last_val'] = 0
                    pairs[reference] = key_in

                    val_in = {}
                    val_in['values'] = []
                    val_in['last_val'] = 0
                    val_in['modified'] = False
                    vals[reference] = val_in

        elif (i.kind is TokenKind.ENDDEFINITIONS):
            print (pairs)
            state = "changes"

    elif (state == "changes"):
        if (i.kind is TokenKind.CHANGE_TIME):
            prev_time = time
            time = int(i.data)
            for j in pairs:
                if (vals[j]['modified'] == True):
                    values = vals[j]['values']
                    lv = vals[j]['last_val']
                    if (((lv >> 12) & 0x1) == 1):
                        values.append([prev_time, lv * -1])
                    else:
                        values.append([prev_time, lv])
                    vals[j]['values'] = values
                    vals[j]['modified'] = False
        elif (i.kind is TokenKind.CHANGE_SCALAR):
            id_code = i.scalar_change.id_code
            for j in pairs:
                if id_code in pairs[j]:
                    bit = pairs[j][id_code]
                    value = i.scalar_change.value
                    previous_val = vals[j]['last_val']
                    if (value == 'x' or value == '0'):
                        val = 0
                        if (bit == None):
                            previous_val = val
                        else:
                            inverse_mask = 1 << bit
                            mask = ~inverse_mask
                            previous_val = previous_val & mask
                    else:
                        val = 1
                        if (bit == None):
                            previous_val = val
                        else:
                            previous_val = previous_val | (val << bit)

                    vals[j]['last_val'] = previous_val
                    vals[j]['modified'] = True
#print(vals['w1']['values'])
a = vals['w1']['values']
x,y = zip(*a)
for num,i in enumerate(y):
    if (num < 500):
        print(bin(i))
plt.plot(x, y)
plt.show()
