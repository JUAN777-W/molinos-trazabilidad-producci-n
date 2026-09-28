import { Component, OnInit, OnDestroy, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink, RouterLinkActive } from '@angular/router';
import { FormatosService } from '../../services/formatos.service';
import { AuthService } from '../../services/auth.service';
import { RegistroPesoEnfardadora, FilaPesoEnfardadora } from '../../models/formatos.model';
import { API_URL } from '../../config';

const HORAS = [
  '6:00-7:00 a.m.','7:00-8:00 a.m.','8:00-9:00 a.m.','9:00-10:00 a.m.',
  '10:00-11:00 a.m.','11:00-12:00 p.m.','12:00-13:00 p.m.','13:00-14:00 p.m.',
  '14:00-15:00 p.m.','15:00-16:00 p.m.','16:00-17:00 p.m.','17:00-18:00 p.m.',
  '18:00-19:00 p.m.','19:00-20:00 p.m.','20:00-21:00 p.m.','21:00-22:00 p.m.',
  '22:00-23:00 p.m.','23:00-24:00 a.m.','24:00-1:00 a.m.','1:00-2:00 a.m.',
  '2:00-3:00 a.m.','3:00-4:00 a.m.','4:00-5:00 a.m.','5:00-6:00 a.m.'
];

// Cada turno cubre 8 horas dentro del arreglo de 24h — T1 empieza en 6am.
const RANGO_HORAS_POR_TURNO: Record<string, [number, number]> = {
  T1: [0, 8], T2: [8, 16], T3: [16, 24],
};

function horasDelTurno(turno: string): string[] {
  const rango = RANGO_HORAS_POR_TURNO[turno] ?? RANGO_HORAS_POR_TURNO['T1'];
  return HORAS.slice(rango[0], rango[1]);
}

export const NUM_MUESTRAS = 15;
export const MUESTRA_KEYS = Array.from({ length: NUM_MUESTRAS }, (_, i) => `muestra_${i + 1}`);

// Mapa fijo de qué máquinas alimentan cada enfardadora física. La enfardadora
// no tiene su propio código de máquina — se identifica por la pareja (o
// máquina sola) de empacadoras conectada a ella. La 4T no tiene enfardadora.
const MAPA_ENFARDADORAS: Record<string, string> = {
  '1P-2Q': 'Enfardadora 1 (Maíz)',
  '5U-6V': 'Enfardadora 2 (Maíz)',
  '7W': 'Enfardadora 3 (Maíz)',
  '8S-9X': 'Enfardadora 1 (Trigo)',
  '10Y-11Z': 'Enfardadora 2 (Trigo)',
};

function claveMaquinas(maquinaA: string, maquinaB?: string | null): string {
  if (!maquinaA) return '';
  return maquinaB ? [maquinaA, maquinaB].sort().join('-') : maquinaA;
}

/** Nombre legible de la enfardadora según la(s) máquina(s) conectada(s), o null si esa máquina no tiene enfardadora (ej. 4T) */
export function enfardadoraDe(maquinaA: string, maquinaB?: string | null): string | null {
  const clave = claveMaquinas(maquinaA, maquinaB);
  return MAPA_ENFARDADORAS[clave] ?? null;
}

type Fila = FilaPesoEnfardadora & { _clases: string[] };

function nuevasFilas(turno = ''): Fila[] {
  return horasDelTurno(turno).map((h, i) => {
    const fila: any = {
      numero_fila: i, hora: h,
      observaciones: '',
      _clases: Array(NUM_MUESTRAS).fill(''),
    };
    MUESTRA_KEYS.forEach(k => fila[k] = null);
    return fila as Fila;
  });
}

@Component({
  selector: 'app-pesos-enfardadora',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, RouterLinkActive],
  templateUrl: './pesos-enfardadora.component.html'
})
export class PesosEnfardadoraComponent implements OnInit, OnDestroy {
  fecha = ''; turno = '';
  turnos = [
    { key: 'T1', label: 'Turno 1 — 6:00 a.m. a 2:00 p.m.' },
    { key: 'T2', label: 'Turno 2 — 2:00 p.m. a 10:00 p.m.' },
    { key: 'T3', label: 'Turno 3 — 10:00 p.m. a 6:00 a.m.' },
  ];
  nombre_operario = '';
  firma_data = '';
  firmaAutomatica = false;
  cargandoFirma = false;
  toast = ''; toastTimer: any;
  muestraIndices = Array.from({ length: NUM_MUESTRAS }, (_, i) => i);

  maquinaA = '';
  maquinaB: string | null = null;
  enfardadora = '';        // etiqueta legible, ej. "Enfardadora 1 (Maíz)"
  referencia = '';         // ancho de fardo, heredado de Bobinas
  filas: Fila[] = nuevasFilas();
  registroId: number | null = null;

