import csv
import sys, os
import matplotlib.pyplot as plt

bins = []

with open('outbin_expected.dat', newline = '') as outbin:
    bin_reader = csv.reader(outbin)
    for i in bin_reader:
        bins.append(i[0])

pks_array = []

with open('pks_expected.dat', newline = '') as pks:
    pks_reader = csv.reader(pks)
    for i in pks_reader:
        pks_array.append(i[0])

bin_array = []
pks_ch1 = []
pks_ch2 = []
state = "initial"
i = 0
loop = 1
for num,bin_num in enumerate(bins):
    if (bin_num == "001"):
        i = i + 1
        if (state != "done"):
            if (i > loop):
                state = "append"
    if (bin_num == "7ff"):
        if (i > loop):
            state = "done"
    if (state == "append"):
        bin_array.append(int(bin_num, 16))
        pks_line = pks_array[num].split()
        pk1 = int(pks_line[0], 16)
        pks_ch1.append(pk1 * (2**15))
        pk2 = int(pks_line[1], 16)
        pks_ch2.append(pk2 * (2**15))

freq = []
for i in bin_array:
    freq.append((i*50)/len(bin_array))

fig, ax = plt.subplots()
ax.plot(freq,pks_ch1)
ax.set_yscale('log')
ax.plot(freq,pks_ch2)
ax.set_yscale('log')
ax.set_xlim([0, 10])

title = "PFB output of 1MHz and 6 MHz sine waves"
fig.suptitle(title, fontsize = 18)
yaxis = "power"
ax.set_ylabel(yaxis, fontsize=14)


ax.set_xlabel('freq [MHz]', fontsize=14)
#ax.ticklabel_format(style='plain', useOffset=False, axis='x')

plot_path = os.path.join(os.getcwd(), "plots")
if not (os.path.exists(plot_path)):
    os.makedirs(plot_path)

fig.savefig (os.path.join(plot_path, f"plot_dat_0.jpg"))
#np.save(os.path.join(plot_path, f"data{self.plot_num}"), x, y)

plt.show()
