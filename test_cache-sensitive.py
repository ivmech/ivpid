import PID
import datetime
import time
import requests
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import BSpline, make_interp_spline 

def test_pid(P = 0.2,  I = 0.0, D= 0.0):
    """Self-test PID class

    .. note::
        ...
        for i in range(1, END):
            pid.update(feedback)
            output = pid.output
            if pid.SetPoint > 0:
                feedback += (output - (1/i))
            if i>9:
                pid.SetPoint = 1
            time.sleep(0.02)
        ---
    """
    r = requests.get('http://192.168.123.207:8001/v1/data')
    r.json()
    print(r.text)
    return

    pid = PID.PID(P, I, D)

    pid.SetPoint=0.0
    pid.setSampleTime(0.01)

    feedback = 4.0

    feedback_list = []
    time_list = []
    setpoint_list = []

    freqs = [ 1800000, 2800000, 3800000, 4800000, 5800000, 6800000, 7800000,]
    pkt_loss = {
        1800000: 2.3,
        2800000: 2,
        3800000: 1.8,
        4800000: 1,
        5800000: 0.5,
        6800000: 0.5,
        7800000: 0.5
    }

    prev_idx = 0
    while True:
        pid.update(feedback)
        output = pid.output
        print("Output:" + str(output))
        if output < 0:
            if i == 1:
                freq = freqs[0]
                prev_idx = 0
            elif prev_idx < len(freqs) - 1:
                freq = freqs[prev_idx + 1]
                prev_idx = prev_idx + 1
            else:
                freq = freqs[prev_idx]
        elif output > 0:
            if i == 1:
                freq = freqs[0]
                prev_idx = 0
            elif prev_idx > 0:
                freq = freqs[prev_idx - 1]
                prev_idx = prev_idx - 1
            else:
                freq = freqs[prev_idx]
        else:
            freq = freqs[prev_idx]

        feedback = pkt_loss[freq]
        time.sleep(0.02)
        print("Feedback:" + str(feedback))

        feedback_list.append(feedback)
        setpoint_list.append(pid.SetPoint)
        time_list.append(i)

    time_sm = np.array(time_list)
    time_smooth = np.linspace(time_sm.min(), time_sm.max(), 300)


if __name__ == "__main__":
    test_pid(1.2, 1, 0.001)