  /** true si la máquina activa en Bobinas no tiene enfardadora asociada (ej. 4T) */
  sinEnfardadora = false;

  camposDesdeBobinas = false;
  soloLectura = false;
  cargandoRegistroGuardado = false;

  /** PRO y lote de exportación — los asigna el admin desde Informes; si están
   *  presentes, se usan para nombrar el PDF al generarlo. */
  pro_numero = '';
  lote = '';

  constructor(private svc: FormatosService, private auth: AuthService, private route: ActivatedRoute) {}

  get esAdmin(): boolean { return this.auth.isAdmin(); }

  ngOnInit(): void {
    const verId = this.route.snapshot.queryParamMap.get('verId');
    if (verId) {
      this.soloLectura = true;
      this.cargarRegistroGuardado(+verId);
      return;
    }
    this.cargarMiFirma();
    this.restaurarBorrador();
    this.cargarContextoCompartido();
    this.nombre_operario = this.auth.getNombre();
  }

  get horasTurnoActual(): string[] { return horasDelTurno(this.turno); }

  turnoLabel(key: string): string {
    return this.turnos.find(t => t.key === key)?.label ?? key;
  }

  private regenerarHoras(): void {
    const tieneAlgo = this.filas.some(f =>MUESTRA_KEYS.some(k => (f as any)[k] != null));
    if (!tieneAlgo) this.filas = nuevasFilas(this.turno);
  }

