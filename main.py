# main.py
from world import World
from meta import EcosystemRegistry


class Logger:
    def log_console(self, message):
        print(message)

if __name__ == "__main__":
    world = World(width=20, height=15, max_ticks=40)
    
    world.run_simulation()
    

    print("\nСтатистика по классам растений:")
    for name, cls in EcosystemRegistry.get_all_plant_classes().items():
        print(f"- {name}")
    
    print("\nСтатистика по классам животных:")
    for name, cls in EcosystemRegistry.get_all_animal_classes().items():
        print(f"- {name}")