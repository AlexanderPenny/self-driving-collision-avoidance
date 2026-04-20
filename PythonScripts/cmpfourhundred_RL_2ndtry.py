from fileinput import filename
import glob
from xml.parsers.expat import model

from matplotlib import image
from matplotlib.pyplot import gray
from wandb import agent
import carla
import os
import sys
import random
import time
import numpy as np
import cv2
import math
from collections import deque
from tensorflow.keras.applications import Xception
from tensorflow.keras.layers import Conv2D, Flatten, Dense, Dropout, Input, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.callbacks import TensorBoard

from tensorflow.keras.models import load_model
from cmpfourhundred_followPath import PATH_ARRAY

import tensorflow as tf
from threading import RLock, Thread, Lock
import cmpfourhundred_logger as cmp_log  # structured session logger
from tqdm import tqdm

random.seed(1)
np.random.seed(1)
tf.random.set_seed(1)

SHOW_PREVIEW = False
IM_WIDTH = 160
IM_HEIGHT = 120
REPLAY_MEMORY_SIZE = 110_000 #RAM Memory Size
MIN_REPLAY_MEMORY_SIZE = 2000
MINIBATCH_SIZE = 32 # was once 16
PREDICTION_BATCH_SIZE = 1
TRAINING_BATCH_SIZE = MINIBATCH_SIZE #// 4
UPDATE_TARGET_EVERY = 100 # was 20
MODEL_NAME = "Model_"
  
MEMORY_FRACTION = 0.4
MIN_REWARD = -200

#episodes arent really in use
SECONDS_PER_EPISODE = 20 
EPISODES = 2000

DISCOUNT = 0.99
EPSILON = 0.2
EPSILON_DECAY = 0.999
MIN_EPSILON = 0.001

AGGREGATE_STATS_EVERY = 10

STUCK_TIMER_INCREMENT = 0.05 # Increment the stuck timer by the simulation tick rate each step the vehicle is below the speed
STUCK_TIMER_THRESHOLD = 5.0 # seconds of being stuck before teleporting

# --------------------
# TensorBoard Logger
# --------------------
class ModifiedTensorBoard(tf.keras.callbacks.Callback): # Add inheritance here
    def __init__(self, log_dir):
        super().__init__() # Initialize the parent class
        self.log_dir = log_dir
        self.step = 1
        self.writer = tf.summary.create_file_writer(self.log_dir)

    def set_model(self, model):
        pass

    # Keras will find the missing methods (like set_params) 
    # inside the parent Callback class.

    def on_epoch_end(self, epoch, logs=None):
        self.update_stats(**logs)

    def on_batch_end(self, batch, logs=None):
        pass

    def on_train_end(self, _):
        pass

    def update_stats(self, **stats):
        with self.writer.as_default():
            for key, value in stats.items():
                tf.summary.scalar(key, value, step=self.step)
            self.writer.flush()
        
        self.step += 1

