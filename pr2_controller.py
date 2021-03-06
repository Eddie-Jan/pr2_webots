from controller import Camera, Device, InertialUnit, Motor, GPS, PositionSensor, Robot, TouchSensor, Lidar
from controller import LidarPoint
import numpy as np
import math
import sys
import tempfile
import ikpy.inverse_kinematics as IK
import ikpy.chain
import ikpy.urdf.URDF
import pandas as pd
import xlsxwriter
from openpyxl import Workbook, load_workbook

TIME_STEP = 16 * 2

# PR2 constants
MAX_WHEEL_SPEED = 3.0  # maximum velocity for the wheels [rad / s]
WHEELS_DISTANCE = 0.4492  # distance between 2 caster wheels (the four wheels are located in square) [m]
SUB_WHEELS_DISTANCE = 0.098  # distance between 2 sub wheels of a caster wheel [m]
WHEEL_RADIUS = 0.08  # wheel radius

# function to check if a double is almost equal to another
TOLERANCE = 0.05  # arbitrary value
# ALMOST_EQUAL(a, b) = ((a < b + TOLERANCE) and (a > b - TOLERANCE))

# helper constants to distinguish the motors
FLL_WHEEL = 0
FLR_WHEEL = 1
FRL_WHEEL = 2
FRR_WHEEL = 3
BLL_WHEEL = 4
BLR_WHEEL = 5
BRL_WHEEL = 6
BRR_WHEEL = 7

FL_ROTATION = 0
FR_ROTATION = 1
BL_ROTATION = 2
BR_ROTATION = 3

SHOULDER_ROLL = 0
SHOULDER_LIFT = 1
UPPER_ARM_ROLL = 2
ELBOW_LIFT = 3
FOREARM_ROLL = 4
WRIST_FLEX = 5
WRIST_ROLL = 6

LEFT_FINGER = 0
RIGHT_FINGER = 1
LEFT_TIP = 2
RIGHT_TIP = 3

# PR2 motors and their sensors
wheel_motors = []
wheel_sensors = []
rotation_motors = []
rotation_sensors = []
left_arm_motors = []
left_arm_sensors = []
right_arm_motors = []
right_arm_sensors = []
right_finger_motors = []
right_finger_sensors = []
left_finger_motors = []
left_finger_sensors = []
head_tilt_motor = []
torso_motor = []
torso_sensor = []

# PR2 sensor devices
left_finger_contact_sensors = []
right_finger_contact_sensors = []
imu_sensor = []
wide_stereo_l_stereo_camera_sensor = []
wide_stereo_r_stereo_camera_sensor = []
high_def_sensor = []
r_forearm_cam_sensor = []
l_forearm_cam_sensor = []
laser_tilt_width = 0
base_laser_width = 0
laser_tilt_maxRange = 0
base_laser_maxRange = 0
head_tilt_joint_sensor = []
lidar = []
gps = []
imu = []
camera = []


def step():
    if robot.step(TIME_STEP) == -1:
        exit(0)


def ALMOST_EQUAL(a, b):
    return (a < b + TOLERANCE) and (a > b - TOLERANCE)


