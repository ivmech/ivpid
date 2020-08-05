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

# title           :PID.py
# description     :python pid controller
# author          :Caner Durmusoglu
# date            :20151218
# version         :0.2
# notes           :
# python_version  :3.8
# ==============================================================================

"""Ivmech PID Controller is simple implementation of a Proportional-Integral-Derivative (PID) Controller in the Python Programming Language.
More information about PID Controller: http://en.wikipedia.org/wiki/PID_controller
"""
import time

class PID:
    """PID Controller
    """

    # PID coefficients (gain)
    Kp = 0.2
    Ki = 0.0
    Kd = 0.0

    # Target value
    target = 0.0

    # Sample state
    last_time = 0
    current_time = 0
    sample_time = 0.00
    # Current values for the PID
    PTerm = 0.0
    ITerm = 0.0
    DTerm = 0.0
    # Difference between the target and the sample
    last_error = 0.0

    # Windup Guard
    windup_guard = 20.0

    output = 0.0

    def __init__(self, p=0.2, i=0.0, d=0.0, sample_time=0.0, current_time=None):
        self.Kp = p
        self.Ki = i
        self.Kd = d
        self.sample_time = sample_time

        # Initialize dynamically computed data members
        self.clear(current_time)

    def clear(self, current_time=None):
        """Clears PID computations, coefficients, and target"""
        self.target = 0.0
        self.PTerm = 0.0
        self.ITerm = 0.0
        self.DTerm = 0.0
        self.last_error = 0.0
        self.windup_guard = 20.0
        self.output = 0.0
        self.current_time = current_time if current_time is not None else time.time()
        self.last_time = self.current_time

    def update(self, feedback_value, current_time=None):
        """Calculates PID value for given reference feedback.

        .. math::
            u(t) = K_p e(t) + K_i \int_{0}^{t} e(t)dt + K_d {de}/{dt}

        .. figure:: images/pid_1.png
           :align:   center

           Test PID with Kp=1.2, Ki=1, Kd=0.001 (test_pid.py)

        """
        error = self.target - feedback_value
        self.current_time = current_time if current_time is not None else time.time()
        delta_time = self.current_time - self.last_time

        if delta_time >= self.sample_time:

            self.PTerm =  error
            self.ITerm += error * delta_time

            # Clamp ITerm between [-windup_guard, windup_guard]
            self.ITerm = min(max(self.ITerm, -self.windup_guard), self.windup_guard)

            self.DTerm = 0.0
            if delta_time > 0:
                delta_error = error - self.last_error
                self.DTerm = delta_error / delta_time

            # Remember last time and last error for next calculation
            self.last_time = self.current_time
            self.last_error = error

            self.output = (self.Kp * self.PTerm) + (self.Ki * self.ITerm) + (self.Kd * self.DTerm)

        return self.output

    def set_p_coefficient(self, proportional_gain):
        """Determines how aggressively the PID reacts to the current error with setting Proportional Gain"""
        self.Kp = proportional_gain

    def set_i_coefficient(self, integral_gain):
        """Determines how aggressively the PID reacts to the current error with setting Integral Gain"""
        self.Ki = integral_gain

    def set_d_coefficient(self, derivative_gain):
        """Determines how aggressively the PID reacts to the current error with setting Derivative Gain"""
        self.Kd = derivative_gain

    def set_target(self, new_target):
        """The target value for the output of the PID"""
        self.target = new_target

    def set_windup(self, windup):
        """Integral windup, also known as integrator windup or reset windup,
        refers to the situation in a PID feedback controller where
        a large change in setpoint occurs (say a positive change)
        and the integral terms accumulates a significant error
        during the rise (windup), thus overshooting and continuing
        to increase as this accumulated error is unwound
        (offset by errors in the other direction).
        The specific problem is the excess overshooting.
        """
        self.windup_guard = windup

    def set_sample_time(self, sample_time):
        """PID that should be updated at a regular interval.
        Based on a pre-determined sample time, the PID decides if it should compute or return
        immediately. Setting `sample_time` to zero effectively forces PID to recompute on every
        call, which might be desirable if the client code handles the waiting itself.
        """
        self.sample_time = sample_time
