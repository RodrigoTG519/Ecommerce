import customtkinter as ctk
import mysql.connector
from tkinter import Listbox, messagebox, END

# Configurações iniciais
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Conexão com o banco de dados
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="db_ecommerce"
)
cursor = conn.cursor()


#Interface Gráfica


# Janela principal
janela = ctk.CTk()
janela.title("E-commerce de Peças de Computador")
janela.geometry("1000x900")
janela.configure(fg_color='#f2f2f2')

# Título Principal
titulo = ctk.CTkLabel(janela, text='Gerenciador de Produtos',font=ctk.CTkFont(size=26,weight='bold'))
titulo.pack(pady=20)


# Controle de seleção
linha_selecionada = None
linha_ids = {}

# ComboBox de categorias
combo_categorias = ctk.CTkComboBox(janela, width=200, command=lambda _: carregar_produtos())
combo_categorias.pack(pady=10)

# Frame com rolagem para simular uma tabela
frame_scroll = ctk.CTkScrollableFrame(janela, width=1000, height=800)
frame_scroll.pack(pady=10)

header_font = ("Arial", 16, "bold")
row_font = ("Arial", 14)

# Cabeçalhos
headers = ["ID", "Nome", "Marca", "Estoque", "Preço (R$)", "Categoria"]
for col, text in enumerate(headers):
    ctk.CTkLabel(frame_scroll, text=text, font=header_font, width=150).grid(row=0, column=col, padx=5, pady=5)

# Dicionário de widgets por linha
linhas_widgets = {}


# Funções principais
def carregar_categorias():
    cursor.execute("SELECT nome FROM categorias ORDER BY nome ASC")
    categorias = [row[0] for row in cursor.fetchall()]
    categorias.insert(0, "Todas")
    combo_categorias.configure(values=categorias)
    combo_categorias.set("Todas")

def selecionar_linha(linha_idx):
    global linha_selecionada

    # Limpa destaque anterior
    for widget in frame_scroll.winfo_children():
        widget.configure(bg_color="transparent")

    # Destaca nova linha
    start_index = (linha_idx - 1) * len(headers) + len(headers)
    for i in range(len(headers)):
        frame_scroll.winfo_children()[start_index + i].configure(bg_color="#ADD8E6")

    linha_selecionada = linha_idx


def carregar_produtos():
    global linha_ids
    for widget in frame_scroll.winfo_children()[len(headers):]:  # mantém cabeçalhos
        widget.destroy()

    categoria = combo_categorias.get()

    if categoria == "Todas":
        cursor.execute("""
            SELECT produtos.id, produtos.nome, produtos.marca, produtos.estoque, produtos.preco, categorias.nome
            FROM produtos
            JOIN categorias ON produtos.categoria_id = categorias.id
            ORDER BY produtos.id ASC
        """)
    else:
        cursor.execute("SELECT id FROM categorias WHERE nome = %s", (categoria,))
        categoria_id = cursor.fetchone()
        if categoria_id:
            cursor.execute("""
                SELECT produtos.id, produtos.nome, produtos.marca, produtos.estoque, produtos.preco, categorias.nome
                FROM produtos
                JOIN categorias ON produtos.categoria_id = categorias.id
                WHERE produtos.categoria_id = %s
                ORDER BY produtos.id ASC
            """, (categoria_id[0],))

    produtos = cursor.fetchall()
    linha_ids.clear()

    for i, (pid, nome, marca, estoque, preco, cat_nome) in enumerate(produtos, start=1):
        linha_ids[i] = pid

        valores = [pid, nome, marca, f"{estoque} un.", f"R${preco:.2f}", cat_nome]
        for j, val in enumerate(valores):
            label = ctk.CTkLabel(frame_scroll, text=val, font=row_font, width=150)
            label.grid(row=i, column=j, padx=5, pady=2)
            label.bind("<Button-1>", lambda e, idx=i: selecionar_linha(idx))