def initialize_devices():
    wheel_motors.append(robot.getDevice("fl_caster_l_wheel_joint"))  # FLL_WHEEL
    wheel_motors.append(robot.getDevice("fl_caster_r_wheel_joint"))  # FLR_WHEEL
    wheel_motors.append(robot.getDevice("fr_caster_l_wheel_joint"))  # FRL_WHEEL
    wheel_motors.append(robot.getDevice("fr_caster_r_wheel_joint"))  # FRR_WHEEL
    wheel_motors.append(robot.getDevice("bl_caster_l_wheel_joint"))  # BLL_WHEEL
    wheel_motors.append(robot.getDevice("bl_caster_r_wheel_joint"))  # BLR_WHEEL
    wheel_motors.append(robot.getDevice("br_caster_l_wheel_joint"))  # BRL_WHEEL
    wheel_motors.append(robot.getDevice("br_caster_r_wheel_joint"))  # BRR_WHEEL
    for i in range(8):
        wheel_sensors.append(wheel_motors[i].getPositionSensor())

    rotation_motors.append(robot.getDevice("fl_caster_rotation_joint"))  # FL_ROTATION
    rotation_motors.append(robot.getDevice("fr_caster_rotation_joint"))  # FR_ROTATION
    rotation_motors.append(robot.getDevice("bl_caster_rotation_joint"))  # BL_ROTATION
    rotation_motors.append(robot.getDevice("br_caster_rotation_joint"))  # BR_ROTATION
    for i in range(4):
        rotation_sensors.append(rotation_motors[i].getPositionSensor())

    left_arm_motors.append(robot.getDevice("l_shoulder_pan_joint"))  # SHOULDER_ROLL
    left_arm_motors.append(robot.getDevice("l_shoulder_lift_joint"))  # SHOULDER_LIFT
    left_arm_motors.append(robot.getDevice("l_upper_arm_roll_joint"))  # UPPER_ARM_ROLL
    left_arm_motors.append(robot.getDevice("l_elbow_flex_joint"))  # ELBOW_LIFT
    left_arm_motors.append(robot.getDevice("l_forearm_roll_joint"))  # FOREARM_ROLL
    left_arm_motors.append(robot.getDevice("l_wrist_flex_joint"))  # WRIST_FLEX
    left_arm_motors.append(robot.getDevice("l_wrist_roll_joint"))  # WRIST_ROLL
    for i in range(7):
        left_arm_sensors.append(left_arm_motors[i].getPositionSensor())

    right_arm_motors.append(robot.getDevice("r_shoulder_pan_joint"))  # SHOULDER_ROLL
    right_arm_motors.append(robot.getDevice("r_shoulder_lift_joint"))  # SHOULDER_LIFT
    right_arm_motors.append(robot.getDevice("r_upper_arm_roll_joint"))  # UPPER_ARM_ROLL
    right_arm_motors.append(robot.getDevice("r_elbow_flex_joint"))  # ELBOW_LIFT
    right_arm_motors.append(robot.getDevice("l_forearm_roll_joint"))  # FOREARM_ROLL
    right_arm_motors.append(robot.getDevice("l_wrist_flex_joint"))  # WRIST_FLEX
    right_arm_motors.append(robot.getDevice("r_wrist_roll_joint"))  # WRIST_ROLL
    for i in range(7):
        right_arm_sensors.append(right_arm_motors[i].getPositionSensor())

    left_finger_motors.append(robot.getDevice("l_gripper_l_finger_joint"))  # LEFT_FINGER
    left_finger_motors.append(robot.getDevice("l_gripper_r_finger_joint"))  # RIGHT_FINGER
    left_finger_motors.append(robot.getDevice("l_gripper_l_finger_tip_joint"))  # LEFT_TIP
    left_finger_motors.append(robot.getDevice("l_gripper_r_finger_tip_joint"))  # RIGHT_TIP
    for i in range(4):
        left_finger_sensors.append(left_finger_motors[i].getPositionSensor())

    right_finger_motors.append(robot.getDevice("r_gripper_l_finger_joint"))  # LEFT_FINGER
    right_finger_motors.append(robot.getDevice("r_gripper_r_finger_joint"))  # RIGHT_FINGER
    right_finger_motors.append(robot.getDevice("r_gripper_l_finger_tip_joint"))  # LEFT_TIP
    right_finger_motors.append(robot.getDevice("r_gripper_r_finger_tip_joint"))  # RIGHT_TIP
    for i in range(4):
        right_finger_sensors.append(right_finger_motors[i].getPositionSensor())

    head_tilt_motor.append(robot.getDevice("head_tilt_joint"))
    torso_motor.append(robot.getDevice("torso_lift_joint"))
    torso_sensor.append(robot.getDevice("torso_lift_joint_sensor"))

    left_finger_contact_sensors.append(robot.getDevice("l_gripper_l_finger_tip_contact_sensor"))  # LEFT_FINGER
    left_finger_contact_sensors.append(robot.getDevice("l_gripper_r_finger_tip_contact_sensor"))  # RIGHT_FINGER
    right_finger_contact_sensors.append(robot.getDevice("r_gripper_l_finger_tip_contact_sensor"))  # LEFT_FINGER
    right_finger_contact_sensors.append(robot.getDevice("r_gripper_r_finger_tip_contact_sensor"))  # RIGHT_FINGER

    # imu_sensor.append(Robot.getMotor("imu_sensor"))
    lidar.append(robot.getDevice("base_laser"))
    gps.append(robot.getDevice("gps"))
    imu.append(robot.getDevice("imu_sensor"))
    camera.append(robot.getDevice("camera"))


