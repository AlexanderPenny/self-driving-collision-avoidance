import carla
import random
import time
import math
from cmpfourhundred_followPath import PATH_ARRAY

DT = 0.05  # Time step for updates
SPAWN_RATE = 0.2  # Seconds between spawns
SLEEP_TIME = 2  # Sleep time for main loop to prevent overload

RELIABLE_PROPS = [
    'static.prop.trafficcone01'      # Cone
]

def get_actor_display_name(actor):
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:15] + '..') if len(name) > 17 else name

class CollisionCauser:
    def __init__(self, host='127.0.0.1', port=2000):
        self.client = carla.Client(host, port)
        self.client.set_timeout(10.0)
        self.world = self.client.get_world()
        self.blueprint_library = self.world.get_blueprint_library()
        self.vehicle = None
        self.spawned_obstacles = []

    def find_hero_vehicle(self):
        for actor in self.world.get_actors():
            if actor.attributes.get('role_name') == 'hero':
                return actor
        return None
    
    def spawn_obstacles_at_all_path_points(self):
        """Spawns obstacles at the midpoint between waypoints if distance >= 50m"""
        ASSUMED_ROAD_Z = -549.3 # I assume (true) that the world/road is at -549.3
        spawn_height = ASSUMED_ROAD_Z + 0.5 # 0.5m above road to prevent clipping
        
        spawn_count = 0
        
        # Iterate through the array to get pairs of consecutive waypoints
        for i in range(len(PATH_ARRAY) - 1):
            p1 = PATH_ARRAY[i]
            p2 = PATH_ARRAY[i + 1]
            
            # Calculate the 2D distance between the two points
            dist = math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
            
            # Only spawn if the distance is 50 meters or more
            if dist >= 50.0:
                # Calculate the midpoint
                mid_x = (p1.x + p2.x) / 2.0
                mid_y = (p1.y + p2.y) / 2.0
                
                # Create the spawn location at the new midpoint
                spawn_loc = carla.Location(x=mid_x, y=mid_y, z=spawn_height)
                spawn_trans = carla.Transform(spawn_loc)
                
                bp_name = random.choice(RELIABLE_PROPS)
                bp = self.blueprint_library.find(bp_name)
                
                # Use try_spawn_actor to avoid crashing if one point is blocked
                obstacle = None  # <-- add this line before the try
                try:
                    obstacle = self.world.spawn_actor(bp, spawn_trans)
                    self.spawned_obstacles.append(obstacle)
                    spawn_count += 1
                except Exception as e:
                    print(f"Skipped spawn at {mid_x:.1f}, {mid_y:.1f}: {e}")

        print(f"SUCCESS: Spawned {spawn_count} obstacles at midpoints with Z: {spawn_height}")

    def spawn_obstacle(self, distance_ahead=40):
        if not self.vehicle:
            self.vehicle = self.find_hero_vehicle()
            if not self.vehicle: return

        # Use a predefined list of reliable props
        bp = self.blueprint_library.find(random.choice(RELIABLE_PROPS))

        # Get vehicle transform
        v_trans = self.vehicle.get_transform()
        v_fwd = v_trans.get_forward_vector()

        # Calculate spawn location (Current Pos + Forward Vector * distance)
        spawn_loc = v_trans.location + v_fwd * distance_ahead
        spawn_loc.z += 0.5  # Spawn slightly above ground to prevent clipping

        # Create transform (align rotation with car or keep random)
        spawn_trans = carla.Transform(spawn_loc, v_trans.rotation)

        obstacle = self.world.try_spawn_actor(bp, spawn_trans)
        if obstacle:
            print(f"Spawned {get_actor_display_name(obstacle)} at {distance_ahead}m ahead.")
            self.spawned_obstacles.append(obstacle)

    def cleanup_passed_obstacles(self):
        """Deletes objects once the car has driven past them"""
        if not self.vehicle: return

        v_loc = self.vehicle.get_location()
        v_fwd = self.vehicle.get_transform().get_forward_vector()

        for obs in self.spawned_obstacles[:]:
            if not obs.is_alive:
                self.spawned_obstacles.remove(obs)
                continue

            # Vector from obstacle to car
            vec_to_car = v_loc - obs.get_location()
            
            # DOT PRODUCT: If positive, the car is 'beyond' the object in the direction it's facing
            dot = vec_to_car.x * v_fwd.x + vec_to_car.y * v_fwd.y
            
            # Alternative condition: Distance is more than 50m behind
            dist = v_loc.distance(obs.get_location())

            if dot > 5 or dist > 100: # 5 meters past the object
                print(f"Passed {get_actor_display_name(obs)}. Deleting.")
                obs.destroy()
                self.spawned_obstacles.remove(obs)

    def run(self):
        last_spawn_time = time.time()
        print("Collision Causer active. Waiting for hero vehicle...")
        try:
            while True:
                # Check for cleanup
                self.cleanup_passed_obstacles()
                
                time.sleep(SLEEP_TIME) # To not overwhelm the CPU
        except KeyboardInterrupt:
            print("\nStopping Causer. Cleaning up...")
            for obs in self.spawned_obstacles:
                if obs.is_alive: obs.destroy()

if __name__ == '__main__':
    causer = CollisionCauser()
    causer.run()