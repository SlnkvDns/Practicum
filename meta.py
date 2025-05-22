# meta.py
from typing import Dict, List, Type, Any, Callable, Set, Optional
import random
from abc import ABC, abstractmethod
from logging import Logger

# Предполагаем, что у нас есть логгер
logger = Logger()

# Глобальный реестр для классов экосистемы
class EcosystemRegistry:
    plant_classes: Dict[str, Type] = {}
    animal_classes: Dict[str, Type] = {}
    
    @classmethod
    def register_plant(cls, plant_class: Type):
        """Регистрирует класс растения в глобальном реестре"""
        cls.plant_classes[plant_class.__name__] = plant_class
        logger.log_console(f"Зарегистрирован новый класс растения: {plant_class.__name__}")
    
    @classmethod
    def register_animal(cls, animal_class: Type):
        """Регистрирует класс животного в глобальном реестре"""
        cls.animal_classes[animal_class.__name__] = animal_class
        logger.log_console(f"Зарегистрирован новый класс животного: {animal_class.__name__}")
    
    @classmethod
    def get_plant_class(cls, name: str):
        """Получает класс растения по имени"""
        return cls.plant_classes.get(name)
    
    @classmethod
    def get_animal_class(cls, name: str):
        """Получает класс животного по имени"""
        return cls.animal_classes.get(name)
    
    @classmethod
    def get_all_plant_classes(cls):
        """Возвращает все зарегистрированные классы растений"""
        return cls.plant_classes
    
    @classmethod
    def get_all_animal_classes(cls):
        """Возвращает все зарегистрированные классы животных"""
        return cls.animal_classes


# Базовый метакласс для экосистемы
class EcosystemMeta(type):
    """Базовый метакласс для всех сущностей экосистемы"""
    
    def __new__(mcs, name, bases, attrs):
        # Создаем новый класс
        cls = super().__new__(mcs, name, bases, attrs)
        
        
        # Добавляем методы для обработки времени суток
        mcs._inject_time_methods(cls, attrs)
        
        return cls
    
    @staticmethod
    def _inject_time_methods(cls, attrs):
        """Инжектирует методы для обработки времени суток"""
        if not hasattr(cls, "_time_behaviors"):
            cls._time_behaviors = {}
        
        # Если есть определение поведения по времени суток
        time_behavior = attrs.get("time_behavior", {})
        if time_behavior:
            cls._time_behaviors.update(time_behavior)


# Метакласс для растений
class EvalPlantMeta(EcosystemMeta):
    """Метакласс для классов растений"""
    
    def __new__(mcs, name, bases, attrs):
        # Создаем новый класс
        cls = super().__new__(mcs, name, bases, attrs)
        

        
        # Регистрируем класс в реестре
        EcosystemRegistry.register_plant(cls)
        
        # Инжектируем методы для распространения
        mcs._inject_spread_method(cls, attrs)
        
        # Инжектируем методы для проверки возможности роста
        mcs._inject_growth_methods(cls, attrs)
        
        return cls
    
    @staticmethod
    def _inject_spread_method(cls, attrs):
        """Инжектирует метод распространения растения"""
        # Определение базового метода распространения
        def spread(self, world):
            """Метод распространения растения"""
            target = world.get_free_adjacent_cells(self.position)
            if not target:
                return False
                
            new_pos = random.choice(target)
            
            # Проверка на возможность замены
            can_replace = getattr(self, "_can_replace", lambda pos: False)
            
            # Определяем вероятность распространения
            if can_replace(new_pos):
                spread_chance = getattr(cls, "aggressive_spread_chance", 0.25)
            else:
                spread_chance = getattr(cls, "default_spread_chance", 0.5)
                
            if random.random() < spread_chance:
                world.add_entity(cls([new_pos[0], new_pos[1]]))
                logger.log_console(f"{cls.__name__} распространился на позицию {new_pos}")
                return True
            return False
            
        # Если метод не определен в классе, добавляем его
        if not hasattr(cls, "try_spread") or getattr(cls, "try_spread") is None:
            cls.try_spread = spread
    
    @staticmethod
    def _inject_growth_methods(cls, attrs):
        """Инжектирует методы для проверки возможности роста"""
        # Определение базового метода проверки возможности роста
        def can_grow(self, current_time):
            """Метод проверки возможности роста"""
            return current_time in self.growth_time
            
        # Если метод не определен в классе, добавляем его
        if not hasattr(cls, "can_grow") or getattr(cls, "can_grow") is None:
            cls.can_grow = can_grow