def enable_devices():
    print("-----------Enable device------------")
    for i in range(8):
        wheel_sensors[i].enable(TIME_STEP)
        # init the motors for speed control
        wheel_motors[i].setPosition(float('Inf'))
        wheel_motors[i].setVelocity(0.0)

    for i in range(4):
        rotation_sensors[i].enable(TIME_STEP)

    for i in range(2):
        left_finger_contact_sensors[i].enable(TIME_STEP)
        right_finger_contact_sensors[i].enable(TIME_STEP)

    for i in range(4):
        left_finger_sensors[i].enable(TIME_STEP)
        right_finger_sensors[i].enable(TIME_STEP)

    for i in range(7):
        left_arm_sensors[i].enable(TIME_STEP)
        right_arm_sensors[i].enable(TIME_STEP)

    torso_sensor[0].enable(TIME_STEP)
    lidar[0].enable(TIME_STEP)
    lidar[0].enablePointCloud()
    gps[0].enable(TIME_STEP)
    imu[0].enable(TIME_STEP)
    camera[0].enable(TIME_STEP)


# set the speeds of the robot wheels
def set_wheels_speeds(fll, flr, frl, frr, bll, blr, brl, brr):
    wheel_motors[FLL_WHEEL].setVelocity(fll)
    wheel_motors[FLR_WHEEL].setVelocity(flr)
    wheel_motors[FRL_WHEEL].setVelocity(frl)
    wheel_motors[FRR_WHEEL].setVelocity(frr)
    wheel_motors[BLL_WHEEL].setVelocity(bll)
    wheel_motors[BLR_WHEEL].setVelocity(blr)
    wheel_motors[BRL_WHEEL].setVelocity(brl)
    wheel_motors[BRR_WHEEL].setVelocity(brr)


def set_wheels_speed(speed):
    set_wheels_speeds(speed, speed, speed, speed, speed, speed, speed, speed)