# --------------------
# CARLA Environment
# --------------------
class CarEnv:
    SHOW_CAM = SHOW_PREVIEW
    STEER_AMT = 1.0
    im_width = IM_WIDTH
    im_height = IM_HEIGHT
    front_camera = None

    def __init__(self, world, vehicle=None, camera_manager=None, collisionCauser=None):
        self.stack_size = 4
        self.frame_stack = deque(maxlen=self.stack_size)
        self.world = world
        self.path_index = 0
        self.stuck_timer = 0.0
        self.collisionCauser = collisionCauser
        self.vehicle = vehicle
        self.camera_manager = camera_manager
        self.blueprint_library = self.world.get_blueprint_library()

        # Get the current settings and enable synchronous mode
        settings = self.world.get_settings()
        settings.synchronous_mode = True
        # Set a fixed time step so every 'tick' represents 0.05s
        settings.fixed_delta_seconds = 0.05 
        self.world.apply_settings(settings)

    def reset(self):
        if hasattr(self, 'actor_list') and len(self.actor_list) > 0:
            self.cleanup()
        else:
            self.actor_list = []
        cmp_log.reset()

        self.collision_hist = []
        self.collisionCauser.spawn_obstacles_at_all_path_points()

        # Spawn vehicle only if not provided
        if self.vehicle is None:
            self.transform = random.choice(self.world.get_map().get_spawn_points())
            car_bp = self.blueprint_library.filter("vehicle.*")[0]
            self.vehicle = self.world.spawn_actor(car_bp, self.transform)

        self.actor_list.append(self.vehicle)

        # Setup Obstacle Sensor
        obs_bp = self.blueprint_library.find('sensor.other.obstacle')
        obs_bp.set_attribute('distance', '15')
        obs_transform = carla.Transform(carla.Location(x=2.5, z=0.7))
        self.obs_sensor = self.world.spawn_actor(obs_bp, obs_transform, attach_to=self.vehicle)
        self.actor_list.append(self.obs_sensor)
        self.obs_sensor.listen(lambda event: self.obstacle_data(event))

        # Setup Collision Sensor
        colsensor = self.blueprint_library.find("sensor.other.collision")
        col_transform = carla.Transform(carla.Location(x=2.5, z=0.7))
        self.colsensor = self.world.spawn_actor(colsensor, col_transform, attach_to=self.vehicle)
        self.actor_list.append(self.colsensor)
        self.colsensor.listen(lambda event: self.collision_data(event))

        # --- Deadlock in Reset ---
        # In synchronous mode, we must tick the world to get initial sensor data
        self.vehicle.apply_control(carla.VehicleControl(throttle=0.0, brake=0.0))
        self.world.tick()
        
        # Give sensors a moment to receive data
        time.sleep(0.1) 

        # Wait until we have a camera image
        while self.camera_manager.raw_image is None:
            time.sleep(0.01)
            #self.world.tick()
            
        self.episode_start = time.time()
            
        # Preprocess the first frame and fill the stack
        first_frame = self.preprocess(self.camera_manager.raw_image)
        for _ in range(self.stack_size):
            self.frame_stack.append(first_frame)
            
        return np.stack(self.frame_stack, axis=-1)

    def collision_data(self, event):
        self.collision_hist.append(event)

    def obstacle_data(self, event):
        self.obstacle_distance = event.distance

    def preprocess(self, image_input):
        # --- Handle raw CARLA images vs processed numpy arrays ---
        if hasattr(image_input, 'raw_data'):
            array = np.frombuffer(image_input.raw_data, dtype=np.uint8)
            array = np.reshape(array, (image_input.height, image_input.width, 4))
        elif isinstance(image_input, np.ndarray):
            array = image_input
        else:
            raise ValueError("Unknown image format")
        
        array = array[:, :, :3] # Remove alpha channel
        gray_img = cv2.cvtColor(array, cv2.COLOR_RGB2GRAY)
        resized = cv2.resize(gray_img, (self.im_width, self.im_height))
        return resized.astype(np.uint8) #/ 255.0

    def get_stacked_state(self, new_raw_frame):
        processed_frame = self.preprocess(new_raw_frame)
        self.frame_stack.append(processed_frame)
        return np.stack(self.frame_stack, axis=-1)

    def teleport_to_last_waypoint(self):
            
        # 1. Get the previous waypoint (spawn point) and current target (for rotation)
        spawn_loc = PATH_ARRAY[(self.path_index - 1) % len(PATH_ARRAY)]
        target_loc = PATH_ARRAY[self.path_index]
        
        # 2. Calculate the yaw (rotation) to face the target waypoint
        dx = target_loc.x - spawn_loc.x
        dy = target_loc.y - spawn_loc.y
        yaw = math.degrees(math.atan2(dy, dx))
        
        # 3. Create transform (spawn 1 meter above the ground to prevent clipping into the road)
        teleport_transform = carla.Transform(
            carla.Location(x=spawn_loc.x, y=spawn_loc.y, z=spawn_loc.z + 1.0),
            carla.Rotation(pitch=0.0, yaw=yaw, roll=0.0)
        )
        
        # 4. Teleport the vehicle and kill all existing momentum
        self.vehicle.set_transform(teleport_transform)
        self.vehicle.set_target_velocity(carla.Vector3D(0, 0, 0))
        self.vehicle.set_target_angular_velocity(carla.Vector3D(0, 0, 0))
        
        # 5. Reset the stuck timer so it doesn't instantly teleport again
        self.stuck_timer = 0.0
        
        print(f"Vehicle stuck! Teleported to waypoint {(self.path_index - 1) % len(PATH_ARRAY)}")
        cmp_log.teleport((self.path_index - 1) % len(PATH_ARRAY))
    
    def get_path_following_reward(self):
        # 1. Setup Path References (Assuming PATH_ARRAY is imported)
        target_loc = PATH_ARRAY[self.path_index]
        prev_loc = PATH_ARRAY[(self.path_index - 1) % len(PATH_ARRAY)]

        v_trans = self.vehicle.get_transform()
        v_loc = v_trans.location
        v_vel = self.vehicle.get_velocity()
        
        # Speed in KM/H
        current_speed = 3.6 * math.sqrt(v_vel.x**2 + v_vel.y**2 + v_vel.z**2)

        # 2. Distance from Path (Cross-Track Error)
        # Using your projection logic (u)
        line_dx = target_loc.x - prev_loc.x
        line_dy = target_loc.y - prev_loc.y
        line_mag_sq = (line_dx**2 + line_dy**2) or 0.1
        
        u = ((v_loc.x - prev_loc.x) * line_dx + (v_loc.y - prev_loc.y) * line_dy) / line_mag_sq
        u = max(0, min(1, u))

        # Find the actual perpendicular distance to the line
        closest_x = prev_loc.x + u * line_dx
        closest_y = prev_loc.y + u * line_dy
        dist_from_path = math.sqrt((v_loc.x - closest_x)**2 + (v_loc.y - closest_y)**2)

        # 3. Heading Alignment (Are we facing the right way?)
        path_angle = math.degrees(math.atan2(line_dy, line_dx))
        v_yaw = v_trans.rotation.yaw
        angle_diff = abs(path_angle - v_yaw)
        while angle_diff > 180: angle_diff -= 360
        angle_diff = abs(angle_diff) # 0 is perfect, 180 is backwards

        # --- CALCULATE REWARD ---
        
        # Component A: Speed (Reward moving, but cap it so it doesn't just speed into walls)
        reward = current_speed * 0.2 
        
        # Component B: Path Penalty (The further from the center, the higher the penalty)
        # We use a multiplier; straying 5 meters off the path is a huge problem.
        reward -= (dist_from_path ** 2) * 1.5 

        # Component C: Alignment Penalty
        # If the car is sideways on the path, penalize it.
        reward -= angle_diff * 0.1

        # 4. Waypoint Progress Logic
        dist_to_target = v_loc.distance(target_loc)
        if dist_to_target < 5.0:
            self.path_index = (self.path_index + 1) % len(PATH_ARRAY)
            reward += 100.0 # Huge bonus for reaching a waypoint!
            print(f"Agent reached waypoint {self.path_index}!")
            cmp_log.waypoint_hit(self.path_index)

        return reward
    
    def step(self, action, apply_control=True):
        self.world.tick()
        
        # INITIALIZE MISSING ATTRIBUTES
        if not hasattr(self, 'last_action'): self.last_action = 1
        if not hasattr(self, 'stuck_timer'): self.stuck_timer = 0.0
        if not hasattr(self, 'path_index'): self.path_index = 0

        # VELOCITY & STUCK LOGIC
        v = self.vehicle.get_velocity()
        kmh = int(3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2))
        
        # We use a small threshold (1.0) because physics jitter often keeps speed > 0
        if kmh < 1.0:
            # Assuming DT (0.05) is your tick rate
            self.stuck_timer += 0.05 
        else:
            self.stuck_timer = 0.0 
            
        # If stuck for more than 5 seconds, teleport
        if self.stuck_timer > 5.0:
            self.teleport_to_last_waypoint()
            # Return immediately after teleport to reset state for next frame
            return getattr(self, 'current_state', None), -1.0, False, None

        # CONTROL MAPPING
        control = carla.VehicleControl()
        if apply_control:
            if action == 0: # LEFT
                control.steer = -0.5
                control.throttle = 0.2
            elif action == 1: # STRAIGHT - now non-intervention 
                control.steer = 0.0
                control.throttle = 0.6
            elif action == 2: # RIGHT
                control.steer = 0.5
                control.throttle = 0.2
            elif action == 3: # BRAKE
                control.throttle = 0.0
                control.brake = 1.0 
                control.steer = 0.0

            control.hand_brake = False
            control.manual_gear_shift = False
            self.vehicle.apply_control(control)

        # -- REWARDS SECTION -- #
        done = False
        reward = 0.0
        
        # Path logic to update path_index
        v_loc = self.vehicle.get_location()
        if v_loc.distance(PATH_ARRAY[self.path_index]) < 4.0:
            self.path_index = (self.path_index + 1) % len(PATH_ARRAY)
            cmp_log.waypoint_hit(self.path_index)

        # 1. Get vehicle orientation and SPEED
        v_trans = self.vehicle.get_transform()
        v_fwd = v_trans.get_forward_vector()
        v_vel = self.vehicle.get_velocity()

        # Calculate speed in meters per second (m/s)
        speed_m_s = math.sqrt(v_vel.x**2 + v_vel.y**2 + v_vel.z**2)

        # 2. Calculate Dynamic Danger Threshold
        # E.g., 1.5 seconds of reaction time, with a minimum floor of 5.0 meters
        danger_threshold = max(5.0, speed_m_s * 1.5) 

        # Always cast a long ray (e.g., 60m) so we can feed accurate distance 
        # to the neural network, even if it's not "dangerous" yet.
        ray_length = 60.0 
        is_danger = False
        self.obstacle_distance = ray_length

        # 3. Define angles for the fan
        angles = [-15.0, -7.5, 0.0, 7.5, 15.0]

        for angle in angles:
            rad = math.radians(angle)
            rotated_x = v_fwd.x * math.cos(rad) - v_fwd.y * math.sin(rad)
            rotated_y = v_fwd.x * math.sin(rad) + v_fwd.y * math.cos(rad)
            
            ray_start = v_trans.location + carla.Location(x=v_fwd.x * 2.5, y=v_fwd.y * 2.5, z=1.0)
            ray_end = ray_start + carla.Location(x=rotated_x * ray_length, y=rotated_y * ray_length, z=0)

            ray_results = self.world.cast_ray(ray_start, ray_end)

            if ray_results:
                for result in ray_results:
                    if result.label not in [carla.CityObjectLabel.Roads, carla.CityObjectLabel.RoadLines]:
                        dist = ray_start.distance(result.location)
                        
                        # Checking against the DYNAMIC threshold instead of a hardcoded number
                        if dist < danger_threshold:
                            is_danger = True
                            #print(f"Danger! Speed: {speed_m_s:.1f}m/s | Hit at: {dist:.1f}m | Threshold: {danger_threshold:.1f}m")

                        # Tracks the closest obstacle for state/rewards
                        if dist < self.obstacle_distance:
                            self.obstacle_distance = dist
                        break
                
                if is_danger: 
                    break 
            
            if not is_danger:
                self.world.debug.draw_line(ray_start, ray_end, thickness=0.1, 
                                         color=carla.Color(0, 255, 0), life_time=0.05) 
        
        if len(self.collision_hist) > 0:
            reward = -200.0  # Death Penalty
            done = True

            # Get the first collision event from the history
            first_collision = self.collision_hist[0]
            object_name = first_collision.other_actor.type_id
            
            #print(f"CRASHED into {object_name}: -200")
            cmp_log.crash(object_name)

            self.collision_hist = []
        elif is_danger:
            if action == 3:   # BRAKE
                reward = 5.0  # High reward for slowing down in danger
            elif action in [0, 2]: # LEFT/RIGHT
                reward = 3.0  # Good reward for steering in danger
            else:             # STRAIGHT
                reward = -10.0 # Heavy penalty for driving straight into a cone
        else:
            # Clear road logic
            if action == 1:   # Driving straight on a clear road
                reward = 1.0
            else:             # Turning for no reason
                reward = -0.5
        
        self.last_action = action

        # -- END OF REWARDS SECTION -- #

        if self.episode_start + SECONDS_PER_EPISODE < time.time():
            done = True

        if getattr(self, 'camera_manager', None) is not None and self.camera_manager.raw_image is not None:
            self.current_state = self.get_stacked_state(self.camera_manager.raw_image)

        if v_loc.z < -600:
            print(f"Height Critical ({v_loc.z:.2f}). Teleporting to last waypoint...")
            self.teleport_to_last_waypoint()

        return getattr(self, 'current_state', None), reward, done, None

    def cleanup(self):
        # Stop sensors from listening first (prevents the IMU/nullptr crash)
        if hasattr(self, 'obs_sensor') and self.obs_sensor.is_listening:
            self.obs_sensor.stop()
        if hasattr(self, 'colsensor') and self.colsensor.is_listening:
            self.colsensor.stop()
        
        # Destroy actors in reverse order
        for actor in reversed(self.actor_list):
            if actor is not None and actor.is_alive:
                actor.destroy()
        
        # Clear the list
        self.actor_list = []

