import csv
import sys
import pandas as pd
import matplotlib.pyplot as plt

# Get file path from cmd argument
file1 = sys.argv[1]
file2 = sys.argv[2]
title = sys.argv[3]

# Get file name without extention from path
filename1 = file1.split("/")[-1].split(".")[0]
filename2 = file2.split("/")[-1].split(".")[0]

# Get folder destination from path
dest = file1.split("/")[0]+"/"


# Define variables
c1 = []
c2 = []
v1 = []
v2 = []
w1 = []
w2 = []

with open(file1, 'r') as csvfile:

    # Open file specified in command
    reader = csv.reader(csvfile)

    # Skip the first two rows to aviod field names
    next(reader)
    next(reader)
    
    # Append all current and voltage readings
    for row in reader:
        c1.append(float(row[2]))
        v1.append(float(row[1]))

with open(file2, 'r') as csvfile:

    # Open file specified in command
    reader = csv.reader(csvfile)

    # Skip the first two rows to aviod field names
    next(reader)
    next(reader)
    
    # Append all current and voltage readings
    for row in reader:
        c2.append(float(row[2]))
        v2.append(float(row[1]))
        

# Calculate watt for file 1
for i in range(len(c1)):
    w1.append(round(float(c1[i]) * float(v1[i]),4))

# Calculate watt for file 2
for i in range(len(c2)):
    w2.append(round(float(c2[i]) * float(v2[i]),4))

# Function to calculate average value of a list
def avg(lst):
    return round(sum(lst) / len(lst),5)


# Create dataframes with measured watts and time
df1 = pd.DataFrame(w1, columns=['Baseline'])
df1['Time'] = df1.index+1
df2 = pd.DataFrame(w2, columns=['Optimized'])
df2['Time'] = df1.index+1

# Create the time series plot with labels and save it as a png
ax = df1.plot(x='Time',y='Baseline')
df2.plot(ax=ax, x='Time', y='Optimized')
ax.set_xlabel('Time in seconds')
ax.set_ylabel('Power in Watt')
ax.set_title(title)
ax.set_ybound(0, 0.6)
plt.legend(loc='upper left',bbox_to_anchor=(0.8, 1.15))
fig = ax.get_figure()
fig.savefig(dest + filename1 +"_comparison.pdf")