def stop_wheels():
    set_wheels_speeds(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


# enable/disable the torques on the wheels motors
def enable_passive_wheels(enable):
    torques = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    if enable:
        for i in range(8):
            torques[i] = wheel_motors[i].getAvailableTorque()
            wheel_motors[i].setAvailableTorque(0.0)
    else:
        for i in range(8):
            wheel_motors[i].setAvailableTorque(torques[i])


# Set the rotation wheels angles.
# If wait_on_feedback is true, the function is left when the rotational motors have reached their target positions.
def set_rotation_wheels_angles(fl, fr, bl, br, wait_on_feedback):
    if wait_on_feedback:
        enable_passive_wheels(True)

    rotation_motors[FL_ROTATION].setPosition(fl)
    rotation_motors[FR_ROTATION].setPosition(fr)
    rotation_motors[BL_ROTATION].setPosition(bl)
    rotation_motors[BR_ROTATION].setPosition(br)

    if wait_on_feedback:
        target = [fl, fr, bl, br]

        while True:
            all_reached = True
            for i in range(4):
                current_position = rotation_sensors[i].getValue()
                if not ALMOST_EQUAL(current_position, target[i]):
                    all_reached = False
                    break

            if all_reached:
                break
            else:
                step()

        enable_passive_wheels(False)


# High level function to rotate the robot around itself of a given angle [rad]
# Note: the angle can be negative
def robot_rotate(angle):
    print("-------------robot rotate---------------")
    stop_wheels()

    set_rotation_wheels_angles(3.0 * math.pi / 4, math.pi / 4, -3.0 * math.pi / 4, -math.pi / 4, True)
    max_wheel_speed = MAX_WHEEL_SPEED if angle > 0 else -MAX_WHEEL_SPEED
    set_wheels_speed(max_wheel_speed)

    initial_wheel0_position = wheel_sensors[FLL_WHEEL].getValue()
    print(initial_wheel0_position)
    # expect travel distance done by the wheel
    expected_travel_distance = math.fabs(angle * 0.5 * (WHEELS_DISTANCE + SUB_WHEELS_DISTANCE))

    while True:
        wheel0_position = wheel_sensors[FLL_WHEEL].getValue()
        print("wheel0_position:", wheel0_position)
        # travel distance done by the wheel
        wheel0_travel_distance = math.fabs(WHEEL_RADIUS * (wheel0_position - initial_wheel0_position))

        if wheel0_travel_distance > expected_travel_distance:
            break

        print(expected_travel_distance, wheel0_travel_distance)
        # reduce the speed before reaching the target
        if expected_travel_distance - wheel0_travel_distance < 0.025:
            set_wheels_speed(0.1 * max_wheel_speed)

        step()

    # reset wheels
    set_rotation_wheels_angles(0.0, 0.0, 0.0, 0.0, True)
    stop_wheels()


def robot_go_forward(distance):
    print("-----------Go forward------------")
    max_wheel_speed = MAX_WHEEL_SPEED if distance > 0 else -MAX_WHEEL_SPEED

    set_wheels_speed(max_wheel_speed)
    initial_wheel0_position = wheel_sensors[FLL_WHEEL].getValue()

    while True:
        wheel0_position = wheel_sensors[FLL_WHEEL].getValue()
        # travel distance by the wheel
        wheel0_travel_distance = math.fabs(WHEEL_RADIUS * (wheel0_position - initial_wheel0_position))

        if wheel0_travel_distance > math.fabs(distance):
            break

        # reduce the speed before reaching the target
        if math.fabs(distance) - wheel0_travel_distance < 0.025:
            set_wheels_speed(0.1 * max_wheel_speed)

        step()


# Idem for the right arm
def set_right_arm_position(shoulder_roll, shoulder_lift, upper_arm_roll, elbow_lift, forearm_roll, wrist_flex,
                           wrist_roll, wait_on_feedback):
    print("------------Set right arm position---------------")
    right_arm_motors[SHOULDER_ROLL].setPosition(shoulder_roll)
    right_arm_motors[SHOULDER_LIFT].setPosition(shoulder_lift)
    right_arm_motors[UPPER_ARM_ROLL].setPosition(upper_arm_roll)
    right_arm_motors[ELBOW_LIFT].setPosition(elbow_lift)
    right_arm_motors[WRIST_ROLL].setPosition(wrist_roll)

    right_arm_motors[SHOULDER_ROLL].setVelocity(10)
    right_arm_motors[SHOULDER_LIFT].setVelocity(10)
    right_arm_motors[UPPER_ARM_ROLL].setVelocity(10)
    right_arm_motors[ELBOW_LIFT].setVelocity(10)
    right_arm_motors[WRIST_ROLL].setVelocity(10)

    if wait_on_feedback:
        while not ALMOST_EQUAL(right_arm_sensors[SHOULDER_ROLL].getValue(), shoulder_roll) or \
                not ALMOST_EQUAL(right_arm_sensors[SHOULDER_LIFT].getValue(), shoulder_lift) or \
                not ALMOST_EQUAL(right_arm_sensors[UPPER_ARM_ROLL].getValue(), upper_arm_roll) or \
                not ALMOST_EQUAL(right_arm_sensors[ELBOW_LIFT].getValue(), elbow_lift) or \
                not ALMOST_EQUAL(right_arm_sensors[WRIST_ROLL].getValue(), wrist_roll):
            step()


# Idem for the left arm
def set_left_arm_position(shoulder_roll, shoulder_lift, upper_arm_roll, elbow_lift, forearm_roll, wrist_flex,
                          wrist_roll, wait_on_feedback):
    print("--------------Set left arm position--------------")
    left_arm_motors[SHOULDER_ROLL].setPosition(shoulder_roll)
    left_arm_motors[SHOULDER_LIFT].setPosition(shoulder_lift)
    left_arm_motors[UPPER_ARM_ROLL].setPosition(upper_arm_roll)
    left_arm_motors[ELBOW_LIFT].setPosition(elbow_lift)
    left_arm_motors[FOREARM_ROLL].setPosition(forearm_roll)
    left_arm_motors[WRIST_FLEX].setPosition(wrist_flex)
    left_arm_motors[WRIST_ROLL].setPosition(wrist_roll)

    left_arm_motors[SHOULDER_ROLL].setVelocity(10)
    left_arm_motors[SHOULDER_LIFT].setVelocity(10)
    left_arm_motors[UPPER_ARM_ROLL].setVelocity(10)
    left_arm_motors[FOREARM_ROLL].setVelocity(10)
    left_arm_motors[WRIST_FLEX].setVelocity(10)
    left_arm_motors[WRIST_ROLL].setVelocity(10)

    if wait_on_feedback:
        while not ALMOST_EQUAL(left_arm_sensors[SHOULDER_ROLL].getValue(), shoulder_roll) or \
                not ALMOST_EQUAL(left_arm_sensors[SHOULDER_LIFT].getValue(), shoulder_lift) or \
                not ALMOST_EQUAL(left_arm_sensors[UPPER_ARM_ROLL].getValue(), upper_arm_roll) or \
                not ALMOST_EQUAL(left_arm_sensors[ELBOW_LIFT].getValue(), elbow_lift) or \
                not ALMOST_EQUAL(left_arm_sensors[FOREARM_ROLL].getValue(), forearm_roll) or \
                not ALMOST_EQUAL(left_arm_sensors[WRIST_FLEX].getValue(), wrist_flex) or \
                not ALMOST_EQUAL(left_arm_sensors[WRIST_ROLL].getValue(), wrist_roll):
            step()


# Open or close the gripper
# If wait_on_feedback is true, the gripper is stopped either when the target is reached
# or when something has been gripped
def set_gripper(left, open, torqueWhenGripping, wait_on_feedback):
    print("------------Set Gripper-----------")
    motors = []
    sensors = []
    contacts = []

    motors.append(left_finger_motors[LEFT_FINGER]) if left else motors.append(right_finger_motors[LEFT_FINGER])
    motors.append(left_finger_motors[RIGHT_FINGER]) if left else motors.append(right_finger_motors[RIGHT_FINGER])
    motors.append(left_finger_motors[LEFT_TIP]) if left else motors.append(right_finger_motors[LEFT_TIP])
    motors.append(left_finger_motors[RIGHT_TIP]) if left else motors.append(right_finger_motors[RIGHT_TIP])

    sensors.append(left_finger_sensors[LEFT_FINGER]) if left else sensors.append(right_finger_sensors[LEFT_FINGER])
    sensors.append(left_finger_sensors[RIGHT_FINGER]) if left else sensors.append(right_finger_sensors[RIGHT_FINGER])
    sensors.append(left_finger_sensors[LEFT_TIP]) if left else sensors.append(right_finger_sensors[LEFT_TIP])
    sensors.append(left_finger_sensors[RIGHT_TIP]) if left else sensors.append(right_finger_sensors[RIGHT_TIP])

    contacts.append(left_finger_contact_sensors[LEFT_FINGER]) \
        if left else contacts.append(right_finger_contact_sensors[LEFT_FINGER])
    contacts.append(left_finger_contact_sensors[RIGHT_FINGER]) \
        if left else contacts.append(right_finger_contact_sensors[RIGHT_FINGER])

    firstCall = True
    maxTorque = 0.0
    if firstCall:
        maxTorque = motors[LEFT_FINGER].getAvailableTorque()
        firstCall = False

    for i in range(4):
        motors[i].setAvailableTorque(maxTorque)

    if open:
        target_open_value = 0.5
        for i in range(4):
            motors[i].setPosition(target_open_value)

        if wait_on_feedback:
            while not ALMOST_EQUAL(sensors[LEFT_FINGER].getValue(), target_open_value):
                step()
    else:
        target_close_value = 0.0
        for i in range(4):
            motors[i].setPosition(target_close_value)

        if wait_on_feedback:
            # wait until the 2 touch sensors are fired or the target value is reached
            while (contacts[LEFT_FINGER].getValue() == 0.0 or contacts[RIGHT_FINGER].getValue() == 0.0) and \
                    not ALMOST_EQUAL(sensors[LEFT_FINGER].getValue(), target_close_value):
                step()

            current_position = sensors[LEFT_FINGER].getValue()
            for i in range(4):
                motors[i].setAvailableTorque(torqueWhenGripping)
                motors[i].setPosition(max(0.0, 0.95 * current_position))


def lidar_setting():
    base_laser_value = lidar[0].getRangeImage()
    print("Lidar => Left:", base_laser_value[639], "Front:", base_laser_value[300], "Right:", base_laser_value[0])
    lidar_value = []
    for i in range(0, 640, 64):
        lidar_value.append(base_laser_value[i])

    lidar_value.append((base_laser_value[639]))
    print(lidar_value)

    loc = gps[0].getValues()
    print("loc", loc)

    RFID = []
    for i in range(0, 640, 10):
        x = loc[0] + base_laser_value[i] * math.cos(-45 + (270 / 640) * i)
        y = loc[2] + base_laser_value[i] * math.sin(-45 + (270 / 640) * i)
        RFID.append([x, y])

    # print("RFID: ", RFID)
    return loc, lidar_value


def camara_setting():
    cameraData = camera[0].getImageArray()
    print(cameraData)


def calculate(old_time, location, new_location, old_angle):
    print("new_location: ", new_location)
    new_time = robot.getTime()
    new_angle = imu[0].getRollPitchYaw()[2]

    velocity = ((new_location[0] - location[0]) ** 2 + (new_location[2] - location[2]) ** 2) ** 0.5 / (
            new_time - old_time)
    if new_angle < 0:
        new_angle = new_angle + 2 * math.pi

    angle_velocity = (new_angle - old_angle) / (new_time - old_time)

    if abs(new_angle - old_angle) > 1 and new_angle > math.pi:
        angle_velocity = (new_angle - 2 * math.pi - old_angle) / (new_time - old_time)
    elif abs(new_angle - old_angle) > 1 and new_angle < math.pi:
        angle_velocity = (new_angle + 2 * math.pi - old_angle) / (new_time - old_time)
    else:
        angle_velocity = (new_angle - old_angle) / (new_time - old_time)

    print("Velocity: ", velocity)
    print("angle: ", old_angle)
    print("Angle velocity: ", angle_velocity)

    old_time = new_time
    location = new_location
    old_angle = new_angle
    return old_time, location, old_angle


def run():
    print("----------run----------")
    old_time = 0
    location = [0, 0, 0]
    old_angle = imu[0].getRollPitchYaw()[2]

    lidar_value = []

    while robot.step(TIME_STEP) != -1:
        # wheel_motors[FLL_WHEEL].setPosition(float('Inf'))
        # wheel_motors[FLR_WHEEL].setPosition(float('Inf'))
        # wheel_motors[FRL_WHEEL].setPosition(float('Inf'))
        # wheel_motors[FRR_WHEEL].setPosition(float('Inf'))
        # wheel_motors[BLL_WHEEL].setPosition(float('Inf'))
        # wheel_motors[BLR_WHEEL].setPosition(float('Inf'))
        # wheel_motors[BRL_WHEEL].setPosition(float('Inf'))
        # wheel_motors[BRR_WHEEL].setPosition(float('Inf'))
        # wheel_motors[FLL_WHEEL].setVelocity(50)
        # wheel_motors[FLR_WHEEL].setVelocity(50)
        # wheel_motors[FRL_WHEEL].setVelocity(50)
        # wheel_motors[FRR_WHEEL].setVelocity(50)
        # wheel_motors[BLL_WHEEL].setVelocity(50)
        # wheel_motors[BLR_WHEEL].setVelocity(50)
        # wheel_motors[BRL_WHEEL].setVelocity(50)
        # wheel_motors[BRR_WHEEL].setVelocity(50)

        new_location, lidar_value = lidar_setting()
        old_time, location, old_angle = calculate(old_time, location, new_location, old_angle)

        # cameraData = camera.getImageArray()
        # print(cameraData)
        print("=================================")
        if robot.getTime() > 5:
            break



    # df = pd.DataFrame(data=lidar_value + new_location[0] + new_location[2] + old_angle,
    #                   columns=['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8', 'L9', 'L10', 'L11', 'X', 'Y', 'Angle'])
    # writer = pd.ExcelWriter('test.xlsx', engine='xlsxwriter')
    # df.to_excel(writer, sheet_name='welcome', index=False)
    # writer.save()


def inverse_kinematics():
    print("----------Inverse Kinematics----------")
    left_arm_chain = ikpy.chain.Chain.from_urdf_file(urdf_file="pr2.urdf",
                                                     base_element_type='link',
                                                     base_elements=[
                                                         "base_link",
                                                         "torso_lift_joint",
                                                         "torso_lift_link",
                                                         "l_shoulder_pan_joint",
                                                         "l_shoulder_pan_link",
                                                         "l_shoulder_lift_joint",
                                                         "solid_0",
                                                         "l_upper_arm_roll_joint",
                                                         "solid_1",
                                                         "solid_1_solid_2_joint",
                                                         "solid_2",
                                                         "l_elbow_flex_joint",
                                                         "solid_3",
                                                         "l_forearm_roll_joint",
                                                         "solid_4",
                                                         "solid_4_solid_6_joint",
                                                         "solid_6",
                                                         "l_wrist_flex_joint",
                                                         "l_wrist_flex_link",
                                                         "l_wrist_roll_joint",
                                                         "solid_7",
                                                         "solid_7_solid_8_joint",
                                                         "solid_8",
                                                         "l_gripper_r_finger_joint",
                                                         "l_gripper_r_finger_link",
                                                         "l_gripper_r_finger_tip_joint",
                                                         "l_gripper_r_finger_tip_contact_sensor",
                                                         "l_gripper_joint",
                                                         "solid_9"
                                                     ],
                                                     active_links_mask=[False, True, True, True, True,
                                                                        False, True, False, False, False,
                                                                        True, False, True, True, False])
    motors = []
    for link in left_arm_chain.links:
        if link.name != 'Base link' and link.name != "solid_1_solid_2_joint" and \
                link.name != "solid_4_solid_6_joint" and link.name != "solid_7_solid_8_joint" and \
                link.name != "l_gripper_joint":
            # print(link.name)
            motor = robot.getDevice(link.name)
            # print(motor)
            motor.setVelocity(1.0)
            position_sensor = motor.getPositionSensor()
            # print(position_sensor)
            position_sensor.enable(TIME_STEP)
            motors.append(motor)
            # print("========================")

    IKPY_MAX_ITERATIONS = 4
    # print("left_arm_chain:", left_arm_chain)
    # print("==========================================")

    position = left_arm_chain.forward_kinematics([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    print("fwResults:", position)

    ikResults = left_arm_chain.inverse_kinematics([position[0][3], position[1][3], position[2][3]])
    print("iKResult:", ikResults)

    print("==========================================================")

    can = [5.1, 0.543, 4.57]
    robot_position = gps_base.getValues()
    print("robot_position", robot_position)
    # robot_position = [4.53, -0.0136, 3.65]
    target_position = [can[2] - robot_position[2], can[0] - robot_position[0], can[1] - robot_position[1]]
    print("target position:", target_position)
    sensor = [m.getPositionSensor().getValue() for m in motors]
    initial_position = [0] + sensor[0:4] + [0] + sensor[4:6] + [0] + sensor[6:8] + [0] + sensor[8:10] + [0]
    print("initial position:", initial_position)
    # print("initial_position:", initial_position)
    ikResults = left_arm_chain.inverse_kinematics(target_position, max_iter=IKPY_MAX_ITERATIONS,
                                                  initial_position=initial_position)
    print("ikResults:", ikResults)
    fw = left_arm_chain.forward_kinematics(ikResults)
    print("fwResults:", fw)

    return ikResults


if __name__ == '__main__':
    robot = Robot()
    initialize_devices()
    enable_devices()

    gps_finger = robot.getDevice("gps_finger")
    gps_base = robot.getDevice("gps_base")
    gps_finger.enable(TIME_STEP)
    gps_base.enable(TIME_STEP)
    # wb = Workbook()
    # ws = wb.active
    # set_left_arm_position(0.0, 1.35, 0.0, -2.2, 0, 0, 0.0, True)
    # set_right_arm_position(0.0, 1.35, 0.0, -2.2, 0.0, 0.0, 0.0,True)
    # old_time = 0
    # location = [0, 0, 0]
    # old_angle = imu[0].getRollPitchYaw()[2]
    # ws.append(['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8', 'L9', 'L10', 'L11', 'X', 'Y', 'Angle'])
    #
    # while robot.step(TIME_STEP) != -1:
    #     new_location, lidar_value = lidar_setting()
    #     old_time, location, old_angle = calculate(old_time, location, new_location, old_angle)
    #     data = lidar_value + [new_location[0]] + [new_location[2]] + [old_angle]
    #     # print(data)
    #     ws.append(data)
    #     # cameraData = camera.getImageArray()
    #     # print(cameraData)
    #     print("=================================")
    #     if robot.getTime() > 30:
    #         break
    #
    # wb.save('excel9.xlsx')


    # df = pd.DataFrame(data=lidar_value + new_location[0] + new_location[2] + old_angle,
    #                   columns=['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8', 'L9', 'L10', 'L11', 'X', 'Y', 'Angle'])
    # writer = pd.ExcelWriter('test.xlsx', engine='xlsxwriter')
    # df.to_excel(writer, sheet_name='welcome', index=False)
    # writer.save()

    x = [0.939, 0.173, 0.74]
    finger_position = gps_finger.getValues()
    print("finger position:", finger_position)
    base_position = gps_base.getValues()
    # base_position = [finger_position[0] - x[0], finger_position[1] - x[1], finger_position[2] - x[2]]
    print("base position:", base_position)
    print("minus:", finger_position[0] - base_position[0], finger_position[1] - base_position[1],
          finger_position[2] - base_position[2])

    # set_left_arm_position(0, 0, 0, 0, 0, 0, 0, True)
    # set_right_arm_position(0, 0, 0, 0, 0, 0, 0, True)
    set_gripper(True, True, 0.0, True)
    set_gripper(False, True, 0.0, True)
    set_left_arm_position(0.0, 1.35, 0.0, -2.2, 0, 0, 0.0, True)
    set_right_arm_position(0.0, 1.35, 0.0, -2.2, 0.0, 0, 0,True)
    # robot_go_forward(2)
    # run()
    ikResults = inverse_kinematics()
    set_left_arm_position(ikResults[2], ikResults[3], ikResults[4], ikResults[6],
                          ikResults[7], ikResults[9], ikResults[10], True)

    set_gripper(True, False, 20.0, True)
    set_gripper(False, False, 20.0, True)
    # set_rotation_wheels_angles(3.0 * math.pi / 4, math.pi / 4, -3.0 * math.pi / 4, -math.pi / 4, True)
    # robot_go_forward(1)
    # robot_rotate(math.pi)
    set_gripper(True, True, 0.0, True)
    set_gripper(True, False, 20.0, True)

    # camara_setting()
    # set_right_arm_position(0.0, 1.35, 0.0, -2.2, 0.0, True)
    # set_right_arm_position(0, 0, 0, 0, 0, True)

    # set_gripper(True, True, 0.0, True)
    # set_gripper(False, True, 0.0, True)
