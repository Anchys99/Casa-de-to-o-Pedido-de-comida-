import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

MENU = [
    {"id": "pozole",     "nombre": "Pozole rojo",        "desc": "Maíz cacahuazintle, cerdo, lechuga y rábano", "precio": 95, "cat": "Platillos"},
    {"id": "sopes",      "nombre": "Sopes (3 pzas)",     "desc": "Frijol, carne a elegir, queso y crema",       "precio": 70, "cat": "Platillos"},
    {"id": "enchiladas", "nombre": "Enchiladas verdes",  "desc": "Pollo, salsa verde, crema y queso fresco",   "precio": 85, "cat": "Platillos"},
    {"id": "tostadas",   "nombre": "Tostadas de tinga",  "desc": "Tinga de pollo, lechuga y aguacate",          "precio": 60, "cat": "Platillos"},
    {"id": "quesadillas","nombre": "Quesadillas (3)",    "desc": "Masa azul con queso Oaxaca",                  "precio": 65, "cat": "Platillos"},
    {"id": "tamales",    "nombre": "Tamal oaxaqueño",    "desc": "Mole negro con pollo, hoja de plátano",       "precio": 35, "cat": "Platillos"},
    {"id": "horchata",   "nombre": "Agua de horchata",   "desc": "Vaso grande, con canela",                     "precio": 35, "cat": "Bebidas"},
    {"id": "cafe",       "nombre": "Café de olla",       "desc": "Piloncillo y canela",                         "precio": 30, "cat": "Bebidas"},
    {"id": "atole",      "nombre": "Atole de vainilla",  "desc": "Caliente, espeso y dulce",                    "precio": 30, "cat": "Bebidas"},
]
PRECIOS = {p["id"]: p for p in MENU}
ENVIO = 30
PAGOS = {"efectivo": "Efectivo", "tarjeta": "Tarjeta", "transferencia": "Transferencia"}
SUCURSALES = ["Centro", "Coyoacán", "Polanco", "Tlalpan", "Satélite"]

PEDIDOS = []  


@app.route("/", methods=["GET"])
def index():
    """GET: muestra el formulario de pedido."""
    return render_template("index.html", menu=MENU, sucursales=SUCURSALES,
                           pagos=PAGOS, envio=ENVIO, datos={}, errores={})


@app.route("/pedido", methods=["POST"])
def pedido():
    """POST: recibe, valida y procesa el pedido con request.form.get()."""
    nombre = (request.form.get("nombre") or "").strip()
    telefono = re.sub(r"\D", "", request.form.get("telefono", ""))
    sucursal = request.form.get("sucursal", "")
    entrega = request.form.get("entrega", "")
    direccion = (request.form.get("direccion") or "").strip()
    pago = request.form.get("pago", "")
    notas = (request.form.get("notas") or "").strip()

    errores = {}
    if len(nombre) < 3:
        errores["nombre"] = "Escribe tu nombre completo (mínimo 3 letras)."
    if not re.fullmatch(r"\d{10}", telefono):
        errores["telefono"] = "El teléfono debe tener 10 dígitos."
    if sucursal not in SUCURSALES:
        errores["sucursal"] = "Elige la sucursal que prepara tu pedido."
    if entrega not in ("sucursal", "domicilio"):
        errores["entrega"] = "Elige cómo recibirás tu pedido."
    if entrega == "domicilio" and len(direccion) < 8:
        errores["direccion"] = "Escribe calle, número y colonia para el envío."
    if pago not in PAGOS:
        errores["pago"] = "Elige un método de pago."
    if len(notas) > 200:
        errores["notas"] = "Las notas no pueden pasar de 200 caracteres."

    items, subtotal = [], 0
    for pid, prod in PRECIOS.items():
        try:
            cant = int(request.form.get(f"qty_{pid}", 0))
        except ValueError:
            cant = 0
        cant = max(0, min(cant, 20))
        if cant:
            importe = cant * prod["precio"]
            subtotal += importe
            items.append({"nombre": prod["nombre"], "cant": cant, "importe": importe})
    if not items:
        errores["items"] = "Agrega al menos un platillo o bebida a tu pedido."

    if errores:
        return render_template("index.html", menu=MENU, sucursales=SUCURSALES,
                               pagos=PAGOS, envio=ENVIO, datos=request.form,
                               errores=errores), 400

    costo_envio = ENVIO if entrega == "domicilio" else 0
    registro = {
        "folio": f"CT-{len(PEDIDOS) + 1:04d}",
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "nombre": nombre, "telefono": telefono, "sucursal": sucursal,
        "entrega": entrega, "direccion": direccion, "pago": PAGOS[pago],
        "notas": notas, "items": items, "subtotal": subtotal,
        "envio": costo_envio, "total": subtotal + costo_envio,
    }
    PEDIDOS.append(registro)
    return render_template("confirmacion.html", p=registro)


@app.route("/pedidos", methods=["GET"])
def pedidos():
    """GET: lista de pedidos recibidos (para la demostración en clase)."""
    return render_template("pedidos.html", pedidos=reversed(PEDIDOS))


if __name__ == "__main__":
    app.run(debug=True)
