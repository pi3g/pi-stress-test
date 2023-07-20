#!/bin/bash
echo "Setting up automatic start of the Stress Test on every boot using crontab"
(crontab -l 2>/dev/null || true; echo "@reboot sleep 15 && export DISPLAY=:0 && sudo -E python $PWD/stress_test.py -r >> $PWD/stress_test.log 2>&1") | crontab -
