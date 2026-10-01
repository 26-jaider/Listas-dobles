class BacterialGeneration:
    def __init__(self, number, mutation, mutation_type, observation, date):
        self.number = number
        self.mutation = mutation
        self.mutation_type = mutation_type
        self.observation = observation
        self.date = date
        self.previous = None
        self.next = None