# Метакласс для животных
class EvalAnimalMeta(EcosystemMeta):
    """Метакласс для классов животных"""
    
    def __new__(mcs, name, bases, attrs):
        # Создаем новый класс
        cls = super().__new__(mcs, name, bases, attrs)
        
        
        # Регистрируем класс в реестре
        EcosystemRegistry.register_animal(cls)
        
        # Инжектируем методы для еды, движения и размножения
        mcs._inject_eat_method(cls, attrs)
        mcs._inject_move_method(cls, attrs)
        mcs._inject_reproduce_method(cls, attrs)
        
        # Инжектируем метод для изменения статуса активности
        mcs._inject_active_status_method(cls, attrs)
        
        return cls
    
    @staticmethod
    def _inject_eat_method(cls, attrs):
        """Инжектирует метод для поедания пищи"""
        # Если есть определение для поедания пищи
        eat_behavior = attrs.get("eat_behavior", {})
        
        # Определение базового метода поедания пищи
        def eat(self, world, day_time):
            """Метод поедания пищи"""
            if not self.is_active:
                return
                
            # Получаем информацию о поведении при поедании пищи
            behavior = getattr(cls, "eat_behavior", {}).get(day_time, {})
            
            # Если нет поведения для текущего времени суток, используем стандартное
            if not behavior:
                behavior = getattr(cls, "eat_behavior", {}).get("default", {})
                
            # Получаем цели для поедания
            targets = world.get_nearby_objects(self.position, behavior.get("radius", 2))
            
            # Получаем классы целей для поедания
            target_classes = behavior.get("target_classes", [])
            
            for target in targets:
                # Проверяем, подходит ли цель для поедания
                if any(isinstance(target, target_class) for target_class in target_classes):
                    # Определяем вероятность поедания
                    eat_chance = behavior.get("probability", 0.25)
                    if self.is_hungry:
                        eat_chance *= behavior.get("hungry_multiplier", 2.0)
                        
                    if random.random() < eat_chance:
                        # Определяем количество пищи
                        food_value = behavior.get("food_values", {}).get(
                            target.__class__.__name__, 30
                        )
                        
                        # Поедаем цель
                        world.delete_unit(target)
                        self.food += food_value
                        logger.log_console(f"{cls.__name__} съел {type(target).__name__}")
                        return True
            
            return False
            
        # Если метод не определен в классе или нужно заменить, добавляем его
        if not hasattr(cls, "eat") or eat_behavior:
            cls.eat = eat
    
    @staticmethod
    def _inject_move_method(cls, attrs):
        """Инжектирует метод для движения"""
        # Определение базового метода движения
        def move(self, world):
            """Метод движения"""
            if not self.is_active or random.randint(1, 100) > self.speed:
                return False
                
            # Генерируем направление движения
            while True:
                dx = random.randint(-1, 1)
                dy = random.randint(-1, 1)
                if dx != 0 or dy != 0:
                    break
                    
            # Вычисляем новую позицию
            new_x = self.position[0] + dx
            new_y = self.position[1] + dy
            
            # Проверяем, валидна ли новая позиция
            if world.is_valid_position(new_x, new_y):
                # Перемещаем животное
                if world.relocate_unit(self, [new_x, new_y]):
                    # Уменьшаем количество пищи
                    self.decrease_food()
                    return True
            
            return False
            
        # Если метод не определен в классе, добавляем его
        if not hasattr(cls, "move") or getattr(cls, "move") is None:
            cls.move = move
    
    @staticmethod
    def _inject_reproduce_method(cls, attrs):
        """Инжектирует метод для размножения"""
        # Определение базового метода размножения
        def reproduce(self, world):
            """Метод размножения"""
            free_cells = world.get_free_adjacent_cells(self.position)
            if free_cells:
                new_pos = random.choice(free_cells)
                child = cls(new_pos)
                world.add_entity(child)
                logger.log_console(f"{cls.__name__} размножился на позиции {new_pos}")
                return True
            return False
            
        # Если метод не определен в классе, добавляем его
        if not hasattr(cls, "reproduce") or getattr(cls, "reproduce") is None:
            cls.reproduce = reproduce
    
    @staticmethod
    def _inject_active_status_method(cls, attrs):
        """Инжектирует метод для изменения статуса активности"""
        # Если есть определение для активности
        active_times = attrs.get("active_times", [])
        
        # Определение базового метода изменения статуса активности
        def change_active_status(self, day_time):
            """Метод изменения статуса активности"""
            # Получаем активные времена суток
            times = getattr(cls, "active_times", [])
            
            # Если нет активных времен суток, используем стандартные
            if not times:
                times = ["morning", "day", "evening"]
                
            # Изменяем статус активности
            new_status = day_time in times
            if new_status != self.is_active:
                self.is_active = new_status
                status = "активен" if new_status else "неактивен"
                logger.log_console(f"{cls.__name__} теперь {status}")
            
        # Если метод не определен в классе или нужно заменить, добавляем его
        if not hasattr(cls, "change_active_status") or active_times:
            cls.change_active_status = change_active_status
            