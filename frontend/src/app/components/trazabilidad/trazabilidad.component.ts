import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { API_URL } from '../../config';
import { MAQUINAS } from '../bobinas/bobinas.component';

interface RecepcionMateriaPrima {
  id: number;
  fecha: string;
  tipo_grano: string;
  proveedor: string;
  lote_proveedor?: string;
  placa_vehiculo?: string;
  cantidad_kg: number;
  silo_destino: string;
  humedad_pct?: number;
  impurezas_pct?: number;
  peso_especifico?: number;
  resultado_calidad: string;
  observaciones_calidad?: string;
  nombre_registrado_por?: string;
}

interface ResumenTrazabilidad {
  total_recepciones: number;
  kg_totales_mes: number;
  pct_aprobado: number;
  silos_activos: string[];
}

interface BobinaResumenItem {
  id: number; turno?: string; referencia_producto?: string; proveedor?: string;
  nombre_operario?: string; materiales_empaque: string[]; kg_consumidos: number;
}
interface RotuladoResumenItem {
  id: number; nombre_operario?: string; total_fechados: number; fechados_cumplen: number; fechados_no_cumplen: number;
}
interface EstibaResumenItem {
  id: number; turno?: string; numero_estiva: number; referencia_producto?: string;
  cantidad_pacas?: number; nombre_operario_montacargas?: string;
}
interface ConsultaTrazabilidadOut {
  fecha: string; maquina: string; tipo_grano: string;
  bobinas: BobinaResumenItem[]; rotulado: RotuladoResumenItem[]; estibas: EstibaResumenItem[];
  materia_prima_aproximada: RecepcionMateriaPrima[];
  nota: string;
}

@Component({
  selector: 'app-trazabilidad',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, RouterLinkActive],
  templateUrl: './trazabilidad.component.html',
})
export class TrazabilidadComponent implements OnInit {

  constructor(private auth: AuthService) {}

  get nombreUsuario(): string { return this.auth.getNombre(); }
  get esAdmin(): boolean { return this.auth.isAdmin(); }

  maquinas = MAQUINAS;

  private hoyISO(): string { return new Date().toISOString().slice(0, 10); }

  private authHeaders(extra: Record<string, string> = {}) {
    return { 'Authorization': `Bearer ${this.auth.getToken()}`, ...extra };
  }

  logout(): void {
    this.auth.logout();
    window.location.href = '/login';
  }

  // ── Registro de recepción de materia prima ──────────────────────────────────
  form = {
    fecha: this.hoyISO(),
    tipo_grano: '',
    proveedor: '',
    lote_proveedor: '',
    placa_vehiculo: '',
    cantidad_kg: null as number | null,
    silo_destino: '',
    humedad_pct: null as number | null,
    impurezas_pct: null as number | null,
    peso_especifico: null as number | null,
    resultado_calidad: 'APROBADO',
    observaciones_calidad: '',
  };
  guardando = false;
  errorForm = '';

  registrarRecepcion(): void {
    this.errorForm = '';
    if (!this.form.tipo_grano || !this.form.proveedor.trim() || !this.form.cantidad_kg || !this.form.silo_destino.trim()) {
      this.errorForm = 'Completa tipo de grano, proveedor, cantidad y silo de destino.';
      return;
    }
    this.guardando = true;
    fetch(`${API_URL}/api/trazabilidad/recepciones`, {
      method: 'POST',
      headers: this.authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(this.form),
    })
      .then(async r => {
        if (!r.ok) {
          const err = await r.json().catch(() => null);
          throw new Error(err?.detail || 'Error al registrar la recepción');
        }
        return r.json();
      })
      .then(() => {
        this.guardando = false;
        const fecha = this.form.fecha;
        this.form = { fecha, tipo_grano: '', proveedor: '', lote_proveedor: '', placa_vehiculo: '', cantidad_kg: null, silo_destino: '', humedad_pct: null, impurezas_pct: null, peso_especifico: null, resultado_calidad: 'APROBADO', observaciones_calidad: '' };
        this.cargarRecepciones();
        this.cargarResumen();
      })
      .catch((e: Error) => {
        this.guardando = false;
        this.errorForm = e.message || 'Error al registrar la recepción';
      });
  }

  recepciones: RecepcionMateriaPrima[] = [];
  cargandoRecepciones = false;

  cargarRecepciones(): void {
    this.cargandoRecepciones = true;
    fetch(`${API_URL}/api/trazabilidad/recepciones`, { headers: this.authHeaders() })
      .then(r => r.json())
      .then(d => { this.recepciones = Array.isArray(d) ? d.slice(0, 20) : []; this.cargandoRecepciones = false; })
      .catch(() => { this.cargandoRecepciones = false; });
  }

  eliminarRecepcion(id: number): void {
    if (!confirm('¿Eliminar esta recepción de materia prima?')) return;
    fetch(`${API_URL}/api/trazabilidad/recepciones/${id}`, { method: 'DELETE', headers: this.authHeaders() })
      .then(() => { this.cargarRecepciones(); this.cargarResumen(); })
      .catch(() => alert('No se pudo eliminar'));
  }

  resumen: ResumenTrazabilidad | null = null;

  cargarResumen(): void {
    fetch(`${API_URL}/api/trazabilidad/resumen`, { headers: this.authHeaders() })
      .then(r => r.json())
      .then(d => { this.resumen = d; })
      .catch(() => {});
  }

  // ── Consulta de trazabilidad (árbol Materia Prima → Empaque → Estibas) ──────
  consulta = { fecha: this.hoyISO(), maquina: '' };
  consultando = false;
  errorConsulta = '';
  resultadoConsulta: ConsultaTrazabilidadOut | null = null;

  consultarTrazabilidad(): void {
    this.errorConsulta = '';
    this.resultadoConsulta = null;
    if (!this.consulta.fecha || !this.consulta.maquina) {
      this.errorConsulta = 'Elige una fecha y una máquina.';
      return;
    }
    this.consultando = true;
    const qs = `fecha=${this.consulta.fecha}&maquina=${encodeURIComponent(this.consulta.maquina)}`;
    fetch(`${API_URL}/api/trazabilidad/consulta?${qs}`, { headers: this.authHeaders() })
      .then(async r => {
        if (!r.ok) {
          const err = await r.json().catch(() => null);
          throw new Error(err?.detail || 'Error al consultar la trazabilidad');
        }
        return r.json();
      })
      .then((d: ConsultaTrazabilidadOut) => { this.consultando = false; this.resultadoConsulta = d; })
      .catch((e: Error) => { this.consultando = false; this.errorConsulta = e.message; });
  }

  ngOnInit(): void {
    this.cargarRecepciones();
    this.cargarResumen();
  }
}
