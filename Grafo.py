class SocialNetwork:
    def __init__(self):
        self.users = {}  # Diccionario para almacenar usuarios y sus amistades (grafo)
    
    def add_user(self, username):
        """Agrega un nuevo usuario a la red social"""
        if username in self.users:
            print(f"El usuario '{username}' ya existe.")
            return False
        self.users[username] = set()
        print(f"Usuario '{username}' agregado exitosamente.")
        return True
    
    def remove_user(self, username):
        """Elimina un usuario y todas sus amistades"""
        if username not in self.users:
            print(f"El usuario '{username}' no existe.")
            return False
        # Eliminar al usuario de las listas de amigos de otros usuarios
        for friend in self.users[username]:
            self.users[friend].discard(username)
        del self.users[username]
        print(f"Usuario '{username}' eliminado exitosamente.")
        return True
    
    def add_friendship(self, user1, user2):
        """Agrega una amistad entre dos usuarios (arista bidireccional)"""
        if user1 not in self.users:
            print(f"El usuario '{user1}' no existe.")
            return False
        if user2 not in self.users:
            print(f"El usuario '{user2}' no existe.")
            return False
        if user1 == user2:
            print("Un usuario no puede ser amigo de sí mismo.")
            return False
        if user2 in self.users[user1]:
            print(f"'{user1}' y '{user2}' ya son amigos.")
            return False
        
        self.users[user1].add(user2)
        self.users[user2].add(user1)
        print(f"Amistad entre '{user1}' y '{user2}' agregada exitosamente.")
        return True
    
    def remove_friendship(self, user1, user2):
        """Elimina una amistad entre dos usuarios"""
        if user1 not in self.users or user2 not in self.users:
            print("Uno o ambos usuarios no existen.")
            return False
        if user2 not in self.users[user1]:
            print(f"'{user1}' y '{user2}' no son amigos.")
            return False
        
        self.users[user1].discard(user2)
        self.users[user2].discard(user1)
        print(f"Amistad entre '{user1}' y '{user2}' eliminada exitosamente.")
        return True
    
    def get_friends(self, username):
        """Obtiene la lista de amigos de un usuario"""
        if username not in self.users:
            print(f"El usuario '{username}' no existe.")
            return None
        return list(self.users[username])
    
    def are_friends(self, user1, user2):
        """Verifica si dos usuarios son amigos"""
        if user1 not in self.users or user2 not in self.users:
            return False
        return user2 in self.users[user1]
    
    def get_mutual_friends(self, user1, user2):
        """Obtiene los amigos en común entre dos usuarios"""
        if user1 not in self.users or user2 not in self.users:
            print("Uno o ambos usuarios no existen.")
            return None
        return list(self.users[user1].intersection(self.users[user2]))
    
    def display_network(self):
        """Muestra toda la red social"""
        print("\n=== Red Social ===")
        if not self.users:
            print("La red está vacía.")
            return
        for user, friends in self.users.items():
            friends_list = ", ".join(friends) if friends else "Sin amigos"
            print(f"{user}: {friends_list}")
        print("==================\n")


