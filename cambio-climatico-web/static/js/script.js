// Colores que se van repitiendo en los sectores de la ruleta
const COLORES_RULETA = ["#0B3D42", "#66C2CE", "#F2A93B", "#E4572E"];

// Pinta el círculo de la ruleta dividiéndolo en sectores de colores,
// uno por cada idea de investigación (usa conic-gradient de CSS)
function pintarRuleta(ideas) {
  const ruleta = document.getElementById("ruleta");
  if (!ruleta) return; // si no existe el elemento en la página, no hace nada

  const porcentaje = 100 / ideas.length; // % que ocupa cada sector
  const partes = ideas.map((idea, i) => {
    const color = COLORES_RULETA[i % COLORES_RULETA.length]; // repite colores si hay más ideas que colores
    const inicio = (porcentaje * i).toFixed(2);
    const fin = (porcentaje * (i + 1)).toFixed(2);
    return `${color} ${inicio}% ${fin}%`;
  });

  ruleta.style.background = `conic-gradient(${partes.join(", ")})`;
}

// Gira la ruleta y, al terminar la animación, muestra el tema elegido al azar
function girarRuleta(ideas) {
  const ruleta = document.getElementById("ruleta");
  const resultado = document.getElementById("resultado-ruleta");
  const boton = document.getElementById("girar-ruleta");
  if (!ruleta || !resultado) return;

  boton.disabled = true;      // evita que se pueda hacer clic mientras gira
  resultado.textContent = ""; // limpia el resultado anterior

  const indiceElegido = Math.floor(Math.random() * ideas.length); // idea al azar
  // gira 5 vueltas completas + el ángulo exacto para caer en la idea elegida
  const grados = 360 * 5 + (360 - (indiceElegido * (360 / ideas.length)));

  ruleta.style.transform = `rotate(${grados}deg)`;

  // espera a que termine la animación (4.1s) antes de mostrar el resultado
  setTimeout(() => {
    resultado.textContent = "Tu tema: " + ideas[indiceElegido];
    boton.disabled = false; // vuelve a habilitar el botón
  }, 4100);
}

// Cuando carga la página: pinta la ruleta y conecta el botón "Girar"
document.addEventListener("DOMContentLoaded", () => {
  if (typeof IDEAS !== "undefined") { // IDEAS viene de index.html (lista de temas)
    pintarRuleta(IDEAS);
    const boton = document.getElementById("girar-ruleta");
    if (boton) {
      boton.addEventListener("click", () => girarRuleta(IDEAS));
    }
  }
});