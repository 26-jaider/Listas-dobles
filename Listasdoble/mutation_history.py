class MutationHistory:
    def __init__(self):
        self.first = None
        self.last = None
        self.current = None

    def is_empty(self):
        return self.first is None

    def search(self, number):
        generation = self.first
        while generation is not None:
            if generation.number == number:
                return generation
            generation = generation.next
        return None

    def add(self, generation):
        if self.first is None:
            self.first = generation
            self.last = generation
        else:
            generation.previous = self.last
            self.last.next = generation
            self.last = generation
        self.current = generation

    def insert(self, generation):
        following = self.first
        while following is not None and following.number < generation.number:
            following = following.next

        if following is None:
            self.add(generation)
            return

        generation.next = following
        generation.previous = following.previous
        if following.previous is None:
            self.first = generation
        else:
            following.previous.next = generation
        following.previous = generation
        self.current = generation

    def delete(self, generation):
        if generation.previous is None:
            self.first = generation.next
        else:
            generation.previous.next = generation.next

        if generation.next is None:
            self.last = generation.previous
        else:
            generation.next.previous = generation.previous

        if self.current is generation:
            self.current = generation.next or generation.previous

        generation.previous = None
        generation.next = None

    def move_next(self):
        if self.current is None or self.current.next is None:
            return False
        self.current = self.current.next
        return True

    def move_previous(self):
        if self.current is None or self.current.previous is None:
            return False
        self.current = self.current.previous
        return True

    def forward_list(self):
        generations = []
        generation = self.first
        while generation is not None:
            generations.append(generation)
            generation = generation.next
        return generations

    def backward_list(self):
        generations = []
        generation = self.last
        while generation is not None:
            generations.append(generation)
            generation = generation.previous
        return generations