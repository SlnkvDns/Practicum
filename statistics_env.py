# stats.py
from typing import Dict, List, Any, Tuple
from animals import Animal, Malheureux, Pauvre
from plants import Plant, Lumiere, Obscurite, Demi

class EcosystemStats:
    """Класс для сбора и анализа статистики экосистемы"""
    
    def __init__(self):
        self.history = []
    
    def collect_stats(self, world, current_tick: int) -> Dict[str, Any]:
        """Собирает статистику о текущем состоянии мира"""
        stats = {
            'tick': current_tick,
            'time': world.time.current_time,
            'entities': {
                'total': len(world.entities),
                'plants': 0,
                'animals': 0
            },
            'species_count': {},
            'animals_data': {
                'active_count': 0,
                'hungry_count': 0,
                'avg_food': 0,
                'avg_vision_radius': 0,
                'group_stats': {}
            },
            'plants_data': {
                'growth_active': 0
            }
        }
        
        # Подсчет различных видов
        animal_food_values = []
        animal_vision_values = []
        active_animals = 0
        hungry_animals = 0
        
        # Статистика групп животных
        groups_by_species = {}
        
        for entity in world.entities:
            species_name = type(entity).__name__
            stats['species_count'][species_name] = stats['species_count'].get(species_name, 0) + 1
            
            if isinstance(entity, Animal):
                stats['entities']['animals'] += 1
                animal_food_values.append(entity.food)
                
                # Добавляем vision_radius если его нет
                if not hasattr(entity, 'vision_radius'):
                    entity.vision_radius = 3
                animal_vision_values.append(entity.vision_radius)
                
                if entity.is_active:
                    active_animals += 1
                if entity.is_hungry:
                    hungry_animals += 1
                
                # Статистика групп
                if hasattr(entity, 'group') and entity.group:
                    if species_name not in groups_by_species:
                        groups_by_species[species_name] = set()
                    groups_by_species[species_name].add(id(entity.group))
            
            elif isinstance(entity, Plant):
                stats['entities']['plants'] += 1
                # Можно добавить проверку активности роста
                if hasattr(entity, 'can_grow') and entity.can_grow(world.time.current_time):
                    stats['plants_data']['growth_active'] += 1
        
        # Вычисляем средние значения для животных
        if animal_food_values:
            stats['animals_data']['avg_food'] = sum(animal_food_values) / len(animal_food_values)
        if animal_vision_values:
            stats['animals_data']['avg_vision_radius'] = sum(animal_vision_values) / len(animal_vision_values)
        
        stats['animals_data']['active_count'] = active_animals
        stats['animals_data']['hungry_count'] = hungry_animals
        
        # Статистика групп
        for species, group_ids in groups_by_species.items():
            stats['animals_data']['group_stats'][species] = {
                'group_count': len(group_ids),
                'individuals': stats['species_count'].get(species, 0)
            }
        
        return stats
    
    def save_stats(self, stats: Dict[str, Any]):
        """Сохраняет статистику в историю"""
        self.history.append(stats)
    
    def get_population_trend(self, species: str, last_n_ticks: int = 10) -> List[int]:
        """Возвращает тренд популяции для указанного вида"""
        if len(self.history) < 2:
            return []
        
        recent_history = self.history[-last_n_ticks:] if len(self.history) >= last_n_ticks else self.history
        return [stat['species_count'].get(species, 0) for stat in recent_history]
    
    def calculate_diversity_index(self, stats: Dict[str, Any]) -> float:
        """Вычисляет индекс разнообразия Шеннона"""
        total = stats['entities']['total']
        if total <= 1:
            return 0.0
        
        import math
        diversity = 0.0
        for count in stats['species_count'].values():
            if count > 0:
                proportion = count / total
                diversity -= proportion * math.log(proportion)
        
        return diversity
    
    def get_ecosystem_health(self, stats: Dict[str, Any]) -> str:
        """Оценивает здоровье экосистемы"""
        total_entities = stats['entities']['total']
        diversity = self.calculate_diversity_index(stats)
        
        if total_entities < 10:
            return "Critical"
        elif diversity < 1.0:
            return "Poor"
        elif diversity < 1.5:
            return "Fair"
        else:
            return "Good"
    
    def format_detailed_stats(self, stats: Dict[str, Any]) -> str:
        """Форматирует детальную статистику для отображения"""
        text = f"=== Ecosystem Stats - Tick {stats['tick']} ===\n"
        text += f"Time of Day: {stats['time']}\n"
        text += f"Total Entities: {stats['entities']['total']}\n"
        text += f"Diversity Index: {self.calculate_diversity_index(stats):.2f}\n"
        text += f"Ecosystem Health: {self.get_ecosystem_health(stats)}\n\n"
        
        # Популяция по видам
        text += "=== SPECIES POPULATION ===\n"
        for species, count in sorted(stats['species_count'].items()):
            text += f"{species}: {count}\n"
        
        text += f"\n=== PLANTS ({stats['entities']['plants']}) ===\n"
        text += f"Growth Active: {stats['plants_data']['growth_active']}\n"
        
        text += f"\n=== ANIMALS ({stats['entities']['animals']}) ===\n"
        if stats['entities']['animals'] > 0:
            text += f"Active: {stats['animals_data']['active_count']}\n"
            text += f"Hungry: {stats['animals_data']['hungry_count']}\n"
            text += f"Avg Food: {stats['animals_data']['avg_food']:.1f}\n"
            text += f"Avg Vision Radius: {stats['animals_data']['avg_vision_radius']:.1f}\n"
            
            text += "\n=== GROUP STATISTICS ===\n"
            for species, group_data in stats['animals_data']['group_stats'].items():
                text += f"{species}: {group_data['group_count']} groups, "
                text += f"{group_data['individuals']} individuals\n"
        
        return text
    
    def export_to_csv(self, filename: str):
        """Экспортирует статистику в CSV файл"""
        import csv
        
        if not self.history:
            return
        
        fieldnames = ['tick', 'time', 'total_entities', 'diversity_index', 'ecosystem_health']
        
        # Добавляем поля для каждого вида
        all_species = set()
        for stats in self.history:
            all_species.update(stats['species_count'].keys())
        
        fieldnames.extend(sorted(all_species))
        fieldnames.extend(['active_animals', 'hungry_animals', 'avg_food', 'avg_vision'])
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for stats in self.history:
                row = {
                    'tick': stats['tick'],
                    'time': stats['time'],
                    'total_entities': stats['entities']['total'],
                    'diversity_index': self.calculate_diversity_index(stats),
                    'ecosystem_health': self.get_ecosystem_health(stats),
                    'active_animals': stats['animals_data']['active_count'],
                    'hungry_animals': stats['animals_data']['hungry_count'],
                    'avg_food': stats['animals_data']['avg_food'],
                    'avg_vision': stats['animals_data']['avg_vision_radius']
                }
                
                # Добавляем данные по видам
                for species in all_species:
                    row[species] = stats['species_count'].get(species, 0)
                
                writer.writerow(row)

# Глобальный экземпляр для удобства использования
ecosystem_stats = EcosystemStats()