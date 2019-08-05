import PID
import json
import time
import sys
import signal
import requests


def signal_handler(sig, frame):
    for cpu in range(0,4):
        fmax = open("/sys/devices/system/cpu/cpu" + str(cpu) + "/cpufreq/scaling_max_freq","w")
        fmin = open("/sys/devices/system/cpu/cpu" + str(cpu) + "/cpufreq/scaling_min_freq","w")

        fmin.write("1000000")
        fmax.write("3700000")
        fmin.close
        fmax.close

    sys.exit(0)

def test_pid(P = 0.2,  I = 0.0, D= 0.0):
    """Self-test PID class

    """
    print("The cache-sensitive app should run on cpus 0-3!!")
    time.sleep(2)

    r = requests.get('http://192.168.122.137:8001/v1/data')
    r.json()
    measurement = json.loads(r.text)

    pid = PID.PID(P, I, D)

    pid.SetPoint=0.9
    pid.setSampleTime(0.01)

    feedback = measurement["TranscodingMbps"]

    feedback_list = []
    setpoint_list = []
    freqs = []

    f = 900000
    for i in range(0, 28):
        f += 100000
        freqs.append(f)

    prev_idx = 0
    freq = -1
    signal.signal(signal.SIGINT, signal_handler)

    while True:
        no_change = False
        pid.update(feedback)
        output = pid.output
        print("Output:" + str(output))

        # Assumption: bigger frequency -> better performance
        #TODO: find a smart way to convert pid output to frequency
        if output > 0:
            if prev_idx < len(freqs) - 1:
                freq = freqs[prev_idx + 1]
                prev_idx = prev_idx + 1
            else:
                no_change = True
        elif output < 0:
            if prev_idx > 0:
                freq = freqs[prev_idx - 1]
                prev_idx = prev_idx - 1
            else:
                if freq == freqs[0]:
                    no_change = True
                else:
                    freq = freqs[0]
        else:
            no_change = True


        print("Frequency:" + str(freq))
        if not no_change:
            for cpu in range(0,4):
                fmax = open("/sys/devices/system/cpu/cpu" + str(cpu) + "/cpufreq/scaling_max_freq","r+")
                fmin = open("/sys/devices/system/cpu/cpu" + str(cpu) + "/cpufreq/scaling_min_freq","r+")

                max_freq = int(fmax.read())
                min_freq = int(fmin.read().strip())
                fmax.seek(0)
                fmin.seek(0)

                if freq <= min_freq:
                    fmin.write(str(freq))
                    fmax.write(str(freq))
                else:
                    fmax.write(str(freq))
                    fmin.write(str(freq))

                fmax.close
                fmin.close

        time.sleep(1)
        r = requests.get('http://192.168.122.137:8001/v1/data')
        r.json()
        measurement = json.loads(r.text)
        feedback = measurement["TranscodingMbps"]
        print("Feedback:" + str(feedback))

        feedback_list.append(feedback)
        setpoint_list.append(pid.SetPoint)



if __name__ == "__main__":
    test_pid(1.2, 1, 0.001)
