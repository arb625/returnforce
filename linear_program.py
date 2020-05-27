from mip import Model, xsum, maximize, BINARY, INTEGER
import math

# Total number of seats
NUM_SEATS = 12

# Seats per row
ROW_SIZE = 3

# An extra distance (in feet) applied to capture the distance b/w aisles
AISLE_FUDGE_FACTOR = 5

# Distance (in feet) from one seat to adjacent seat in same row/column
SEAT_DISTANCE = 3

# Max number of days/shifts to partition across
NUM_ROTATION_DAYS = 4


def solve_linear_model():
    """
    Solves the linear model to determine the best seating arrangement to maximize social distancing.
    """
    m = Model()

    d = [[distance_bw_seats(i, j) for j in range(NUM_SEATS)] for i in range(NUM_SEATS)]
    w = [[m.add_var(var_type=BINARY) for j in range(NUM_SEATS)] for i in range(NUM_SEATS)] # 1 = same day, 0 = else
    n = [m.add_var(var_type=BINARY) for i in range(NUM_SEATS)]
    t1 = [[[m.add_var(var_type=INTEGER) for k in range(NUM_SEATS)] for j in range(NUM_SEATS)] for i in range(NUM_SEATS)]
    t2 = [[[m.add_var(var_type=INTEGER) for k in range(NUM_SEATS)] for j in range(NUM_SEATS)] for i in range(NUM_SEATS)]

    m.objective = maximize(xsum([w[i][j] * d[i][j] for j in range(i+1, NUM_SEATS)] for i in range(NUM_SEATS)))

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
                m += w[j][k] <= t1[i][j][k] + t2[i][j][k]
                m += t1[i][j][k] - t2[i][j][k] == w[i][j] + w[i][k] - 1
                m += t1[i][j][k] >= 0

    s = [xsum(w[j][i] for j in range(i)) for i in range(NUM_SEATS)]
    ss = [s[i]/(i+1) for i in range(NUM_SEATS)]
    for i in range(NUM_SEATS):
        m += n[i] >= (1-ss[i])-.999
        m += n[i] <= 1-ss[i]
    # total number of days constraint
    m += xsum(n[i] for i in range(NUM_SEATS)) <= NUM_ROTATION_DAYS

    # solve the linear program
    m.optimize()

    print(f"Number of solutions:{m.num_solutions}")

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

    obj_val = 0
    for i in range(NUM_SEATS):
        for j in range(i+1, NUM_SEATS):
            obj_val += w[i][j].x * d[i][j]
    print(f"obj_val:{obj_val}")

    # objective value of a standard seating arrangement
    # obj_val = 0
    # on_weights = [(0,2),(0,7),(2,7),(1,6),(1,8),(6,8),(3,5),(3,10),(5,10),(4,9),(4,11),(9,11)]
    # for i in range(NUM_SEATS):
    #     for j in range(i+1,NUM_SEATS):
    #         weight = 0
    #         if (i,j) in on_weights or (j,i) in on_weights:
    #             weight = 1
    #         if i != j:
    #             obj_val += weight * d[i][j]
    # print(f"obj_val:{obj_val}")

    return seat_to_day


def distance_bw_seats(seat1, seat2):
    """
    Returns distance between two seats. Works by first converting them to cartesian
    points and then calculating the Euclidean distance between the points.
    :param seat1: the first seat
    :param seat2: the second seat
    :return: the Euclidean distance between two seats
    """
    row1, col1 = seat_to_point(seat1)
    row2, col2 = seat_to_point(seat2)
    dist = math.sqrt((row1-row2) ** 2 + (col1-col2) ** 2)
    fudge = AISLE_FUDGE_FACTOR if are_different_aisles(seat1, seat2) else 0
    return dist + fudge


def seat_to_point(seat):
    """
    Seat number to a cartesian point
    :param seat: the seat
    :return: row and col of the seat
    """
    row = math.floor(seat/ROW_SIZE)
    col = seat % ROW_SIZE
    return row, col


def are_different_aisles(seat1, seat2):
    """
    Returns true if the seats are in different aisles, false otherwise
    :param seat1: the first seat
    :param seat2: the second seat
    :return: true if the seats are in different aisles, false otherwise
    """
    row1, col1 = seat_to_point(seat1)
    row2, col2 = seat_to_point(seat2)
    aisle1 = math.floor(row1/2)
    aisle2 = math.floor(row2/2)
    return aisle1 != aisle2
