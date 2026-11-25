import re
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# ---------------------------------
# CONFIGURACION DEL MENU
# ---------------------------------

MENU = [
    {"id": "pozole", "nombre": "Pozole rojo",
     "desc": "Maíz cacahuazintle, cerdo, lechuga y rábano",
     "precio": 95, "cat": "Platillos"},

    {"id": "sopes", "nombre": "Sopes (3 pzas)",
     "desc": "Frijol, carne a elegir, queso y crema",
     "precio": 70, "cat": "Platillos"},

    {"id": "enchiladas", "nombre": "Enchiladas verdes",
     "desc": "Pollo, salsa verde, crema y queso fresco",
     "precio": 85, "cat": "Platillos"},

    {"id": "tostadas", "nombre": "Tostadas de tinga",
     "desc": "Tinga de pollo, lechuga y aguacate",
     "precio": 60, "cat": "Platillos"},

    {"id": "quesadillas", "nombre": "Quesadillas (3)",
     "desc": "Masa azul con queso Oaxaca",
     "precio": 65, "cat": "Platillos"},

    {"id": "tamales", "nombre": "Tamal oaxaqueño",
     "desc": "Mole negro con pollo, hoja de plátano",
     "precio": 35, "cat": "Platillos"},

    {"id": "horchata", "nombre": "Agua de horchata",
     "desc": "Vaso grande, con canela",
     "precio": 35, "cat": "Bebidas"},

    {"id": "cafe", "nombre": "Café de olla",
     "desc": "Piloncillo y canela",
     "precio": 30, "cat": "Bebidas"},

    {"id": "atole", "nombre": "Atole de vainilla",
     "desc": "Caliente, espeso y dulce",
     "precio": 30, "cat": "Bebidas"},
]

PRECIOS = {p["id"]: p for p in MENU}
ENVIO = 30

PAGOS = {
    "efectivo": "Efectivo",
    "tarjeta": "Tarjeta",
    "transferencia": "Transferencia"
}

SUCURSALES = ["Centro", "Coyoacán", "Polanco",
              "Tlalpan", "Satélite"]


# ---------------------------------
# CONEXION CON SQLITE
# ---------------------------------

def conectar():
    conexion = sqlite3.connect("database.db")
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


# ---------------------------------
# CREAR BASE DE DATOS Y TABLAS
# ---------------------------------

