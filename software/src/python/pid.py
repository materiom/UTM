# Digital PID class
# from https://thingsdaq.org/2022/04/07/digital-pid-controller/



class PID:
    def __init__(self, Ts, kp, ki, kd, umax=1, umin=-1, tau=0):
        #
        self._Ts = Ts  # Sampling period (s)
        self._kp = kp  # Proportional gain
        self._ki = ki  # Integral gain
        self._kd = kd  # Derivative gain
        self._umax = umax  # Upper output saturation limit
        self._umin = umin  # Lower output saturation limit
        self._tau = tau  # Derivative term filter time constant (s)
        #
        self._eprev = [0, 0]  # Previous errors e[n-1], e[n-2]
        self._uprev = 0  # Previous controller output u[n-1]
        self._udfiltprev = 0  # Previous derivative term filtered value

    def control(self, ysp, y, uff=0):
        #
        # Calculating error e[n]
        e = ysp - y
        # Calculating proportional term
        up = self._kp * (e - self._eprev[0])
        # Calculating integral term (with anti-windup)
        ui = self._ki*self._Ts * e
        if (self._uprev+uff >= self._umax) or (self._uprev+uff <= self._umin):
            ui = 0
        # Calculating derivative term
        ud = self._kd/self._Ts * (e - 2*self._eprev[0] + self._eprev[1])
        # Filtering derivative term
        udfilt = (
            self._tau/(self._tau+self._Ts)*self._udfiltprev +
            self._Ts/(self._tau+self._Ts)*ud
        )
        # Calculating PID controller output u[n]
        u = self._uprev + up + ui + udfilt + uff
        # Updating previous time step errors e[n-1], e[n-2]
        self._eprev[1] = self._eprev[0]
        self._eprev[0] = e
        # Updating previous time step output value u[n-1]
        self._uprev = u - uff
        # Updating previous time step derivative term filtered value
        self._udfiltprev = udfilt
        # Limiting output (just to be safe)
        if u < self._umin:
            u = self._umin
        elif u > self._umax:
            u = self._umax
        # Returning controller output at current time step
        return u