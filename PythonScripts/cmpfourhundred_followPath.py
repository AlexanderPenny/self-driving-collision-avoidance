import numbers

import carla
import re 
import math
THRESHOLD_DISTANCE = 15.0 # How close it needs to be to switch to the next point
PATH_ARRAY = [
    carla.Location(x=3112.8, y=-335.8, z=-548.6), # 2
    carla.Location(x=3073.2, y=-463.7, z=-548.6), # 3
    carla.Location(x=3009.6, y=-668.5, z=-548.6), # 4
    carla.Location(x=2999.5, y=-696.4, z=-548.6), # 5
    carla.Location(x=2971.5, y=-774.6, z=-548.6), # 6
    carla.Location(x=2962.8, y=-788.1, z=-548.6), # 7
    carla.Location(x=2938.8, y=-816.3, z=-548.6), # 8
    carla.Location(x=2860.2, y=-896.8, z=-548.6), # 9
    carla.Location(x=2842.8, y=-915.2, z=-548.6), # 10
    carla.Location(x=2824.2, y=-927.7, z=-548.6), # 11
    carla.Location(x=2716.8, y=-1003.3, z=-548.6), # 12
    carla.Location(x=2705.6, y=-1010.8, z=-548.6), # 13
    carla.Location(x=2687.7, y=-1025.2, z=-548.6), # 14
    carla.Location(x=2596.6, y=-1098.6, z=-548.6), # 15
    carla.Location(x=2573.8, y=-1117.8, z=-548.6), # 16
    carla.Location(x=2557.6, y=-1137.1, z=-548.6), # 17
    carla.Location(x=2518.0, y=-1185.8, z=-548.6), # 18
    carla.Location(x=2465.5, y=-1258.9, z=-548.6), # 19
    carla.Location(x=2428.5, y=-1317.5, z=-548.6), # 20
    carla.Location(x=2365.5, y=-1417.9, z=-548.6), # 21
    carla.Location(x=2267.7, y=-1574.1, z=-548.6), # 22
    carla.Location(x=2250.1, y=-1606.0, z=-548.6), # 23
    carla.Location(x=2225.0, y=-1647.1, z=-548.6), # 24
    carla.Location(x=2203.0, y=-1680.9, z=-548.6), # 25
    carla.Location(x=2184.0, y=-1712.0, z=-548.6), # 26
    carla.Location(x=2141.3, y=-1783.2, z=-548.6), # 27
    carla.Location(x=2068.3, y=-1903.5, z=-548.6), # 28
    carla.Location(x=1989.5, y=-2036.3, z=-548.6), # 29
    carla.Location(x=1955.6, y=-2073.9, z=-548.6), # 30
    carla.Location(x=1903.4, y=-2088.4, z=-548.6), # 31
    carla.Location(x=1651.6, y=-2125.7, z=-548.6), # 32
    carla.Location(x=1479.3, y=-2150.9, z=-548.6), # 33
    carla.Location(x=1225.6, y=-2219.0, z=-548.6), # 34
    carla.Location(x=915.9, y=-2320.0, z=-548.6), # 35
    carla.Location(x=823.2, y=-2336.1, z=-548.6), # 36
    carla.Location(x=698.8, y=-2333.7, z=-548.6), # 37
    carla.Location(x=346.9, y=-2349.5, z=-548.6), # 38
    carla.Location(x=26.3, y=-2365.0, z=-548.6), # 39
    carla.Location(x=-43.3, y=-2372.7, z=-548.6), # 40
    carla.Location(x=-59.5, y=-2377.9, z=-548.6), # 41
    carla.Location(x=-67.1, y=-2393.5, z=-548.6), # 42
    carla.Location(x=-86.0, y=-2491.6, z=-548.6), # 43
    carla.Location(x=-130.1, y=-2693.3, z=-548.6), # 44
    carla.Location(x=-187.1, y=-2964.3, z=-548.6), # 45
    carla.Location(x=-231.6, y=-3160.2, z=-548.6), # 46
    carla.Location(x=-282.6, y=-3395.5, z=-548.6), # 47
    carla.Location(x=-312.2, y=-3519.5, z=-548.6), # 48
    carla.Location(x=-338.5, y=-3630.4, z=-548.6), # 49
    carla.Location(x=-363.6, y=-3738.6, z=-548.6), # 50
    carla.Location(x=-389.1, y=-3843.5, z=-548.6), # 51
    carla.Location(x=-428.5, y=-3842.6, z=-548.6), # 52
    carla.Location(x=-490.8, y=-3841.9, z=-548.6), # 53
    carla.Location(x=-607.6, y=-3839.9, z=-548.6), # 54
    carla.Location(x=-715.9, y=-3838.9, z=-548.6), # 55
    carla.Location(x=-839.7, y=-3837.2, z=-548.6), # 56
    carla.Location(x=-940.9, y=-3833.8, z=-548.6), # 57
    carla.Location(x=-1108.3, y=-3827.7, z=-548.6), # 58
    carla.Location(x=-1249.4, y=-3821.6, z=-548.6), # 59
    carla.Location(x=-1412.8, y=-3816.3, z=-548.6), # 60
    carla.Location(x=-1457.2, y=-3815.9, z=-548.6), # 61
    carla.Location(x=-1520.4, y=-3822.0, z=-548.6), # 62
    carla.Location(x=-1680.4, y=-3862.5, z=-548.6), # 63
    carla.Location(x=-1813.9, y=-3897.4, z=-548.6), # 64
    carla.Location(x=-1842.2, y=-3905.2, z=-548.6), # 65
    carla.Location(x=-1951.5, y=-3922.5, z=-548.6), # 66
    carla.Location(x=-2117.6, y=-3941.3, z=-548.6), # 67
    carla.Location(x=-2230.7, y=-3952.1, z=-548.6), # 68
    carla.Location(x=-2445.3, y=-3972.6, z=-548.6), # 69
    carla.Location(x=-2932.6, y=-4019.7, z=-548.6), # 70
    carla.Location(x=-2978.8, y=-4020.0, z=-548.6), # 71
    carla.Location(x=-2972.7, y=-3956.0, z=-548.6), # 72
    carla.Location(x=-2948.5, y=-3712.5, z=-548.6), # 73
    carla.Location(x=-2930.7, y=-3517.2, z=-548.6), # 74
    carla.Location(x=-2918.4, y=-3407.0, z=-548.6), # 75
    carla.Location(x=-2907.8, y=-3331.9, z=-548.6), # 76
    carla.Location(x=-2877.5, y=-3227.1, z=-548.6), # 77
    carla.Location(x=-2858.1, y=-3118.1, z=-548.6), # 78
    carla.Location(x=-2786.1, y=-2511.3, z=-548.6), # 79
    carla.Location(x=-2757.3, y=-2406.2, z=-548.6), # 80
    carla.Location(x=-2682.2, y=-2238.7, z=-548.6), # 81
    carla.Location(x=-2602.5, y=-2019.6, z=-548.6), # 82
    carla.Location(x=-2426.5, y=-1476.1, z=-548.6), # 83
    carla.Location(x=-2375.2, y=-1322.2, z=-548.6), # 84
    carla.Location(x=-2318.3, y=-1146.1, z=-548.6), # 85
    carla.Location(x=-2162.8, y=-661.4, z=-548.6), # 86
    carla.Location(x=-2081.8, y=-471.1, z=-548.6), # 87
    carla.Location(x=-2021.7, y=-283.4, z=-548.6), # 88
    carla.Location(x=-2008.1, y=-218.7, z=-548.6), # 89
    carla.Location(x=-1985.7, y=9.4, z=-548.6), # 90
    carla.Location(x=-1984.3, y=80.4, z=-548.6), # 91
    carla.Location(x=-2002.9, y=152.7, z=-548.6), # 92
    carla.Location(x=-2098.5, y=411.7, z=-548.6), # 93
    carla.Location(x=-2123.1, y=484.8, z=-548.6), # 94
    carla.Location(x=-2120.3, y=521.5, z=-548.6), # 95
    carla.Location(x=-2064.9, y=671.3, z=-548.6), # 96
    carla.Location(x=-2026.4, y=752.1, z=-548.6), # 97
    carla.Location(x=-1954.4, y=790.3, z=-548.6), # 98
    carla.Location(x=-1878.0, y=823.5, z=-548.6), # 99
    carla.Location(x=-1663.4, y=941.0, z=-548.6), # 100
    carla.Location(x=-1478.2, y=1047.7, z=-548.6), # 101
    carla.Location(x=-1278.5, y=1166.0, z=-548.6), # 102
    carla.Location(x=-1021.5, y=1308.5, z=-548.6), # 103
    carla.Location(x=-948.0, y=1354.1, z=-548.6), # 104
    carla.Location(x=-894.3, y=1394.4, z=-548.6), # 105
    carla.Location(x=-819.2, y=1462.7, z=-548.6), # 106
    carla.Location(x=-713.5, y=1568.8, z=-548.6), # 107
    carla.Location(x=-712.5, y=1567.1, z=-548.6), # 108
    carla.Location(x=-657.6, y=1619.4, z=-548.6), # 109
    carla.Location(x=-596.7, y=1700.3, z=-548.6), # 110
    carla.Location(x=-515.1, y=1815.9, z=-548.6), # 111
    carla.Location(x=-452.1, y=1914.5, z=-548.6), # 112
    carla.Location(x=-417.0, y=1988.4, z=-548.6), # 113
    carla.Location(x=-353.4, y=2135.9, z=-548.6), # 114
    carla.Location(x=-262.9, y=2336.5, z=-548.6), # 115
    carla.Location(x=-154.2, y=2573.9, z=-548.6), # 116
    carla.Location(x=-96.9, y=2643.9, z=-548.6), # 117
    carla.Location(x=-6.1, y=2744.2, z=-548.6), # 118
    carla.Location(x=291.6, y=2970.6, z=-548.6), # 119
    carla.Location(x=377.6, y=3058.2, z=-548.6), # 120
    carla.Location(x=605.6, y=3216.5, z=-548.6), # 121
    carla.Location(x=806.1, y=3344.1, z=-548.6), # 122
    carla.Location(x=1088.9, y=3531.8, z=-548.6), # 123
    carla.Location(x=1151.9, y=3607.8, z=-548.6), # 124
    carla.Location(x=1261.0, y=3699.9, z=-548.6), # 125
    carla.Location(x=1391.1, y=3849.7, z=-548.6), # 126
    carla.Location(x=1458.9, y=3906.5, z=-548.6), # 127
    carla.Location(x=1527.9, y=3935.8, z=-548.6), # 128
    carla.Location(x=1617.6, y=3954.5, z=-548.6), # 129
    carla.Location(x=1838.3, y=4064.0, z=-548.6), # 130
    carla.Location(x=2113.3, y=4217.3, z=-548.6), # 131
    carla.Location(x=2189.1, y=4248.2, z=-548.6), # 132
    carla.Location(x=2217.7, y=4254.0, z=-548.6), # 133
    carla.Location(x=2232.3, y=4187.1, z=-548.6), # 134
    carla.Location(x=2266.2, y=4075.4, z=-548.6), # 135
    carla.Location(x=2317.5, y=3945.4, z=-548.6), # 136
    carla.Location(x=2362.1, y=3855.9, z=-548.6), # 137
    carla.Location(x=2403.7, y=3795.1, z=-548.6), # 138
    carla.Location(x=2453.5, y=3749.8, z=-548.6), # 139
    carla.Location(x=2522.5, y=3688.5, z=-548.6), # 140
    carla.Location(x=2567.6, y=3642.9, z=-548.6), # 141
    carla.Location(x=2585.9, y=3609.0, z=-548.6), # 142
    carla.Location(x=2620.7, y=3375.9, z=-548.6), # 143
    carla.Location(x=2601.2, y=3274.9, z=-548.6), # 144
    carla.Location(x=2601.0, y=3169.3, z=-548.6), # 145
    carla.Location(x=2616.7, y=3082.2, z=-548.6), # 146
    carla.Location(x=2657.0, y=2996.3, z=-548.6), # 147
    carla.Location(x=2765.9, y=2823.3, z=-548.6), # 148
    carla.Location(x=2888.3, y=2640.3, z=-548.6), # 149
    carla.Location(x=2918.0, y=2591.0, z=-548.6), # 150
    carla.Location(x=2950.1, y=2516.8, z=-548.6), # 151
    carla.Location(x=2967.4, y=2428.6, z=-548.6), # 152
    carla.Location(x=2969.2, y=2388.9, z=-548.6), # 153
    carla.Location(x=2952.6, y=2351.8, z=-548.6), # 154
    carla.Location(x=2896.1, y=2245.9, z=-548.6), # 155
    carla.Location(x=2910.4, y=2287.0, z=-548.6), # 156
    carla.Location(x=2893.2, y=2201.6, z=-548.6), # 157
    carla.Location(x=2918.1, y=2048.7, z=-548.6), # 158
    carla.Location(x=2913.5, y=2011.8, z=-548.6), # 159
    carla.Location(x=2896.8, y=1949.1, z=-548.6), # 160
    carla.Location(x=2872.2, y=1890.8, z=-548.6), # 161
    carla.Location(x=2841.2, y=1820.0, z=-548.6), # 162
    carla.Location(x=2810.1, y=1749.0, z=-548.6), # 163
    carla.Location(x=2709.8, y=1548.8, z=-548.6), # 164
    carla.Location(x=2696.1, y=1490.7, z=-548.6), # 165
    carla.Location(x=2699.0, y=1376.2, z=-548.6), # 166
    carla.Location(x=2703.8, y=1100.3, z=-548.6), # 167
    carla.Location(x=2704.3, y=784.4, z=-548.6), # 168
    carla.Location(x=2732.7, y=726.3, z=-548.6), # 169
    carla.Location(x=3038.6, y=481.0, z=-548.6), # 170
    carla.Location(x=3064.9, y=422.2, z=-548.6), # 171
    carla.Location(x=3005.2, y=-24.0, z=-548.6), # 172
    carla.Location(x=3018.1, y=-107.6, z=-548.6), # 174
    carla.Location(x=3093.7, y=-227.0, z=-548.6), # 173 # 174 and 173 need to be swapped because of the order they were placed in UE5, but I want to keep the original order numbering for reference
]


