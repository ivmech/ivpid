import PID
import json
import time
import sys
import signal
import requests


cpus = [15,63]
goal = "higher"
metric = "TranscodingMbps"
endpoint = 'http://192.168.122.137:8001/v1/data'
target_value = 0.4
#cpus = [1,49,2,50,3,51,4,52]
#goal = "lower"
#metric = "pkt-loss"
#endpoint = 'http://127.0.0.1:5000/latency_stats'
#target_value = 5.0

perc = 0.001
old_perc = perc
extension = 0.5
tolerance = 0

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


def test():
    print("The cache-sensitive app should run on cpus: ", cpus)
    time.sleep(2)

    freqs = []

    f = 900000
    for i in range(0, 12):
        f += 100000
        freqs.append(f)
    print freqs

    signal.signal(signal.SIGINT, signal_handler)

    prev_idx = 0
    freq = freqs[prev_idx]
    setfreq(freq)

    time_now = time.time()

    while True:
        print("Frequency: " +str(freq))
        changed = False
        changed_sc = False

        time.sleep(2)
        r = requests.get(endpoint)
        r.json()
        measurement = json.loads(r.text)
        feedback = measurement[metric]

        if target_value == 0:
            tolerance =  abs(extension)
        else:
            tolerance =  abs(perc*target_value)

        if (feedback >= (target_value - tolerance)) and (feedback <= (target_value + tolerance)):
            feedback = target_value

        if feedback == target_value:
            print("No change! Reached the target")
        else:
            if feedback < target_value and goal == "higher" and (prev_idx == len(freqs)-1):
                print("Can't go higher")
            elif feedback > target_value and goal == "lower" and (prev_idx == len(freqs)-1):
                print("Can't go higher")
            elif feedback > target_value and goal == "higher" and prev_idx == 0:
                print("Can't go lower")
            elif feedback < target_value and goal == "lower" and prev_idx == 0:
                print("Can't go lower")
            elif (feedback < target_value and goal == "higher") or (feedback > target_value and goal == "lower"):
                new_freq, new_idx = binarySearch(freqs, prev_idx, len(freqs)-1)
                changed = True
            elif (feedback > target_value and goal == "higher") or (feedback < target_value and goal == "lower"):
                new_freq, new_idx = binarySearch(freqs, 0, prev_idx)
                changed = True
            else:
                print("Shouldn't reach here!!!")

        if changed:
            freq = new_freq
            prev_idx = new_idx
            time_now = time.time()
        else:
            if (time.time() - time_now) >= 10:
                print("Second stage!")
                changed_sc, new_freq, new_idx = second_stage(freq, prev_idx, feedback, freqs)
                if changed_sc:
                    print("SC final: new_freq= " + str(new_freq) + " prev_idx= " + str(new_idx))
                    freq = new_freq
                    prev_idx = new_idx

                time_now = time.time()
            else:
                print("No change!")


        print("------")


def binarySearch(freqs, l, r):
    print("Binary Search!!!")
    global perc, extension

    while l <= r:
        mid = l + (r - l)/2;

        freq = freqs[mid]
        setfreq(freq)
        time.sleep(2)

        res = requests.get(endpoint)
        res.json()
        measurement = json.loads(res.text)
        feedback = measurement[metric]

        print("freq= " + str(freq) + " feedback= " + str(feedback))

        if target_value == 0:
            tolerance = abs(extension)
        else:
            tolerance = abs(perc*target_value)

        if (feedback >= (target_value - tolerance)) and (feedback <= (target_value + tolerance)):
            feedback = target_value

        print("feedback after tolerance : " + str(feedback))

        if feedback == target_value:
            return freq, mid
        elif (feedback < target_value and goal == "higher") or (feedback > target_value and goal == "lower"):
            l = mid + 1
        else:
            r = mid - 1


    #if we reach here, then there wasn't frequency that achieves the target_value, so return the last one which was the closest one and change the tolerance
    print("No frequency for the target")

    if mid > 0 and mid < (len(freqs) - 1):
        if target_value == 0:
            extension = abs(target_value - feedback) + 0.01
        else:
            perc = abs((target_value - feedback) / target_value) + 0.01
    return freq, mid


def second_stage(freq, idx, feedback, freqs):
    if not idx:
        return False, None, None
    else:
        while idx > 0:
            idx -= 1
            freq = freqs[idx]
            setfreq(freq)

            time.sleep(2)
            r = requests.get(endpoint)
            r.json()
            measurement = json.loads(r.text)
            new_feedback = measurement[metric]

            print("SC: freq= " + str(freq) + " new_feedback= " + str(new_feedback))

            if feedback == 0:
                tolerance =  abs(extension)
            else:
                tolerance =  abs(perc*feedback)


            if (new_feedback >= (feedback - tolerance)) and (new_feedback <= (feedback + tolerance)):
                continue
            else:
                idx += 1
                freq = freqs[idx]
                setfreq(freq)
                return True, freq, idx

        return True, freq, idx



if __name__ == "__main__":
    test()
