# pi3g Raspberry Stress Test
This stress test uses the same method as described on this website: https://www.raspberrypi.com/news/thermal-testing-raspberry-pi-4/  
For ease of use the test provides a graphical overlay, where you can switch between stressing both the GPU and CPU or the CPU only and set the SOC Temperature Limit.

## Installation
1. Clone this repository to your local machine using:
    ```sh
    git clone https://github.com/pi3g/pi-stress-test
    ```
2. Install prerequisites
    ```sh
    pip install pysimplegui gpiozero
    sudo apt install stress-ng mesa-utils
    ```
3. Set DISPLAY Env variable (only necessary if connected via SSH)
    ```sh
    export DISPLAY=:0
    ```
4. Start script
    ```sh
    python stress_test.py
    ```
    For setting the Temperature Limit the Script needs root permissions (to edit /boot/config.txt). The `-r` / `--autoreboot` option will restart the Pi automatically after editing the temperature limit to apply it.
    ```
    sudo -E python stress_test.py -r
    ```
    For headless usage use `--no-gui`. To edit the temperature limit you'll have to manually edit or insert `temp_limit=<limit>` in `/boot/config.txt`
5. (Optional) Setup autostart
    With `autostart.sh` you can automatically let the script run at boot using crontab
    ```
    bash autostart.sh
    ```
    To remove the script from autostart use `crontab -e` and remove this line:  
    `@reboot sleep 15 && export DISPLAY=:0 && sudo -E python $PWD/stress_test.py -r >> $PWD/stress_test.log 2>&1`
