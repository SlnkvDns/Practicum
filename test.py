# test_metaclasses.py
import unittest
from meta import EcosystemRegistry
from plants import Plant, Lumiere, Obscurite, Demi
from animals import Animal, Malheureux, Pauvre
import random

# Мок-класс для симуляции мира
class World:
    def __init__(self):
        self.width = 10
        self.height = 10
        self.matrix = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.entities = []
    
    def add_entity(self, entity):
        self.entities.append(entity)
        x, y = entity.position
        self.matrix[x][y] = entity
    
    def delete_unit(self, entity):
        if entity in self.entities:
            self.entities.remove(entity)
            x, y = entity.position
            self.matrix[x][y] = None
    
    def get_nearby_objects(self, position, radius):
        x, y = position
        nearby = []
        for dx in range(-radius, radius+1):
            for dy in range(-radius, radius+1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.height and 0 <= ny < self.width:
                    obj = self.matrix[nx][ny]
                    if obj and obj.position != position:
                        nearby.append(obj)
        return nearby
    
    def get_free_adjacent_cells(self, position):
        x, y = position
        cells = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.height and 0 <= ny < self.width and self.matrix[nx][ny] is None:
                    cells.append((nx, ny))
        return cells
    
    def is_valid_position(self, x, y):
        return 0 <= x < self.height and 0 <= y < self.width
    
    def relocate_unit(self, obj, new_pos):
        old_x, old_y = obj.position
        new_x, new_y = new_pos
        
        if self.is_valid_position(new_x, new_y) and self.matrix[new_x][new_y] is None:
            self.matrix[old_x][old_y] = None
            obj.position = [new_x, new_y]
            self.matrix[new_x][new_y] = obj
            return True
        return False
    
    def remove_group(self, group):
        for animal in group:
            if animal in self.entities:
                self.entities.remove(animal)
                x, y = animal.position
                self.matrix[x][y] = None


class TestMetaclasses(unittest.TestCase):
    
    def setUp(self):
        self.world = World()
        random.seed(42)
    
    def test_registry(self):
        """Тест регистрации классов в реестре"""
        # Проверяем наличие классов растений в реестре
        self.assertIn("Lumiere", EcosystemRegistry.get_all_plant_classes())
        self.assertIn("Obscurite", EcosystemRegistry.get_all_plant_classes())
        self.assertIn("Demi", EcosystemRegistry.get_all_plant_classes())
        
        # Проверяем наличие классов животных в реестре
        self.assertIn("Malheureux", EcosystemRegistry.get_all_animal_classes())
        self.assertIn("Pauvre", EcosystemRegistry.get_all_animal_classes())
    
    def test_plant_methods(self):
        """Тест автоматически сгенерированных методов для растений"""
        # Создаем экземпляр растения
        plant = Lumiere([5, 5])
        
        # Проверяем наличие методов
        self.assertTrue(hasattr(plant, "try_spread"))
        self.assertTrue(hasattr(plant, "can_grow"))
        self.assertTrue(hasattr(plant, "grow"))
        self.assertTrue(hasattr(plant, "update_state"))
        
        # Проверяем корректность методов

        self.assertFalse(plant.can_grow("night"))
    
    def test_animal_methods(self):
        """Тест автоматически сгенерированных методов для животных"""
        # Создаем экземпляр животного
        animal = Malheureux([5, 5])
        
        # Проверяем наличие методов
        self.assertTrue(hasattr(animal, "eat"))
        self.assertTrue(hasattr(animal, "move"))
        self.assertTrue(hasattr(animal, "reproduce"))
        self.assertTrue(hasattr(animal, "change_active_status"))
        
        # Проверяем корректность методов
        animal.change_active_status("morning")
        self.assertTrue(animal.is_active)
        
        animal.change_active_status("night")
        self.assertFalse(animal.is_active)
    
    def test_plant_behavior(self):
        """Тест поведения растений в разных режимах времени"""
        # Создаем растения
        lumiere = Lumiere([5, 5])
        obscurite = Obscurite([4, 4])
        demi = Demi([6, 6])
        
        # Добавляем растения в мир
        self.world.add_entity(lumiere)
        self.world.add_entity(obscurite)
        self.world.add_entity(demi)
        

    
    def test_animal_behavior(self):
        """Тест поведения животных в разных режимах времени"""
        # Создаем животных
        malheureux = Malheureux([5, 5])
        pauvre = Pauvre([7, 7])
        
        # Добавляем животных в мир
        self.world.add_entity(malheureux)
        self.world.add_entity(pauvre)
        
        # Проверяем активность в соответствующее время суток
        malheureux.change_active_status("morning")
        self.assertTrue(malheureux.is_active)
        
        malheureux.change_active_status("night")
        self.assertFalse(malheureux.is_active)
        
        pauvre.change_active_status("day")
        self.assertTrue(pauvre.is_active)
        
        pauvre.change_active_status("night")
        self.assertFalse(pauvre.is_active)
    
    def test_self_modification(self):
        """Тест самомодификации классов"""
        # Создаем животное
        malheureux = Malheureux([5, 5])
        
        # Добавляем животное в мир
        self.world.add_entity(malheureux)
        
        # Создаем большую группу для проверки самомодификации
        for i in range(5):
            member = Malheureux([5 + i, 5])
            self.world.add_entity(member)
            malheureux.group.append(member)
            member.group = malheureux.group
        
        # Проверяем самомодификацию
        self.assertFalse(hasattr(malheureux, "_is_predatory"))
        malheureux.check_self_modification()
        self.assertTrue(hasattr(malheureux, "_is_predatory"))


if __name__ == "__main__":
    unittest.main()
    