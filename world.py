import random
from typing import List, Type
from time import sleep
from animals import *
from plants import *
from time_1 import Time


class World:
    def __init__(self, width: int, height: int, max_ticks: int):
        self.width = width
        self.height = height
        self.max_ticks = max_ticks
        self.matrix = [[None for _ in range(width)] for _ in range(height)]
        self.entities: List[object] = []
        self.time = Time()
        
        # Конфигурация начальной популяции
        self.initial_population = {
            Malheureux: 3,
            Pauvre: 5,
            Lumiere: 10,
            Obscurite: 8,
            Demi: 7
        }
    def remove_group(self, group: List[Animal]):
        # Удаляем группу из общего списка
        for animal in group:
            if animal in self.entities:
                self.entities.remove(animal)
                x, y = animal.position
                self.matrix[x][y] = None

    def get_nearby_objects(self, position: List[int], radius: int) -> List[object]:
        x, y = position
        nearby = []
        for dx in range(-radius, radius+1):
            for dy in range(-radius, radius+1):
                if 0 <= x+dx < self.height and 0 <= y+dy < self.width:
                    obj = self.matrix[x+dx][y+dy]
                    if obj and (dx != 0 or dy != 0):
                        nearby.append(obj)
        return nearby
    
    def is_valid_position(self, x: int, y: int) -> bool:
        return 0 <= x < self.height and 0 <= y < self.width


    def add_entity(self, new_entity: Type, count: int = 1):
        self.matrix[new_entity.position[0]][new_entity.position[1]] = new_entity
        self.entities.append(new_entity)
        

    def delete_unit(self, entity: object):
        if entity in self.entities:
            x, y = entity.position
            self.matrix[x][y] = None
            self.entities.remove(entity)

    def move_entity(self, entity: object, new_pos: List[int]):
        old_x, old_y = entity.position
        new_x, new_y = new_pos
        
        if self.is_valid_position(new_x, new_y) and self.matrix[new_x][new_y] is None:
            self.matrix[old_x][old_y] = None
            entity.position = [new_x, new_y]
            self.matrix[new_x][new_y] = entity
            return True
        return False
    
    def relocate_unit(self, obj: object, new_pos: List[int]):
            success = self.move_entity(obj, new_pos)
            if success:
                logger.log_console(f"{obj.__class__.__name__} переместился на {new_pos}")
            return success
    
    def process_tick(self):
        current_time = self.time.get_time()
        
        for entity in list(self.entities):
            entity.update_state(self, current_time)
                
        self.time.change_time()

    def initial_spawn(self, entity_class: Type, count: int = 1):
        for _ in range(count):
            while True:
                x = random.randint(0, self.height-1)
                y = random.randint(0, self.width-1)
                if self.matrix[x][y] is None:
                    entity = entity_class([x, y])
                    self.matrix[x][y] = entity
                    self.entities.append(entity)
                    break

    def initialize_ecosystem(self):
        for entity_class, count in self.initial_population.items():
            self.initial_spawn(entity_class, count)

    def run_simulation(self):
        self.initialize_ecosystem()
        
        for tick in range(self.max_ticks):
            print(f"\n=== Tick {tick+1} ===")
            print(f"Current time: {self.time.current_time}")
            self.print_world_state()
            self.process_tick()
            sleep(1)

    def print_world_state(self):
        symbols = {
            Malheureux: 'M',
            Pauvre: 'P',
            Lumiere: '☀',
            Obscurite: '🌙',
            Demi: '🌓',
            None: '·'
        }
        
        for row in self.matrix:
            print(' '.join([symbols[type(obj)] if obj else symbols[None] for obj in row]))


    def get_free_adjacent_cells(self, position: List[int]) -> List[Tuple[int, int]]:
        x, y = position
        cells = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if self.is_valid_position(nx, ny) and self.matrix[nx][ny] is None:
                    cells.append((nx, ny))
        return cells