class FollowPath(object):

    def __init__(self, world, vehicle, env=None):
        self.world = world
        self.vehicle = vehicle # this is passed in so I don't need to constantly pass in the vehicle variable over and over again when moving the vehicle along the path
        self.env = env
        self.path = self.get_ordered_path()
        self.path_index = 0
        print(f"Successfully loaded {len(self.path)} points into the array.")
        self.resetObjects = False;

    def find_next_waypoint(self):
        if not self.path:
            return None

        target_loc = self.path[self.path_index]
        v_loc = self.vehicle.get_location()

        # Check if we've arrived at the current target point
        if v_loc.distance(target_loc) < THRESHOLD_DISTANCE:
            # Move to the next point
            self.path_index = (self.path_index + 1) % len(self.path)
            target_loc = self.path[self.path_index]
            print(f"Switched to Waypoint {self.path_index}")

        return target_loc
    
    def reset(self):
        self.path_index = 0
    
    def get_ordered_path(self):
        print(f"Hardcoded path loaded with {len(PATH_ARRAY)} points")
        return PATH_ARRAY
    
    def isLastPoint(self):
        if ((self.path_index == len(self.path) - 1) and (not self.resetObjects)):
            self.resetObjects = True
            return True
        elif (self.path_index == 0):
            self.resetObjects = False
            return False
        return False # otherwise, false

    def drive_to_next_waypoint(self):
        
        # Path Safety Check
        if not self.path or self.path_index >= len(self.path):
            self.vehicle.apply_control(carla.VehicleControl(hand_brake=True))
            return

        # --- TUNING PARAMETERS --- #
        TARGET_SPEED_KMH = 96.4   # Cap speed  for stability, this is 60MPH in KM/H
        TURN_SPEED_KMH = 80.4     # Slow down for sharp turns, this is 50MPH in KM/H
        LOOK_AHEAD_DISTANCE = 5.0 
        THRESHOLD_2D = 4.0        

        # Get the Segment and Vehicle state
        target_loc = self.path[self.path_index]
        prev_idx = (self.path_index - 1) % len(self.path)
        prev_loc = self.path[prev_idx]

        v_transform = self.vehicle.get_transform()
        v_loc = v_transform.location
        v_yaw = v_transform.rotation.yaw
        
        # Calculate actual velocity in KM/H
        v_vel = self.vehicle.get_velocity()
        current_speed = 3.6 * math.sqrt(v_vel.x**2 + v_vel.y**2 + v_vel.z**2)

        # 2D DISTANCE CHECK
        dx_to_target = target_loc.x - v_loc.x
        dy_to_target = target_loc.y - v_loc.y
        dist_2d = math.sqrt(dx_to_target**2 + dy_to_target**2)

        if dist_2d < THRESHOLD_2D:
            self.path_index = (self.path_index + 1) % len(self.path)
            print(f"Waypoint {self.path_index} reached. Speed: {current_speed:.1f} km/h")
            return

        # LINE PROJECTION (Cleaving Logic)
        line_dx = target_loc.x - prev_loc.x
        line_dy = target_loc.y - prev_loc.y
        line_mag_sq = (line_dx**2 + line_dy**2) or 0.1

        u = ((v_loc.x - prev_loc.x) * line_dx + (v_loc.y - prev_loc.y) * line_dy) / line_mag_sq
        u = max(0, min(1, u))

        # AIM POINT
        line_mag = math.sqrt(line_mag_sq)
        look_ahead_u = min(1.0, u + (LOOK_AHEAD_DISTANCE / line_mag))
        aim_x = prev_loc.x + look_ahead_u * line_dx
        aim_y = prev_loc.y + look_ahead_u * line_dy

        # STEERING
        angle_to_aim = math.degrees(math.atan2(aim_y - v_loc.y, aim_x - v_loc.x))
        steer_err = angle_to_aim - v_yaw

        while steer_err > 180: steer_err -= 360
        while steer_err < -180: steer_err += 360

        # Adjust steering sensitivity based on speed (higher speed = more careful steering)
        steer_input = steer_err / 50.0 
        steer_input = max(-1.0, min(1.0, steer_input))

        # DYNAMIC THROTTLE & BRAKING
        # If we are steering hard, our "desired speed" should be the TURN_SPEED
        desired_speed = TARGET_SPEED_KMH if abs(steer_input) < 0.2 else TURN_SPEED_KMH
        
        throttle = 0.0
        brake = 0.0

        if current_speed < desired_speed:
            throttle = 1.0 # Gentle acceleration
            brake = 0.0
        elif current_speed > desired_speed + 2.0:
            throttle = 0.0
            brake = 0.3 # Apply light brakes if sliding/overspeeding

        self.vehicle.apply_control(carla.VehicleControl(
            throttle=throttle,
            steer=steer_input,
            brake=brake
        ))

        if self.isLastPoint(): # quite inefficient but should work
            self.env.collisionCauser.spawn_obstacles_at_all_path_points()