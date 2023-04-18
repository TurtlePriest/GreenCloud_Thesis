import csv
import sys
import pandas as pd
import matplotlib.pyplot as plt

# Get file name from cmd argument
filepath = sys.argv[1]
filename = filepath.split("/")[-1].split(".")[0]
dest = filepath.split("/")[0]+"/"
duration = 0
current = []
voltage = []
watt = []

with open(filepath, 'r') as csvfile:

    # Open file specified in command
    reader = csv.reader(csvfile)

    # Skip the first two rows to aviod field names
    next(reader)
    next(reader)
    
    # Append all current and voltage readings
    for row in reader:
        current.append(float(row[2]))
        voltage.append(float(row[1]))
        
    # Get test duration
    duration = reader.line_num-2

# Calculate watt for each reading
for i in range(len(current)):
    watt.append(round(float(current[i]) * float(voltage[i]),4))

# Function to calculate average value of a list
def avg(lst):
    return round(sum(lst) / len(lst),5)

# Create textfile with summary of test in same folder as the csvfile
with open(dest+filename+"_summary.txt", 'w') as summ:
    summ.write("Test duration: %s" %duration + " seconds\n\n")
    summ.write("Voltage stats:\n"+
               "Voltage max: %s" %max(voltage) + " V\n" +
               "Voltage min: %s" %min(voltage) + " V\n" +
               "Voltage average: %s" %float(avg(voltage)) + " V\n\n")
    summ.write("Current stats:\n"+
               "Current max: %s" %max(current) + " A\n" +
               "Current min: %s" %min(current) + " A\n" +
               "Current average: %s" %float(avg(current)) + " A\n\n")
    summ.write("Wattage stats:\n"+
               "Wattage max: %s" %max(watt) + " W\n" +
               "Wattage min: %s" %min(watt) + " W\n" +
               "Wattage average: %s" %float(avg(watt)) + " W")


# Create dataframe with measured watts and time
df = pd.DataFrame(watt, columns=['Watt'])
df['Time'] = df.index+1

# Create the time series plot with labels and save it as a png
ax = df.plot(x='Time',y='Watt')
ax.set_xlabel('Time in seconds')
ax.set_ylabel('Power in Watt')
ax.set_title('Time series of power consumption')
fig = ax.get_figure()
fig.savefig(dest + filename +"_plot.png")