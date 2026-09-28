import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  RegistroBobinas,
  RegistroRotulado,
  RegistroPesos,
  RegistroPesoEnfardadora
} from '../models/formatos.model';
import { API_URL } from '../config';

const BASE = `${API_URL}/api`;

@Injectable({ providedIn: 'root' })
export class FormatosService {
  constructor(private http: HttpClient) {}

  // ── BOBINAS ──────────────────────────────────────────────────
  getBobinas(): Observable<RegistroBobinas[]> {
    return this.http.get<RegistroBobinas[]>(`${BASE}/bobinas/`);
  }
  createBobinas(data: RegistroBobinas): Observable<RegistroBobinas> {
    return this.http.post<RegistroBobinas>(`${BASE}/bobinas/`, data);
  }
  updateBobinas(id: number, data: RegistroBobinas): Observable<RegistroBobinas> {
    return this.http.put<RegistroBobinas>(`${BASE}/bobinas/${id}`, data);
  }

  // ── ROTULADO ─────────────────────────────────────────────────
  getRotulado(): Observable<RegistroRotulado[]> {
    return this.http.get<RegistroRotulado[]>(`${BASE}/rotulado/`);
  }
  createRotulado(data: RegistroRotulado): Observable<RegistroRotulado> {
    return this.http.post<RegistroRotulado>(`${BASE}/rotulado/`, data);
  }
  updateRotulado(id: number, data: RegistroRotulado): Observable<RegistroRotulado> {
    return this.http.put<RegistroRotulado>(`${BASE}/rotulado/${id}`, data);
  }

  // ── PESOS ────────────────────────────────────────────────────
  getPesos(): Observable<RegistroPesos[]> {
    return this.http.get<RegistroPesos[]>(`${BASE}/pesos/`);
  }
  createPesos(data: RegistroPesos): Observable<RegistroPesos> {
    return this.http.post<RegistroPesos>(`${BASE}/pesos/`, data);
  }
  updatePesos(id: number, data: RegistroPesos): Observable<RegistroPesos> {
    return this.http.put<RegistroPesos>(`${BASE}/pesos/${id}`, data);
  }

  // ── CONTROL DE PESO — ENFARDADORAS ────────────────────────────
  getPesosEnfardadora(): Observable<RegistroPesoEnfardadora[]> {
    return this.http.get<RegistroPesoEnfardadora[]>(`${BASE}/pesos-enfardadora/`);
  }
  createPesosEnfardadora(data: RegistroPesoEnfardadora): Observable<RegistroPesoEnfardadora> {
    return this.http.post<RegistroPesoEnfardadora>(`${BASE}/pesos-enfardadora/`, data);
  }
  updatePesosEnfardadora(id: number, data: RegistroPesoEnfardadora): Observable<RegistroPesoEnfardadora> {
    return this.http.put<RegistroPesoEnfardadora>(`${BASE}/pesos-enfardadora/${id}`, data);
  }
}
