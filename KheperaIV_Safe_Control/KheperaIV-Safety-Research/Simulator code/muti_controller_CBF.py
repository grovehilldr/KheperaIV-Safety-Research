from utilities.barrier_certificates import *

#from utilities.Telemetry import Telemetry
from utilities.controllers import *

from utilities import util

import numpy as np
import random

"""
Implements CBF on multiple Khepera IV robots in Coppelia Sim
The program will grab all available robots in a scene.
The robot will move to their target destination.
Once all targets are reached, the program will
wait for user input to exit the simulation. The program
will also make sure that robots do not collide.
PSEUDOCODE:
1. Start simulation
2. Get all agents
3. Initialize Robotarium helper functions
4. Iterate until all agents reach goal:
5.   Retrieve the most recent poses of the robots
6.   Control agents
7.   Check collisions of agents
8.   Calculate and update agents' velocities
"""

# Future tunings: understand gamma value and how that affects pose controller
# Future tunings: understand Quadradtic programing and how that impacts the controller
# TODO: Work on improving crashing in 8 robot scene

# Start Sim and get all agents (robots)
sim, client = util.start_sim()
agents, targets, n = util.init_robots(sim)


# Initialize velocity vector for agents. Each agent expects a 2x1 velocity
#   vector containing the linear and angular velocity, respectively.
targets = np.array([util.get_target_position(sim, target) for target in targets])
x_goal = targets.T

# Barrier Parameters
safety_radius = 0.5 #0.2

# We're working in unicycle dynamics, and we don't want the robots
# to collide.  Thus, we're going to use unicycle barrier certificates
# TODO: play around with the unicycle barrier certificate functions robotarium offers
uni_barrier_cert = create_unicycle_barrier_certificate(safety_radius=safety_radius)

# Create unicycle pose controller
# Decided to use pose-based over position-based because the postion-based controller creates zig-zag motion
# TODO: see if we can move from using custom version of position_uni_clf_controller
position_uni_clf_controller = create_clf_unicycle_position_controller()

x_rand_span_x = 0.02 * np.random.randint(3, 4, (1, n)) # setting up position error range for each robot,
x_rand_span_y = 0.02 * np.random.randint(1, 4, (1, n)) # rand_span serves as the upper bound of uncertainty for each of the robot

x_rand_span_xy = np.concatenate((x_rand_span_x, x_rand_span_y))

pos_error = np.zeros((2, n))

loop = True
stopped = np.zeros(len(agents))

# test_name = input('Enter name of Map: ')
#test_name = 'Plus Cross'
#telemetry = Telemetry(len(agents), test_name, 'SBC', do_uBox=True)
while loop:

    # ALGORITHM
    positions = np.array([agent.get_position(sim) for agent in agents])

    # reshape positions so that its 2 x n
    x = positions.T.copy()

    # add noise
    x[:2, :] += pos_error
    pos_error = x_rand_span_xy * ((np.random.rand(2, n) - 0.5) * 2.0)
    # x[:2, :] += .1 * random.random()

    # get distance to gaol for all robots
    d = np.sqrt((x_goal[0] - x[0]) ** 2 + (x_goal[1] - x[1]) ** 2)

    # stop if distance threshold is met
    if (d < .05).all() or (stopped == 1).all():
        util.stop_all(sim, agents)
        loop = False
        continue

    # Use a position controller to drive to the goal position
    dxu = position_uni_clf_controller(x, x_goal)


    for i in range(len(agents)):
        if round(d[i], 2) < .05 or stopped[i] == 1:
            dxu[0, i] = 0
            dxu[1, i] = 0
            stopped[i] = 1

    # Use the barrier certificates to make sure that the agents don't collide
    dxu = uni_barrier_cert(dxu, x)

    util.set_velocities(sim, agents, dxu)

    #telemetry.update(x, positions)

input('Press any key to continue')
sim.stopSimulation()

#telemetry.create_graph(.33, False, error_bound_x=x_rand_span_x, error_bound_y=x_rand_span_y)
#telemetry.create_graph(.66, False, error_bound_x=x_rand_span_x, error_bound_y=x_rand_span_y)
#telemetry.create_graph(error_bound_x=x_rand_span_x, error_bound_y=x_rand_span_y)
#telemetry.create_graph(min_dist=True)
#telemetry.create_graph(minest_dist=True, error_bound_x=x_rand_span_x, error_bound_y=x_rand_span_y)