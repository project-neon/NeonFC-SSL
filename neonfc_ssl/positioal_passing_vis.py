import socket
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as patches
from threading import Thread
from matplotlib import colormaps

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
UDP_PORT2 = 5006

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock2.bind((UDP_IP, UDP_PORT2))


def passing_targets():
    dx, dy = 0.1, 0.1
    # Area 0
    lwx, upx = 4.5, 9
    lwy, upy = 0, 2

    x = np.linspace(lwx + dx, upx - dx, 18)
    y = np.linspace(lwy + dy, upy - dy, 8)
    xs, ys = np.meshgrid(x, y)
    a0 = np.transpose(np.array([xs.flatten(), ys.flatten()]))

    # Area 1
    lwx, upx = 4.5, 8
    lwy, upy = 2, 4

    x = np.linspace(lwx + dx, upx - dx, 14)
    y = np.linspace(lwy + dy, upy - dy, 10)
    xs, ys = np.meshgrid(x, y)
    a1 = np.transpose(np.array([xs.flatten(), ys.flatten()]))

    # Area 2
    lwx, upx = 4.5, 9
    lwy, upy = 4, 6

    x = np.linspace(lwx + dx, upx - dx, 18)
    y = np.linspace(lwy + dy, upy - dy, 8)
    xs, ys = np.meshgrid(x, y)
    a2 = np.transpose(np.array([xs.flatten(), ys.flatten()]))

    return np.concatenate((a0, a1, a2))


fig = plt.figure()
ax1 = fig.add_subplot(1, 1, 1)
# ax1.set_xlim(0, 9)
# ax1.set_ylim(0, 6)
scat = ax1.scatter(*np.transpose(passing_targets()), c=np.random.rand((passing_targets().shape[0])), cmap='YlGn')


def gen_triangles(center, radius):
    # P1: [robot.x, 2 * radius + robot.y]
    # P2: [robot.x - (sin(60)  2 * radius), robot.y - radius]
    # P3: [robot.x + (sin(60)  2 * radius), robot.y - radius]

    return [
        [center[0], 2 * radius + center[1]],
        [center[0] - 1.7 * radius, center[1] - radius],
        [center[0] + 1.7 * radius, center[1] - radius]
    ]


r = 0.09
field_w = 6
field_h = 9
h05 = field_w / 2

opponents_poly = [gen_triangles((0, 0), .18 + 0.1) for _ in range(6)]
opponents_patch = [patches.Polygon(p, closed=True, ec='r') for p in opponents_poly]
for p in opponents_patch:
    ax1.add_patch(p)
paths_patch = [[[0, 0], [0, 0]] for _ in range(6)]
paths_patch = [patches.Polygon(p, closed=False, ec='b') for p in paths_patch]
for p in paths_patch:
    ax1.add_patch(p)

field = [
    [0, 0],
    [field_h, 0],
    [field_h, field_w],
    [0, field_w],
]

field_poly = [[
    [-0.3 + r, -0.3 + r],
    [field_h + 0.3 - r, -0.3 + r],
    [field_h + 0.3 - r, field_w + 0.3 - r],
    [-0.3 + r, field_w + 0.3 - r]
], [
    [9 - r, h05 - 0.52 - r],
    [9 - (-0.2 - r), h05 - 0.52 - r],
    [9 - (-0.2 - r), h05 + 0.52 + r],
    [9 - r, h05 + 0.52 + r],
    [9 - r, h05 + 0.5 - r],
    [9 - (r - 0.18), h05 + 0.5 - r],
    [9 - (r - 0.18), h05 - 0.5 + r],
    [9 - r, h05 - 0.5 + r]
], [
    [r, h05 - 0.52 - r],
    [-0.2 - r, h05 - 0.52 - r],
    [-0.2 - r, h05 + 0.52 + r],
    [r, h05 + 0.52 + r],
    [r, h05 + 0.5 - r],
    [r - 0.18, h05 + 0.5 - r],
    [r - 0.18, h05 - 0.5 + r],
    [r, h05 - 0.5 + r]
]]

field_patch = patches.Polygon(field, closed=True, ec='black', fill=False)
ax1.add_patch(field_patch)
patch = patches.Polygon(field_poly[0], closed=True, ec='r', fill=False)
ax1.add_patch(patch)
patch2 = patches.Polygon(field_poly[1], closed=True, ec='r', fill=False)
ax1.add_patch(patch2)
patch3 = patches.Polygon(field_poly[2], closed=True, ec='r', fill=False)
ax1.add_patch(patch3)

