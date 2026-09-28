import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { API_URL } from '../../config';
import { MAQUINAS } from '../bobinas/bobinas.component';

interface RegistroMerma {
  id: number;
  fecha: string;
  turno: string;
  maquina: string;
  referencia_producto?: string;
  proveedor_empaque?: string;
  tipo_merma: string;
  cantidad: number;
  unidad_medida: string;
  causa_raiz?: string;
  observaciones?: string;
  nombre_operario?: string;
}

interface ResumenProveedorMermaItem { proveedor: string; total_kg: number; total_und: number; registros: number; }
interface ResumenTipoMermaItem { tipo_merma: string; total_kg: number; total_und: number; registros: number; }
interface ResumenMermasOut {
  por_proveedor: ResumenProveedorMermaItem[];
  por_tipo: ResumenTipoMermaItem[];
  total_registros: number;
}

@Component({
  selector: 'app-mermas',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, RouterLinkActive],
  templateUrl: './mermas.component.html',
})
export class MermasComponent implements OnInit {

  constructor(private auth: AuthService) {}

  get nombreUsuario(): string { return this.auth.getNombre(); }
  get esAdmin(): boolean { return this.auth.isAdmin(); }

  maquinas = MAQUINAS;
  turnos = [
    { key: 'T1', label: 'Turno 1 — 6:00 a.m. a 2:00 p.m.' },
    { key: 'T2', label: 'Turno 2 — 2:00 p.m. a 10:00 p.m.' },
    { key: 'T3', label: 'Turno 3 — 10:00 p.m. a 6:00 a.m.' },
  ];
  tiposMerma = [
    { key: 'BOLSA_ROTA', label: 'Bolsa Rota' },
    { key: 'HARINA_BARRIDO', label: 'Harina Barrida' },
    { key: 'DEFECTO_SELLADO', label: 'Defecto de Sellado' },
    { key: 'SCRAP_BOBINA', label: 'Scrap de Bobina' },
    { key: 'OTRO', label: 'Otro' },
  ];

  private hoyISO(): string { return new Date().toISOString().slice(0, 10); }

  form = {
    fecha: this.hoyISO(),
    turno: '',
    maquina: '',
    referencia_producto: '',
    proveedor_empaque: '',
    tipo_merma: '',
    cantidad: null as number | null,
    unidad_medida: 'KG',
    causa_raiz: '',
    observaciones: '',
  };
  guardando = false;
  errorForm = '';

  registros: RegistroMerma[] = [];
  cargandoLista = false;

  resumen: ResumenMermasOut | null = null;
  cargandoResumen = false;

  ngOnInit(): void {
    this.cargarRegistros();
    if (this.esAdmin) this.cargarResumen();
  }

  logout(): void {
    this.auth.logout();
    window.location.href = '/login';
  }

  private authHeaders(extra: Record<string, string> = {}) {
    return { 'Authorization': `Bearer ${this.auth.getToken()}`, ...extra };
  }

  registrarMerma(): void {
    this.errorForm = '';
    if (!this.form.turno || !this.form.maquina || !this.form.tipo_merma || !this.form.cantidad || this.form.cantidad <= 0) {
      this.errorForm = 'Completa turno, máquina, tipo de merma y una cantidad mayor a cero.';
      return;
    }
    this.guardando = true;
    fetch(`${API_URL}/api/mermas/`, {
      method: 'POST',
      headers: this.authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(this.form),
    })
      .then(async r => {
        if (!r.ok) {
          const err = await r.json().catch(() => null);
          throw new Error(err?.detail || 'Error al registrar la merma');
        }
        return r.json();
      })
      .then(() => {
        this.guardando = false;
        const fecha = this.form.fecha, turno = this.form.turno, maquina = this.form.maquina;
        this.form = { fecha, turno, maquina, referencia_producto: '', proveedor_empaque: '', tipo_merma: '', cantidad: null, unidad_medida: 'KG', causa_raiz: '', observaciones: '' };
        this.cargarRegistros();
        if (this.esAdmin) this.cargarResumen();
      })
      .catch((e: Error) => {
        this.guardando = false;
        this.errorForm = e.message || 'Error al registrar la merma';
      });
  }

  cargarRegistros(): void {
    this.cargandoLista = true;
    fetch(`${API_URL}/api/mermas/?fecha=${this.form.fecha}`, { headers: this.authHeaders() })
      .then(r => r.json())
      .then(d => { this.registros = Array.isArray(d) ? d : []; this.cargandoLista = false; })
      .catch(() => { this.cargandoLista = false; });
  }

  cargarResumen(): void {
    this.cargandoResumen = true;
    fetch(`${API_URL}/api/mermas/resumen`, { headers: this.authHeaders() })
      .then(r => r.json())
      .then(d => { this.resumen = d; this.cargandoResumen = false; })
      .catch(() => { this.cargandoResumen = false; });
  }

  eliminarRegistro(id: number): void {
    if (!confirm('¿Eliminar este registro de merma?')) return;
    fetch(`${API_URL}/api/mermas/${id}`, { method: 'DELETE', headers: this.authHeaders() })
      .then(() => { this.cargarRegistros(); if (this.esAdmin) this.cargarResumen(); })
      .catch(() => alert('No se pudo eliminar'));
  }

  etiquetaTipo(key: string): string {
    return this.tiposMerma.find(t => t.key === key)?.label || key;
  }
}
