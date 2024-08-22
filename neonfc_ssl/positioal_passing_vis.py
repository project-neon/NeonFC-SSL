import socket
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from threading import Thread
from matplotlib import colormaps

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))


def passing_targets():
    dx, dy = 0.1, 0.1
    # Area 0
    lwx, upx = 4.5, 9
    lwy, upy = 0, 2

    x = np.linspace(lwx+dx, upx-dx, 18)
    y = np.linspace(lwy+dy, upy-dy, 8)
    xs, ys = np.meshgrid(x, y)
    a0 = np.transpose(np.array([xs.flatten(), ys.flatten()]))

    # Area 1
    lwx, upx = 4.5, 8
    lwy, upy = 2, 4

    x = np.linspace(lwx+dx, upx-dx, 14)
    y = np.linspace(lwy+dy, upy-dy, 10)
    xs, ys = np.meshgrid(x, y)
    a1 = np.transpose(np.array([xs.flatten(), ys.flatten()]))

    # Area 2
    lwx, upx = 4.5, 9
    lwy, upy = 4, 6

    x = np.linspace(lwx+dx, upx-dx, 18)
    y = np.linspace(lwy+dy, upy-dy, 8)
    xs, ys = np.meshgrid(x, y)
    a2 = np.transpose(np.array([xs.flatten(), ys.flatten()]))

    return np.concatenate((a0, a1, a2))


fig = plt.figure()
ax1 = fig.add_subplot(1, 1, 1)
ax1.set_xlim(0, 9)
ax1.set_ylim(0, 6)
scat = ax1.scatter(*np.transpose(passing_targets()), c=np.random.rand((passing_targets().shape[0])), cmap='YlGn')

data = [[np.array([1, 1])], [np.array([1, 1])], np.array([1, 1])]


def receiver(d):
    while True:
        new_data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes

        if new_data is None:
            continue

        new_data = new_data.decode('ascii')
        # MESSAGE = 'a'.join([
        #     ';'.join([f"%0.2f,%0.2f" % (r.x, r.y) for r in self.passable_robots]),
        #     ';'.join([f"%0.2f,%0.2f" % (r.x, r.y) for r in self.intercepting_robots]),
        #     "%0.2f,%0.2f" % (self._robot.x, self._robot.y)
        # ])
        try:
            new_data=new_data.split('a')
            d[0] = []
            for r in new_data[0].split(';'):
                rc = r.split(',')
                d[0].append(np.array([float(rc[0]), float(rc[1])]))

            d[1] = []
            for r in new_data[1].split(';'):
                rc = r.split(',')
                d[1].append(np.array([float(rc[0]), float(rc[1])]))

            d[2] = []
            for r in new_data[2].split(';'):
                rc = r.split(',')
                d[2]=np.array([float(rc[0]), float(rc[1])])

        except ValueError:
            continue


def animate(i):
    p = passing_targets()
    # scat.set_array(1*pass_probability(p))
    # scat.set_array(1*goal_probability(p))
    # scat.set_array(1*receiving_probability(p))
    print(data[2])
    scat.set_array(1*receiving_probability(p)*pass_probability(p)*goal_probability(p))
    return scat,


robot = np.array([4.5, 3])
intercepting_robots = [np.array([5.5, 4]), np.array([5.5, 2]), np.array([6.5, 3]), np.array([8.7, 3])]


def pass_probability(p, v=False):
    dp = p - data[2]
    px = dp[:, 0]
    py = dp[:, 1]

    norm = px * px + py * py
    total = np.inf*np.ones(p.shape[0])

    for op in data[1]:
        u = np.divide((op[0] - data[2][0]) * px + (op[1] - data[2][1]) * py, norm)
        if v:
            print('u', u)
        u = np.minimum(np.maximum(u, 0), 1)
        if v:
            print('u', u)

        dx = data[2][0] + u * px - op[0]
        dy = data[2][1] + u * py - op[1]

        total = np.minimum(dx**2 + dy**2, total)
        if v:
            print('total', total)

    # return total
    return np.minimum(np.sqrt(total), 1)


def receiving_probability(p):
    closest_teammate_dist = np.inf * np.ones(p.shape[0])
    for r in data[0]:
        closest_teammate_dist = np.minimum(np.sum(np.square(r-p), axis=1), closest_teammate_dist)

    closest_opponent_dist = np.inf * np.ones(p.shape[0])
    for r in data[1]:
        closest_opponent_dist = np.minimum(np.sum(np.square(r-p), axis=1), closest_opponent_dist)

    return closest_opponent_dist > closest_teammate_dist


def goal_probability(p, v=False):
    dp = np.array([9, 3]) - p
    px = dp[:, 0]
    py = dp[:, 1]

    norm = px * px + py * py
    total = np.inf*np.ones(p.shape[0])

    for op in data[1]:
        u = np.divide((op[0] - p[:, 0]) * px + (op[1] - p[:, 1]) * py, norm)
        if v:
            print('u', u)
        u = np.minimum(np.maximum(u, 0), 1)
        if v:
            print('u', u)

        dx = p[:, 0] + u * px - op[0]
        dy = p[:, 1] + u * py - op[1]

        total = np.minimum(dx**2 + dy**2, total)
        if v:
            print('total', total)

    # return total
    return np.minimum(np.sqrt(total), 1)


client = Thread(target=receiver, args=(data,))
client.start()
ani = animation.FuncAnimation(fig, animate, interval=10)
p = passing_targets()
# print(p.shape)
# scat.set_array(goal_probability(p)*pass_probability(p))
# vs = [float(i) for i in str((goal_probability(p)*pass_probability(p)).tolist()).encode('utf-8').decode('utf-8')[1:-1].split(',') if i]
# print(len(vs))
# scat.set_array(vs)
# print(pass_probability(np.array([[5, 3], [7, 3]]), v=True))
fig.colorbar(scat, ax=ax1)
plt.show()
# plt.gray()
