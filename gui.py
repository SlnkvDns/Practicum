# gui_main.py
import PySimpleGUI as sg
import random
from typing import List, Dict, Any, Optional, Tuple
from world import World
from animals import Malheureux, Pauvre
from plants import Lumiere, Obscurite, Demi
from meta import EcosystemRegistry
import math

class EcosystemGUI:
    def __init__(self):
        self.world = World(width=30, height=20, max_ticks=1000)
        self.current_tick = 0
        self.max_ticks = 200
        self.simulation_running = False
        self.selected_entity = None
        self.canvas_size = (800, 600)
        self.cell_size = min(self.canvas_size[0] // self.world.width, 
                           self.canvas_size[1] // self.world.height)
        
        # История состояний для перемотки
        self.simulation_history = []
        self.save_initial_state()
        
        # Настройка интерфейса
        self.setup_layout()
        self.window = sg.Window('Ecosystem Simulator', self.layout, finalize=True)
        self.graph = self.window['-MAP-']
        
        # Инициализация экосистемы
        self.world.initialize_ecosystem()
        self.save_state()
        self.update_display()

    def setup_layout(self):
        """Создание макета интерфейса"""
        # Верхняя панель с элементами управления
        top_panel = [
            [sg.Text('Time Control:', font=('Arial', 12, 'bold'))],
            [sg.Text('Tick:'), 
             sg.Slider(range=(0, self.max_ticks), orientation='h', 
                      key='-TIME-', enable_events=True, size=(60, 20),
                      default_value=0, resolution=1)],
            [sg.Button('Play/Pause', key='-PLAY_PAUSE-', size=(10, 1)),
             sg.Button('Step Forward', key='-STEP-', size=(12, 1)),
             sg.Button('Reset', key='-RESET-', size=(8, 1)),
             sg.Text('Speed:'), 
             sg.Slider(range=(1, 10), orientation='h', key='-SPEED-', 
                      default_value=5, size=(20, 15))]
        ]
        
        # Центральная карта
        map_panel = [
            [sg.Graph(canvas_size=self.canvas_size, 
                     graph_bottom_left=(0, 0),
                     graph_top_right=(self.canvas_size[0], self.canvas_size[1]),
                     key='-MAP-', 
                     enable_events=True,
                     background_color='black')]
        ]
        
        # Нижняя панель статистики
        stats_panel = [
            [sg.Text('Statistics:', font=('Arial', 12, 'bold'))],
            [sg.Multiline(size=(100, 8), key='-STATS-', disabled=True, 
                         background_color='white', text_color='black')],
            [sg.Text('Entity Info:', font=('Arial', 10, 'bold'))],
            [sg.Multiline(size=(100, 4), key='-ENTITY_INFO-', disabled=True,
                         background_color='lightgray', text_color='black')]
        ]
        
        self.layout = [
            [sg.Column(top_panel, justification='center')],
            [sg.Column(map_panel, justification='center')],
            [sg.Column(stats_panel, justification='center')]
        ]

    def save_initial_state(self):
        """Сохраняет начальное состояние мира"""
        self.simulation_history = []
        self.current_tick = 0

    def save_state(self):
        """Сохраняет текущее состояние симуляции"""
        state = {
            'tick': self.current_tick,
            'time': self.world.time.current_time,
            'entities': []
        }
        
        for entity in self.world.entities:
            entity_data = {
                'type': type(entity).__name__,
                'position': entity.position.copy(),
                'class': type(entity)
            }
            
            # Дополнительные данные для животных
            if hasattr(entity, 'food'):
                entity_data.update({
                    'food': entity.food,
                    'is_active': entity.is_active,
                    'is_hungry': entity.is_hungry,
                    'speed': entity.speed
                })
            
            state['entities'].append(entity_data)
        
        # Ограничиваем историю для экономии памяти
        if len(self.simulation_history) >= self.max_ticks:
            self.simulation_history.pop(0)
        
        self.simulation_history.append(state)

    def restore_state(self, tick: int):
        """Восстанавливает состояние симуляции на указанный тик"""
        if tick < 0 or tick >= len(self.simulation_history):
            return
            
        state = self.simulation_history[tick]
        
        # Очищаем текущий мир
        self.world.entities.clear()
        self.world.matrix = [[None for _ in range(self.world.width)] 
                            for _ in range(self.world.height)]
        
        # Восстанавливаем сущности
        for entity_data in state['entities']:
            entity_class = entity_data['class']
            entity = entity_class(entity_data['position'])
            
            # Восстанавливаем дополнительные данные для животных
            if hasattr(entity, 'food'):
                entity.food = entity_data.get('food', 100)
                entity.is_active = entity_data.get('is_active', True)
                entity.is_hungry = entity_data.get('is_hungry', False)
                entity.speed = entity_data.get('speed', 50)
            
            self.world.entities.append(entity)
            x, y = entity.position
            if 0 <= x < self.world.height and 0 <= y < self.world.width:
                self.world.matrix[x][y] = entity
        
        self.current_tick = state['tick']
        # Установка времени суток
        time_cycle = ["morning", "day", "evening", "night"]
        if state['time'] in time_cycle:
            self.world.time.current_time = state['time']
            self.world.time.tick_counter = time_cycle.index(state['time'])

    def world_to_canvas_coords(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Преобразует координаты мира в координаты canvas"""
        canvas_x = world_y * self.cell_size + self.cell_size // 2
        canvas_y = self.canvas_size[1] - (world_x * self.cell_size + self.cell_size // 2)
        return canvas_x, canvas_y

    def canvas_to_world_coords(self, canvas_x: int, canvas_y: int) -> Tuple[int, int]:
        """Преобразует координаты canvas в координаты мира"""
        world_y = int(canvas_x // self.cell_size)
        world_x = int((self.canvas_size[1] - canvas_y) // self.cell_size)
        return world_x, world_y

    def draw_entity(self, entity):
        """Рисует сущность на карте"""
        x, y = self.world_to_canvas_coords(entity.position[0], entity.position[1])
        
        # Цвета и формы для разных типов
        if isinstance(entity, Lumiere):
            return self.graph.draw_rectangle((x-8, y-8), (x+8, y+8), 
                                           fill_color='#FFFF00', line_color='#CCCC00')
        elif isinstance(entity, Obscurite):
            return self.graph.draw_rectangle((x-8, y-8), (x+8, y+8), 
                                           fill_color='#0000FF', line_color='#0000CC')
        elif isinstance(entity, Demi):
            return self.graph.draw_rectangle((x-8, y-8), (x+8, y+8), 
                                           fill_color='#808080', line_color='#606060')
        elif isinstance(entity, Malheureux):
            # Размер пропорционален "масштабу" (количеству особей в группе)
            group_size = len(getattr(entity, 'group', [entity]))
            radius = max(6, min(15, 6 + group_size))
            return self.graph.draw_circle((x, y), radius, 
                                        fill_color='#800080', line_color='#600060')
        elif isinstance(entity, Pauvre):
            group_size = len(getattr(entity, 'group', [entity]))
            radius = max(6, min(15, 6 + group_size))
            return self.graph.draw_circle((x, y), radius, 
                                        fill_color='#FFFF00', line_color='#CCCC00')
        
        return None

    def draw_vision_radius(self, entity):
        """Рисует радиус обзора животного"""
        if not hasattr(entity, 'vision_radius'):
            # Добавляем vision_radius, если его нет
            entity.vision_radius = 3
            
        x, y = self.world_to_canvas_coords(entity.position[0], entity.position[1])
        vision_pixels = entity.vision_radius * self.cell_size
        
        return self.graph.draw_circle((x, y), vision_pixels, 
                                    line_color='white', line_width=2, fill_color='')

    def update_display(self):
        """Обновляет отображение карты и статистики"""
        self.graph.erase()
        
        # Рисуем сетку
        for i in range(0, self.canvas_size[0], self.cell_size):
            self.graph.draw_line((i, 0), (i, self.canvas_size[1]), color='#333333')
        for i in range(0, self.canvas_size[1], self.cell_size):
            self.graph.draw_line((0, i), (self.canvas_size[0], i), color='#333333')
        
        # Рисуем сущности
        entity_figures = {}
        for entity in self.world.entities:
            figure = self.draw_entity(entity)
            if figure:
                entity_figures[figure] = entity
        
        # Рисуем радиус обзора для выбранной сущности
        if self.selected_entity and self.selected_entity in self.world.entities:
            if hasattr(self.selected_entity, 'vision_radius'):
                self.draw_vision_radius(self.selected_entity)
        
        self.entity_figures = entity_figures
        self.update_statistics()

    def update_statistics(self):
        """Обновляет панель статистики"""
        stats = self.calculate_statistics()
        stats_text = f"=== Tick {self.current_tick} | Time: {self.world.time.current_time} ===\n"
        stats_text += f"Total Entities: {stats['total']}\n\n"
        
        stats_text += "PLANTS:\n"
        stats_text += f"  Lumiere (☀): {stats['Lumiere']}\n"
        stats_text += f"  Obscurite (🌙): {stats['Obscurite']}\n"
        stats_text += f"  Demi (🌓): {stats['Demi']}\n\n"
        
        stats_text += "ANIMALS:\n"
        stats_text += f"  Malheureux: {stats['Malheureux']} (avg vision: {stats.get('malheureux_avg_vision', 0):.1f})\n"
        stats_text += f"  Pauvre: {stats['Pauvre']} (avg vision: {stats.get('pauvre_avg_vision', 0):.1f})\n\n"
        
        stats_text += f"Groups: Malheureux({stats.get('malheureux_groups', 0)}), "
        stats_text += f"Pauvre({stats.get('pauvre_groups', 0)})\n"
        
        active_animals = sum(1 for e in self.world.entities 
                           if hasattr(e, 'is_active') and e.is_active)
        stats_text += f"Active Animals: {active_animals}"
        
        self.window['-STATS-'].update(stats_text)

    def calculate_statistics(self) -> Dict[str, Any]:
        """Вычисляет статистику мира"""
        stats = {
            'total': len(self.world.entities),
            'Lumiere': 0, 'Obscurite': 0, 'Demi': 0,
            'Malheureux': 0, 'Pauvre': 0
        }
        
        malheureux_visions = []
        pauvre_visions = []
        malheureux_groups_set = set()
        pauvre_groups_set = set()
        
        for entity in self.world.entities:
            entity_type = type(entity).__name__
            if entity_type in stats:
                stats[entity_type] += 1
            
            # Собираем данные о радиусе обзора
            if hasattr(entity, 'vision_radius'):
                if isinstance(entity, Malheureux):
                    malheureux_visions.append(entity.vision_radius)
                    if hasattr(entity, 'group'):
                        malheureux_groups_set.add(id(entity.group))
                elif isinstance(entity, Pauvre):
                    pauvre_visions.append(entity.vision_radius)
                    if hasattr(entity, 'group'):
                        pauvre_groups_set.add(id(entity.group))
            else:
                # Добавляем vision_radius, если его нет
                entity.vision_radius = 3
                if isinstance(entity, Malheureux):
                    malheureux_visions.append(3)
                elif isinstance(entity, Pauvre):
                    pauvre_visions.append(3)
        
        # Вычисляем средние значения
        if malheureux_visions:
            stats['malheureux_avg_vision'] = sum(malheureux_visions) / len(malheureux_visions)
        if pauvre_visions:
            stats['pauvre_avg_vision'] = sum(pauvre_visions) / len(pauvre_visions)
            
        stats['malheureux_groups'] = len(malheureux_groups_set)
        stats['pauvre_groups'] = len(pauvre_groups_set)
        
        return stats

    def update_entity_info(self, entity):
        """Обновляет информацию о выбранной сущности"""
        if not entity:
            self.window['-ENTITY_INFO-'].update("Click on an entity to see its info")
            return
        
        info = f"=== {type(entity).__name__} ===\n"
        info += f"Position: {entity.position}\n"
        
        if hasattr(entity, 'food'):
            info += f"Food: {entity.food}\n"
            info += f"Active: {entity.is_active}\n"
            info += f"Hungry: {entity.is_hungry}\n"
            info += f"Speed: {entity.speed}\n"
            info += f"Vision Radius: {getattr(entity, 'vision_radius', 3)}\n"
            
            if hasattr(entity, 'group'):
                info += f"Group Size: {len(entity.group)}\n"
            
            # Информация об окружении
            nearby = self.world.get_nearby_objects(entity.position, 
                                                 getattr(entity, 'vision_radius', 3))
            info += f"Nearby Entities: {len(nearby)}\n"
            
            if nearby:
                entity_counts = {}
                for nearby_entity in nearby:
                    entity_type = type(nearby_entity).__name__
                    entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
                
                for entity_type, count in entity_counts.items():
                    info += f"  {entity_type}: {count}\n"
        
        self.window['-ENTITY_INFO-'].update(info)

    def handle_mouse_click(self, mouse_pos):
        """Обрабатывает клик мыши по карте"""
        if not mouse_pos:
            return
            
        # Найдем сущность в точке клика
        clicked_entity = None
        min_distance = float('inf')
        
        for entity in self.world.entities:
            entity_x, entity_y = self.world_to_canvas_coords(entity.position[0], entity.position[1])
            distance = math.sqrt((mouse_pos[0] - entity_x)**2 + (mouse_pos[1] - entity_y)**2)
            
            if distance < 15 and distance < min_distance:  # 15 пикселей - радиус клика
                clicked_entity = entity
                min_distance = distance
        
        self.selected_entity = clicked_entity
        self.update_entity_info(clicked_entity)
        self.update_display()  # Перерисовываем для показа радиуса обзора

    def run_simulation_step(self):
        """Выполняет один шаг симуляции"""
        if self.current_tick >= self.max_ticks:
            return False
            
        self.world.process_tick()
        self.current_tick += 1
        self.save_state()
        return True

    def run(self):
        """Основной цикл приложения"""
        try:
            while True:
                timeout = 100 if self.simulation_running else None
                event, values = self.window.read(timeout=timeout)
                
                if event == sg.WIN_CLOSED:
                    break
                
                elif event == '-TIME-':
                    # Перемотка симуляции
                    target_tick = int(values['-TIME-'])
                    if target_tick < len(self.simulation_history):
                        self.restore_state(target_tick)
                        self.update_display()
                
                elif event == '-PLAY_PAUSE-':
                    self.simulation_running = not self.simulation_running
                
                elif event == '-STEP-':
                    if self.run_simulation_step():
                        self.window['-TIME-'].update(value=self.current_tick)
                        self.update_display()
                
                elif event == '-RESET-':
                    self.world = World(width=30, height=20, max_ticks=1000)
                    self.world.initialize_ecosystem()
                    self.current_tick = 0
                    self.simulation_running = False
                    self.selected_entity = None
                    self.save_initial_state()
                    self.save_state()
                    self.window['-TIME-'].update(value=0)
                    self.update_display()
                
                elif event == '-MAP-':
                    # Обработка клика по карте
                    mouse_pos = values['-MAP-']
                    if mouse_pos != (None, None):
                        self.handle_mouse_click(mouse_pos)
                
                # Автоматическое выполнение симуляции
                if self.simulation_running:
                    speed = int(values['-SPEED-'])
                    if self.current_tick % (11 - speed) == 0:  # Регулировка скорости
                        if self.run_simulation_step():
                            self.window['-TIME-'].update(value=self.current_tick)
                            self.update_display()
                        else:
                            self.simulation_running = False
        
        finally:
            self.window.close()


if __name__ == "__main__":
    app = EcosystemGUI()
    app.run()

