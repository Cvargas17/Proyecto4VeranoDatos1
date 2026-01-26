import socket
import threading
import json
import os
import ssl
from passlib.hash import pbkdf2_sha256

# Ruta para guardar los datos de usuarios
DATA_FILE = "users_data.json"

# Rutas de certificados SSL
CERT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.crt")
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.key")


def merge_sort(arr):
    """Implementación del algoritmo Merge Sort para ordenar listas"""
    if len(arr) <= 1:
        return arr
    
    # Dividir el array en dos mitades
    mid = len(arr) // 2
    left_half = arr[:mid]
    right_half = arr[mid:]
    
    # Recursivamente ordenar ambas mitades
    left_sorted = merge_sort(left_half)
    right_sorted = merge_sort(right_half)
    
    # Combinar las mitades ordenadas
    return merge(left_sorted, right_sorted)


def merge(left, right):
    """Combina dos listas ordenadas en una sola lista ordenada"""
    result = []
    i = j = 0
    
    # Comparar elementos y agregar el menor
    while i < len(left) and j < len(right):
        if left[i].lower() <= right[j].lower():  # Comparación case-insensitive
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    # Agregar elementos restantes
    result.extend(left[i:])
    result.extend(right[j:])
    
    return result


class SocialNetworkServer:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.server_socket = None
        self.users = {}  # {username: {"password_hash": hash, "friends": set(), "pending_requests": set(), "sent_requests": set()}}
        self.logged_in_users = {}  # {client_address: username}
        self.lock = threading.Lock()
        self.running = False
        
        # Cargar datos existentes
        self.load_data()
    
    def load_data(self):
        """Carga los datos de usuarios desde archivo"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for username, user_data in data.items():
                        self.users[username] = {
                            "password_hash": user_data["password_hash"],
                            "friends": set(user_data.get("friends", [])),
                            "pending_requests": set(user_data.get("pending_requests", [])),
                            "sent_requests": set(user_data.get("sent_requests", [])),
                            "description": user_data.get("description", ""),
                            "photo_url": user_data.get("photo_url", "")
                        }
                print(f"[SERVER] Datos cargados: {len(self.users)} usuarios")
            except Exception as e:
                print(f"[SERVER] Error cargando datos: {e}")
    
    def save_data(self):
        """Guarda los datos de usuarios en archivo"""
        try:
            data = {}
            for username, user_data in self.users.items():
                data[username] = {
                    "password_hash": user_data["password_hash"],
                    "friends": list(user_data["friends"]),
                    "pending_requests": list(user_data.get("pending_requests", [])),
                    "sent_requests": list(user_data.get("sent_requests", [])),
                    "description": user_data.get("description", ""),
                    "photo_url": user_data.get("photo_url", "")
                }
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("[SERVER] Datos guardados")
        except Exception as e:
            print(f"[SERVER] Error guardando datos: {e}")
    
    def start(self):
        """Inicia el servidor con SSL/TLS"""
        # Verificar que existan los certificados
        if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
            print("[SERVER] ❌ ERROR: Certificados SSL no encontrados.")
            print("[SERVER] Ejecute 'python generate_certs.py' primero.")
            return
        
        # Crear contexto SSL
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ssl_context.load_cert_chain(CERT_FILE, KEY_FILE)
        
        # Crear socket TCP
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f"[SERVER] 🔐 Servidor SSL iniciado en {self.host}:{self.port}")
        print("[SERVER] ✅ Comunicación encriptada con TLS")
        print("[SERVER] Esperando conexiones seguras...")
        
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                # Envolver socket con SSL
                try:
                    ssl_socket = self.ssl_context.wrap_socket(client_socket, server_side=True)
                    print(f"[SERVER] 🔒 Conexión segura desde {client_address}")
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(ssl_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except ssl.SSLError as ssl_err:
                    print(f"[SERVER] ⚠️ Error SSL con {client_address}: {ssl_err}")
                    client_socket.close()
            except Exception as e:
                if self.running:
                    print(f"[SERVER] Error: {e}")
    
    def handle_client(self, client_socket, client_address):
        """Maneja las solicitudes de un cliente"""
        try:
            while self.running:
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                try:
                    request = json.loads(data)
                    response = self.process_request(request, client_address)
                    client_socket.send(json.dumps(response).encode('utf-8'))
                except json.JSONDecodeError:
                    error_response = {"status": "error", "message": "Formato de mensaje inválido"}
                    client_socket.send(json.dumps(error_response).encode('utf-8'))
        except Exception as e:
            print(f"[SERVER] Error con cliente {client_address}: {e}")
        finally:
            # Desloguear al usuario si estaba conectado
            with self.lock:
                if client_address in self.logged_in_users:
                    username = self.logged_in_users.pop(client_address)
                    print(f"[SERVER] Usuario '{username}' desconectado")
            client_socket.close()
            print(f"[SERVER] Conexión cerrada: {client_address}")
    
    def process_request(self, request, client_address):
        """Procesa una solicitud del cliente"""
        action = request.get("action")
        
        # Acciones que no requieren autenticación
        if action == "register":
            return self.register_user(request)
        elif action == "login":
            return self.login_user(request, client_address)
        
        # Verificar si el usuario está autenticado para otras acciones
        with self.lock:
            if client_address not in self.logged_in_users:
                return {"status": "error", "message": "Debe iniciar sesión primero"}
            current_user = self.logged_in_users[client_address]
        
        # Acciones que requieren autenticación
        if action == "logout":
            return self.logout_user(client_address)
        # Solicitudes de amistad
        elif action == "send_friend_request":
            return self.send_friend_request(current_user, request.get("to_user"))
        elif action == "get_pending_requests":
            return self.get_pending_requests(current_user)
        elif action == "get_sent_requests":
            return self.get_sent_requests(current_user)
        elif action == "accept_friend_request":
            return self.accept_friend_request(current_user, request.get("from_user"))
        elif action == "reject_friend_request":
            return self.reject_friend_request(current_user, request.get("from_user"))
        elif action == "cancel_friend_request":
            return self.cancel_friend_request(current_user, request.get("to_user"))
        # Gestión de amigos existentes
        elif action == "remove_friend":
            return self.remove_friend(current_user, request.get("friend"))
        elif action == "get_friends":
            return self.get_friends(current_user)
        elif action == "get_all_users":
            return self.get_all_users()
        elif action == "get_mutual_friends":
            return self.get_mutual_friends(current_user, request.get("other_user"))
        elif action == "are_friends":
            return self.are_friends(current_user, request.get("other_user"))
        elif action == "get_network":
            return self.get_network()
        elif action == "delete_account":
            return self.delete_account(current_user, client_address)
        elif action == "search_users":
            return self.search_users(request.get("query", ""))
        elif action == "get_user_profile":
            return self.get_user_profile(request.get("username"))
        elif action == "update_profile":
            return self.update_profile(current_user, request.get("description"), request.get("photo_url"))
        elif action == "find_path":
            return self.find_path(request.get("from_user"), request.get("to_user"))
        elif action == "get_statistics":
            return self.get_statistics()
        else:
            return {"status": "error", "message": f"Acción desconocida: {action}"}
    
    
    def register_user(self, request):
        """Registra un nuevo usuario"""
        username = request.get("username", "").strip()
        password = request.get("password", "")
        
        if not username or not password:
            return {"status": "error", "message": "Usuario y contraseña son requeridos"}
        
        if len(username) < 3:
            return {"status": "error", "message": "El nombre de usuario debe tener al menos 3 caracteres"}
        
        if len(password) < 4:
            return {"status": "error", "message": "La contraseña debe tener al menos 4 caracteres"}
        
        with self.lock:
            if username in self.users:
                return {"status": "error", "message": f"El usuario '{username}' ya existe"}
            
            # Hashear la contraseña con Passlib
            password_hash = pbkdf2_sha256.hash(password)
            
            self.users[username] = {
                "password_hash": password_hash,
                "friends": set(),
                "pending_requests": set(),
                "sent_requests": set(),
                "description": "",
                "photo_url": ""
            }
            self.save_data()
        
        print(f"[SERVER] Usuario registrado: {username}")
        return {"status": "success", "message": f"Usuario '{username}' registrado exitosamente"}
    
    def login_user(self, request, client_address):
        """Inicia sesión de un usuario"""
        username = request.get("username", "").strip()
        password = request.get("password", "")
        
        if not username or not password:
            return {"status": "error", "message": "Usuario y contraseña son requeridos"}
        
        with self.lock:
            if username not in self.users:
                return {"status": "error", "message": "Usuario o contraseña incorrectos"}
            
            # Verificar contraseña con Passlib
            if not pbkdf2_sha256.verify(password, self.users[username]["password_hash"]):
                return {"status": "error", "message": "Usuario o contraseña incorrectos"}
            
            # Verificar si ya está logueado desde otra conexión
            for addr, user in self.logged_in_users.items():
                if user == username:
                    return {"status": "error", "message": "Este usuario ya tiene una sesión activa"}
            
            self.logged_in_users[client_address] = username
            
            # Contar solicitudes pendientes
            pending_count = len(self.users[username].get("pending_requests", set()))
        
        print(f"[SERVER] Usuario conectado: {username}")
        return {
            "status": "success", 
            "message": f"Bienvenido, {username}!", 
            "username": username,
            "pending_requests": pending_count
        }
    
    def logout_user(self, client_address):
        """Cierra sesión del usuario"""
        with self.lock:
            if client_address in self.logged_in_users:
                username = self.logged_in_users.pop(client_address)
                print(f"[SERVER] Usuario desconectado: {username}")
                return {"status": "success", "message": "Sesión cerrada"}
        return {"status": "error", "message": "No hay sesión activa"}
    
    
    def send_friend_request(self, from_user, to_user):
        """Envía una solicitud de amistad"""
        if not to_user:
            return {"status": "error", "message": "Debe especificar un usuario"}
        
        with self.lock:
            if to_user not in self.users:
                return {"status": "error", "message": f"El usuario '{to_user}' no existe"}
            
            if to_user == from_user:
                return {"status": "error", "message": "No puedes enviarte una solicitud a ti mismo"}
            
            if to_user in self.users[from_user]["friends"]:
                return {"status": "error", "message": f"Ya eres amigo de '{to_user}'"}
            
            if to_user in self.users[from_user].get("sent_requests", set()):
                return {"status": "error", "message": f"Ya enviaste una solicitud a '{to_user}'"}
            
            # Verificar si el otro usuario ya te envió una solicitud
            if from_user in self.users[to_user].get("sent_requests", set()):
                return {"status": "error", "message": f"'{to_user}' ya te envió una solicitud. Revisa tus solicitudes pendientes."}
            
            # Agregar solicitud
            if "sent_requests" not in self.users[from_user]:
                self.users[from_user]["sent_requests"] = set()
            if "pending_requests" not in self.users[to_user]:
                self.users[to_user]["pending_requests"] = set()
            
            self.users[from_user]["sent_requests"].add(to_user)
            self.users[to_user]["pending_requests"].add(from_user)
            self.save_data()
        
        print(f"[SERVER] Solicitud de amistad: {from_user} -> {to_user}")
        return {"status": "success", "message": f"Solicitud enviada a '{to_user}'"}
    
    def get_pending_requests(self, username):
        """Obtiene las solicitudes de amistad pendientes (recibidas)"""
        with self.lock:
            pending = list(self.users[username].get("pending_requests", set()))
        return {"status": "success", "pending_requests": sorted(pending)}
    
    def get_sent_requests(self, username):
        """Obtiene las solicitudes de amistad enviadas"""
        with self.lock:
            sent = list(self.users[username].get("sent_requests", set()))
        return {"status": "success", "sent_requests": sorted(sent)}
    
    def accept_friend_request(self, current_user, from_user):
        """Acepta una solicitud de amistad"""
        if not from_user:
            return {"status": "error", "message": "Debe especificar un usuario"}
        
        with self.lock:
            if from_user not in self.users[current_user].get("pending_requests", set()):
                return {"status": "error", "message": f"No hay solicitud pendiente de '{from_user}'"}
            
            # Crear la amistad bidireccional
            self.users[current_user]["friends"].add(from_user)
            self.users[from_user]["friends"].add(current_user)
            
            # Eliminar la solicitud
            self.users[current_user]["pending_requests"].discard(from_user)
            self.users[from_user]["sent_requests"].discard(current_user)
            
            self.save_data()
        
        print(f"[SERVER] Amistad creada: {current_user} <-> {from_user}")
        return {"status": "success", "message": f"¡Ahora eres amigo de '{from_user}'!"}
    
    def reject_friend_request(self, current_user, from_user):
        """Rechaza una solicitud de amistad"""
        if not from_user:
            return {"status": "error", "message": "Debe especificar un usuario"}
        
        with self.lock:
            if from_user not in self.users[current_user].get("pending_requests", set()):
                return {"status": "error", "message": f"No hay solicitud pendiente de '{from_user}'"}
            
            # Eliminar la solicitud
            self.users[current_user]["pending_requests"].discard(from_user)
            self.users[from_user]["sent_requests"].discard(current_user)
            
            self.save_data()
        
        print(f"[SERVER] Solicitud rechazada: {from_user} -> {current_user}")
        return {"status": "success", "message": f"Solicitud de '{from_user}' rechazada"}
    
    def cancel_friend_request(self, current_user, to_user):
        """Cancela una solicitud de amistad enviada"""
        if not to_user:
            return {"status": "error", "message": "Debe especificar un usuario"}
        
        with self.lock:
            if to_user not in self.users[current_user].get("sent_requests", set()):
                return {"status": "error", "message": f"No hay solicitud enviada a '{to_user}'"}
            
            # Eliminar la solicitud
            self.users[current_user]["sent_requests"].discard(to_user)
            self.users[to_user]["pending_requests"].discard(current_user)
            
            self.save_data()
        
        print(f"[SERVER] Solicitud cancelada: {current_user} -> {to_user}")
        return {"status": "success", "message": f"Solicitud a '{to_user}' cancelada"}
    
    
    def remove_friend(self, current_user, friend_username):
        """Elimina un amigo"""
        if not friend_username:
            return {"status": "error", "message": "Debe especificar un usuario"}
        
        with self.lock:
            if friend_username not in self.users[current_user]["friends"]:
                return {"status": "error", "message": f"No eres amigo de '{friend_username}'"}
            
            # Eliminar amistad bidireccional
            self.users[current_user]["friends"].discard(friend_username)
            if friend_username in self.users:
                self.users[friend_username]["friends"].discard(current_user)
            self.save_data()
        
        return {"status": "success", "message": f"Ya no eres amigo de '{friend_username}'"}
    
    def get_friends(self, current_user):
        """Obtiene la lista de amigos del usuario actual, ordenada con Merge Sort"""
        with self.lock:
            friends = list(self.users[current_user]["friends"])
        # Ordenar usando Merge Sort
        friends_sorted = merge_sort(friends)
        return {"status": "success", "friends": friends_sorted}
    
    def get_all_users(self):
        """Obtiene todos los usuarios registrados"""
        with self.lock:
            users = list(self.users.keys())
        return {"status": "success", "users": sorted(users)}
    
    def get_mutual_friends(self, current_user, other_user):
        """Obtiene amigos en común"""
        if not other_user:
            return {"status": "error", "message": "Debe especificar un usuario"}
        
        with self.lock:
            if other_user not in self.users:
                return {"status": "error", "message": f"El usuario '{other_user}' no existe"}
            
            mutual = self.users[current_user]["friends"].intersection(
                self.users[other_user]["friends"]
            )
        
        return {"status": "success", "mutual_friends": sorted(list(mutual))}
    
    def are_friends(self, current_user, other_user):
        """Verifica si son amigos"""
        if not other_user:
            return {"status": "error", "message": "Debe especificar un usuario"}
        
        with self.lock:
            if other_user not in self.users:
                return {"status": "error", "message": f"El usuario '{other_user}' no existe"}
            
            are_friends = other_user in self.users[current_user]["friends"]
        
        return {"status": "success", "are_friends": are_friends}
    
    def get_network(self):
        """Obtiene toda la red social para visualización"""
        with self.lock:
            network = {}
            for username, data in self.users.items():
                network[username] = sorted(list(data["friends"]))
        return {"status": "success", "network": network}
    
    def delete_account(self, current_user, client_address):
        """Elimina la cuenta del usuario"""
        with self.lock:
            # Eliminar de las listas de amigos de otros usuarios
            for username, data in self.users.items():
                data["friends"].discard(current_user)
                data.get("pending_requests", set()).discard(current_user)
                data.get("sent_requests", set()).discard(current_user)
            
            # Eliminar el usuario
            del self.users[current_user]
            
            # Cerrar sesión
            if client_address in self.logged_in_users:
                del self.logged_in_users[client_address]
            
            self.save_data()
        
        print(f"[SERVER] Cuenta eliminada: {current_user}")
        return {"status": "success", "message": "Cuenta eliminada exitosamente", "logout": True}
    
    
    def search_users(self, query):
        """Busca usuarios por nombre (nombre y apellido)"""
        if not query or not query.strip():
            return {"status": "error", "message": "Ingrese un término de búsqueda"}
        
        query = query.strip().lower()
        with self.lock:
            results = []
            for username in self.users.keys():
                if query in username.lower():
                    results.append(username)
        
        return {"status": "success", "results": sorted(results)}
    
    def get_user_profile(self, username):
        """Obtiene el perfil de un usuario"""
        if not username:
            return {"status": "error", "message": "Debe especificar un usuario"}
        
        with self.lock:
            if username not in self.users:
                return {"status": "error", "message": f"El usuario '{username}' no existe"}
            
            user_data = self.users[username]
            profile = {
                "username": username,
                "friends_count": len(user_data["friends"]),
                "friends": sorted(list(user_data["friends"])),
                "description": user_data.get("description", ""),
                "photo_url": user_data.get("photo_url", "")
            }
        
        return {"status": "success", "profile": profile}
    
    def update_profile(self, current_user, description, photo_url):
        """Actualiza el perfil del usuario actual"""
        with self.lock:
            if description is not None:
                self.users[current_user]["description"] = description
            if photo_url is not None:
                self.users[current_user]["photo_url"] = photo_url
            self.save_data()
        
        print(f"[SERVER] Perfil actualizado: {current_user}")
        return {"status": "success", "message": "Perfil actualizado exitosamente"}
    
    def find_path(self, from_user, to_user):
        """Busca un camino de amigos entre dos usuarios usando BFS"""
        if not from_user or not to_user:
            return {"status": "error", "message": "Debe especificar ambos usuarios"}
        
        with self.lock:
            if from_user not in self.users:
                return {"status": "error", "message": f"El usuario '{from_user}' no existe"}
            if to_user not in self.users:
                return {"status": "error", "message": f"El usuario '{to_user}' no existe"}
            
            # BFS para encontrar el camino más corto
            if from_user == to_user:
                return {"status": "success", "path": [from_user]}
            
            visited = set()
            queue = [(from_user, [from_user])]  # (usuario_actual, camino_hasta_aquí)
            
            while queue:
                current, path = queue.pop(0)
                
                if current in visited:
                    continue
                
                visited.add(current)
                
                # Obtener amigos del usuario actual
                friends = self.users[current]["friends"]
                
                for friend in friends:
                    if friend == to_user:
                        # ¡Encontramos el destino!
                        return {"status": "success", "path": path + [friend]}
                    
                    if friend not in visited:
                        queue.append((friend, path + [friend]))
            
            # No se encontró camino
            return {"status": "success", "path": []}
    
    def get_statistics(self):
        """Obtiene estadísticas de la red social"""
        with self.lock:
            if not self.users:
                return {"status": "error", "message": "No hay usuarios en la red"}
            
            # Calcular cantidad de amigos por usuario
            user_friends_count = {}
            for username, user_data in self.users.items():
                user_friends_count[username] = len(user_data["friends"])
            
            # Usuario con más amigos
            max_friends_user = max(user_friends_count, key=user_friends_count.get)
            max_friends_count = user_friends_count[max_friends_user]
            
            # Usuario con menos amigos
            min_friends_user = min(user_friends_count, key=user_friends_count.get)
            min_friends_count = user_friends_count[min_friends_user]
            
            # Promedio de amigos
            total_friends = sum(user_friends_count.values())
            total_users = len(self.users)
            average_friends = total_friends / total_users if total_users > 0 else 0
            
            # Usuarios con más amigos (en caso de empate)
            users_with_max = [u for u, c in user_friends_count.items() if c == max_friends_count]
            users_with_min = [u for u, c in user_friends_count.items() if c == min_friends_count]
        
        return {
            "status": "success",
            "statistics": {
                "max_friends_users": users_with_max,
                "max_friends_count": max_friends_count,
                "min_friends_users": users_with_min,
                "min_friends_count": min_friends_count,
                "average_friends": round(average_friends, 2),
                "total_users": total_users,
                "total_friendships": total_friends // 2  # Dividir entre 2 porque son bidireccionales
            }
        }
    
    def stop(self):
        """Detiene el servidor"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("[SERVER] Servidor detenido")


def main():
    print("=" * 50)
    print("   SERVIDOR DE RED SOCIAL (SSL/TLS)")
    print("=" * 50)
    print("🔐 Comunicación encriptada habilitada")
    print()
    
    server = SocialNetworkServer(host='localhost', port=5000)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[SERVER] Cerrando servidor...")
        server.stop()


if __name__ == "__main__":
    main()