# --------------------
def sanitize_filename(name: str) -> str:
    # Replace common invalid filename characters with underscores
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for ch in invalid_chars:
        name = name.replace(ch, '_')
    return name


class DQNAgent:
    def __init__(self):
        LOADING_MODEL = True
        # Load the main model
        if LOADING_MODEL:   
            self.model = load_model("models/GoodModel.keras")
            print("Loaded model successfully.")
            # Target Model
            self.target_model = self.create_model()
            self.target_model.set_weights(self.model.get_weights())
        else:
            self.model = self.create_model()
            print("Created new model.")

        self.replay_memory = deque(maxlen=REPLAY_MEMORY_SIZE)
        self.tensorboard = ModifiedTensorBoard(log_dir=f"logs/{MODEL_NAME}-{int(time.time())}")
        self.target_update_counter = 0

        self.terminate = False
        self.last_logged_episode = 0
        self.training_initialized = False

        self.request_counter = 0
        self.model_lock = RLock()

    def get_qs(self, state):
        with self.model_lock: # Lock during inference
            normalized_state = state.reshape(-1, IM_HEIGHT, IM_WIDTH, 4).astype('float32') / 255.0
            return self.model(normalized_state, training=False).numpy()[0]

    def create_model(self):
        # This architecture is optimized for low-latency driving regression
        model = Sequential([
        # Standard driving-task convolutions
        Conv2D(24, (5, 5), strides=(2, 2), activation='relu', input_shape=(IM_HEIGHT, IM_WIDTH, 4)),
        Conv2D(36, (5, 5), strides=(2, 2), activation='relu'),
        Conv2D(48, (5, 5), strides=(2, 2), activation='relu'),
        Conv2D(64, (3, 3), activation='relu'),
        
        Flatten(),
        Dense(100, activation='relu'),
        Dense(50, activation='relu'),
        Dense(4, activation='linear')
        ])
        model.compile(loss="mse", optimizer=Adam(learning_rate=0.001), metrics=["accuracy"])
        return model

    def update_replay_memory(self, transition):
        self.replay_memory.append(transition)
        #print(f"Replay size: {len(self.replay_memory)}")

    def train(self):
        if len(self.replay_memory) < MIN_REPLAY_MEMORY_SIZE:
            return

        minibatch = random.sample(self.replay_memory, MINIBATCH_SIZE)

        # --- Validate Replay Memory Shapes ---
        valid_minibatch = []
        expected_shape = (IM_HEIGHT, IM_WIDTH, 4)
        for sample in minibatch:
            # Check if state is shaped correctly (H, W, Channels)
            if sample[0].shape == expected_shape:
                valid_minibatch.append(sample)
    
        if len(valid_minibatch) < 2: # Need at least a couple samples to train
            return
        
        minibatch = valid_minibatch
    # ------------------------------------------

        
        # Normalize the entire batch at once before passing to the model
        current_states = np.array([t[0] for t in minibatch]).astype('float32') / 255.0
        future_states = np.array([t[3] for t in minibatch]).astype('float32') / 255.0
        
        # Lock during calculations (mutex essentially)
        with self.model_lock:
            current_qs = self.model(current_states, training=False).numpy()
            future_qs = self.target_model(future_states, training=False).numpy()

        X, y = [], []
        for i, (state, action, reward, new_state, done) in enumerate(minibatch):
            if not done:
                max_future = np.max(future_qs[i])
                new_q = reward + DISCOUNT * max_future
            else:
                new_q = reward

            updated_q = current_qs[i]
            updated_q[action] = new_q
            X.append(state)
            y.append(updated_q)

        log_this_step = self.tensorboard.step > self.last_logged_episode
        if log_this_step:
            self.last_logged_episode = self.tensorboard.step

        # Use an empty list instead of None if not logging
        callbacks_list = [self.tensorboard] if log_this_step else []

        # Lock during fit (mutex essentially)
        with self.model_lock:
            self.model.fit(
                np.array(X).astype('float32') / 255.0,
                np.array(y), 
                batch_size=TRAINING_BATCH_SIZE,
                verbose=0, 
                shuffle=False,
                callbacks=callbacks_list
            )

        if log_this_step:
            self.target_update_counter += 1

        if self.target_update_counter > UPDATE_TARGET_EVERY:
            self.target_model.set_weights(self.model.get_weights())
            self.target_update_counter = 0
    
    def train_in_loop(self):
        X = np.random.uniform(size=(1, IM_HEIGHT, IM_WIDTH, 4)).astype(np.float32)
        y = np.random.uniform(size=(1, 4)).astype(np.float32)
        self.model.fit(X, y, verbose=0, batch_size=1, callbacks=[])
        self.training_initialized = True

        while not self.terminate:
            self.train()
            time.sleep(0.05) # correlates to DT