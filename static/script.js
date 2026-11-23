const form = document.getElementById('form-pedido');
const fmt = n => '$' + n;

function actualizarResumen() {
  const lista = document.getElementById('lista-resumen');
  let subtotal = 0, html = '';
  document.querySelectorAll('.item').forEach(item => {
    const input = item.querySelector('input');
    const cant = parseInt(input.value, 10) || 0;
    item.classList.toggle('activo', cant > 0);
    if (cant > 0) {
      const importe = cant * parseInt(item.dataset.precio, 10);
      subtotal += importe;
      const nombre = item.querySelector('strong').textContent;
      html += `<li><span>${cant} × ${nombre}</span><span>${fmt(importe)}</span></li>`;
    }
  });
  lista.innerHTML = html || '<li class="vacio">Aún no agregas nada.</li>';
  const domicilio = form.querySelector('input[name=entrega]:checked')?.value === 'domicilio';
  const envio = domicilio && subtotal > 0 ? window.ENVIO : 0;
  document.getElementById('subtotal').textContent = fmt(subtotal);
  document.getElementById('envio').textContent = fmt(envio);
  document.getElementById('total').textContent = fmt(subtotal + envio);
  return subtotal;
}

document.querySelectorAll('.item').forEach(item => {
  const input = item.querySelector('input');
  item.querySelector('.mas').addEventListener('click', () => {
    input.value = Math.min(20, (parseInt(input.value, 10) || 0) + 1); actualizarResumen();
  });
  item.querySelector('.menos').addEventListener('click', () => {
    input.value = Math.max(0, (parseInt(input.value, 10) || 0) - 1); actualizarResumen();
  });
});

const campoDir = document.getElementById('campo-direccion');
function alternarDireccion() {
  const dom = form.querySelector('input[name=entrega]:checked')?.value === 'domicilio';
  campoDir.hidden = !dom;
  actualizarResumen();
}
form.querySelectorAll('input[name=entrega]').forEach(r => r.addEventListener('change', alternarDireccion));

const notas = document.getElementById('notas');
const cuenta = document.getElementById('cuenta');
notas.addEventListener('input', () => cuenta.textContent = notas.value.length);
document.getElementById('telefono').addEventListener('input', e => {
  e.target.value = e.target.value.replace(/\D/g, '').slice(0, 10);
});

function mostrar(campo, msg) {
  const err = document.getElementById('err-' + campo);
  const el = document.getElementById(campo);
  if (err) err.textContent = msg;
  if (el) el.classList.toggle('invalido', !!msg);
}

form.addEventListener('submit', e => {
  const v = id => form.elements[id].value.trim();
  const dom = form.querySelector('input[name=entrega]:checked')?.value === 'domicilio';
  const reglas = {
    nombre:    v('nombre').length < 3 ? 'Escribe tu nombre completo (mínimo 3 letras).' : '',
    telefono:  !/^\d{10}$/.test(v('telefono')) ? 'El teléfono debe tener 10 dígitos.' : '',
    sucursal:  !v('sucursal') ? 'Elige la sucursal que prepara tu pedido.' : '',
    direccion: dom && v('direccion').length < 8 ? 'Escribe calle, número y colonia para el envío.' : '',
    pago:      !v('pago') ? 'Elige un método de pago.' : ''
  };
  let hayError = false;
  for (const [campo, msg] of Object.entries(reglas)) { mostrar(campo, msg); if (msg) hayError = true; }

  const sinEntrega = !form.querySelector('input[name=entrega]:checked');
  document.getElementById('err-entrega').textContent = sinEntrega ? 'Elige cómo recibirás tu pedido.' : '';
  const sinItems = actualizarResumen() === 0;
  document.getElementById('err-items').textContent = sinItems ? 'Agrega al menos un platillo o bebida a tu pedido.' : '';

  if (hayError || sinEntrega || sinItems) {
    e.preventDefault();
    document.querySelector('.error:not(:empty)')?.scrollIntoView({behavior: 'smooth', block: 'center'});
  }
});

cuenta.textContent = notas.value.length;
alternarDireccion();
