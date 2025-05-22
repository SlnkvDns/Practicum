# plants.py
from typing import List
from abc import abstractmethod
import random
from meta import EvalPlantMeta, EcosystemRegistry
from logging import Logger

logger = Logger()

# Базовый класс для всех растений с метаклассом
class Plant(metaclass=EvalPlantMeta):
    def __init__(self, position: List[int]):
        self.position = position.copy()
        self.growth_time = []
        self.competitors = []
        self.failed_growth_ticks = 0  # Счётчик неудачных попыток роста
        logger.log_console(f"Создан {self.__class__.__name__}. Позиция: {self.position}")

    @abstractmethod
    def can_grow(self, current_time: str) -> bool:
        """Определяет, может ли растение расти в текущее время суток"""
        pass

    def _can_replace(self, other):
        """Проверяет, может ли растение заменить другое"""
        return isinstance(other, tuple(self.competitors)) if other else False

    def grow(self, world, day_time):
        """Метод роста растения"""
        if self.can_grow(day_time):
            self.failed_growth_ticks = 0
            self.try_spread(world)
        else:
            self.failed_growth_ticks += 1

    def update_state(self, world, day_time):
        """Обновление состояния растения"""
        self.check_self_modification(day_time)
        self.grow(world, day_time)

    def check_self_modification(self, day_time):
        """Проверка и модификация растения при необходимости"""
        if self.failed_growth_ticks >= 3 and not hasattr(self, "_is_aggressive"):
            self._is_aggressive = True
            self.make_aggressive_spread()

    def make_aggressive_spread(self):
        """Модификация метода распространения для более агрессивного поведения"""
        # Новый метод распространения с более высокой вероятностью
        def aggressive_spread(self, world):
            target = world.get_free_adjacent_cells(self.position)
            if target:
                new_pos = random.choice(target)
                if self._can_replace(new_pos):
                    if random.random() < 0.75:  # Более высокая агрессия
                        world.add_entity(self.__class__([new_pos[0], new_pos[1]]))
                        logger.log_console(f"{self.__class__.__name__} агрессивно распространился на {new_pos}")
                        return True
                elif target is None:
                    if random.random() < 0.9:
                        world.add_entity(self.__class__([new_pos[0], new_pos[1]]))
                        logger.log_console(f"{self.__class__.__name__} агрессивно распространился на {new_pos}")
                        return True
            return False

        # Заменяем метод распространения
        self.try_spread = aggressive_spread.__get__(self)
        logger.log_console(f"{self.__class__.__name__} стал агрессивным в распространении")


# Растение света - активно днем
class Lumiere(Plant):
    # Определение поведения по времени суток через метаклассы
    time_behavior = {
        "day": {"active": True, "spread_chance": 0.4},
        "morning": {"active": False, "spread_chance": 0.1},
        "evening": {"active": False, "spread_chance": 0.1},
        "night": {"active": False, "spread_chance": 0.0}
    }
    
    # Настройки распространения
    aggressive_spread_chance = 0.4
    default_spread_chance = 0.25
    
    def __init__(self, position: List[int]):
        super().__init__(position)
        self.growth_time = ["day"]
        
        # Получаем классы конкурентов из реестра
        self.competitors = [
            EcosystemRegistry.get_plant_class("Obscurite"),
            EcosystemRegistry.get_plant_class("Demi")
        ]
        
        # Если классы еще не зарегистрированы, используем строки
        if None in self.competitors:
            self.competitors = []


class Demi(Plant):
    # Определение поведения по времени суток через метаклассы
    time_behavior = {
        "day": {"active": False, "spread_chance": 0.1},
        "morning": {"active": True, "spread_chance": 0.4},
        "evening": {"active": True, "spread_chance": 0.4},
        "night": {"active": False, "spread_chance": 0.0}
    }
    
    # Настройки распространения
    aggressive_spread_chance = 0.5
    default_spread_chance = 0.3
    
    def __init__(self, position: List[int]):
        super().__init__(position)
        self.growth_time = ["morning", "evening"]
        
        # Получаем классы конкурентов из реестра
        self.competitors = [
            EcosystemRegistry.get_plant_class("Obscurite"),
            EcosystemRegistry.get_plant_class("Lumiere")
        ]
        
        # Если классы еще не зарегистрированы, используем строки
        if None in self.competitors:
            self.competitors = []


class Obscurite(Plant):
    # Определение поведения по времени суток через метаклассы
    time_behavior = {
        "day": {"active": False, "spread_chance": 0.0},
        "morning": {"active": False, "spread_chance": 0.1},
        "evening": {"active": False, "spread_chance": 0.1},
        "night": {"active": True, "spread_chance": 0.5}
    }
    
    # Настройки распространения
    aggressive_spread_chance = 0.6
    default_spread_chance = 0.35
    
    def __init__(self, position: List[int]):
        super().__init__(position)
        self.growth_time = ["night"]
        
        # Получаем классы конкурентов из реестра
        self.competitors = [
            EcosystemRegistry.get_plant_class("Lumiere"),
            EcosystemRegistry.get_plant_class("Demi")
        ]
        
        # Если классы еще не зарегистрированы, используем строки
        if None in self.competitors:
            self.competitors = []
            