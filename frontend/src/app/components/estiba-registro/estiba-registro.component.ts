import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { API_URL } from '../../config';

// Mismo catálogo de máquinas y turnos que usa Bobinas
const MAQUINAS_TRIGO = new Set(['8S', '9X', '10Y', '11Z']);
const TURNOS = [
  { key: 'T1', label: 'Turno 1 — 6:00 a.m. a 2:00 p.m.' },
  { key: 'T2', label: 'Turno 2 — 2:00 p.m. a 10:00 p.m.' },
  { key: 'T3', label: 'Turno 3 — 10:00 p.m. a 6:00 a.m.' },
];

interface InfoMaquina {
  maquina: string;
  turno: string;
  fecha: string;
  referencia_producto: string | null;
  referencia_label: string | null;
  siguiente_numero_estiva: number;
  tipo: string | null;
}

@Component({
  selector: 'app-estiba-registro',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './estiba-registro.component.html'
})
export class EstibaRegistroComponent implements OnInit {
  maquina = '';
  turno = '';
  turnos = TURNOS;

  cargandoInfo = false;
  info: InfoMaquina | null = null;
  errorMaquina = false;

  // Campos del formulario
  referenciaProducto = '';
  referenciaLabel = '';
  cantidadPacas: number | null = null;
  plancha = '';
  alto = '';
  nombreOperario = '';

  enviando = false;
  enviado = false;
  errorEnvio = '';
  numeroEstivaAsignado: number | null = null;

  constructor(private route: ActivatedRoute) {}

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      this.maquina = (params['maquina'] || '').toUpperCase();
      if (!this.maquina) {
        this.errorMaquina = true;
      }
    });
  }

  onTurnoChange(): void {
    if (!this.turno || !this.maquina) return;
    this.cargandoInfo = true;
    this.info = null;
    fetch(`${API_URL}/api/estiba/info-maquina/${this.maquina}?turno=${this.turno}`)
      .then(r => {
        if (!r.ok) throw new Error();
        return r.json();
      })
      .then((d: InfoMaquina) => {
        this.info = d;
        this.referenciaProducto = d.referencia_producto || '';
        this.referenciaLabel = d.referencia_label || '';
        this.cargandoInfo = false;
      })
      .catch(() => { this.cargandoInfo = false; });
  }

  get tipoMaquina(): 'TRIGO' | 'MAIZ' {
    return MAQUINAS_TRIGO.has(this.maquina) ? 'TRIGO' : 'MAIZ';
  }

  enviar(): void {
    if (!this.turno) { alert('Selecciona el turno.'); return; }
    if (!this.referenciaProducto) { alert('Falta la referencia — no se pudo sugerir automáticamente, escribe el código.'); return; }
    if (!this.cantidadPacas || this.cantidadPacas <= 0) { alert('Escribe la cantidad de pacas.'); return; }
    if (!this.plancha) { alert('Falta la plancha.'); return; }
    if (!this.alto) { alert('Falta el alto.'); return; }
    if (!this.nombreOperario.trim()) { alert('Escribe tu nombre.'); return; }

    this.enviando = true;
    this.errorEnvio = '';

    const payload = {
      fecha: this.info?.fecha || new Date().toISOString().slice(0, 10),
      turno: this.turno,
      maquina: this.maquina,
      referencia_producto: this.referenciaProducto,
      cantidad_pacas: this.cantidadPacas,
      plancha: this.plancha,
      alto: this.alto,
      nombre_operario_montacargas: this.nombreOperario.trim(),
    };

    fetch(`${API_URL}/api/estiba/estibas`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(res => {
        this.enviando = false;
        this.enviado = true;
        this.numeroEstivaAsignado = res.numero_estiva;
      })
      .catch(() => {
        this.enviando = false;
        this.errorEnvio = 'No se pudo enviar. Revisa tu conexión e intenta de nuevo.';
      });
  }

  registrarOtra(): void {
    this.enviado = false;
    this.cantidadPacas = null;
    this.plancha = '';
    this.alto = '';
    // Turno, referencia y nombre del operario se mantienen — lo normal es que
    // sigan haciendo estibas seguidas del mismo turno y con el mismo operario
    this.onTurnoChange();
  }
}
