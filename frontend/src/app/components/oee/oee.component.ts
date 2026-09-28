import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { API_URL } from '../../config';
import { MAQUINAS } from '../bobinas/bobinas.component';

interface RegistroParo {
  id: number;
  fecha: string;
  turno: string;
  maquina: string;
  hora_inicio: string;
  hora_fin: string;
  duracion_minutos: number;
  categoria_paro: string;
  descripcion_motivo?: string;
  requirio_mantenimiento: boolean;
  solicitud_mantenimiento_id?: number | null;
  nombre_operario?: string;
}

interface DisponibilidadMaquinaItem {
  maquina: string; turnos_trabajados: number; minutos_turno_teorico: number;
  minutos_parado: number; disponibilidad_pct: number;
}
interface ParoPorCategoriaItem { categoria_paro: string; cantidad_paros: number; minutos: number; pct_del_total: number; }
interface OEEResumenOut {
  fecha_desde: string; fecha_hasta: string;
  disponibilidad_pct: number; rendimiento_pct: number; calidad_pct: number; oee_pct: number;
  total_paros: number; minutos_totales_parada: number;
  disponibilidad_por_maquina: DisponibilidadMaquinaItem[];
  paros_por_categoria: ParoPorCategoriaItem[];
  nota_metodologia: string;
}

@Component({
  selector: 'app-oee',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, RouterLinkActive],
  templateUrl: './oee.component.html',
})
export class OeeComponent implements OnInit {

  constructor(private auth: AuthService) {}

  get nombreUsuario(): string { return this.auth.getNombre(); }
  get esAdmin(): boolean { return this.auth.isAdmin(); }

  maquinas = MAQUINAS;
  turnos = [
    { key: 'T1', label: 'Turno 1 — 6:00 a.m. a 2:00 p.m.' },
    { key: 'T2', label: 'Turno 2 — 2:00 p.m. a 10:00 p.m.' },
    { key: 'T3', label: 'Turno 3 — 10:00 p.m. a 6:00 a.m.' },
  ];
  categorias = [
    { key: 'MECANICO', label: 'Mecánico' },
    { key: 'ELECTRICO', label: 'Eléctrico' },
    { key: 'FALTA_MATERIA_PRIMA', label: 'Falta Materia Prima' },
    { key: 'CAMBIO_FORMATO', label: 'Cambio de Formato' },
    { key: 'LIMPIEZA', label: 'Limpieza' },
    { key: 'OTRO', label: 'Otro' },
  ];

  private hoyISO(): string { return new Date().toISOString().slice(0, 10); }

  form = {
    fecha: this.hoyISO(),
    turno: '',
    maquina: '',
    hora_inicio: '',
    hora_fin: '',
    categoria_paro: '',
    descripcion_motivo: '',
    requirio_mantenimiento: false,
  };
  guardando = false;
  errorForm = '';
  ultimoRegistro: RegistroParo | null = null;

  paros: RegistroParo[] = [];
  cargandoLista = false;

  resumen: OEEResumenOut | null = null;
  cargandoResumen = false;
  rangoResumen = { fecha_desde: this.hoyISO(), fecha_hasta: this.hoyISO() };

  ngOnInit(): void {
    this.cargarParos();
    if (this.esAdmin) this.cargarResumen();
  }

  logout(): void {
    this.auth.logout();
    window.location.href = '/login';
  }

  private authHeaders(extra: Record<string, string> = {}) {
    return { 'Authorization': `Bearer ${this.auth.getToken()}`, ...extra };
  }

  etiquetaCategoria(key: string): string {
    return this.categorias.find(c => c.key === key)?.label || key;
  }

  registrarParo(): void {
    this.errorForm = '';
    this.ultimoRegistro = null;
    if (!this.form.turno || !this.form.maquina || !this.form.hora_inicio || !this.form.hora_fin || !this.form.categoria_paro) {
      this.errorForm = 'Completa turno, máquina, hora de inicio, hora de fin y categoría del paro.';
      return;
    }
    this.guardando = true;
    fetch(`${API_URL}/api/oee/paros`, {
      method: 'POST',
      headers: this.authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(this.form),
    })
      .then(async r => {
        if (!r.ok) {
          const err = await r.json().catch(() => null);
          throw new Error(err?.detail || 'Error al registrar el paro');
        }
        return r.json();
      })
      .then((p: RegistroParo) => {
        this.guardando = false;
        this.ultimoRegistro = p;
        const fecha = this.form.fecha, turno = this.form.turno, maquina = this.form.maquina;
        this.form = { fecha, turno, maquina, hora_inicio: '', hora_fin: '', categoria_paro: '', descripcion_motivo: '', requirio_mantenimiento: false };
        this.cargarParos();
        if (this.esAdmin) this.cargarResumen();
      })
      .catch((e: Error) => {
        this.guardando = false;
        this.errorForm = e.message || 'Error al registrar el paro';
      });
  }

  cargarParos(): void {
    this.cargandoLista = true;
    fetch(`${API_URL}/api/oee/paros?fecha=${this.form.fecha}`, { headers: this.authHeaders() })
      .then(r => r.json())
      .then(d => { this.paros = Array.isArray(d) ? d : []; this.cargandoLista = false; })
      .catch(() => { this.cargandoLista = false; });
  }

  eliminarParo(id: number): void {
    if (!confirm('¿Eliminar este registro de paro?')) return;
    fetch(`${API_URL}/api/oee/paros/${id}`, { method: 'DELETE', headers: this.authHeaders() })
      .then(() => { this.cargarParos(); if (this.esAdmin) this.cargarResumen(); })
      .catch(() => alert('No se pudo eliminar'));
  }

  cargarResumen(): void {
    this.cargandoResumen = true;
    const qs = `fecha_desde=${this.rangoResumen.fecha_desde}&fecha_hasta=${this.rangoResumen.fecha_hasta}`;
    fetch(`${API_URL}/api/oee/resumen?${qs}`, { headers: this.authHeaders() })
      .then(r => r.json())
      .then(d => { this.resumen = d; this.cargandoResumen = false; })
      .catch(() => { this.cargandoResumen = false; });
  }

  colorPct(pct: number): string {
    if (pct >= 85) return 'text-emerald-600';
    if (pct >= 60) return 'text-amber-600';
    return 'text-brand-red';
  }
}
