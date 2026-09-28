import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { API_URL } from '../config';

const BASE = `${API_URL}/api/auth`;

export interface LoginResponse {
  access_token: string;
  token_type: string;
  rol: string;
  nombre: string;
  username: string;
  maquinas_asignadas: string;
}

export interface Usuario {
  id: number;
  nombre: string;
  cedula: string;
  username: string;
  rol: string;
  maquinas_asignadas: string;
  activo: string;
}

export interface UsuarioCreate {
  nombre: string;
  cedula: string;
  username: string;
  password: string;
  rol: string;
  maquinas_asignadas: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  constructor(private http: HttpClient) {}

  login(username: string, password: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${BASE}/login`, { username, password }).pipe(
      tap(res => {
        localStorage.setItem('token', res.access_token);
        localStorage.setItem('rol', res.rol);
        localStorage.setItem('nombre', res.nombre);
        localStorage.setItem('username', res.username);
        localStorage.setItem('maquinas', res.maquinas_asignadas);
      })
    );
  }

  logout(): void {
    localStorage.clear();
  }

  getToken(): string | null {
    return localStorage.getItem('token');
  }

  getRol(): string {
    return localStorage.getItem('rol') ?? '';
  }

  getNombre(): string {
    return localStorage.getItem('nombre') ?? '';
  }

  getMaquinas(): string {
    return localStorage.getItem('maquinas') ?? '';
  }

  isLoggedIn(): boolean {
    return !!this.getToken();
  }

  isAdmin(): boolean {
    return this.getRol() === 'admin';
  }

  isBodega(): boolean {
    return this.getRol() === 'bodega';
  }
  
  isCalidad(): boolean {
  return this.getRol() === 'calidad';
}

  // ── Gestión de usuarios (admin) ──────────────────────────────
  getUsuarios(): Observable<Usuario[]> {
    return this.http.get<Usuario[]>(`${BASE}/usuarios`);
  }

  crearUsuario(data: UsuarioCreate): Observable<Usuario> {
    return this.http.post<Usuario>(`${BASE}/usuarios`, data);
  }

  actualizarUsuario(id: number, data: Partial<UsuarioCreate & { activo: string }>): Observable<Usuario> {
    return this.http.put<Usuario>(`${BASE}/usuarios/${id}`, data);
  }

  eliminarUsuario(id: number): Observable<void> {
    return this.http.delete<void>(`${BASE}/usuarios/${id}`);
  }

  // ── Firma escaneada (se pega sola en las planillas al guardar) ───────────────
  subirFirma(userId: number, firmaImagen: string): Observable<{ firma_imagen: string | null }> {
    return this.http.put<{ firma_imagen: string | null }>(`${BASE}/usuarios/${userId}/firma`, { firma_imagen: firmaImagen });
  }

  obtenerMiFirma(): Observable<{ firma_imagen: string | null }> {
    return this.http.get<{ firma_imagen: string | null }>(`${BASE}/mi-firma`);
  }
}