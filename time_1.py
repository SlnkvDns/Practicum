class Time:
    def __init__(self):
        self.cycle = ["morning", "day", "evening", "night"]
        self.current_time = self.cycle[0]
        self.tick_counter = 0

    def change_time(self):
        self.tick_counter += 1
        self.current_time = self.cycle[self.tick_counter % len(self.cycle)]

    def get_time(self):
        return self.current_time