#!/usr/bin/python
#
# This file is part of IvPID.
# Copyright (C) 2015 Ivmech Mechatronics Ltd. <bilgi@ivmech.com>
#
# IvPID is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IvPID is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#title           :test_pid.py
#description     :python pid controller test
#author          :Caner Durmusoglu
#date            :20151218
#version         :0.1
#notes           :
#python_version  :2.7
#dependencies    : matplotlib, numpy, scipy
#==============================================================================

import PID
import time
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np
from scipy.interpolate import spline

trackbars = []
TB_KP = 0
TB_KI = 1
TB_KD = 2

knob_labels = ["Kp", "Ki", "Kd"]
knobs =       [.2,    0.0,  0.0]
knob_gain =   [ 1,      1,    1]





def test_pid(P = 0.2,  I = 0.0, D= 0.0, L=100, input_axis=None, output_axis=None):
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
    pid = PID.PID(P, I, D)

    pid.SetPoint=0.0
    pid.setSampleTime(0.01)

    END = L
    feedback = 0

    feedback_list = []
    time_list = []
    setpoint_list = []

    for i in range(1, END):
        pid.update(feedback)
        output = pid.output
        if pid.SetPoint > 0:
            feedback += (output - (1/i))
        if i>9:
            pid.SetPoint = 1
        time.sleep(0.02)

        feedback_list.append(feedback)
        setpoint_list.append(pid.SetPoint)
        time_list.append(i)

    time_sm = np.array(time_list)
    time_smooth = np.linspace(time_sm.min(), time_sm.max(), 300)
    feedback_smooth = spline(time_list, feedback_list, time_smooth)

    if (input_axis is None):
        input_axis, =plt.plot(time_smooth, feedback_smooth)
    else:
        input_axis.set_xdata(time_smooth)
        input_axis.set_ydata(feedback_smooth)   

    if output_axis is None:       
        output_axis, = plt.plot(time_list, setpoint_list)
    else:
        output_axis.set_xdata(time_list)
        output_axis.set_ydata(setpoint_list)   

    
    plt.xlim((0, L))
    plt.ylim((min(feedback_list)-0.5, max(feedback_list)+0.5))
    
    plt.ylim((1-0.5, 1+0.5))

    

    
    
    return input_axis, output_axis


def setup_plt():
    #Make room for sliders:
    fig, ax = plt.subplots()
    plt.subplots_adjust(left=0.25, bottom=0.25)
    plt.axis([0, 1, -10, 10])
    
    #Apply labels once
    plt.xlabel('time (s)')
    plt.ylabel('PID Controller Trying to Follow Input')
    plt.title('Pure Proportional Control')
    plt.grid(True)

    return fig

def setup_sliders(fig, signal1_axis, signal2_axis):    
    axcolor = 'lightgoldenrodyellow'
    ax_kp = plt.axes([0.25, 0.1, 0.65, 0.03], axisbg=axcolor)
    ax_ki = plt.axes([0.25, 0.15, 0.65, 0.03], axisbg=axcolor)
    ax_kd = plt.axes([0.25, 0.2,  0.65, 0.03], axisbg=axcolor)


    kp_slider = Slider(ax_kp, 'Kp', 0.0, 10.0, valinit=0.8)
    ki_slider = Slider(ax_ki, 'Ki', 0.0, 10.0, valinit=0.0)
    kd_slider = Slider(ax_kd, 'Kd', 0.0, 10.0, valinit=0.0)
  

    def update(val):
            signal1, signal2 = test_pid(kp_slider.val, ki_slider.val, kd_slider.val, L=100, input_axis=signal1_axis, output_axis=signal2_axis)
            fig.canvas.draw_idle()
    
    kp_slider.on_changed(update)
    ki_slider.on_changed(update)
    kd_slider.on_changed(update)
  



if __name__ == "__main__":
    fig = setup_plt()

    input_signal_ax, output_signal_ax = test_pid(.8, 0, 0.00, L=50)
    
    setup_sliders(fig, input_signal_ax, output_signal_ax)

    
    plt.show()
    
