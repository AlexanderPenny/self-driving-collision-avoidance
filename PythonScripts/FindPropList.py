import carla

client = carla.Client('172.25.176.1', 2000)
world = client.get_world()
bp_lib = world.get_blueprint_library()

# Search for any static props available
props = bp_lib.filter('static.prop.*')
for bp in props:
    print(f"Available Prop: {bp.id}")

# Search for decorations (sometimes cones are here)
decos = bp_lib.filter('static.decoration.*')
for bp in decos:
    print(f"Available Deco: {bp.id}")