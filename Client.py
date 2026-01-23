import socket
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import tempfile

# Ruta de Graphviz
GRAPHVIZ_PATH = r"C:\Program Files\Graphviz\bin"


class SocialNetworkClient:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.logged_in = False
        self.username = None
    
    def connect(self):
        """Conecta al servidor"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            return True, "Conectado al servidor"
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


class LoginWindow:
    def __init__(self, root, client, on_login_success):
        self.root = root
        self.client = client
        self.on_login_success = on_login_success
        
        self.root.title("Red Social - Iniciar Sesión")
        self.root.geometry("450x450")
        self.root.resizable(False, False)
        
        self.create_widgets()
    
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="🌐 Red Social", font=('Arial', 20, 'bold'))
        title_label.pack(pady=10)
        
        subtitle = ttk.Label(main_frame, text="Cliente TCP con Solicitudes de Amistad", font=('Arial', 10))
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
        
        self.root.title(f"Red Social - {username}")
        self.root.geometry("950x700")
        self.root.resizable(True, True)
        
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
        
        list_frame = ttk.LabelFrame(users_frame, text="Usuarios Registrados", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.users_listbox = tk.Listbox(list_frame, font=('Consolas', 11))
        self.users_listbox.pack(fill='both', expand=True, side='left')
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.users_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.users_listbox.config(yscrollcommand=scrollbar.set)
        
        # Leyenda
        legend_frame = ttk.Frame(users_frame)
        legend_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(legend_frame, text="Leyenda: ✓ = Amigo | ⏳ = Solicitud enviada | 📬 = Te envió solicitud", 
                  font=('Arial', 9)).pack()
    
    # ==================== PESTAÑA DE CONSULTAS ====================
    def create_queries_tab(self):
        queries_frame = ttk.Frame(self.notebook)
        self.notebook.add(queries_frame, text="🔍 Consultas")
        
        # Amigos en común
        mutual_frame = ttk.LabelFrame(queries_frame, text="Amigos en Común", padding=10)
        mutual_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(mutual_frame, text="Con usuario:").grid(row=0, column=0, padx=5)
        self.mutual_combo = ttk.Combobox(mutual_frame, width=25, state="readonly")
        self.mutual_combo.grid(row=0, column=1, padx=5)
        ttk.Button(mutual_frame, text="Buscar", command=self.show_mutual_friends).grid(row=0, column=2, padx=5)
        
        # Verificar amistad
        check_frame = ttk.LabelFrame(queries_frame, text="Verificar Amistad", padding=10)
        check_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(check_frame, text="¿Soy amigo de:").grid(row=0, column=0, padx=5)
        self.check_combo = ttk.Combobox(check_frame, width=25, state="readonly")
        self.check_combo.grid(row=0, column=1, padx=5)
        ttk.Button(check_frame, text="Verificar", command=self.check_friendship).grid(row=0, column=2, padx=5)
        
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
    
    def check_friendship(self):
        other = self.check_combo.get()
        if not other:
            messagebox.showwarning("Advertencia", "Seleccione un usuario")
            return
        
        response = self.client.are_friends(other)
        self.query_result.delete(1.0, tk.END)
        
        if response.get("status") == "success":
            if response.get("are_friends"):
                self.query_result.insert(tk.END, f"✅ SÍ eres amigo de {other}")
            else:
                self.query_result.insert(tk.END, f"❌ NO eres amigo de {other}")
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
        
        # Actualizar listbox de usuarios
        self.users_listbox.delete(0, tk.END)
        for user in all_users:
            if user == self.username:
                self.users_listbox.insert(tk.END, f"👤 {user} (tú)")
            elif user in friends:
                self.users_listbox.insert(tk.END, f"👤 {user} ✓")
            elif user in sent:
                self.users_listbox.insert(tk.END, f"👤 {user} ⏳")
            elif user in pending:
                self.users_listbox.insert(tk.END, f"👤 {user} 📬")
            else:
                self.users_listbox.insert(tk.END, f"👤 {user}")
        
        # Actualizar combos
        self.send_request_combo['values'] = available_for_request
        self.remove_friend_combo['values'] = friends
        self.mutual_combo['values'] = [u for u in all_users if u != self.username]
        self.check_combo['values'] = [u for u in all_users if u != self.username]
        
        # Actualizar título de pestaña de solicitudes
        if pending:
            self.notebook.tab(0, text=f"📬 Solicitudes ({len(pending)})")
        else:
            self.notebook.tab(0, text="📬 Solicitudes")
        
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
