import socket
import json
import ssl
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import subprocess
import os
import tempfile
import urllib.request
import io
import base64

# Intentar importar PIL para manejo de imágenes
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Advertencia: PIL/Pillow no está instalado. Las fotos de perfil se mostrarán como texto.")

# Ruta de Graphviz
GRAPHVIZ_PATH = r"C:\Program Files\Graphviz\bin"

# Ruta del certificado SSL del servidor
CERT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.crt")


class SocialNetworkClient:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.logged_in = False
        self.username = None
    
    def connect(self):
        """Conecta al servidor usando SSL/TLS"""
        try:
            # Crear contexto SSL
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            
            # Cargar certificado del servidor para verificación
            if os.path.exists(CERT_FILE):
                ssl_context.load_verify_locations(CERT_FILE)
                ssl_context.check_hostname = False  # Para certificados autofirmados
                ssl_context.verify_mode = ssl.CERT_REQUIRED
            else:
                # Si no hay certificado, aceptar cualquiera (solo desarrollo)
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                print("⚠️ Advertencia: Conectando sin verificar certificado del servidor")
            
            # Crear socket TCP y envolverlo con SSL
            raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket = ssl_context.wrap_socket(raw_socket, server_hostname=self.host)
            self.socket.connect((self.host, self.port))
            self.connected = True
            return True, "🔒 Conectado al servidor (conexión encriptada)"
        except ssl.SSLError as ssl_err:
            return False, f"Error SSL: {str(ssl_err)}"
        except ConnectionRefusedError:
            return False, "No se pudo conectar al servidor. ¿Está el servidor ejecutándose?"
        except Exception as e:
            return False, f"Error de conexión: {str(e)}"
    
    def disconnect(self):
        """Desconecta del servidor"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        self.logged_in = False
        self.username = None
    
    def send_request(self, request):
        """Envía una solicitud al servidor y recibe la respuesta"""
        if not self.connected:
            return {"status": "error", "message": "No conectado al servidor"}
        
        try:
            self.socket.send(json.dumps(request).encode('utf-8'))
            response = self.socket.recv(4096).decode('utf-8')
            return json.loads(response)
        except Exception as e:
            self.connected = False
            return {"status": "error", "message": f"Error de comunicación: {str(e)}"}
    
    def register(self, username, password):
        """Registra un nuevo usuario"""
        return self.send_request({
            "action": "register",
            "username": username,
            "password": password
        })
    
    def login(self, username, password):
        """Inicia sesión"""
        response = self.send_request({
            "action": "login",
            "username": username,
            "password": password
        })
        
        if response.get("status") == "success":
            self.logged_in = True
            self.username = username
        
        return response
    
    def logout(self):
        """Cierra sesión"""
        response = self.send_request({"action": "logout"})
        if response.get("status") == "success":
            self.logged_in = False
            self.username = None
        return response
    
    # ==================== SOLICITUDES DE AMISTAD ====================
    
    def send_friend_request(self, to_user):
        """Envía una solicitud de amistad"""
        return self.send_request({"action": "send_friend_request", "to_user": to_user})
    
    def get_pending_requests(self):
        """Obtiene solicitudes recibidas pendientes"""
        return self.send_request({"action": "get_pending_requests"})
    
    def get_sent_requests(self):
        """Obtiene solicitudes enviadas"""
        return self.send_request({"action": "get_sent_requests"})
    
    def accept_friend_request(self, from_user):
        """Acepta una solicitud de amistad"""
        return self.send_request({"action": "accept_friend_request", "from_user": from_user})
    
    def reject_friend_request(self, from_user):
        """Rechaza una solicitud de amistad"""
        return self.send_request({"action": "reject_friend_request", "from_user": from_user})
    
    def cancel_friend_request(self, to_user):
        """Cancela una solicitud enviada"""
        return self.send_request({"action": "cancel_friend_request", "to_user": to_user})
    
    # ==================== GESTIÓN DE AMIGOS ====================
    
    def remove_friend(self, friend):
        """Elimina un amigo"""
        return self.send_request({"action": "remove_friend", "friend": friend})
    
    def get_friends(self):
        """Obtiene la lista de amigos"""
        return self.send_request({"action": "get_friends"})
    
    def get_all_users(self):
        """Obtiene todos los usuarios"""
        return self.send_request({"action": "get_all_users"})
    
    def get_mutual_friends(self, other_user):
        """Obtiene amigos en común"""
        return self.send_request({"action": "get_mutual_friends", "other_user": other_user})
    
    def are_friends(self, other_user):
        """Verifica si son amigos"""
        return self.send_request({"action": "are_friends", "other_user": other_user})
    
    def get_network(self):
        """Obtiene toda la red"""
        return self.send_request({"action": "get_network"})
    
    def delete_account(self):
        """Elimina la cuenta"""
        response = self.send_request({"action": "delete_account"})
        if response.get("logout"):
            self.logged_in = False
            self.username = None
        return response
    
    # ==================== BÚSQUEDA Y PERFIL ====================
    
    def search_users(self, query):
        """Busca usuarios por nombre"""
        return self.send_request({"action": "search_users", "query": query})
    
    def get_user_profile(self, username):
        """Obtiene el perfil de un usuario"""
        return self.send_request({"action": "get_user_profile", "username": username})
    
    def update_profile(self, description=None, photo_url=None):
        """Actualiza el perfil del usuario actual"""
        return self.send_request({
            "action": "update_profile",
            "description": description,
            "photo_url": photo_url
        })
    
    def find_path(self, from_user, to_user):
        """Busca un camino de amigos entre dos usuarios"""
        return self.send_request({
            "action": "find_path",
            "from_user": from_user,
            "to_user": to_user
        })
    
    def get_statistics(self):
        """Obtiene estadísticas de la red social"""
        return self.send_request({"action": "get_statistics"})


class LoginWindow:
    def __init__(self, root, client, on_login_success):
        self.root = root
        self.client = client
        self.on_login_success = on_login_success
        
        self.root.title("SocialTEC - Iniciar Sesión")
        self.root.geometry("450x450")
        self.root.resizable(False, False)
        
        self.create_widgets()
    
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="🌐 SocialTEC", font=('Arial', 20, 'bold'))
        title_label.pack(pady=10)
        
        subtitle = ttk.Label(main_frame, text="Red Social Segura con Conexión Encriptada", font=('Arial', 10))
        subtitle.pack()
        
        # Notebook para Login/Registro
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True, pady=20)
        
        # Tab de Login
        login_frame = ttk.Frame(notebook, padding=20)
        notebook.add(login_frame, text="Iniciar Sesión")
        
        ttk.Label(login_frame, text="Usuario:", font=('Arial', 11)).pack(anchor='w', pady=(10,0))
        self.login_user_entry = ttk.Entry(login_frame, width=35, font=('Arial', 11))
        self.login_user_entry.pack(pady=5, ipady=5)
        
        ttk.Label(login_frame, text="Contraseña:", font=('Arial', 11)).pack(anchor='w', pady=(10,0))
        self.login_pass_entry = ttk.Entry(login_frame, width=35, show="*", font=('Arial', 11))
        self.login_pass_entry.pack(pady=5, ipady=5)
        
        # Botón de Login
        login_btn = tk.Button(login_frame, text="✅ Iniciar Sesión", command=self.do_login,
                              font=('Arial', 12, 'bold'), bg='#4CAF50', fg='white',
                              padx=20, pady=10, cursor='hand2')
        login_btn.pack(pady=25)
        
        # Tab de Registro
        register_frame = ttk.Frame(notebook, padding=20)
        notebook.add(register_frame, text="Registrarse")
        
        ttk.Label(register_frame, text="Usuario:", font=('Arial', 11)).pack(anchor='w', pady=(10,0))
        self.reg_user_entry = ttk.Entry(register_frame, width=35, font=('Arial', 11))
        self.reg_user_entry.pack(pady=5, ipady=5)
        
        ttk.Label(register_frame, text="Contraseña:", font=('Arial', 11)).pack(anchor='w', pady=(10,0))
        self.reg_pass_entry = ttk.Entry(register_frame, width=35, show="*", font=('Arial', 11))
        self.reg_pass_entry.pack(pady=5, ipady=5)
        
        # Botón de Registro
        register_btn = tk.Button(register_frame, text="📝 Crear Cuenta", command=self.do_register,
                                 font=('Arial', 12, 'bold'), bg='#2196F3', fg='white',
                                 padx=20, pady=10, cursor='hand2')
        register_btn.pack(pady=25)
        
        # Estado de conexión
        self.status_label = ttk.Label(main_frame, text="", foreground="gray")
        self.status_label.pack()
        
        # Conectar al servidor
        self.connect_to_server()
    
    def connect_to_server(self):
        success, message = self.client.connect()
        if success:
            self.status_label.config(text="✅ Conectado al servidor", foreground="green")
        else:
            self.status_label.config(text=f"❌ {message}", foreground="red")
            messagebox.showerror("Error de Conexión", message)
    
    def do_login(self):
        if not self.client.connected:
            messagebox.showerror("Error", "No hay conexión con el servidor")
            return
        
        username = self.login_user_entry.get().strip()
        password = self.login_pass_entry.get()
        
        if not username or not password:
            messagebox.showwarning("Advertencia", "Complete todos los campos")
            return
        
        response = self.client.login(username, password)
        
        if response.get("status") == "success":
            pending = response.get("pending_requests", 0)
            msg = response.get("message")
            if pending > 0:
                msg += f"\n\n📬 Tienes {pending} solicitud(es) de amistad pendiente(s)!"
            messagebox.showinfo("Bienvenido", msg)
            self.on_login_success(username)
        else:
            messagebox.showerror("Error", response.get("message"))
    
    def do_register(self):
        if not self.client.connected:
            messagebox.showerror("Error", "No hay conexión con el servidor")
            return
        
        username = self.reg_user_entry.get().strip()
        password = self.reg_pass_entry.get()
        
        if not username or not password:
            messagebox.showwarning("Advertencia", "Complete todos los campos")
            return
        
        response = self.client.register(username, password)
        
        if response.get("status") == "success":
            messagebox.showinfo("Éxito", response.get("message") + "\nAhora puede iniciar sesión.")
            self.reg_user_entry.delete(0, tk.END)
            self.reg_pass_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", response.get("message"))


class MainWindow:
    def __init__(self, root, client, username, on_logout):
        self.root = root
        self.client = client
        self.username = username
        self.on_logout = on_logout
        
        self.root.title(f"SocialTEC - {username}")
        self.root.geometry("950x700")
        self.root.resizable(True, True)
        
        # Variables para almacenar datos localmente
        self.all_users_cache = []
        self.friends_cache = []
        self.sent_cache = []
        self.pending_cache = []
        
        self.create_widgets()
        self.refresh_data()
    
    def create_widgets(self):
        # Header con información del usuario
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(header_frame, text=f"👤 Sesión: {self.username}", font=('Arial', 12, 'bold')).pack(side='left')
        ttk.Button(header_frame, text="🚪 Cerrar Sesión", command=self.do_logout).pack(side='right')
        ttk.Button(header_frame, text="🗑️ Eliminar Cuenta", command=self.do_delete_account).pack(side='right', padx=5)
        
        # Notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Crear pestañas
        self.create_requests_tab()  # Nueva pestaña de solicitudes
        self.create_friends_tab()
        self.create_users_tab()
        self.create_profile_tab()   # Nueva pestaña de perfil
        self.create_queries_tab()
        self.create_visualization_tab()
        self.create_network_tab()
    
    # ==================== PESTAÑA DE SOLICITUDES ====================
    def create_requests_tab(self):
        requests_frame = ttk.Frame(self.notebook)
        self.notebook.add(requests_frame, text="📬 Solicitudes")
        
        # Frame superior - Enviar solicitud
        send_frame = ttk.LabelFrame(requests_frame, text="Enviar Solicitud de Amistad", padding=10)
        send_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(send_frame, text="Enviar solicitud a:").grid(row=0, column=0, padx=5)
        self.send_request_combo = ttk.Combobox(send_frame, width=25, state="readonly")
        self.send_request_combo.grid(row=0, column=1, padx=5)
        
        send_btn = tk.Button(send_frame, text="📤 Enviar Solicitud", command=self.send_friend_request,
                             bg='#2196F3', fg='white', font=('Arial', 10, 'bold'))
        send_btn.grid(row=0, column=2, padx=10)
        
        # Frame izquierdo - Solicitudes recibidas
        left_frame = ttk.Frame(requests_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        pending_frame = ttk.LabelFrame(left_frame, text="📥 Solicitudes Recibidas", padding=10)
        pending_frame.pack(fill='both', expand=True)
        
        self.pending_listbox = tk.Listbox(pending_frame, font=('Consolas', 11), height=10)
        self.pending_listbox.pack(fill='both', expand=True, side='left')
        scrollbar1 = ttk.Scrollbar(pending_frame, orient='vertical', command=self.pending_listbox.yview)
        scrollbar1.pack(side='right', fill='y')
        self.pending_listbox.config(yscrollcommand=scrollbar1.set)
        
        pending_buttons = ttk.Frame(left_frame)
        pending_buttons.pack(fill='x', pady=5)
        
        accept_btn = tk.Button(pending_buttons, text="✅ Aceptar", command=self.accept_request,
                               bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'))
        accept_btn.pack(side='left', padx=5)
        
        reject_btn = tk.Button(pending_buttons, text="❌ Rechazar", command=self.reject_request,
                               bg='#f44336', fg='white', font=('Arial', 10, 'bold'))
        reject_btn.pack(side='left', padx=5)
        
        # Frame derecho - Solicitudes enviadas
        right_frame = ttk.Frame(requests_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        sent_frame = ttk.LabelFrame(right_frame, text="📤 Solicitudes Enviadas", padding=10)
        sent_frame.pack(fill='both', expand=True)
        
        self.sent_listbox = tk.Listbox(sent_frame, font=('Consolas', 11), height=10)
        self.sent_listbox.pack(fill='both', expand=True, side='left')
        scrollbar2 = ttk.Scrollbar(sent_frame, orient='vertical', command=self.sent_listbox.yview)
        scrollbar2.pack(side='right', fill='y')
        self.sent_listbox.config(yscrollcommand=scrollbar2.set)
        
        sent_buttons = ttk.Frame(right_frame)
        sent_buttons.pack(fill='x', pady=5)
        
        cancel_btn = tk.Button(sent_buttons, text="🚫 Cancelar Solicitud", command=self.cancel_request,
                               bg='#FF9800', fg='white', font=('Arial', 10, 'bold'))
        cancel_btn.pack(side='left', padx=5)
        
        # Botón de actualizar
        ttk.Button(requests_frame, text="🔄 Actualizar", command=self.refresh_data).pack(side='bottom', pady=10)
    
    def send_friend_request(self):
        to_user = self.send_request_combo.get()
        if not to_user:
            messagebox.showwarning("Advertencia", "Seleccione un usuario")
            return
        
        response = self.client.send_friend_request(to_user)
        if response.get("status") == "success":
            messagebox.showinfo("Éxito", response.get("message"))
            self.refresh_data()
        else:
            messagebox.showerror("Error", response.get("message"))
    
    def accept_request(self):
        selection = self.pending_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione una solicitud")
            return
        
        from_user = self.pending_listbox.get(selection[0]).replace("👤 ", "")
        response = self.client.accept_friend_request(from_user)
        
        if response.get("status") == "success":
            messagebox.showinfo("Éxito", response.get("message"))
            self.refresh_data()
        else:
            messagebox.showerror("Error", response.get("message"))
    
    def reject_request(self):
        selection = self.pending_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione una solicitud")
            return
        
        from_user = self.pending_listbox.get(selection[0]).replace("👤 ", "")
        
        if messagebox.askyesno("Confirmar", f"¿Rechazar solicitud de '{from_user}'?"):
            response = self.client.reject_friend_request(from_user)
            
            if response.get("status") == "success":
                messagebox.showinfo("Éxito", response.get("message"))
                self.refresh_data()
            else:
                messagebox.showerror("Error", response.get("message"))
    
    def cancel_request(self):
        selection = self.sent_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione una solicitud")
            return
        
        to_user = self.sent_listbox.get(selection[0]).replace("⏳ ", "")
        
        if messagebox.askyesno("Confirmar", f"¿Cancelar solicitud a '{to_user}'?"):
            response = self.client.cancel_friend_request(to_user)
            
            if response.get("status") == "success":
                messagebox.showinfo("Éxito", response.get("message"))
                self.refresh_data()
            else:
                messagebox.showerror("Error", response.get("message"))
    
    # ==================== PESTAÑA DE AMIGOS ====================
    def create_friends_tab(self):
        friends_frame = ttk.Frame(self.notebook)
        self.notebook.add(friends_frame, text="👥 Mis Amigos")
        
        # Eliminar amigo
        remove_frame = ttk.LabelFrame(friends_frame, text="Eliminar Amigo", padding=10)
        remove_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(remove_frame, text="Amigo:").grid(row=0, column=0, padx=5)
        self.remove_friend_combo = ttk.Combobox(remove_frame, width=25, state="readonly")
        self.remove_friend_combo.grid(row=0, column=1, padx=5)
        
        remove_btn = tk.Button(remove_frame, text="❌ Eliminar Amigo", command=self.remove_friend,
                               bg='#f44336', fg='white', font=('Arial', 10))
        remove_btn.grid(row=0, column=2, padx=10)
        
        # Lista de amigos
        list_frame = ttk.LabelFrame(friends_frame, text="Mis Amigos", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.friends_listbox = tk.Listbox(list_frame, font=('Consolas', 11))
        self.friends_listbox.pack(fill='both', expand=True, side='left')
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.friends_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.friends_listbox.config(yscrollcommand=scrollbar.set)
        
        ttk.Button(friends_frame, text="🔄 Actualizar", command=self.refresh_data).pack(pady=5)
    
    def remove_friend(self):
        friend = self.remove_friend_combo.get()
        if not friend:
            messagebox.showwarning("Advertencia", "Seleccione un amigo")
            return
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar a '{friend}' de tus amigos?"):
            response = self.client.remove_friend(friend)
            if response.get("status") == "success":
                messagebox.showinfo("Éxito", response.get("message"))
                self.refresh_data()
            else:
                messagebox.showerror("Error", response.get("message"))
    
    # ==================== PESTAÑA DE USUARIOS ====================
    def create_users_tab(self):
        users_frame = ttk.Frame(self.notebook)
        self.notebook.add(users_frame, text="👤 Usuarios")
        
        # Frame de búsqueda
        search_frame = ttk.LabelFrame(users_frame, text="🔍 Buscar Usuarios", padding=10)
        search_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(search_frame, text="Nombre:").grid(row=0, column=0, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30, font=('Arial', 11))
        self.search_entry.grid(row=0, column=1, padx=5, ipady=3)
        self.search_entry.bind('<KeyRelease>', self.on_search_key)
        
        search_btn = tk.Button(search_frame, text="🔍 Buscar", command=self.do_search,
                               bg='#2196F3', fg='white', font=('Arial', 10, 'bold'))
        search_btn.grid(row=0, column=2, padx=10)
        
        clear_btn = tk.Button(search_frame, text="✖ Limpiar", command=self.clear_search,
                              bg='#9E9E9E', fg='white', font=('Arial', 10))
        clear_btn.grid(row=0, column=3, padx=5)
        
        list_frame = ttk.LabelFrame(users_frame, text="Usuarios Registrados", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.users_listbox = tk.Listbox(list_frame, font=('Consolas', 11))
        self.users_listbox.pack(fill='both', expand=True, side='left')
        self.users_listbox.bind('<Double-Button-1>', self.on_user_double_click)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.users_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.users_listbox.config(yscrollcommand=scrollbar.set)
        
        # Botón para ver perfil
        btn_frame = ttk.Frame(users_frame)
        btn_frame.pack(fill='x', padx=10, pady=5)
        
        view_profile_btn = tk.Button(btn_frame, text="👁️ Ver Perfil", command=self.view_selected_profile,
                                     bg='#673AB7', fg='white', font=('Arial', 10, 'bold'))
        view_profile_btn.pack(side='left', padx=5)
        
        # Leyenda
        legend_frame = ttk.Frame(users_frame)
        legend_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(legend_frame, text="Leyenda: ✓ = Amigo | ⏳ = Solicitud enviada | 📬 = Te envió solicitud | Doble clic = Ver perfil", 
                  font=('Arial', 9)).pack()
    
    def on_search_key(self, event):
        """Búsqueda en tiempo real al escribir (filtrado local)"""
        self.filter_users_list()
    
    def do_search(self):
        """Realiza la búsqueda de usuarios (filtrado local)"""
        self.filter_users_list()
    
    def filter_users_list(self):
        """Filtra la lista de usuarios localmente según el texto de búsqueda"""
        query = self.search_entry.get().strip().lower()
        
        # Usar los datos en caché
        if query:
            # Filtrar usuarios que contengan el texto de búsqueda
            filtered_users = [u for u in self.all_users_cache if query in u.lower()]
        else:
            # Mostrar todos los usuarios si no hay búsqueda
            filtered_users = self.all_users_cache
        
        # Actualizar la lista
        self.users_listbox.delete(0, tk.END)
        if filtered_users:
            for user in filtered_users:
                if user == self.username:
                    self.users_listbox.insert(tk.END, f"👤 {user} (tú)")
                elif user in self.friends_cache:
                    self.users_listbox.insert(tk.END, f"👤 {user} ✓")
                elif user in self.sent_cache:
                    self.users_listbox.insert(tk.END, f"👤 {user} ⏳")
                elif user in self.pending_cache:
                    self.users_listbox.insert(tk.END, f"👤 {user} 📬")
                else:
                    self.users_listbox.insert(tk.END, f"👤 {user}")
        else:
            self.users_listbox.insert(tk.END, "No se encontraron usuarios")
    
    def clear_search(self):
        """Limpia la búsqueda y muestra todos los usuarios"""
        self.search_entry.delete(0, tk.END)
        self.refresh_data()
    
    def on_user_double_click(self, event):
        """Abre el perfil al hacer doble clic en un usuario"""
        self.view_selected_profile()
    
    def view_selected_profile(self):
        """Muestra el perfil del usuario seleccionado"""
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un usuario")
            return
        
        user_text = self.users_listbox.get(selection[0])
        # Extraer nombre de usuario quitando emoji y marcadores
        username = user_text.replace("👤 ", "").split(" ")[0]
        if "(tú)" in user_text:
            username = user_text.replace("👤 ", "").replace(" (tú)", "")
        elif "✓" in user_text:
            username = user_text.replace("👤 ", "").replace(" ✓", "")
        elif "⏳" in user_text:
            username = user_text.replace("👤 ", "").replace(" ⏳", "")
        elif "📬" in user_text:
            username = user_text.replace("👤 ", "").replace(" 📬", "")
        else:
            username = user_text.replace("👤 ", "").strip()
        
        self.show_user_profile_window(username)
    
    def show_user_profile_window(self, username):
        """Muestra una ventana con el perfil del usuario"""
        response = self.client.get_user_profile(username)
        if response.get("status") != "success":
            messagebox.showerror("Error", response.get("message"))
            return
        
        profile = response.get("profile", {})
        
        # Crear ventana de perfil
        profile_window = tk.Toplevel(self.root)
        profile_window.title(f"Perfil de {username}")
        profile_window.geometry("450x550")
        profile_window.resizable(False, False)
        
        # Frame principal
        main_frame = ttk.Frame(profile_window, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Foto de perfil
        photo_frame = ttk.Frame(main_frame)
        photo_frame.pack(pady=10)
        
        photo_url = profile.get("photo_url", "")
        self.display_profile_photo(photo_frame, photo_url, size=150)
        
        # Nombre de usuario
        ttk.Label(main_frame, text=f"👤 {username}", font=('Arial', 18, 'bold')).pack(pady=10)
        
        # Estadísticas
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(pady=10)
        
        friends_count = profile.get("friends_count", 0)
        ttk.Label(stats_frame, text=f"👥 {friends_count} amigo(s)", font=('Arial', 12)).pack()
        
        # Descripción
        desc_frame = ttk.LabelFrame(main_frame, text="📝 Descripción", padding=10)
        desc_frame.pack(fill='x', pady=10)
        
        description = profile.get("description", "")
        if description:
            desc_label = ttk.Label(desc_frame, text=description, font=('Arial', 11), wraplength=380)
        else:
            desc_label = ttk.Label(desc_frame, text="(Sin descripción)", font=('Arial', 11, 'italic'), foreground='gray')
        desc_label.pack(pady=5)
        
        # Lista de amigos
        friends_frame = ttk.LabelFrame(main_frame, text="👥 Amigos", padding=10)
        friends_frame.pack(fill='both', expand=True, pady=10)
        
        friends = profile.get("friends", [])
        if friends:
            friends_listbox = tk.Listbox(friends_frame, font=('Consolas', 10), height=6)
            friends_listbox.pack(fill='both', expand=True, side='left')
            scrollbar = ttk.Scrollbar(friends_frame, orient='vertical', command=friends_listbox.yview)
            scrollbar.pack(side='right', fill='y')
            friends_listbox.config(yscrollcommand=scrollbar.set)
            for friend in friends:
                friends_listbox.insert(tk.END, f"  👤 {friend}")
        else:
            ttk.Label(friends_frame, text="(Sin amigos aún)", font=('Arial', 10, 'italic'), foreground='gray').pack()
        
        # Verificar si es amigo y mostrar botón
        if username != self.username:
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(pady=10)
            
            are_friends_response = self.client.are_friends(username)
            if are_friends_response.get("status") == "success" and are_friends_response.get("are_friends"):
                # Ya son amigos - mostrar botón para eliminar amistad
                ttk.Label(btn_frame, text="✓ Son amigos", foreground='green', font=('Arial', 11, 'bold')).pack(pady=5)
                remove_btn = tk.Button(btn_frame, text="❌ Eliminar amistad", 
                                       command=lambda: self.remove_friend_from_profile(username, profile_window),
                                       bg='#f44336', fg='white', font=('Arial', 10, 'bold'))
                remove_btn.pack()
            else:
                # Verificar si ya se envió solicitud
                sent_response = self.client.get_sent_requests()
                sent = sent_response.get("sent_requests", []) if sent_response.get("status") == "success" else []
                
                pending_response = self.client.get_pending_requests()
                pending = pending_response.get("pending_requests", []) if pending_response.get("status") == "success" else []
                
                if username in sent:
                    ttk.Label(btn_frame, text="⏳ Solicitud enviada", foreground='orange', font=('Arial', 11)).pack()
                elif username in pending:
                    accept_btn = tk.Button(btn_frame, text="✅ Aceptar solicitud", 
                                           command=lambda: self.accept_from_profile(username, profile_window),
                                           bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'))
                    accept_btn.pack()
                else:
                    add_btn = tk.Button(btn_frame, text="➕ Enviar solicitud de amistad", 
                                        command=lambda: self.send_request_from_profile(username, profile_window),
                                        bg='#2196F3', fg='white', font=('Arial', 10, 'bold'))
                    add_btn.pack()
        
        # Botón cerrar
        tk.Button(main_frame, text="Cerrar", command=profile_window.destroy,
                  font=('Arial', 10), padx=20, pady=5).pack(pady=10)
    
    def display_profile_photo(self, frame, url_or_path, size=100):
        """Muestra la foto de perfil desde una URL o archivo local"""
        photo_label = ttk.Label(frame)
        photo_label.pack()
        
        if url_or_path and url_or_path.strip() and PIL_AVAILABLE:
            try:
                # Verificar si es un archivo local o URL
                if os.path.isfile(url_or_path):
                    # Es un archivo local
                    image = Image.open(url_or_path)
                elif url_or_path.startswith(('http://', 'https://')):
                    # Es una URL
                    with urllib.request.urlopen(url_or_path, timeout=5) as response:
                        image_data = response.read()
                    image = Image.open(io.BytesIO(image_data))
                else:
                    # Podría ser una ruta relativa o inválida
                    raise Exception("Ruta no válida")
                
                image = image.resize((size, size), Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(image)
                photo_label.config(image=photo)
                photo_label.image = photo  # Mantener referencia
            except Exception as e:
                # Si falla, mostrar placeholder
                photo_label.config(text="📷", font=('Arial', 40))
        elif url_or_path and url_or_path.strip() and not PIL_AVAILABLE:
            # PIL no disponible, mostrar indicador con URL
            photo_label.config(text="🖼️", font=('Arial', 40))
            url_label = ttk.Label(frame, text="(Foto configurada)", font=('Arial', 9), foreground='gray')
            url_label.pack()
        else:
            # Sin foto, mostrar placeholder
            photo_label.config(text="📷", font=('Arial', 40))
    
    def send_request_from_profile(self, username, window):
        """Envía solicitud de amistad desde la ventana de perfil"""
        response = self.client.send_friend_request(username)
        if response.get("status") == "success":
            messagebox.showinfo("Éxito", response.get("message"))
            window.destroy()
            self.refresh_data()
        else:
            messagebox.showerror("Error", response.get("message"))
    
    def accept_from_profile(self, username, window):
        """Acepta solicitud desde la ventana de perfil"""
        response = self.client.accept_friend_request(username)
        if response.get("status") == "success":
            messagebox.showinfo("Éxito", response.get("message"))
            window.destroy()
            self.refresh_data()
        else:
            messagebox.showerror("Error", response.get("message"))
    
    def remove_friend_from_profile(self, username, window):
        """Elimina amistad desde la ventana de perfil"""
        if messagebox.askyesno("Confirmar", f"¿Eliminar a '{username}' de tus amigos?"):
            response = self.client.remove_friend(username)
            if response.get("status") == "success":
                messagebox.showinfo("Éxito", response.get("message"))
                window.destroy()
                self.refresh_data()
            else:
                messagebox.showerror("Error", response.get("message"))
    
    # ==================== PESTAÑA DE MI PERFIL ====================
    def create_profile_tab(self):
        profile_frame = ttk.Frame(self.notebook)
        self.notebook.add(profile_frame, text="🪪 Mi Perfil")
        
        # Frame principal
        main_frame = ttk.Frame(profile_frame, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Foto de perfil
        self.my_photo_frame = ttk.LabelFrame(main_frame, text="📷 Foto de Perfil", padding=10)
        self.my_photo_frame.pack(fill='x', padx=10, pady=10)
        
        self.photo_display_frame = ttk.Frame(self.my_photo_frame)
        self.photo_display_frame.pack(pady=10)
        
        ttk.Label(self.my_photo_frame, text="URL o ruta de la imagen:").pack(anchor='w')
        self.photo_url_entry = ttk.Entry(self.my_photo_frame, width=60, font=('Arial', 10))
        self.photo_url_entry.pack(fill='x', pady=5, ipady=3)
        
        photo_btn_frame = ttk.Frame(self.my_photo_frame)
        photo_btn_frame.pack(fill='x', pady=5)
        
        tk.Button(photo_btn_frame, text="📁 Seleccionar Archivo", command=self.select_photo_file,
                  bg='#2196F3', fg='white', font=('Arial', 9)).pack(side='left', padx=5)
        
        tk.Button(photo_btn_frame, text="🔄 Previsualizar", command=self.preview_photo,
                  bg='#9E9E9E', fg='white', font=('Arial', 9)).pack(side='left', padx=5)
        
        # Descripción
        desc_frame = ttk.LabelFrame(main_frame, text="📝 Descripción / Bio", padding=10)
        desc_frame.pack(fill='x', padx=10, pady=10)
        
        self.description_text = tk.Text(desc_frame, height=4, font=('Arial', 11), wrap='word')
        self.description_text.pack(fill='x', pady=5)
        
        # Estadísticas
        self.my_stats_frame = ttk.LabelFrame(main_frame, text="📊 Estadísticas", padding=10)
        self.my_stats_frame.pack(fill='x', padx=10, pady=10)
        
        self.my_friends_count_label = ttk.Label(self.my_stats_frame, text="👥 Amigos: 0", font=('Arial', 12))
        self.my_friends_count_label.pack(anchor='w')
        
        # Botón guardar
        save_btn = tk.Button(main_frame, text="💾 Guardar Perfil", command=self.save_profile,
                             bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'), padx=30, pady=10)
        save_btn.pack(pady=20)
        
        # Cargar datos actuales del perfil
        self.load_my_profile()
    
    def load_my_profile(self):
        """Carga los datos del perfil del usuario actual"""
        response = self.client.get_user_profile(self.username)
        if response.get("status") == "success":
            profile = response.get("profile", {})
            
            # Actualizar campos
            self.photo_url_entry.delete(0, tk.END)
            self.photo_url_entry.insert(0, profile.get("photo_url", ""))
            
            self.description_text.delete(1.0, tk.END)
            self.description_text.insert(tk.END, profile.get("description", ""))
            
            friends_count = profile.get("friends_count", 0)
            self.my_friends_count_label.config(text=f"👥 Amigos: {friends_count}")
            
            # Mostrar foto actual
            self.preview_photo()
    
    def select_photo_file(self):
        """Abre un diálogo para seleccionar una imagen local"""
        filetypes = [
            ("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
            ("PNG", "*.png"),
            ("JPEG", "*.jpg *.jpeg"),
            ("GIF", "*.gif"),
            ("Todos los archivos", "*.*")
        ]
        
        filepath = filedialog.askopenfilename(
            title="Seleccionar imagen de perfil",
            filetypes=filetypes
        )
        
        if filepath:
            # Poner la ruta en el campo de entrada
            self.photo_url_entry.delete(0, tk.END)
            self.photo_url_entry.insert(0, filepath)
            # Previsualizar automáticamente
            self.preview_photo()
    
    def preview_photo(self):
        """Previsualiza la foto de perfil"""
        # Limpiar frame de foto
        for widget in self.photo_display_frame.winfo_children():
            widget.destroy()
        
        url = self.photo_url_entry.get().strip()
        self.display_profile_photo(self.photo_display_frame, url, size=120)
    
    def save_profile(self):
        """Guarda los cambios del perfil"""
        description = self.description_text.get(1.0, tk.END).strip()
        photo_url = self.photo_url_entry.get().strip()
        
        response = self.client.update_profile(description=description, photo_url=photo_url)
        if response.get("status") == "success":
            messagebox.showinfo("Éxito", "Perfil actualizado correctamente")
            self.preview_photo()
        else:
            messagebox.showerror("Error", response.get("message"))
    
    # ==================== PESTAÑA DE CONSULTAS ====================
    def create_queries_tab(self):
        queries_frame = ttk.Frame(self.notebook)
        self.notebook.add(queries_frame, text="🔍 Consultas")
        
        # Amigos en común
        mutual_frame = ttk.LabelFrame(queries_frame, text="Amigos en Común", padding=10)
        mutual_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(mutual_frame, text="Con usuario:").grid(row=0, column=0, padx=5)
        self.mutual_combo = ttk.Combobox(mutual_frame, width=25, state="readonly")
        self.mutual_combo.grid(row=0, column=1, padx=5)
        ttk.Button(mutual_frame, text="Buscar", command=self.show_mutual_friends).grid(row=0, column=2, padx=5)
        
        # Buscar camino entre usuarios
        path_frame = ttk.LabelFrame(queries_frame, text="🛤️ Buscar Camino de Amigos", padding=10)
        path_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(path_frame, text="Desde:").grid(row=0, column=0, padx=5)
        self.path_from_combo = ttk.Combobox(path_frame, width=20, state="readonly")
        self.path_from_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(path_frame, text="Hasta:").grid(row=0, column=2, padx=5)
        self.path_to_combo = ttk.Combobox(path_frame, width=20, state="readonly")
        self.path_to_combo.grid(row=0, column=3, padx=5)
        
        path_btn = tk.Button(path_frame, text="🔍 Buscar Camino", command=self.find_friend_path,
                             bg='#673AB7', fg='white', font=('Arial', 10, 'bold'))
        path_btn.grid(row=0, column=4, padx=10)
        
        # Estadísticas de la red
        stats_frame = ttk.LabelFrame(queries_frame, text="📊 Estadísticas de la Red", padding=10)
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        stats_btn = tk.Button(stats_frame, text="📊 Obtener Estadísticas", command=self.show_statistics,
                              bg='#FF5722', fg='white', font=('Arial', 10, 'bold'))
        stats_btn.pack(pady=5)
        
        # Resultados
        result_frame = ttk.LabelFrame(queries_frame, text="Resultados", padding=10)
        result_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.query_result = scrolledtext.ScrolledText(result_frame, font=('Consolas', 11), height=10)
        self.query_result.pack(fill='both', expand=True)
    
    def show_mutual_friends(self):
        other = self.mutual_combo.get()
        if not other:
            messagebox.showwarning("Advertencia", "Seleccione un usuario")
            return
        
        response = self.client.get_mutual_friends(other)
        self.query_result.delete(1.0, tk.END)
        
        if response.get("status") == "success":
            mutual = response.get("mutual_friends", [])
            if mutual:
                self.query_result.insert(tk.END, f"Amigos en común con {other}:\n\n")
                for friend in mutual:
                    self.query_result.insert(tk.END, f"  • {friend}\n")
            else:
                self.query_result.insert(tk.END, f"No tienes amigos en común con {other}")
        else:
            self.query_result.insert(tk.END, response.get("message"))
    
    def find_friend_path(self):
        """Busca un camino de amigos entre dos usuarios"""
        from_user = self.path_from_combo.get()
        to_user = self.path_to_combo.get()
        
        if not from_user or not to_user:
            messagebox.showwarning("Advertencia", "Seleccione ambos usuarios")
            return
        
        if from_user == to_user:
            messagebox.showwarning("Advertencia", "Seleccione dos usuarios diferentes")
            return
        
        response = self.client.find_path(from_user, to_user)
        self.query_result.delete(1.0, tk.END)
        
        if response.get("status") == "success":
            path = response.get("path", [])
            if path:
                self.query_result.insert(tk.END, f"✅ ¡SÍ existe un camino de amigos entre {from_user} y {to_user}!\n\n")
                self.query_result.insert(tk.END, "Camino encontrado:\n\n")
                
                # Mostrar el camino de forma visual
                path_str = ""
                for i, user in enumerate(path):
                    if i > 0:
                        path_str += " → "
                    path_str += f"👤 {user}"
                
                self.query_result.insert(tk.END, f"   {path_str}\n\n")
                self.query_result.insert(tk.END, f"📊 Longitud del camino: {len(path)} usuarios ({len(path)-1} conexiones)")
            else:
                self.query_result.insert(tk.END, f"❌ NO existe un camino de amigos entre {from_user} y {to_user}\n\n")
                self.query_result.insert(tk.END, "Estos usuarios no están conectados en la red de amigos.")
        else:
            self.query_result.insert(tk.END, response.get("message"))
    
    def show_statistics(self):
        """Muestra las estadísticas de la red social"""
        response = self.client.get_statistics()
        self.query_result.delete(1.0, tk.END)
        
        if response.get("status") == "success":
            stats = response.get("statistics", {})
            
            self.query_result.insert(tk.END, "╔═══════════════════════════════════════════════════╗\n")
            self.query_result.insert(tk.END, "║         📊 ESTADÍSTICAS DE LA RED SOCIAL          ║\n")
            self.query_result.insert(tk.END, "╚═══════════════════════════════════════════════════╝\n\n")
            
            # Usuario(s) con más amigos
            max_users = stats.get("max_friends_users", [])
            max_count = stats.get("max_friends_count", 0)
            self.query_result.insert(tk.END, "🏆 Usuario(s) con MÁS amigos:\n")
            for user in max_users:
                self.query_result.insert(tk.END, f"   👤 {user} → {max_count} amigo(s)\n")
            self.query_result.insert(tk.END, "\n")
            
            # Usuario(s) con menos amigos
            min_users = stats.get("min_friends_users", [])
            min_count = stats.get("min_friends_count", 0)
            self.query_result.insert(tk.END, "📉 Usuario(s) con MENOS amigos:\n")
            for user in min_users:
                self.query_result.insert(tk.END, f"   👤 {user} → {min_count} amigo(s)\n")
            self.query_result.insert(tk.END, "\n")
            
            # Promedio de amigos
            average = stats.get("average_friends", 0)
            self.query_result.insert(tk.END, f"📊 Promedio de amigos por usuario: {average}\n\n")
            
            # Información adicional
            total_users = stats.get("total_users", 0)
            total_friendships = stats.get("total_friendships", 0)
            self.query_result.insert(tk.END, "═══════════════════════════════════════════════════\n")
            self.query_result.insert(tk.END, f"👥 Total de usuarios: {total_users}\n")
            self.query_result.insert(tk.END, f"🤝 Total de amistades: {total_friendships}\n")
        else:
            self.query_result.insert(tk.END, response.get("message"))
    
    # ==================== PESTAÑA DE VISUALIZACIÓN ====================
    def create_visualization_tab(self):
        viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(viz_frame, text="📊 Visualizar Grafo")
        
        # Controles
        controls_frame = ttk.LabelFrame(viz_frame, text="Opciones", padding=10)
        controls_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(controls_frame, text="Formato:").grid(row=0, column=0, padx=5)
        self.format_combo = ttk.Combobox(controls_frame, width=10, state="readonly", 
                                         values=["png", "pdf", "svg", "jpg"])
        self.format_combo.set("png")
        self.format_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(controls_frame, text="Layout:").grid(row=0, column=2, padx=5)
        self.layout_combo = ttk.Combobox(controls_frame, width=10, state="readonly", 
                                         values=["neato", "dot", "circo", "fdp", "twopi"])
        self.layout_combo.set("neato")
        self.layout_combo.grid(row=0, column=3, padx=5)
        
        ttk.Button(controls_frame, text="🖼️ Generar Imagen", 
                   command=self.generate_graph).grid(row=0, column=4, padx=10)
        ttk.Button(controls_frame, text="🔄 Actualizar DOT", 
                   command=self.update_dot).grid(row=0, column=5, padx=5)
        
        # Código DOT
        dot_frame = ttk.LabelFrame(viz_frame, text="Código DOT", padding=10)
        dot_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.dot_text = scrolledtext.ScrolledText(dot_frame, font=('Consolas', 10), height=20)
        self.dot_text.pack(fill='both', expand=True)
    
    def update_dot(self):
        response = self.client.get_network()
        if response.get("status") != "success":
            messagebox.showerror("Error", response.get("message"))
            return
        
        network = response.get("network", {})
        
        dot = ['graph RedSocial {']
        dot.append('    graph [overlap=false, splines=true];')
        dot.append('    node [shape=circle, style=filled, fillcolor=lightblue, fontname="Arial"];')
        dot.append('    edge [color=gray50, penwidth=2];')
        dot.append('')
        
        # Nodos
        for user in network:
            color = "lightgreen" if user == self.username else "lightblue"
            dot.append(f'    "{user}" [fillcolor={color}];')
        
        dot.append('')
        
        # Aristas
        added = set()
        for user, friends in network.items():
            for friend in friends:
                edge = tuple(sorted([user, friend]))
                if edge not in added:
                    dot.append(f'    "{user}" -- "{friend}";')
                    added.add(edge)
        
        dot.append('}')
        
        self.dot_text.delete(1.0, tk.END)
        self.dot_text.insert(tk.END, '\n'.join(dot))
    
    def generate_graph(self):
        dot_code = self.dot_text.get(1.0, tk.END)
        if not dot_code.strip():
            self.update_dot()
            dot_code = self.dot_text.get(1.0, tk.END)
        
        output_format = self.format_combo.get()
        layout = self.layout_combo.get()
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False, encoding='utf-8') as f:
                f.write(dot_code)
                dot_path = f.name
            
            output_path = dot_path.replace('.dot', f'.{output_format}')
            graphviz_exe = os.path.join(GRAPHVIZ_PATH, f"{layout}.exe")
            
            result = subprocess.run(
                [graphviz_exe, f'-T{output_format}', dot_path, '-o', output_path],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                messagebox.showerror("Error", f"Error de Graphviz:\n{result.stderr}")
                return
            
            os.startfile(output_path)
            
        except FileNotFoundError:
            messagebox.showerror("Error", "Graphviz no encontrado. Verifique la instalación.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    # ==================== PESTAÑA DE RED ====================
    def create_network_tab(self):
        network_frame = ttk.Frame(self.notebook)
        self.notebook.add(network_frame, text="🌐 Red Completa")
        
        # Estadísticas
        self.stats_label = ttk.Label(network_frame, text="", font=('Arial', 11))
        self.stats_label.pack(pady=10)
        
        # Vista de red
        view_frame = ttk.LabelFrame(network_frame, text="Red Social", padding=10)
        view_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.network_text = scrolledtext.ScrolledText(view_frame, font=('Consolas', 11), height=20)
        self.network_text.pack(fill='both', expand=True)
        
        ttk.Button(network_frame, text="🔄 Actualizar", command=self.update_network_view).pack(pady=5)
    
    def update_network_view(self):
        response = self.client.get_network()
        if response.get("status") != "success":
            return
        
        network = response.get("network", {})
        
        num_users = len(network)
        num_friendships = sum(len(friends) for friends in network.values()) // 2
        
        self.stats_label.config(text=f"Usuarios: {num_users} | Amistades: {num_friendships}")
        
        self.network_text.delete(1.0, tk.END)
        self.network_text.insert(tk.END, "╔═══════════════════════════════════════╗\n")
        self.network_text.insert(tk.END, "║            RED SOCIAL                 ║\n")
        self.network_text.insert(tk.END, "╚═══════════════════════════════════════╝\n\n")
        
        for user in sorted(network.keys()):
            friends = network[user]
            marker = " (tú)" if user == self.username else ""
            friends_str = ", ".join(friends) if friends else "Sin amigos"
            self.network_text.insert(tk.END, f"👤 {user}{marker}\n")
            self.network_text.insert(tk.END, f"   └── Amigos: {friends_str}\n\n")
    
    # ==================== ACCIONES GENERALES ====================
    def refresh_data(self):
        # Obtener amigos
        friends_response = self.client.get_friends()
        friends = friends_response.get("friends", []) if friends_response.get("status") == "success" else []
        
        # Obtener usuarios
        users_response = self.client.get_all_users()
        all_users = users_response.get("users", []) if users_response.get("status") == "success" else []
        
        # Obtener solicitudes
        pending_response = self.client.get_pending_requests()
        pending = pending_response.get("pending_requests", []) if pending_response.get("status") == "success" else []
        
        sent_response = self.client.get_sent_requests()
        sent = sent_response.get("sent_requests", []) if sent_response.get("status") == "success" else []
        
        # Guardar en caché para búsqueda local
        self.all_users_cache = all_users
        self.friends_cache = friends
        self.sent_cache = sent
        self.pending_cache = pending
        
        # Actualizar listbox de solicitudes pendientes
        self.pending_listbox.delete(0, tk.END)
        for user in pending:
            self.pending_listbox.insert(tk.END, f"👤 {user}")
        
        # Actualizar listbox de solicitudes enviadas
        self.sent_listbox.delete(0, tk.END)
        for user in sent:
            self.sent_listbox.insert(tk.END, f"⏳ {user}")
        
        # Actualizar listbox de amigos
        self.friends_listbox.delete(0, tk.END)
        for friend in friends:
            self.friends_listbox.insert(tk.END, f"👤 {friend}")
        
        # Usuarios disponibles para enviar solicitud (no amigos, no solicitud pendiente)
        available_for_request = [u for u in all_users 
                                 if u != self.username 
                                 and u not in friends 
                                 and u not in sent
                                 and u not in pending]
        
        # Actualizar listbox de usuarios (respetando el filtro de búsqueda actual)
        self.filter_users_list()
        
        # Actualizar combos
        self.send_request_combo['values'] = available_for_request
        self.remove_friend_combo['values'] = friends
        self.mutual_combo['values'] = [u for u in all_users if u != self.username]
        self.path_from_combo['values'] = all_users
        self.path_to_combo['values'] = all_users
        
        # Actualizar título de pestaña de solicitudes
        if pending:
            self.notebook.tab(0, text=f"📬 Solicitudes ({len(pending)})")
        else:
            self.notebook.tab(0, text="📬 Solicitudes")
        
        # Actualizar estadísticas de mi perfil
        self.my_friends_count_label.config(text=f"👥 Amigos: {len(friends)}")
        
        # Actualizar vista de red
        self.update_network_view()
        self.update_dot()
    
    def do_logout(self):
        if messagebox.askyesno("Confirmar", "¿Cerrar sesión?"):
            self.client.logout()
            self.on_logout()
    
    def do_delete_account(self):
        if messagebox.askyesno("⚠️ Advertencia", 
            "¿Está seguro de eliminar su cuenta?\nEsta acción no se puede deshacer."):
            response = self.client.delete_account()
            if response.get("status") == "success":
                messagebox.showinfo("Cuenta Eliminada", response.get("message"))
                self.on_logout()
            else:
                messagebox.showerror("Error", response.get("message"))


class Application:
    def __init__(self):
        self.root = tk.Tk()
        self.client = SocialNetworkClient()
        self.current_window = None
        
        self.show_login()
    
    def show_login(self):
        if self.current_window:
            for widget in self.root.winfo_children():
                widget.destroy()
        
        self.client.disconnect()
        self.client.connect()
        
        self.current_window = LoginWindow(self.root, self.client, self.on_login_success)
    
    def on_login_success(self, username):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.current_window = MainWindow(self.root, self.client, username, self.show_login)
    
    def run(self):
        self.root.mainloop()
        self.client.disconnect()


def main():
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
