# debug plots
import matplotlib.pyplot as plt
import pandas as pd
import sys
import tkinter as tk
from tkinter import filedialog as fd


def getfilepath():
    
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-alpha", 0)
    path = fd.askopenfilename(defaultextension=".csv", initialdir="../../data")
    root.destroy()
    return path


filepath = getfilepath()

df = pd.read_csv(filepath)

print(df.columns)

fig1 = plt.figure()

ax1 = fig1.add_subplot(221)
ax1.plot(df["time"],df["disp_rel"])
ax1.set_title("Displacement")


ax2 = fig1.add_subplot(222)
ax2.plot(df["time"],df["speed"])
ax2.set_title("Speed")



ax3 = fig1.add_subplot(223)
ax3.plot(df["disp_rel"],df["load_N_rel"])
ax3.set_title("Load vs Disp")



ax4 = fig1.add_subplot(224)
ax4.plot(df["strain_eng"],df["stress_eng"])
ax4.set_title("Engineering Stress v Strain")




plt.show()