def crear_base_datos():

    conexion = conectar()

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL UNIQUE
        )
    """)

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folio TEXT UNIQUE,
            fecha TEXT NOT NULL,
            cliente_id INTEGER NOT NULL,
            sucursal TEXT NOT NULL,
            entrega TEXT NOT NULL,
            direccion TEXT,
            pago TEXT NOT NULL,
            notas TEXT,
            subtotal REAL NOT NULL,
            envio REAL NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (cliente_id)
                REFERENCES clientes(id)
        )
    """)

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS detalle_pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            producto_id TEXT NOT NULL,
            nombre TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio REAL NOT NULL,
            importe REAL NOT NULL,
            FOREIGN KEY (pedido_id)
                REFERENCES pedidos(id)
        )
    """)

    conexion.commit()
    conexion.close()


# ---------------------------------
# PAGINA PRINCIPAL
# ---------------------------------

@app.route("/", methods=["GET"])
def index():

    return render_template(
        "index.html",
        menu=MENU,
        sucursales=SUCURSALES,
        pagos=PAGOS,
        envio=ENVIO,
        datos={},
        errores={}
    )


# ---------------------------------
# REGISTRO DE CLIENTES
# ---------------------------------

@app.route("/clientes", methods=["GET", "POST"])
def clientes():

    conexion = conectar()

    if request.method == "POST":

        nombre = (request.form.get("nombre") or "").strip()
        telefono = re.sub(
            r"\D", "", request.form.get("telefono", "")
        )

        if len(nombre) < 3 or not re.fullmatch(r"\d{10}", telefono):
            lista = conexion.execute(
                "SELECT * FROM clientes ORDER BY id DESC"
            ).fetchall()

            conexion.close()

            return render_template(
                "clientes.html",
                clientes=lista,
                error="Verifica el nombre y el teléfono de 10 dígitos."
            ), 400

        conexion.execute("""
            INSERT INTO clientes (nombre, telefono)
            VALUES (?, ?)
            ON CONFLICT(telefono)
            DO UPDATE SET nombre = excluded.nombre
        """, (nombre, telefono))

        conexion.commit()
        conexion.close()

        return redirect(url_for("clientes"))

    lista = conexion.execute(
        "SELECT * FROM clientes ORDER BY id DESC"
    ).fetchall()

    conexion.close()

    return render_template(
        "clientes.html",
        clientes=lista,
        error=None
    )


# ---------------------------------
# REGISTRO DE PEDIDOS
# ---------------------------------

@app.route("/pedido", methods=["POST"])
def pedido():

    nombre = (request.form.get("nombre") or "").strip()
    telefono = re.sub(
        r"\D", "", request.form.get("telefono", "")
    )

    sucursal = request.form.get("sucursal", "")
    entrega = request.form.get("entrega", "")
    direccion = (request.form.get("direccion") or "").strip()
    pago = request.form.get("pago", "")
    notas = (request.form.get("notas") or "").strip()

    errores = {}

    if len(nombre) < 3:
        errores["nombre"] = "Escribe tu nombre completo."

    if not re.fullmatch(r"\d{10}", telefono):
        errores["telefono"] = "El teléfono debe tener 10 dígitos."

    if sucursal not in SUCURSALES:
        errores["sucursal"] = "Elige una sucursal."

    if entrega not in ("sucursal", "domicilio"):
        errores["entrega"] = "Elige cómo recibirás tu pedido."

    if entrega == "domicilio" and len(direccion) < 8:
        errores["direccion"] = "Escribe tu dirección completa."

    if pago not in PAGOS:
        errores["pago"] = "Elige un método de pago."

    if len(notas) > 200:
        errores["notas"] = "Las notas no pueden pasar de 200 caracteres."

    items = []
    subtotal = 0

    for pid, prod in PRECIOS.items():

        try:
            cant = int(request.form.get(f"qty_{pid}", 0))
        except (ValueError, TypeError):
            cant = 0

        cant = max(0, min(cant, 20))

        if cant:
            importe = cant * prod["precio"]
            subtotal += importe

            items.append({
                "id": pid,
                "nombre": prod["nombre"],
                "cant": cant,
                "precio": prod["precio"],
                "importe": importe
            })

    if not items:
        errores["items"] = "Agrega al menos un alimento."

    if errores:

        return render_template(
            "index.html",
            menu=MENU,
            sucursales=SUCURSALES,
            pagos=PAGOS,
            envio=ENVIO,
            datos=request.form,
            errores=errores
        ), 400

    costo_envio = ENVIO if entrega == "domicilio" else 0
    total = subtotal + costo_envio

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    conexion = conectar()

    try:

        # Buscar o registrar al cliente
        conexion.execute("""
            INSERT INTO clientes (nombre, telefono)
            VALUES (?, ?)
            ON CONFLICT(telefono)
            DO UPDATE SET nombre = excluded.nombre
        """, (nombre, telefono))

        cliente = conexion.execute(
            "SELECT id FROM clientes WHERE telefono = ?",
            (telefono,)
        ).fetchone()

        cliente_id = cliente["id"]

        # Guardar el pedido
        cursor = conexion.execute("""
            INSERT INTO pedidos (
                fecha, cliente_id, sucursal, entrega,
                direccion, pago, notas, subtotal, envio, total
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fecha, cliente_id, sucursal, entrega,
            direccion, PAGOS[pago], notas,
            subtotal, costo_envio, total
        ))

        pedido_id = cursor.lastrowid
        folio = f"CT-{pedido_id:04d}"

        conexion.execute(
            "UPDATE pedidos SET folio = ? WHERE id = ?",
            (folio, pedido_id)
        )

        # Guardar cada alimento del pedido
        for item in items:

            conexion.execute("""
                INSERT INTO detalle_pedidos (
                    pedido_id, producto_id, nombre,
                    cantidad, precio, importe
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                pedido_id,
                item["id"],
                item["nombre"],
                item["cant"],
                item["precio"],
                item["importe"]
            ))

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()

    registro = {
        "folio": folio,
        "fecha": fecha,
        "nombre": nombre,
        "telefono": telefono,
        "sucursal": sucursal,
        "entrega": entrega,
        "direccion": direccion,
        "pago": PAGOS[pago],
        "notas": notas,
        "items": items,
        "subtotal": subtotal,
        "envio": costo_envio,
        "total": total
    }

    return render_template("confirmacion.html", p=registro)


# ---------------------------------
# LISTA DE PEDIDOS RECIBIDOS
# ---------------------------------

@app.route("/pedidos", methods=["GET"])
def pedidos():

    conexion = conectar()

    lista = conexion.execute("""
        SELECT
            pedidos.folio,
            pedidos.fecha,
            clientes.nombre,
            pedidos.sucursal,
            pedidos.entrega,
            pedidos.total
        FROM pedidos
        INNER JOIN clientes
        ON pedidos.cliente_id = clientes.id
        ORDER BY pedidos.id DESC
    """).fetchall()

    pedidos_lista = [dict(p) for p in lista]

    conexion.close()

    return render_template(
        "pedidos.html",
        pedidos=pedidos_lista
    )


# ---------------------------------
# EJECUTAR APLICACION
# ---------------------------------

crear_base_datos()

if __name__ == "__main__":
    app.run(debug=True)