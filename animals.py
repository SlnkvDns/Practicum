# animals.py
from typing import List, Tuple
import random
from abc import abstractmethod
from meta import EvalAnimalMeta, EcosystemRegistry
from logging import Logger

logger = Logger()

# Базовый класс для всех животных с метаклассом
class Animal(metaclass=EvalAnimalMeta):
    def __init__(
        self,
        position: List[int],
        speed: int = 10,
        food: int = 100,
        is_active: bool = True,
        is_hungry: bool = False
    ):
        self.position = position
        self.speed = speed
        self.food = food
        self.is_active = is_active
        self.is_hungry = is_hungry
        self.group: List[Animal] = [self]
        self._register_in_world()

    def _register_in_world(self):
        """Регистрация в глобальных группах"""
        if not hasattr(self.__class__, "groups"):
            self.__class__.groups = []
            
        self.__class__.groups.append(self.group)
        self.group_index = len(self.__class__.groups) - 1
        logger.log_console(
            f"Создан {self.__class__.__name__}. Позиция: {self.position}. Группа: {self.group_index}"
        )

    def _generate_move_delta(self) -> Tuple[int, int]:
        """Генерирует направление движения"""
        while True:
            dx = random.randint(-1, 1)
            dy = random.randint(-1, 1)
            if dx != 0 or dy != 0:
                return dx, dy

    def decrease_food(self):
        """Уменьшает количество пищи"""
        self.food = max(0, self.food - 1)

    def change_hungry_status(self):
        """Изменяет статус голода в зависимости от количества пищи"""
        new_status = self.food < 30
        if new_status != self.is_hungry:
            self.is_hungry = new_status
            status = "проголодался" if new_status else "не голоден"
            logger.log_console(f"{self.__class__.__name__} {status}")

    def change_speed_status(self):
        """Изменяет скорость в зависимости от статуса голода"""
        self.speed = 50 if self.is_hungry else 100

    def try_reproduce(self, world):
        """Пытается размножиться в зависимости от вероятности"""
        if random.random() < self.reproduction_probability():
            self.reproduce(world)

    def update_state(self, world, day_time: str):
        """Обновляет состояние животного"""
        self.change_active_status(day_time)
        self.change_hungry_status()
        self.change_speed_status()

        self.check_self_modification()

        if self.is_active:
            self.try_merge_groups(world)
            self.move(world)
            self.eat(world, day_time)
            self.try_reproduce(world)

    def check_self_modification(self):
        """Проверяет и модифицирует животное при необходимости"""
        pass  # Переопределяется в подклассах

    @abstractmethod
    def eat(self, world, day_time: str) -> None:
        """Метод поедания пищи"""
        pass

    @abstractmethod
    def change_active_status(self, day_time: str) -> None:
        """Метод изменения статуса активности"""
        pass

    @abstractmethod
    def reproduction_probability(self) -> float:
        """Метод определения вероятности размножения"""
        pass

    @abstractmethod
    def reproduce(self, world):
        """Метод размножения"""
        pass


class GroupBehaviorMixin:
    groups: List[List[Animal]] = []

    def try_merge_groups(self, world) -> None:
        """Пытается объединить группы животных"""
        nearby_entities = world.get_nearby_objects(self.position, 2)
        for entity in nearby_entities:
            if isinstance(entity, self.__class__) and \
               entity is not self and \
               random.random() < 0.25:
                
                self.group.extend(entity.group)
                for member in entity.group:
                    member.group = self.group
                world.remove_group(entity.group)
                logger.log_console(f"Группы объединены. Новая группа: {len(self.group)} особей")
                break

    def _distance_to(self, other: Animal) -> int:
        """Вычисляет расстояние до другого животного"""
        return abs(self.position[0] - other.position[0]) + abs(self.position[1] - other.position[1])


