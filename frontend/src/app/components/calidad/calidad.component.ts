import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { API_URL } from '../../config';

interface MuestraCalidadItem {
  id: number;
  numero_muestra: number;
  turno_origen: string;
  maquina_origen: string;
  hora_origen: string;
  posicion_muestra: number;
  valor_peso: number;
  cumple: string;
  observaciones_calidad: string | null;
}

interface MuestreoCalidadResumen {
  id: number;
  fecha: string;
  referencia: string;
  cantidad_solicitada: number;
  cantidad_encontrada: number;
  nombre_generado_por: string | null;
  creado_en: string | null;
  pct_cumple: number;
}

interface MuestreoCalidadDetalle {
  id: number;
  fecha: string;
  referencia: string;
  cantidad_solicitada: number;
  cantidad_encontrada: number;
  nombre_generado_por: string | null;
  creado_en: string | null;
  items: MuestraCalidadItem[];
}

@Component({
  selector: 'app-calidad',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, RouterLinkActive],
  templateUrl: './calidad.component.html',
})
export class CalidadComponent implements OnInit {

  constructor(private auth: AuthService) {}

  get nombreUsuario(): string { return this.auth.getNombre(); }
  get esAdmin(): boolean { return this.auth.isAdmin(); }

  ngOnInit(): void {
    this.cargarMuestreos();
    this.cargarReferenciasDisponibles();
  }

  logout(): void {
    this.auth.logout();
    window.location.href = '/login';
  }

  generarPDF(): void { setTimeout(() => window.print(), 150); }

  private hoyISO(): string {
    return new Date().toISOString().slice(0, 10);
  }

  // ── Muestreo de Calidad ──────────────────────────────────────────────────────
  formMuestreo = { fecha: this.hoyISO(), referencia: '', cantidad_solicitada: 98 };
  generandoMuestreo = false;
  errorMuestreo = '';
  muestreos: MuestreoCalidadResumen[] = [];
  muestreoDetalle: MuestreoCalidadDetalle | null = null;
  referenciasDisponibles: { codigo: string; descripcion: string }[] = [];
  cargandoReferencias = false;

  cargarReferenciasDisponibles(): void {
    if (!this.formMuestreo.fecha) return;
    this.cargandoReferencias = true;
    fetch(`${API_URL}/api/calidad/referencias-disponibles?fecha=${this.formMuestreo.fecha}`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => {
        this.referenciasDisponibles = Array.isArray(d) ? d : [];
        // Si la referencia elegida ya no está disponible para la nueva fecha, se limpia
        if (this.formMuestreo.referencia && !this.referenciasDisponibles.some(r => r.codigo === this.formMuestreo.referencia)) {
          this.formMuestreo.referencia = '';
        }
        this.cargandoReferencias = false;
      })
      .catch(() => { this.cargandoReferencias = false; });
  }


  generarMuestreo(): void {
    this.errorMuestreo = '';
    if (!this.formMuestreo.fecha || !this.formMuestreo.referencia.trim()) {
      this.errorMuestreo = 'Completa la fecha y la referencia.';
      return;
    }
    this.generandoMuestreo = true;
    fetch(`${API_URL}/api/calidad/muestreos/generar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${this.auth.getToken()}` },
      body: JSON.stringify(this.formMuestreo)
    })
      .then(async r => {
        if (!r.ok) {
          const err = await r.json().catch(() => null);
          throw new Error(err?.detail || 'Error al generar el muestreo');
        }
        return r.json();
      })
      .then((m: MuestreoCalidadDetalle) => {
        this.generandoMuestreo = false;
        this.muestreoDetalle = m;
        this.cargarMuestreos();
      })
      .catch((e: Error) => {
        this.generandoMuestreo = false;
        this.errorMuestreo = e.message || 'Error al generar el muestreo';
      });
  }

  cargarMuestreos(): void {
    fetch(`${API_URL}/api/calidad/muestreos`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => { this.muestreos = Array.isArray(d) ? d : []; })
      .catch(() => {});
  }

  verMuestreo(id: number): void {
    fetch(`${API_URL}/api/calidad/muestreos/${id}`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => { this.muestreoDetalle = d; })
      .catch(() => alert('No se pudo cargar el muestreo'));
  }

  guardarObservacionMuestra(it: MuestraCalidadItem): void {
    fetch(`${API_URL}/api/calidad/muestras/${it.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${this.auth.getToken()}` },
      body: JSON.stringify({ observaciones_calidad: it.observaciones_calidad })
    }).catch(() => {});
  }
}