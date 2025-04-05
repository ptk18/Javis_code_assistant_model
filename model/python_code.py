class Animal:
    species_count = 0  
    def __init__(self, name, age):
        self.name = name
        self.age = age
        Animal.species_count += 1
    def speak(self):
        print("Some sound")

class Dog(Animal):
    def __init__(self, name, age, breed):
        super().__init__(name, age)
        self.breed = breed
    def speak(self):
        print("Woof!")

def calculate_animal_stats(animals):
    total_age = 0
    for animal in animals:
        total_age += animal.age
    return total_age / len(animals)