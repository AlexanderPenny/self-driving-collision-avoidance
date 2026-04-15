import carla

class CarlaUtils:
    @staticmethod
    def switchMap(args, world):
        client = carla.Client(args.host, args.port)
        client.set_timeout(20.0)

        available_maps = client.get_available_maps()
        print("Available maps on server:", available_maps)

        map_name = 'RuralMap0' 
    
        if any(map_name in m for m in available_maps):
            print(f"Loading {map_name}...")
            world = client.load_world(map_name)
        else:
            print(f"FAILED: {map_name} is not in the packaged build's map list.")
    
        return world