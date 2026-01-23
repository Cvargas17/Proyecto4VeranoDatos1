import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from Grafo import SocialNetwork
import subprocess
import os
import tempfile

# Ruta de Graphviz (ajustar si es necesario)
GRAPHVIZ_PATH = r"C:\Program Files\Graphviz\bin"

class SocialNetworkGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Red Social - Visualizador de Grafo")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Crear la red social
        self.network = SocialNetwork()
        
        # Crear el notebook (pestañas)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Crear las pestañas
        self.create_users_tab()
        self.create_friendships_tab()
        self.create_queries_tab()
        self.create_visualization_tab()
        self.create_network_view_tab()
        
        # Agregar algunos usuarios de ejemplo
        self.load_example_data()
    
    def load_example_data(self):
        """Carga datos de ejemplo para demostración"""
        self.network.add_user("Alice")
        self.network.add_user("Bob")
        self.network.add_user("Carlos")
        self.network.add_user("Diana")
        self.network.add_friendship("Alice", "Bob")
        self.network.add_friendship("Alice", "Carlos")
        self.network.add_friendship("Bob", "Carlos")
        self.network.add_friendship("Diana", "Alice")
        self.update_user_lists()
    
    # ==================== PESTAÑA DE USUARIOS ====================
    def create_users_tab(self):
        """Crea la pestaña para gestionar usuarios"""
        users_frame = ttk.Frame(self.notebook)
        self.notebook.add(users_frame, text="👤 Usuarios")
        
        # Frame para agregar usuario
        add_frame = ttk.LabelFrame(users_frame, text="Agregar Usuario", padding=10)
        add_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(add_frame, text="Nombre de usuario:").grid(row=0, column=0, padx=5, pady=5)
        self.new_user_entry = ttk.Entry(add_frame, width=30)
        self.new_user_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(add_frame, text="Agregar", command=self.add_user).grid(row=0, column=2, padx=5, pady=5)
        
        # Frame para eliminar usuario
        remove_frame = ttk.LabelFrame(users_frame, text="Eliminar Usuario", padding=10)
        remove_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(remove_frame, text="Seleccionar usuario:").grid(row=0, column=0, padx=5, pady=5)
        self.remove_user_combo = ttk.Combobox(remove_frame, width=27, state="readonly")
        self.remove_user_combo.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(remove_frame, text="Eliminar", command=self.remove_user).grid(row=0, column=2, padx=5, pady=5)
        
        # Lista de usuarios actuales
        list_frame = ttk.LabelFrame(users_frame, text="Usuarios Actuales", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.users_listbox = tk.Listbox(list_frame, font=('Consolas', 11))
        self.users_listbox.pack(fill='both', expand=True, side='left')
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.users_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.users_listbox.config(yscrollcommand=scrollbar.set)
    
    def add_user(self):
        """Agrega un nuevo usuario"""
        username = self.new_user_entry.get().strip()
        if not username:
            messagebox.showwarning("Advertencia", "Por favor ingrese un nombre de usuario.")
            return
        
        if self.network.add_user(username):
            messagebox.showinfo("Éxito", f"Usuario '{username}' agregado exitosamente.")
            self.new_user_entry.delete(0, tk.END)
            self.update_user_lists()
        else:
            messagebox.showerror("Error", f"El usuario '{username}' ya existe.")
    
    def remove_user(self):
        """Elimina un usuario seleccionado"""
        username = self.remove_user_combo.get()
        if not username:
            messagebox.showwarning("Advertencia", "Por favor seleccione un usuario.")
            return
        
        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar a '{username}'?"):
            if self.network.remove_user(username):
                messagebox.showinfo("Éxito", f"Usuario '{username}' eliminado.")
                self.update_user_lists()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el usuario.")
    
    # ==================== PESTAÑA DE AMISTADES ====================
    def create_friendships_tab(self):
        """Crea la pestaña para gestionar amistades"""
        friendships_frame = ttk.Frame(self.notebook)
        self.notebook.add(friendships_frame, text="🤝 Amistades")
        
        # Frame para agregar amistad
        add_frame = ttk.LabelFrame(friendships_frame, text="Agregar Amistad", padding=10)
        add_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(add_frame, text="Usuario 1:").grid(row=0, column=0, padx=5, pady=5)
        self.friend1_combo = ttk.Combobox(add_frame, width=20, state="readonly")
        self.friend1_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Usuario 2:").grid(row=0, column=2, padx=5, pady=5)
        self.friend2_combo = ttk.Combobox(add_frame, width=20, state="readonly")
        self.friend2_combo.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(add_frame, text="Agregar Amistad", command=self.add_friendship).grid(row=0, column=4, padx=5, pady=5)
        
        # Frame para eliminar amistad
        remove_frame = ttk.LabelFrame(friendships_frame, text="Eliminar Amistad", padding=10)
        remove_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(remove_frame, text="Usuario 1:").grid(row=0, column=0, padx=5, pady=5)
        self.unfriend1_combo = ttk.Combobox(remove_frame, width=20, state="readonly")
        self.unfriend1_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(remove_frame, text="Usuario 2:").grid(row=0, column=2, padx=5, pady=5)
        self.unfriend2_combo = ttk.Combobox(remove_frame, width=20, state="readonly")
        self.unfriend2_combo.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(remove_frame, text="Eliminar Amistad", command=self.remove_friendship).grid(row=0, column=4, padx=5, pady=5)
        
        # Lista de amistades actuales
        list_frame = ttk.LabelFrame(friendships_frame, text="Amistades Actuales", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.friendships_text = scrolledtext.ScrolledText(list_frame, font=('Consolas', 11), height=15)
        self.friendships_text.pack(fill='both', expand=True)
    
    def add_friendship(self):
        """Agrega una amistad entre dos usuarios"""
        user1 = self.friend1_combo.get()
        user2 = self.friend2_combo.get()
        
        if not user1 or not user2:
            messagebox.showwarning("Advertencia", "Por favor seleccione ambos usuarios.")
            return
        
        if self.network.add_friendship(user1, user2):
            messagebox.showinfo("Éxito", f"Amistad entre '{user1}' y '{user2}' agregada.")
            self.update_user_lists()
        else:
            if user1 == user2:
                messagebox.showerror("Error", "Un usuario no puede ser amigo de sí mismo.")
            else:
                messagebox.showerror("Error", f"'{user1}' y '{user2}' ya son amigos.")
    
    def remove_friendship(self):
        """Elimina una amistad entre dos usuarios"""
        user1 = self.unfriend1_combo.get()
        user2 = self.unfriend2_combo.get()
        
        if not user1 or not user2:
            messagebox.showwarning("Advertencia", "Por favor seleccione ambos usuarios.")
            return
        
        if self.network.remove_friendship(user1, user2):
            messagebox.showinfo("Éxito", f"Amistad entre '{user1}' y '{user2}' eliminada.")
            self.update_user_lists()
        else:
            messagebox.showerror("Error", f"'{user1}' y '{user2}' no son amigos.")
    
    # ==================== PESTAÑA DE CONSULTAS ====================
    def create_queries_tab(self):
        """Crea la pestaña para consultas"""
        queries_frame = ttk.Frame(self.notebook)
        self.notebook.add(queries_frame, text="🔍 Consultas")
        
        # Frame para ver amigos de un usuario
        friends_frame = ttk.LabelFrame(queries_frame, text="Ver Amigos de Usuario", padding=10)
        friends_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(friends_frame, text="Seleccionar usuario:").grid(row=0, column=0, padx=5, pady=5)
        self.query_user_combo = ttk.Combobox(friends_frame, width=20, state="readonly")
        self.query_user_combo.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(friends_frame, text="Ver Amigos", command=self.show_friends).grid(row=0, column=2, padx=5, pady=5)
        
        # Frame para amigos en común
        mutual_frame = ttk.LabelFrame(queries_frame, text="Amigos en Común", padding=10)
        mutual_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(mutual_frame, text="Usuario 1:").grid(row=0, column=0, padx=5, pady=5)
        self.mutual1_combo = ttk.Combobox(mutual_frame, width=20, state="readonly")
        self.mutual1_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(mutual_frame, text="Usuario 2:").grid(row=0, column=2, padx=5, pady=5)
        self.mutual2_combo = ttk.Combobox(mutual_frame, width=20, state="readonly")
        self.mutual2_combo.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(mutual_frame, text="Buscar", command=self.show_mutual_friends).grid(row=0, column=4, padx=5, pady=5)
        
        # Frame para verificar amistad
        check_frame = ttk.LabelFrame(queries_frame, text="Verificar Amistad", padding=10)
        check_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(check_frame, text="Usuario 1:").grid(row=0, column=0, padx=5, pady=5)
        self.check1_combo = ttk.Combobox(check_frame, width=20, state="readonly")
        self.check1_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(check_frame, text="Usuario 2:").grid(row=0, column=2, padx=5, pady=5)
        self.check2_combo = ttk.Combobox(check_frame, width=20, state="readonly")
        self.check2_combo.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(check_frame, text="Verificar", command=self.check_friendship).grid(row=0, column=4, padx=5, pady=5)
        
        # Área de resultados
        result_frame = ttk.LabelFrame(queries_frame, text="Resultados", padding=10)
        result_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.query_result_text = scrolledtext.ScrolledText(result_frame, font=('Consolas', 11), height=10)
        self.query_result_text.pack(fill='both', expand=True)
    
    def show_friends(self):
        """Muestra los amigos de un usuario"""
        username = self.query_user_combo.get()
        if not username:
            messagebox.showwarning("Advertencia", "Por favor seleccione un usuario.")
            return
        
        friends = self.network.get_friends(username)
        self.query_result_text.delete(1.0, tk.END)
        if friends:
            self.query_result_text.insert(tk.END, f"Amigos de {username}:\n")
            for friend in friends:
                self.query_result_text.insert(tk.END, f"  • {friend}\n")
        else:
            self.query_result_text.insert(tk.END, f"{username} no tiene amigos.")
    
    def show_mutual_friends(self):
        """Muestra los amigos en común entre dos usuarios"""
        user1 = self.mutual1_combo.get()
        user2 = self.mutual2_combo.get()
        
        if not user1 or not user2:
            messagebox.showwarning("Advertencia", "Por favor seleccione ambos usuarios.")
            return
        
        mutual = self.network.get_mutual_friends(user1, user2)
        self.query_result_text.delete(1.0, tk.END)
        if mutual:
            self.query_result_text.insert(tk.END, f"Amigos en común entre {user1} y {user2}:\n")
            for friend in mutual:
                self.query_result_text.insert(tk.END, f"  • {friend}\n")
        else:
            self.query_result_text.insert(tk.END, f"{user1} y {user2} no tienen amigos en común.")
    
    def check_friendship(self):
        """Verifica si dos usuarios son amigos"""
        user1 = self.check1_combo.get()
        user2 = self.check2_combo.get()
        
        if not user1 or not user2:
            messagebox.showwarning("Advertencia", "Por favor seleccione ambos usuarios.")
            return
        
        self.query_result_text.delete(1.0, tk.END)
        if self.network.are_friends(user1, user2):
            self.query_result_text.insert(tk.END, f"✅ {user1} y {user2} SÍ son amigos.")
        else:
            self.query_result_text.insert(tk.END, f"❌ {user1} y {user2} NO son amigos.")
    
    # ==================== PESTAÑA DE VISUALIZACIÓN (GRAPHVIZ) ====================
    def create_visualization_tab(self):
        """Crea la pestaña para visualizar el grafo con Graphviz"""
        viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(viz_frame, text="📊 Visualizar Grafo")
        
        # Frame de controles
        controls_frame = ttk.LabelFrame(viz_frame, text="Opciones de Visualización", padding=10)
        controls_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(controls_frame, text="Formato de salida:").grid(row=0, column=0, padx=5, pady=5)
        self.format_combo = ttk.Combobox(controls_frame, width=15, state="readonly", 
                                         values=["png", "pdf", "svg", "jpg"])
        self.format_combo.set("png")
        self.format_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(controls_frame, text="Layout:").grid(row=0, column=2, padx=5, pady=5)
        self.layout_combo = ttk.Combobox(controls_frame, width=15, state="readonly", 
                                         values=["dot", "neato", "circo", "fdp", "sfdp", "twopi"])
        self.layout_combo.set("neato")
        self.layout_combo.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(controls_frame, text="🖼️ Generar y Abrir Imagen", 
                   command=self.generate_graph_image).grid(row=0, column=4, padx=10, pady=5)
        
        ttk.Button(controls_frame, text="💾 Guardar Código DOT", 
                   command=self.save_dot_code).grid(row=0, column=5, padx=5, pady=5)
        
        # Frame para el código DOT
        dot_frame = ttk.LabelFrame(viz_frame, text="Código DOT (Graphviz)", padding=10)
        dot_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.dot_text = scrolledtext.ScrolledText(dot_frame, font=('Consolas', 11), height=20)
        self.dot_text.pack(fill='both', expand=True)
        
        # Botón para actualizar código DOT
        ttk.Button(dot_frame, text="🔄 Actualizar Código DOT", 
                   command=self.update_dot_code).pack(pady=5)
        
        # Generar código DOT inicial
        self.update_dot_code()
    
    def generate_dot_code(self):
        """Genera el código DOT para Graphviz"""
        dot = ['graph RedSocial {']
        dot.append('    // Configuración del grafo')
        dot.append('    graph [overlap=false, splines=true];')
        dot.append('    node [shape=circle, style=filled, fillcolor=lightblue, fontname="Arial"];')
        dot.append('    edge [color=gray50, penwidth=2];')
        dot.append('')
        dot.append('    // Nodos (usuarios)')
        
        for user in self.network.users:
            dot.append(f'    "{user}";')
        
        dot.append('')
        dot.append('    // Aristas (amistades)')
        
        # Para evitar duplicados (ya que es un grafo no dirigido)
        added_edges = set()
        for user, friends in self.network.users.items():
            for friend in friends:
                edge = tuple(sorted([user, friend]))
                if edge not in added_edges:
                    dot.append(f'    "{user}" -- "{friend}";')
                    added_edges.add(edge)
        
        dot.append('}')
        return '\n'.join(dot)
    
    def update_dot_code(self):
        """Actualiza el código DOT en el área de texto"""
        self.dot_text.delete(1.0, tk.END)
        self.dot_text.insert(tk.END, self.generate_dot_code())
    
    def generate_graph_image(self):
        """Genera y abre la imagen del grafo usando Graphviz"""
        try:
            dot_code = self.dot_text.get(1.0, tk.END)
            output_format = self.format_combo.get()
            layout = self.layout_combo.get()
            
            # Crear archivo temporal para el código DOT
            with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False, encoding='utf-8') as dot_file:
                dot_file.write(dot_code)
                dot_path = dot_file.name
            
            # Crear ruta para la imagen de salida
            output_path = dot_path.replace('.dot', f'.{output_format}')
            
            # Ejecutar Graphviz
            try:
                # Usar la ruta completa de Graphviz
                graphviz_exe = os.path.join(GRAPHVIZ_PATH, f"{layout}.exe")
                result = subprocess.run(
                    [graphviz_exe, f'-T{output_format}', dot_path, '-o', output_path],
                    capture_output=True, text=True, timeout=30
                )
                
                if result.returncode != 0:
                    messagebox.showerror("Error de Graphviz", 
                        f"Error al generar el grafo:\n{result.stderr}\n\n"
                        "Asegúrese de que Graphviz esté instalado y en el PATH.")
                    return
                
                # Abrir la imagen con el visor predeterminado
                os.startfile(output_path)
                messagebox.showinfo("Éxito", f"Imagen generada: {output_path}")
                
            except FileNotFoundError:
                messagebox.showerror("Error", 
                    "Graphviz no está instalado o no está en el PATH.\n\n"
                    "Por favor instale Graphviz desde:\nhttps://graphviz.org/download/\n\n"
                    "Y asegúrese de agregar la carpeta 'bin' al PATH del sistema.")
            except subprocess.TimeoutExpired:
                messagebox.showerror("Error", "Tiempo de espera agotado al generar el grafo.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")
    
    def save_dot_code(self):
        """Guarda el código DOT en un archivo"""
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".dot",
            filetypes=[("Archivos DOT", "*.dot"), ("Todos los archivos", "*.*")],
            title="Guardar código DOT"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.dot_text.get(1.0, tk.END))
                messagebox.showinfo("Éxito", f"Archivo guardado: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo: {str(e)}")
    
    # ==================== PESTAÑA DE VISTA DE RED ====================
    def create_network_view_tab(self):
        """Crea la pestaña para ver toda la red"""
        network_frame = ttk.Frame(self.notebook)
        self.notebook.add(network_frame, text="🌐 Vista de Red")
        
        # Estadísticas
        stats_frame = ttk.LabelFrame(network_frame, text="Estadísticas", padding=10)
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        self.stats_label = ttk.Label(stats_frame, text="", font=('Arial', 11))
        self.stats_label.pack()
        
        # Vista completa de la red
        view_frame = ttk.LabelFrame(network_frame, text="Red Social Completa", padding=10)
        view_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.network_text = scrolledtext.ScrolledText(view_frame, font=('Consolas', 12), height=20)
        self.network_text.pack(fill='both', expand=True)
        
        ttk.Button(view_frame, text="🔄 Actualizar Vista", command=self.update_network_view).pack(pady=5)
    
    def update_network_view(self):
        """Actualiza la vista de la red completa"""
        self.network_text.delete(1.0, tk.END)
        
        if not self.network.users:
            self.network_text.insert(tk.END, "La red está vacía.\n")
            self.stats_label.config(text="Usuarios: 0 | Amistades: 0")
            return
        
        # Calcular estadísticas
        num_users = len(self.network.users)
        num_friendships = sum(len(friends) for friends in self.network.users.values()) // 2
        
        self.stats_label.config(text=f"Usuarios: {num_users} | Amistades: {num_friendships}")
        
        # Mostrar la red
        self.network_text.insert(tk.END, "╔══════════════════════════════════════╗\n")
        self.network_text.insert(tk.END, "║           RED SOCIAL                 ║\n")
        self.network_text.insert(tk.END, "╚══════════════════════════════════════╝\n\n")
        
        for user, friends in sorted(self.network.users.items()):
            friends_list = ", ".join(sorted(friends)) if friends else "Sin amigos"
            self.network_text.insert(tk.END, f"👤 {user}\n")
            self.network_text.insert(tk.END, f"   └── Amigos: {friends_list}\n\n")
    
    # ==================== ACTUALIZACIÓN DE LISTAS ====================
    def update_user_lists(self):
        """Actualiza todas las listas de usuarios en la interfaz"""
        users = list(self.network.users.keys())
        users.sort()
        
        # Actualizar listbox de usuarios
        self.users_listbox.delete(0, tk.END)
        for user in users:
            self.users_listbox.insert(tk.END, f"👤 {user}")
        
        # Actualizar todos los comboboxes
        combos = [
            self.remove_user_combo,
            self.friend1_combo, self.friend2_combo,
            self.unfriend1_combo, self.unfriend2_combo,
            self.query_user_combo,
            self.mutual1_combo, self.mutual2_combo,
            self.check1_combo, self.check2_combo
        ]
        
        for combo in combos:
            current = combo.get()
            combo['values'] = users
            if current in users:
                combo.set(current)
            else:
                combo.set('')
        
        # Actualizar texto de amistades
        self.friendships_text.delete(1.0, tk.END)
        added_edges = set()
        for user, friends in self.network.users.items():
            for friend in friends:
                edge = tuple(sorted([user, friend]))
                if edge not in added_edges:
                    self.friendships_text.insert(tk.END, f"🤝 {edge[0]} ↔ {edge[1]}\n")
                    added_edges.add(edge)
        
        # Actualizar código DOT
        self.update_dot_code()
        
        # Actualizar vista de red
        self.update_network_view()


def main():
    root = tk.Tk()
    app = SocialNetworkGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
