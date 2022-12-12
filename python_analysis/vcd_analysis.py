import io
from vcd.reader import TokenKind, tokenize

signals_of_interest = ["w1",
                       "w1_done",
                       "w2"]

#Example status: {'w1_done': {None: 'B', 'bits': 1, 'last_val': 0}, 'w1': {13: 'I', 'bits': 14, 'last_val': 0, 12: 'J', 11: 'K', 10: 'L', 9: 'M', 8: 'N', 7: 'O', 6: 'P', 5: 'Q', 4: 'R', 3: 'S', 2: 'T', 1: 'U', 0: 'V'}, 'w2': {13: 'W', 'bits': 12, 'last_val': 0, 12: 'X', 11: 'Y', 10: 'Z', 9: '[', 8: '\\', 7: ']', 6: '^', 5: '_', 4: '`', 3: 'a', 2: 'b'}}

pairs = {}
f = open("weight_streamer_waveform.vcd", "rb")
tokens = tokenize(f)
top = None
time = 0
prev_time = 0
state = "get_signals"
for num,i in enumerate(tokens):
    if ((num>0) and (num<500)):
        print(i)

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
                    key_in[bit_index]=id_code
                    key_in['bits'] = pairs[reference]['bits'] + 1
                    pairs[reference].update(key_in)
                else:
                    key_in = {}
                    key_in[bit_index] = id_code
                    key_in['bits'] = 1
                    key_in['last_val'] = 0
                    pairs[reference] = key_in

        elif (i.kind is TokenKind.ENDDEFINITIONS):
            print (pairs)
            state = "changes"

    elif (state == "changes"):
        if (i.kind is TokenKind.CHANGE_TIME):
            prev_time = time
            time = int(i.data)
        elif (
