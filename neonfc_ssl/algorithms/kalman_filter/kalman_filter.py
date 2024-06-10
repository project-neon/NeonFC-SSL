import numpy as np


class KalmanFilter:
    def __init__(self, var_size, ctrl_size, obs_size):
        self._A = np.zeros([var_size, var_size])
        self._At = np.transpose(self._A)

        self._B = np.zeros([var_size, ctrl_size])

        self._C = np.zeros([obs_size, var_size])
        self._Ct = np.transpose(self._C)

        self._R = .1 * np.identity(var_size)
        self._Q = .003 * np.identity(obs_size)

        self.belief = np.zeros([var_size, 1])
        self.uncert = np.zeros([var_size, var_size])

        self.n = var_size

    def change_matrices(self, A=None, B=None, C=None):
        if A is not None:
            self._A = A
            self._At = A.transpose()

        if B is not None:
            self._B = B

        if C is not None:
            self._C = C
            self._Ct = C.transpose()

    def predict(self, ctrl):
        self.belief = np.dot(self._A, self.belief) + np.dot(self._B, ctrl)
        self.uncert = np.dot(np.dot(self._A, self.uncert), self._At) + self._R

    def correct(self, obs):
        K = np.dot(np.dot(self.uncert, self._Ct), np.linalg.inv(np.dot(np.dot(self._C, self.uncert), self._Ct)+self._Q))
        self.belief = self.belief + np.dot(K, obs - np.dot(self._C, self.belief))
        self.uncert = np.dot(np.identity(self.n) - np.dot(K, self._C), self.uncert)

    def __call__(self, ctrl, obs):
        self.predict(ctrl)
        self.correct(obs)
        return self.belief