class Malheureux(Animal, GroupBehaviorMixin):
    # Регистрация групп через метакласс
    groups: List[List[Animal]] = []
    
    # Определение активных времен суток
    active_times = ["morning", "evening"]
    
    # Определение поведения при поедании пищи
    eat_behavior = {
        "morning": {
            "radius": 2,
            "target_classes": [], 
            "probability": 0.25,
            "hungry_multiplier": 2.0,
            "food_values": {
                "Demi": 30,
                "Obscurite": 40,
                "Pauvre": 60
            }
        },
        "evening": {
            "radius": 2,
            "target_classes": [],  # Будет заполнено в __init__
            "probability": 0.25,
            "hungry_multiplier": 1.5,
            "food_values": {
                "Demi": 30,
                "Obscurite": 40,
                "Pauvre": 60
            }
        },
        "default": {
            "radius": 2,
            "target_classes": [],  # Будет заполнено в __init__
            "probability": 0.1,
            "hungry_multiplier": 1.0,
            "food_values": {
                "Demi": 30,
                "Obscurite": 40,
                "Pauvre": 60
            }
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.speed = 100
        
        # Получаем классы целей из реестра
        target_classes = [
            EcosystemRegistry.get_plant_class("Demi"),
            EcosystemRegistry.get_plant_class("Obscurite"),
            EcosystemRegistry.get_animal_class("Pauvre")
        ]
        
        # Если классы уже зарегистрированы, добавляем их
        if None not in target_classes:
            # Обновляем поведение при поедании пищи
            for time_key in self.__class__.eat_behavior:
                self.__class__.eat_behavior[time_key]["target_classes"] = target_classes

    def reproduction_probability(self) -> float:
        """Определяет вероятность размножения в зависимости от размера группы"""
        return 0.2 if len(self.group) > 3 else 0.05

    def check_self_modification(self):
        """Проверяет и модифицирует животное при необходимости"""
        if len(self.group) > 5 and not hasattr(self, "_is_predatory"):
            self._is_predatory = True
            self.make_predatory_merge()

    def make_predatory_merge(self):
        """Модифицирует метод объединения групп для более агрессивного поведения"""
        def predatory_merge(world):
            nearby_entities = world.get_nearby_objects(self.position, 2)
            for entity in nearby_entities:
                if isinstance(entity, self.__class__) and entity is not self:
                    if len(entity.group) < 3:
                        self.group.extend(entity.group)
                        for member in entity.group:
                            member.group = self.group
                        world.remove_group(entity.group)
                        logger.log_console(f"{self.__class__.__name__} агрессивно поглотил другую группу.")
                        break
        self.try_merge_groups = predatory_merge.__get__(self)


# Добавьте это в конец файла animals.py
class Pauvre(Animal, GroupBehaviorMixin):
    # Регистрация групп через метакласс
    groups: List[List[Animal]] = []
    
    # Определение активных времен суток
    active_times = ["morning", "day", "evening"]
    
    # Определение поведения при поедании пищи
    eat_behavior = {
        "morning": {
            "radius": 2,
            "target_classes": [],  # Будет заполнено в __init__
            "probability": 0.33,
            "hungry_multiplier": 2.0,
            "food_values": {
                "Lumiere": 30
            }
        },
        "evening": {
            "radius": 2,
            "target_classes": [],  # Будет заполнено в __init__
            "probability": 0.11,
            "hungry_multiplier": 1.0,
            "food_values": {
                "Lumiere": 30
            }
        },
        "default": {
            "radius": 2,
            "target_classes": [],  # Будет заполнено в __init__
            "probability": 0.16,
            "hungry_multiplier": 1.0,
            "food_values": {
                "Lumiere": 30
            }
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.speed = 50
        
        # Получаем классы целей из реестра
        target_classes = [
            EcosystemRegistry.get_plant_class("Lumiere")
        ]
        
        # Если классы уже зарегистрированы, добавляем их
        if None not in target_classes:
            # Обновляем поведение при поедании пищи
            for time_key in self.__class__.eat_behavior:
                self.__class__.eat_behavior[time_key]["target_classes"] = target_classes

    def reproduction_probability(self) -> float:
        """Определяет вероятность размножения в зависимости от размера группы"""
        return 0.3 if len(self.group) > 2 else 0.1

    def check_self_modification(self):
        """Проверяет и модифицирует животное при необходимости"""
        if self.is_hungry and self.food < 10 and not hasattr(self, "_is_aggressive"):
            self._is_aggressive = True
            self.make_aggressive_eat()

    def make_aggressive_eat(self):
        """Модифицирует метод поедания пищи для более агрессивного поведения"""
        def aggressive_eat(world, day_time):
            if not self.is_active:
                return

            targets = world.get_nearby_objects(self.position, 2)
            for target in targets:
                if isinstance(target, (EcosystemRegistry.get_plant_class("Lumiere"), 
                                       EcosystemRegistry.get_animal_class("Pauvre"))) and target is not self:
                    if random.random() < 0.2:
                        world.delete_unit(target)
                        self.food += 20
                        logger.log_console(f"{self.__class__.__name__} в агрессии съел {type(target).__name__}")
                        break
        self.eat = aggressive_eat.__get__(self)