  private cargarRegistroGuardado(id: number): void {
    this.cargandoRegistroGuardado = true;
    fetch(`${API_URL}/api/pesos-enfardadora/${id}`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then((reg: RegistroPesoEnfardadora) => {
        this.fecha = reg.fecha || '';
        this.turno = reg.turno || '';
        this.enfardadora = reg.enfardadora || '';
        this.referencia = reg.referencia || '';
        this.nombre_operario = reg.nombre_operario || '';
        this.firma_data = reg.firma_data || '';
        this.firmaAutomatica = !!reg.firma_data;
        this.camposDesdeBobinas = true;
        this.pro_numero = reg.pro_numero || '';
        this.lote = reg.lote || '';
        this.filas = (reg.filas || []).map(f => ({ ...f, _clases: Array(NUM_MUESTRAS).fill('') })) as Fila[];
        this.registroId = reg.id ?? null;
        this.cargandoRegistroGuardado = false;
      })
      .catch(() => { this.cargandoRegistroGuardado = false; });
  }

  ngOnDestroy(): void {
    if (!this.soloLectura) this.guardarBorrador();
  }

  // ngOnDestroy no siempre se alcanza a ejecutar en una recarga real del
  // navegador (F5, deslizar para refrescar, cerrar la pestaña) — el motor de
  // JavaScript se puede cortar antes de que Angular termine de limpiar. Estos
  // dos eventos sí se disparan de forma confiable en esos casos, así que
  // guardamos el borrador ahí también para no perder lo que llevaba escrito.
  @HostListener('window:beforeunload')
  @HostListener('document:visibilitychange')
  private guardarAntesDeSalir(): void {
    if (!this.soloLectura) this.guardarBorrador();
  }

  private readonly DRAFT_KEY = 'borrador_pesos_enfardadora';

  private guardarBorrador(): void {
    const vacio = !this.fecha && !this.turno && !this.maquinaA;
    if (vacio) {
      localStorage.removeItem(this.DRAFT_KEY);
      return;
    }
    const snapshot = {
      fecha: this.fecha, turno: this.turno, nombre_operario: this.nombre_operario,
      maquinaA: this.maquinaA, maquinaB: this.maquinaB, enfardadora: this.enfardadora,
      referencia: this.referencia, filas: this.filas, registroId: this.registroId,
    };
    localStorage.setItem(this.DRAFT_KEY, JSON.stringify(snapshot));
  }

  private restaurarBorrador(): void {
    const raw = localStorage.getItem(this.DRAFT_KEY);
    if (!raw) return;
    try {
      const s = JSON.parse(raw);
      this.fecha = s.fecha ?? '';
      this.turno = s.turno ?? '';
      this.nombre_operario = s.nombre_operario ?? '';
      this.maquinaA = s.maquinaA ?? '';
      this.maquinaB = s.maquinaB ?? null;
      this.enfardadora = s.enfardadora ?? '';
      this.referencia = s.referencia ?? '';
      this.filas = (s.filas && s.filas.length) ? s.filas : this.filas;
      this.registroId = s.registroId ?? null;
    } catch { /* borrador corrupto: se ignora */ }
  }

  private limpiarBorrador(): void {
    localStorage.removeItem(this.DRAFT_KEY);
  }

  cargarContextoCompartido(): void {
    const raw = localStorage.getItem('contexto_activo_turno');
    if (!raw) return;
    try {
      const ctx = JSON.parse(raw);
      const esReciente = ctx.actualizado_en && (Date.now() - ctx.actualizado_en) < 16 * 60 * 60 * 1000;
      if (!esReciente) return;

      if (ctx.fecha) this.fecha = ctx.fecha;
      if (ctx.turno) this.turno = ctx.turno;
      this.regenerarHoras();

      if (ctx.maquina) {
        this.maquinaA = ctx.maquina;
        this.maquinaB = ctx.maquinaB || null;
        const nombre = enfardadoraDe(this.maquinaA, this.maquinaB);
        this.sinEnfardadora = !nombre;
        this.enfardadora = nombre ?? '';
        if (ctx.referencia_enfardadora) this.referencia = ctx.referencia_enfardadora;
        this.camposDesdeBobinas = true;
      }
    } catch { /* contexto corrupto: se ignora */ }
  }

  cargarMiFirma(): void {
    this.cargandoFirma = true;
    this.auth.obtenerMiFirma().subscribe({
      next: (res) => {
        this.cargandoFirma = false;
        if (res?.firma_imagen) {
          this.firma_data = res.firma_imagen;
          this.firmaAutomatica = true;
        } else {
          this.firma_data = '';
          this.firmaAutomatica = false;
        }
      },
      error: () => { this.cargandoFirma = false; }
    });
  }

  getMuestra(f: Fila, idx: number): number | null {
    return (f as any)[MUESTRA_KEYS[idx]] ?? null;
  }

  onMuestraChange(f: Fila, idx: number, valor: number | null): void {
    (f as any)[MUESTRA_KEYS[idx]] = valor;
  }

  camposFaltantes: string[] = [];
  alertaConsistencia: string | null = null;

  private validarCamposObligatorios(): string[] {
    const faltan: string[] = [];
    if (!this.fecha) faltan.push('Fecha');
    if (!this.turno) faltan.push('Turno');
    if (!this.maquinaA) faltan.push('Máquina (selecciónala primero en Bobinas)');
    if (!this.referencia) faltan.push('Referencia de fardo (selecciónala primero en Bobinas)');
    if (!this.firma_data) faltan.push('Firma del Operario (pide al administrador que registre tu firma)');
    return faltan;
  }

  async guardar(): Promise<void> {
    this.alertaConsistencia = null;
    this.camposFaltantes = [];

    const faltan = this.validarCamposObligatorios();
    if (faltan.length > 0) {
      this.camposFaltantes = faltan;
      this.alertaConsistencia = 'Antes de guardar, completa estos campos obligatorios:';
      return;
    }

    const payload: RegistroPesoEnfardadora = {
      fecha: this.fecha, turno: this.turno,
      enfardadora: this.enfardadora,
      maquinas: this.maquinaB ? `${this.maquinaA}-${this.maquinaB}` : this.maquinaA,
      referencia: this.referencia,
      nombre_operario: this.nombre_operario, firma_data: this.firma_data,
      filas: this.filas.map(f => {
        const out: any = { numero_fila: f.numero_fila, hora: f.hora, observaciones: f.observaciones };
        MUESTRA_KEYS.forEach(k => out[k] = (f as any)[k]);
        return out;
      })
    };

    try {
      if (this.registroId) {
        await this.svc.updatePesosEnfardadora(this.registroId, payload).toPromise();
      } else {
        const res: any = await this.svc.createPesosEnfardadora(payload).toPromise();
        this.registroId = res.id!;
      }
      this.limpiarBorrador();
      this.mostrarToast('Guardado');
    } catch {
      this.mostrarToast('Error al guardar — revisa tu conexión e intenta de nuevo');
    }
  }

  limpiar(): void {
    if (!confirm('¿Limpiar todos los datos del turno?')) return;
    this.fecha = ''; this.turno = '';
    this.nombre_operario = this.auth.getNombre();
    this.maquinaA = ''; this.maquinaB = null; this.enfardadora = ''; this.referencia = '';
    this.filas = nuevasFilas();
    this.registroId = null;
    this.camposDesdeBobinas = false;
    this.cargarMiFirma();
    this.limpiarBorrador();
    this.cargarContextoCompartido();
    this.mostrarToast('Turno limpiado');
  }

  generarPDF(): void {
    const tituloOriginal = document.title;
    if (this.pro_numero || this.lote) {
      document.title = ['CONTROL DE PESO ENFARDADORA', this.pro_numero ? `PRO${this.pro_numero}` : '', this.lote ? `LOTE ${this.lote}` : '']
        .filter(Boolean).join(' - ');
      const restaurar = () => { document.title = tituloOriginal; window.removeEventListener('afterprint', restaurar); };
      window.addEventListener('afterprint', restaurar);
    }
    setTimeout(() => window.print(), 150);
  }

  mostrarToast(msg: string): void {
    this.toast = msg; clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => this.toast = '', 2500);
  }
}
