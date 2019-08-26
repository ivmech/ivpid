import PID
import json
import time
import sys
import signal
import requests


#cpus = [0,48]
#goal = "higher"
#metric = "TranscodingMbps"
#endpoint = 'http://192.168.122.137:8001/v1/data'
#target_value = 0.7
cpus = [1,49,2,50,3,51,4,52]
goal = "lower"
metric = "pkt-loss"
endpoint = 'http://127.0.0.1:5000/latency_stats'
target_value = 5.0

def signal_handler(sig, frame):
    for cpu in cpus:
        fmax = open("/sys/devices/system/cpu/cpu" + str(cpu) + "/cpufreq/cpuinfo_max_freq","r")
        max_freq = int(fmax.readline().strip("\n"))
        fmax.close()
        fmin = open("/sys/devices/system/cpu/cpu" + str(cpu) + "/cpufreq/cpuinfo_min_freq","r")
        min_freq = int(fmin.readline().strip("\n"))
        fmin.close()

        fmax = open("/sys/devices/system/cpu/cpu" + str(cpu) + "/cpufreq/scaling_max_freq","w")
        fmin = open("/sys/devices/system/cpu/cpu" + str(cpu) + "/cpufreq/scaling_min_freq","w")

        fmin.write(str(min_freq))
        fmin.close()
        fmax.write(str(max_freq))
        fmax.close()

    sys.exit(0)


def setfreq(freq):
    for cpu in cpus:
        fmax = open("/sys/devices/system/cpu/cpu" + str(cpu) + "/cpufreq/scaling_max_freq","r")
        fmin = open("/sys/devices/system/cpu/cpu" + str(cpu) + "/cpufreq/scaling_min_freq","r")

        max_freq = int(fmax.readline().strip("\n"))
        min_freq = int(fmin.readline().strip("\n"))
        fmax.close()
        fmin.close()

        fmax = open("/sys/devices/system/cpu/cpu" + str(cpu) + "/cpufreq/scaling_max_freq","w")
        fmin = open("/sys/devices/system/cpu/cpu" + str(cpu) + "/cpufreq/scaling_min_freq","w")
        if freq <= min_freq:
            fmin.write(str(freq))
            fmin.close()
            fmax.write(str(freq))
            fmax.close()
        else:
            fmax.write(str(freq))
            fmax.close()
            fmin.write(str(freq))
            fmin.close()


def test_pid(P = 0.2,  I = 0.0, D= 0.0):
    """Self-test PID class

    """
    print("The cache-sensitive app should run on cpus: ", cpus)
    time.sleep(2)

    feedback_list = []
    setpoint_list = []
    freqs = []

    f = 900000
    for i in range(0, 25):
        f += 100000
        freqs.append(f)


    signal.signal(signal.SIGINT, signal_handler)

    prev_idx = 0
    freq = freqs[prev_idx]
    setfreq(freq)
    time.sleep(2)

    r = requests.get(endpoint)
    r.json()
    measurement = json.loads(r.text)

    pid = PID.PID(P, I, D)

    pid.SetPoint = target_value
    pid.setSampleTime(0.01)

    feedback = measurement[metric]
    prev_output = 0
    y = 1
    count = 0

    while True:
        no_change = False
        print("Real Feedback: " + str(feedback))
        if (feedback > (pid.SetPoint - abs(0.1*pid.SetPoint))) and (feedback < (pid.SetPoint + abs(0.1*pid.SetPoint))):
            feedback = pid.SetPoint
        pid.update(feedback)
        print("Feedback: " + str(feedback))
        output = pid.output
        print("Output: " + str(output))
        print("------")

        if count == 1:
            str_output = str(abs(output))
            digits = len(str_output.split('.')[0])
            y = abs(output) * 2.5
            #for k in range(0, digits):
            #    y *= 10.0
            print("Divisor: ", str(y))

        count += 1

        #convert pid output to frequency

        diff = output - prev_output
        print("Diff: " + str(diff))

        # find how many steps we need to increase/decrease the current index of the freqs list
        i = int(round(abs(output) * len(freqs) / y))
        if i == 0:
            i = 1
        #print("i: " + str(i))


        if feedback == pid.SetPoint:
            no_change = True
        elif (output > 0 and goal == "higher") or (output < 0 and goal == "lower"):
            if prev_idx + i < len(freqs):
                freq = freqs[prev_idx + i]
                prev_idx = prev_idx + i
            elif prev_idx != len(freqs) - 1:
                freq = freqs[len(freqs) - 1]
                prev_idx = len(freqs) - 1
            else:
                no_change = True
        elif (output < 0 and goal == "higher") or (output > 0 and goal == "lower"):
            if prev_idx - i >= 0:
                freq = freqs[prev_idx - i]
                prev_idx = prev_idx - i
            elif prev_idx != 0:
                freq = freqs[0]
                prev_idx = 0
            else:
                no_change = True
        else:
            no_change = True

        prev_output = output

        print("Frequency: " + str(freq))
        if not no_change:
            setfreq(freq)
        else:
            print("No change!")


        time.sleep(2)
        r = requests.get(endpoint)
        r.json()
        measurement = json.loads(r.text)
        feedback = measurement[metric]

        feedback_list.append(feedback)
        setpoint_list.append(pid.SetPoint)



if __name__ == "__main__":
    test_pid(10.0, 1, 0.001)
