// URL base del backend (FastAPI). Es el ÚNICO lugar que hay que editar si el
// backend corre en otra máquina/servidor — todo el resto del código importa
// esta constante en vez de tener la URL escrita a mano en cada archivo.
//
// - Si el backend y el navegador corren en el mismo equipo: dejar 'http://localhost:8000'.
// - Si el backend corre en un servidor aparte (ej. para que tablets/otras
//   máquinas lo abran en red): cambiar por 'http://<IP-o-dominio-del-servidor>:8000'.
export const API_URL = 'http://localhost:8000';
