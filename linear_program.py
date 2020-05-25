from mip import Model, xsum, maximize, BINARY, INTEGER
import math

NUM_SEATS = 12
ROW_SIZE = 3
AISLE_FUDGE_FACTOR = 5 #feet
SEAT_DISTANCE = 3 #feet

NUM_ROTATION_DAYS = 4


def solve_linear_model():
    m = Model()

    d = [[distance_bw_seats(i, j) for j in range(NUM_SEATS)] for i in range(NUM_SEATS)]
    w = [[m.add_var(var_type=BINARY) for j in range(NUM_SEATS)] for i in range(NUM_SEATS)] # 1 = same day, 0 = else
    n = [m.add_var(var_type=BINARY) for i in range(NUM_SEATS)]
    # t1 = [[m.add_var(var_type=INTEGER) for j in range(NUM_SEATS)] for i in range(NUM_SEATS)]
    # t2 = [[m.add_var(var_type=INTEGER) for j in range(NUM_SEATS)] for i in range(NUM_SEATS)]

    m.objective = maximize(xsum([w[i][j] * d[i][j] for j in range(NUM_SEATS) if j != i] for i in range(NUM_SEATS)))

    for i in range(NUM_SEATS):
        # you have to show up on the same day as yourself
        m += w[i][i] == 1

    for i in range(NUM_SEATS):
        for j in range(i, NUM_SEATS):
            # commutative property: weights should be match both ways
            m += w[i][j] == w[j][i]

    for i in range(NUM_SEATS):
        for j in range(NUM_SEATS):
            if i != j:
                # 6 feet constraint
                if d[i][j] < 6/SEAT_DISTANCE:
                    m += w[i][j] == 0

    for i in range(NUM_SEATS):
        for j in range(NUM_SEATS):
            for k in range(NUM_SEATS):
                # transitive property
                m += w[i][j] + w[i][k] - 1 <= w[j][k]
                # m += w[j][k] <= t1[j][k] + t2[j][k]
                # m += t1[j][k] - t2[j][k] == w[i][j] + w[i][k] - 1
                # m += t1[j][k] >= 0

    s = [xsum(w[j][i] for j in range(i)) for i in range(NUM_SEATS)]
    ss = [s[i]/(i+1) for i in range(NUM_SEATS)]
    for i in range(NUM_SEATS):
        m += n[i] >= 1-ss[i]-.999
        m += n[i] <= 1-ss[i]
    # total number of days constraint
    m += xsum(n[i] for i in range(NUM_SEATS)) <= NUM_ROTATION_DAYS

    m.optimize()

    print(f"num sol:{m.num_solutions}")

    if m.num_solutions == 0:
        return

    print("sol_w")
    sol_w = [[w[i][j].x for j in range(NUM_SEATS)] for i in range(NUM_SEATS)]
    for row in sol_w:
        print(row)
    print("sol_n")
    sol_n = [n[i].x for i in range(NUM_SEATS)]
    print(sol_n)

    total_days = 0
    for i in range(NUM_SEATS):
        new_days = 1
        for j in range(i):
            if w[j][i].x == 1.0:
                new_days = 0
        total_days += new_days
    print(f"total days:{total_days}")

    print("----Schedule----")
    seat_to_day = {}
    day = 0
    for i in range(NUM_SEATS):
        for j in range(i):
            if w[j][i].x == 1.0:
                seat_to_day[i] = seat_to_day[j]
                break
        if i in seat_to_day:
            continue
        day = day + 1
        seat_to_day[i] = day
    for i in range(NUM_SEATS):
        print(f"Seat {i} assigned to day {seat_to_day[i]}")

    return seat_to_day


def distance_bw_seats(seat1, seat2):
    row1, col1 = seat_to_point(seat1)
    row2, col2 = seat_to_point(seat2)
    dist = math.sqrt((row1-row2) ** 2 + (col1-col2) ** 2)
    fudge = AISLE_FUDGE_FACTOR if are_different_aisles(seat1, seat1) else 0
    return dist + fudge


def seat_to_point(seat):
    row = math.floor(seat/ROW_SIZE)
    col = seat % ROW_SIZE
    return row, col


def are_different_aisles(seat1, seat2):
    row1, col1 = seat_to_point(seat1)
    row2, col2 = seat_to_point(seat2)
    aisle1 = math.floor(row1/2)
    aisle2 = math.floor(row2/2)
    return aisle1 != aisle2
