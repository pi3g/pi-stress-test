# Copyright (c) 2023 pi3g GmbH & Co. KG

import PySimpleGUI as sg
import subprocess
from subprocess import STDOUT, DEVNULL
import os
import signal
import click
import time
import re
from gpiozero import CPUTemperature

stress_cpu_command = "stress-ng --cpu 0 --cpu-method fft"
stress_gpu_command = "export DISPLAY=:0 && glxgears -fullscreen"
stress_cpu_process = None
stress_gpu_process = None
cpuonly_mode = False
autorestart = False

try:
    curr_temp_limit = subprocess.check_output(["cat /boot/config.txt | grep temp_limit"], shell=True)
except:
    curr_temp_limit = b'temp_limit=85\n'

def start_gui():
    layout = [
        [sg.Text("SOC Temperature Limit", font=["normal", 24]), sg.HorizontalSeparator(pad=[0,30])], 
        [
         sg.Button("85°C", font=["normal", 32], expand_x=True, key="-85_DEGREE_LIMIT-", disabled=curr_temp_limit == b'temp_limit=85\n'),
         sg.Button("75°C", font=["normal", 32], expand_x=True, key="-75_DEGREE_LIMIT-", disabled=curr_temp_limit == b'temp_limit=75\n'),
         sg.Button("70°C", font=["normal", 32], expand_x=True, key="-70_DEGREE_LIMIT-", disabled=curr_temp_limit == b'temp_limit=70\n')
        ], 
        [sg.Text("Switch to:", font=["normal", 24]), sg.HorizontalSeparator(pad=[0,15])], 
        [sg.Button("CPU Only", font=["normal", 32], expand_x=True, key="-MODE_BUTTON-"), sg.Button("Exit", font=["normal", 32])],
        [sg.HorizontalSeparator(pad=[0,30])], 
        [sg.Text("max. normal load reached (CPU+GPU)", font=["normal", 24], justification="center", key="-STATUS_TEXT-")], 
        [sg.Text("", font=["normal", 24], justification="center", key="-INFO_TEXT-")],
    ]

    window = sg.Window(title="Stress Test", layout=layout, 
        finalize=True, auto_size_buttons=True, 
        auto_size_text=True, size=[640, 445], no_titlebar=True,
        location=[0,35]
    )

    return window

def start_stressing():
    global cpuonly_mode
    global stress_gpu_process
    global stress_cpu_process
    
    # Start stress-ng
    if stress_cpu_process is None:
        stress_cpu_process = subprocess.Popen(stress_cpu_command, shell=True, 
                                          preexec_fn=os.setsid, stdout=DEVNULL,
                                          stderr=STDOUT)
    
    # Start or kill glxgears
    if not cpuonly_mode:
        stress_gpu_process = subprocess.Popen(stress_gpu_command, shell=True, 
                                              preexec_fn=os.setsid, stdout=DEVNULL,
                                              stderr=STDOUT)
    elif stress_gpu_process is not None:
        os.killpg(os.getpgid(stress_gpu_process.pid), signal.SIGTERM)    

def get_cpu_freq():
    freq = subprocess.check_output(["vcgencmd measure_clock arm | sed 's/frequency(48)=//g'"], shell=True)
    return int(freq) / 1000000

def set_temp_limit(limit):
    global autorestart
    pattern_replace("/boot/config.txt", r"^.*temp_limit.*$", "temp_limit={0}".format(limit), insert=True)
    if autorestart:
        print("Rebooting to set Temp Limit.")
        run("reboot")


def pattern_replace(filename, pattern, replacement, insert = False):
    with open(filename, "r") as file:
        data = file.read()

    if len(re.findall(pattern, data, flags=re.MULTILINE)) == 0:
        if insert:
            data += "\n{0}".format(replacement)
    else:
        data = re.sub(pattern, replacement, data, flags=re.MULTILINE)
   
    with open(filename, "w") as file:
        file.write(data)
    
def run(command):
    return subprocess.run(command, shell=True, stdout=DEVNULL, stderr=STDOUT)
    
@click.command()
@click.option("--gui/--no-gui", default=True, help="Run with or without GUI")
@click.option("--cpuonly/--cpugpu", default=False, help="Specify if you want to stress the GPU and CPU or only the CPU")
@click.option("--autoreboot", "-r", is_flag=True, help="Automatically reboot the Pi when necessary")
def cli(gui, cpuonly, autoreboot):
    global cpuonly_mode
    global autorestart
    cpuonly_mode = cpuonly
    autorestart = autoreboot

    
    cpu = CPUTemperature()

    if gui:
        try:
            window = start_gui()
        except:
            print("Error starting GUI, Exiting.")
            return
        start_stressing()
        if cpuonly_mode:
            window["-MODE_BUTTON-"].update("CPU and GPU")
            window["-STATUS_TEXT-"].update("max. load reached (CPU)")
        while True:
            window.force_focus()
            event, values = window.read(timeout=1000)
            if event == "Exit" or event == sg.WIN_CLOSED:
                break
            elif event == "-MODE_BUTTON-":
                if cpuonly_mode:
                    cpuonly_mode = False
                    window["-MODE_BUTTON-"].update("CPU Only")
                    window["-STATUS_TEXT-"].update("max. load reached (CPU+GPU)")
                    start_stressing()
                else:
                    cpuonly_mode = True
                    window["-MODE_BUTTON-"].update("CPU and GPU")
                    window["-STATUS_TEXT-"].update("max. load reached (CPU)")
                    start_stressing()
            elif event == "-85_DEGREE_LIMIT-":
                set_temp_limit(85)
            elif event == "-75_DEGREE_LIMIT-":
                set_temp_limit(75)
            elif event == "-70_DEGREE_LIMIT-":
                set_temp_limit(70)
            
            window["-INFO_TEXT-"].update("{0}°C, {1}MHz".format(cpu.temperature, get_cpu_freq()))
        window.close()
    else:
        start_stressing()
        try:
            while True:
                time.sleep(1)
                print(cpu.temperature, "°C,", get_cpu_freq(), "MHz")
        except KeyboardInterrupt:
            print("Exiting")
            pass

    try:
        os.killpg(os.getpgid(stress_cpu_process.pid), signal.SIGTERM)
        os.killpg(os.getpgid(stress_gpu_process.pid), signal.SIGTERM)
    except:
        pass

if __name__ == '__main__':
    cli()
