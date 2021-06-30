def is_between_times(low, high, cur):
    low = [int(x) for x in low.split(':')]
    high = [int(x) for x in high.split(':')]
    cur = [int(x) for x in cur.split(':')]

    if high > low:
        return cur > low and cur < high
    else:
        return cur > low or cur < high

def add_time(t, a):
    t = [int(x) for x in t.split(':')]
    a = [int(x) for x in a.split(':')]
    t[2] = t[2] + a[2]
    if t[2] > 59:
        t[2] -= 60
        t[1] += 1
    t[1] = t[1] + a[1]
    if t[1] > 59:
        t[2] -= 60
        t[0] += 1
    t[0] = t[0] + a[0]
    if t[0] > 23:
        t[0] -= 24
    return '{0:02}:{1:02}:{2:02}'.format(*t)