def adicionar_produto():
    def salvar():
        nome = entry_nome.get()
        marca = entry_marca.get()
        estoque = entry_estoque.get()
        preco = entry_preco.get()
        categoria_nome = combo_categoria.get()

        if not nome or not marca or not estoque or not preco or categoria_nome == "":
            messagebox.showwarning("Aviso", "Todos os campos devem ser preenchidos.")
            return

        try:
            estoque = int(estoque)
            preco = float(preco)
        except ValueError:
            messagebox.showwarning("Erro", "Estoque deve ser um número inteiro e preço deve ser decimal.")
            return

        cursor.execute("SELECT id FROM categorias WHERE nome = %s", (categoria_nome,))
        resultado = cursor.fetchone()
        if resultado is None:
            messagebox.showerror("Erro", "Categoria inválida.")
            return

        cursor.execute("""
            INSERT INTO produtos (nome, marca, estoque, preco, categoria_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (nome, marca, estoque, preco, resultado[0]))
        conn.commit()
        carregar_produtos()
        janela_add.destroy()

    janela_add = ctk.CTkToplevel(janela)
    janela_add.title("Adicionar Produto")
    janela_add.geometry("400x400")
    janela_add.lift()
    janela_add.focus_force()
    janela_add.grab_set()

    ctk.CTkLabel(janela_add, text="Nome:").pack(pady=5)
    entry_nome = ctk.CTkEntry(janela_add, width=300)
    entry_nome.pack()

    ctk.CTkLabel(janela_add, text="Marca:").pack(pady=5)
    entry_marca = ctk.CTkEntry(janela_add, width=300)
    entry_marca.pack()

    ctk.CTkLabel(janela_add, text="Estoque:").pack(pady=5)
    entry_estoque = ctk.CTkEntry(janela_add, width=300)
    entry_estoque.pack()

    ctk.CTkLabel(janela_add, text="Preço (R$):").pack(pady=5)
    entry_preco = ctk.CTkEntry(janela_add, width=300)
    entry_preco.pack()

    ctk.CTkLabel(janela_add, text="Categoria:").pack(pady=5)
    combo_categoria = ctk.CTkComboBox(janela_add, width=300)
    cursor.execute("SELECT nome FROM categorias ORDER BY nome ASC")
    categorias = [row[0] for row in cursor.fetchall()]
    combo_categoria.configure(values=categorias)
    if categorias:
        combo_categoria.set(categorias[0])
    combo_categoria.pack()

    ctk.CTkButton(janela_add, text="Salvar", command=salvar).pack(pady=20)

def editar_produto():
    try:
        if linha_selecionada is None:
            raise ValueError

        prod_id = linha_ids.get(linha_selecionada)
        cursor.execute("""
            SELECT produtos.nome, produtos.marca, produtos.estoque, produtos.preco, categorias.nome
            FROM produtos
            JOIN categorias ON produtos.categoria_id = categorias.id
            WHERE produtos.id = %s
        """, (prod_id,))
        resultado = cursor.fetchone()

        if resultado is None:
            raise ValueError

        nome_atual, marca_atual, estoque_atual, preco_atual, categoria_atual = resultado

        janela_edit = ctk.CTkToplevel(janela)
        janela_edit.title("Editar Produto")
        janela_edit.geometry("400x450")
        janela_edit.lift()
        janela_edit.focus_force()
        janela_edit.grab_set()
        

        ctk.CTkLabel(janela_edit, text="Nome:").pack(pady=5)
        entry_nome = ctk.CTkEntry(janela_edit, width=300, placeholder_text=nome_atual)
        entry_nome.pack()

        ctk.CTkLabel(janela_edit, text="Marca:").pack(pady=5)
        entry_marca = ctk.CTkEntry(janela_edit, width=300, placeholder_text=marca_atual)
        entry_marca.pack()

        ctk.CTkLabel(janela_edit, text="Estoque:").pack(pady=5)
        entry_estoque = ctk.CTkEntry(janela_edit, width=300, placeholder_text=str(estoque_atual))
        entry_estoque.pack()

        ctk.CTkLabel(janela_edit, text="Preço (R$):").pack(pady=5)
        entry_preco = ctk.CTkEntry(janela_edit, width=300, placeholder_text=f"{preco_atual:.2f}")
        entry_preco.pack()

        ctk.CTkLabel(janela_edit, text="Categoria:").pack(pady=5)
        combo_categoria = ctk.CTkComboBox(janela_edit, width=300)
        cursor.execute("SELECT nome FROM categorias ORDER BY nome ASC")
        categorias = [row[0] for row in cursor.fetchall()]
        combo_categoria.configure(values=categorias)
        combo_categoria.set(categoria_atual)
        combo_categoria.pack()

        def salvar_edicao():
            novo_nome = entry_nome.get() or nome_atual
            nova_marca = entry_marca.get() or marca_atual
            novo_estoque = entry_estoque.get() or estoque_atual
            novo_preco = entry_preco.get() or preco_atual
            nova_categoria = combo_categoria.get() or categoria_atual

            try:
                novo_estoque = int(novo_estoque)
                novo_preco = float(novo_preco)
            except ValueError:
                messagebox.showerror("Erro", "Estoque deve ser inteiro e preço decimal.")
                return

            cursor.execute("SELECT id FROM categorias WHERE nome = %s", (nova_categoria,))
            categoria_result = cursor.fetchone()
            if not categoria_result:
                messagebox.showerror("Erro", "Categoria inválida.")
                return

            cursor.execute("""
                UPDATE produtos
                SET nome = %s, marca = %s, estoque = %s, preco = %s, categoria_id = %s
                WHERE id = %s
            """, (novo_nome, nova_marca, novo_estoque, novo_preco, categoria_result[0], prod_id))
            conn.commit()
            carregar_produtos()
            janela_edit.destroy()

        ctk.CTkButton(janela_edit, text="Salvar Alterações", command=salvar_edicao).pack(pady=20)

    except:
        messagebox.showwarning("Aviso", "Selecione um produto válido para editar.")

def deletar_produto():
    global linha_selecionada
    if linha_selecionada is None:
        messagebox.showwarning("Aviso", "Selecione um produto para excluir.")
        return

    prod_id = linha_ids.get(linha_selecionada)
    confirm = messagebox.askyesno("Confirmação", "Tem certeza que deseja excluir este produto?")
    if confirm:
        cursor.execute("DELETE FROM produtos WHERE id = %s", (prod_id,))
        conn.commit()
        carregar_produtos()
        linha_selecionada = None

def ao_fechar():
    conn.close()
    janela.destroy()

janela.protocol("WM_DELETE_WINDOW", ao_fechar)

# Frame dos botões CRUD
frame_botoes = ctk.CTkFrame(janela,fg_color='#f2f2f2',corner_radius=0)
frame_botoes.pack(side="bottom", pady=20)



ctk.CTkButton(frame_botoes, text="Adicionar", command=adicionar_produto).pack(side="left", padx=10)
ctk.CTkButton(frame_botoes, text="Editar", command=editar_produto).pack(side="left", padx=10)
ctk.CTkButton(frame_botoes, text="Excluir", command=deletar_produto).pack(side="left", padx=10)
ctk.CTkButton(frame_botoes, text="Atualizar", command=carregar_produtos).pack(side="left", padx=10)


carregar_categorias()
carregar_produtos()
janela.mainloop()