data = [[np.array([1, 1])], [np.array([1, 1])], np.array([1, 1])]
paths = [[[0, 0], [0, 0]] for _ in range(6)]


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
            new_data = new_data.split('a')
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
                d[2] = np.array([float(rc[0]), float(rc[1])])

        except ValueError:
            continue


def path_receiver(p):
    while True:
        new_data, addr = sock2.recvfrom(1024)  # buffer size is 1024 bytes

        if new_data is None:
            continue

        new_data = new_data.decode('ascii')
        # MESSAGE = 'a'.join([
        #     ';'.join([f"%0.2f,%0.2f" % (r.x, r.y) for r in self.passable_robots]),
        #     ';'.join([f"%0.2f,%0.2f" % (r.x, r.y) for r in self.intercepting_robots]),
        #     "%0.2f,%0.2f" % (self._robot.x, self._robot.y)
        # ])
        # paths = []
        # for path in all_paths:
        #     paths.append(';'.join(f"%0.2f,%0.2f" % (point[0], point[1]) for point in path))
        # MESSAGE = 'a'.join(paths)
        try:
            new_data = new_data.split('a')
            for idx in range(len(p)):
                p[idx] = []
                if idx < len(new_data):
                    for point in new_data[idx].split(';'):
                        rc = point.split(',')
                        p[idx].append([float(rc[0]), float(rc[1])])
                else:
                    p[idx] = [[0, 0], [0, 0]]

            print(p)

        except ValueError:
            continue


def animate(i):
    p = passing_targets()
    # scat.set_array(1*pass_probability(p))
    # scat.set_array(1*goal_probability(p))
    # scat.set_array(1*receiving_probability(p))
    scat.set_array(1 * receiving_probability(p) * pass_probability(p) * goal_probability(p))
    update_ops()
    update_paths()
    out = [scat]
    out.extend(opponents_patch)
    return out.extend(paths_patch)


robot = np.array([4.5, 3])
intercepting_robots = [np.array([5.5, 4]), np.array([5.5, 2]), np.array([6.5, 3]), np.array([8.7, 3])]


def pass_probability(p, v=False):
    dp = p - data[2]
    px = dp[:, 0]
    py = dp[:, 1]

    norm = px * px + py * py
    total = np.inf * np.ones(p.shape[0])

    for op in data[1]:
        u = np.divide((op[0] - data[2][0]) * px + (op[1] - data[2][1]) * py, norm)
        if v:
            print('u', u)
        u = np.minimum(np.maximum(u, 0), 1)
        if v:
            print('u', u)

        dx = data[2][0] + u * px - op[0]
        dy = data[2][1] + u * py - op[1]

        total = np.minimum(dx ** 2 + dy ** 2, total)
        if v:
            print('total', total)

    # return total
    return np.minimum(np.sqrt(total), 1)


def receiving_probability(p):
    closest_teammate_dist = np.inf * np.ones(p.shape[0])
    for r in data[0]:
        closest_teammate_dist = np.minimum(np.sum(np.square(r - p), axis=1), closest_teammate_dist)

    closest_opponent_dist = np.inf * np.ones(p.shape[0])
    for r in data[1]:
        closest_opponent_dist = np.minimum(np.sum(np.square(r - p), axis=1), closest_opponent_dist)

    return closest_opponent_dist > closest_teammate_dist


def goal_probability(p, v=False):
    dp = np.array([9, 3]) - p
    px = dp[:, 0]
    py = dp[:, 1]

    norm = px * px + py * py
    total = np.inf * np.ones(p.shape[0])

    for op in data[1]:
        u = np.divide((op[0] - p[:, 0]) * px + (op[1] - p[:, 1]) * py, norm)
        if v:
            print('u', u)
        u = np.minimum(np.maximum(u, 0), 1)
        if v:
            print('u', u)

        dx = p[:, 0] + u * px - op[0]
        dy = p[:, 1] + u * py - op[1]

        total = np.minimum(dx ** 2 + dy ** 2, total)
        if v:
            print('total', total)

    # return total
    return np.minimum(np.sqrt(total), 1)


def update_ops():
    poly = [gen_triangles(c, .18 + 0.1) for c in data[1]]
    for idx, p in enumerate(opponents_patch):
        if idx < len(poly):
            p.set(xy=poly[idx], alpha=1, fill=None, ec='r')
        else:
            p.set_alpha(0)


def update_paths():
    print(paths)
    for idx, p in enumerate(paths_patch):
        if paths[idx] == []:
            p.set(xy=[[0,0], [0,0]], fill=False, ec='b', closed=False)
        else:
            p.set(xy=paths[idx], fill=False, ec='b', closed=False)


client = Thread(target=receiver, args=(data,))
client.start()
client2 = Thread(target=path_receiver, args=(paths,))
client2.start()
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
