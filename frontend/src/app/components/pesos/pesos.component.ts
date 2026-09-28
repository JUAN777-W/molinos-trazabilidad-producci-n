import { Component, OnInit, OnDestroy, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { FormatosService } from '../../services/formatos.service';
import { AuthService } from '../../services/auth.service';
import { RegistroPesos, FilaPeso } from '../../models/formatos.model';
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

export const MAQUINAS = ['1P','2Q','4T','5U','6V','7W','8S','9X','10Y','11Z'];
const MAQUINAS_TRIGO = new Set(['8S','9X','10Y','11Z']);

// Mismo catálogo de referencias que Bobinas y Rotulado (mismos códigos) — si
// cambia allá, actualizar aquí también.
export const REFERENCIAS_PESOS = [
  // Trigo
  { key: '10-20-5', label: 'EMP TRIGO TRADICIONAL 1000GR', tipo: 'trigo' },
  { key: '10-20-6', label: 'EMP TRIGO TRADICIONAL 500GR', tipo: 'trigo' },
  { key: '10-20-64', label: 'EMP LAMINA HNA TRIGO QUICKSY 500GR', tipo: 'trigo' },
  { key: '10-20-65', label: 'EMP LAMINADO TRIGO LEUDANTE QUICKSY 500GR', tipo: 'trigo' },
  { key: '10-20-66', label: 'EMP LAMINA TRIGO DEL COSTAL 500 G CALOR CONST', tipo: 'trigo' },
  { key: '10-20-7', label: 'EMP TRIGO LEUDANTE 1000GR', tipo: 'trigo' },
  { key: '10-20-8', label: 'EMP TRIGO LEUDANTE 500GR', tipo: 'trigo' },
  // Maíz
  { key: '11-20-19', label: 'EMP MAIZ BCO 1000 NAL ROVEMA', tipo: 'maiz' },
  { key: '11-20-20', label: 'EMP MAIZ BLANCO MASAPAN NAL ROVEMA', tipo: 'maiz' },
  { key: '11-20-21', label: 'EMP MAIZ AMARILLO 1000G NAL ROVEMA', tipo: 'maiz' },
  { key: '11-20-25', label: 'EMP MAIZ BLANCO 250GR', tipo: 'maiz' },
  { key: '11-20-3', label: 'EMP MAIZ AMARILLO 500GR', tipo: 'maiz' },
  { key: '11-20-5', label: 'EMP MAIZ BLANCO 1000GR', tipo: 'maiz' },
  { key: '11-20-57', label: 'EMP MAIZ BLANCO 500GR MANTEQUILLA Y SAL', tipo: 'maiz' },
  { key: '11-20-59', label: 'EMP LAM MANTEQUILLA SAL KL EXPORTACION PANAMA', tipo: 'maiz' },
  { key: '11-20-6', label: 'EMP MAIZ BL. LAM EXPO PANAMA 1000KG', tipo: 'maiz' },
  { key: '11-20-61', label: 'EMP MASAPAN LIBRA', tipo: 'maiz' },
  { key: '11-20-62', label: 'EMP MASAPAN 1000 GMS ALMOHADILLA', tipo: 'maiz' },
  { key: '11-20-65', label: 'EMP MAIZ AMARLLO 1000 GMS', tipo: 'maiz' },
  { key: '11-20-66', label: 'EMP MAIZ AMARILLO EXP 1000 CATEDRAL PANAMA', tipo: 'maiz' },
  { key: '11-20-72', label: 'EMP MAIZ BCO EXP 1000G DISTRISANDER CATEDRAL', tipo: 'maiz' },
  { key: '11-20-73', label: 'EMP MAIZ B ALMO DISTRISANDER 1000GRM', tipo: 'maiz' },
  { key: '11-20-76', label: 'EMP HNA MAIZ BLANCO QUICKSY 1000 GR NO ROVEMA', tipo: 'maiz' },
  { key: '11-20-77', label: 'EMP MAIZ AMARILLO 1000 GR QUICKSY NO ROVEMA', tipo: 'maiz' },
  { key: '11-20-79', label: 'EMP HNA PREC MAIZ BCO DEL COSTAL 1000 GRARA', tipo: 'maiz' },
  { key: '11-20-83', label: 'EMP PREC BLANCA 1010G NEW BRAZ.', tipo: 'maiz' },
  { key: '11-20-84', label: 'EMP MAIZ BLANCO 500GR CATEDRA', tipo: 'maiz' },
  { key: '11-20-85', label: 'EMP MAIZ BLANCO EXP 1000GR ROVEMA USA', tipo: 'maiz' },
  { key: '11-20-86', label: 'EMP PREC BLANCA LA COMADRE 1000G', tipo: 'maiz' },
  { key: '11-20-87', label: 'EMP PREC AMARILLA LA COMADRE 1000G', tipo: 'maiz' },
];

type Fila = FilaPeso & { _clases: string[]; _confirmadoAtipico: boolean };

interface Planilla {
  maquina: string;
  referencia: string;
  filas: Fila[];
  registroId: number | null;
}

function nuevasFilas(turno = ''): Fila[] {
  return horasDelTurno(turno).map((h, i) => {
    const fila: any = {
      numero_fila: i, hora: h,
      observaciones: '',
      _clases: Array(NUM_MUESTRAS).fill(''),
      _confirmadoAtipico: false,
    };
    MUESTRA_KEYS.forEach(k => fila[k] = null);
    return fila as Fila;
  });
}

function nuevaPlanilla(maquina = '', turno = ''): Planilla {
  return { maquina, referencia: '', filas: nuevasFilas(turno), registroId: null };
}

@Component({
  selector: 'app-pesos',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './pesos.component.html'
})
export class PesosComponent implements OnInit, OnDestroy {
  fecha = ''; turno = '';
  maquinas = MAQUINAS;
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

  // Igual que Rotulado: Pesos es por máquina individual. Si la máquina activa
  // (compartida desde Bobinas) es pareja, aquí se arman 2 planillas.
  planillas: Planilla[] = [nuevaPlanilla()];
  planillaActivaIdx = 0;

  private get planillaActiva(): Planilla { return this.planillas[this.planillaActivaIdx]; }

  // Redirigen a la planilla activa, así el resto del código sigue usando
  // this.maquina/this.referencia/this.filas/this.registroId como si hubiera una sola.
  get maquina(): string { return this.planillaActiva.maquina; }
  set maquina(v: string) { this.planillaActiva.maquina = v; }

  get referencia(): string { return this.planillaActiva.referencia; }
  set referencia(v: string) { this.planillaActiva.referencia = v; }

  get filas(): Fila[] { return this.planillaActiva.filas; }
  set filas(v: Fila[]) { this.planillaActiva.filas = v; }

  get registroId(): number | null { return this.planillaActiva.registroId; }
  set registroId(v: number | null) { this.planillaActiva.registroId = v; }

  cambiarPlanillaActiva(idx: number): void {
    if (idx >= 0 && idx < this.planillas.length) this.planillaActivaIdx = idx;
  }

  /** Referencias válidas para la máquina de la planilla activa (mismo filtro trigo/maíz que Bobinas) */
  get referenciasFiltradas(): typeof REFERENCIAS_PESOS {
    if (!this.maquina) return REFERENCIAS_PESOS;
    const tipo = MAQUINAS_TRIGO.has(this.maquina) ? 'trigo' : 'maiz';
    return REFERENCIAS_PESOS.filter(r => r.tipo === tipo);
  }

  /** Etiquetas legibles (para mostrar como texto plano cuando está bloqueado) */
  turnoLabel(key: string): string {
    return this.turnos.find(t => t.key === key)?.label ?? key;
  }

  referenciaLabel(key: string): string {
    return REFERENCIAS_PESOS.find(r => r.key === key)?.label ?? key;
  }

  // Modo solo lectura (registro ya guardado, visto desde el panel admin)
  soloLectura = false;
  cargandoRegistroGuardado = false;

  /** PRO y lote de exportación — los asigna el admin desde Informes; si están
   *  presentes, se usan para nombrar el PDF al generarlo. */
  pro_numero = '';
  lote = '';

  constructor(private svc: FormatosService, private auth: AuthService, private route: ActivatedRoute) {}

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

  /** Horas de las 8 que le corresponden al turno activo */
  get horasTurnoActual(): string[] { return horasDelTurno(this.turno); }

  private regenerarHorasPlanilla(p: Planilla): void {
    const tieneAlgo = p.filas.some(f =>MUESTRA_KEYS.some(k => (f as any)[k] != null));
    if (!tieneAlgo) {
      p.filas = nuevasFilas(this.turno);
    }
  }

  private cargarRegistroGuardado(id: number): void {
    this.cargandoRegistroGuardado = true;
    fetch(`${API_URL}/api/pesos/${id}`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then((reg: RegistroPesos) => {
        this.fecha = reg.fecha || '';
        this.turno = reg.turno || '';
        this.nombre_operario = reg.nombre_operario || '';
        this.firma_data = reg.firma_data || '';
        this.firmaAutomatica = !!reg.firma_data;
        this.camposDesdeBobinas = true;
        this.pro_numero = reg.pro_numero || '';
        this.lote = reg.lote || '';

        this.planillas = [{
          maquina: reg.maquina || '',
          referencia: reg.referencia || '',
          filas: (reg.filas || []).map(f => ({
            ...f, _clases: Array(NUM_MUESTRAS).fill(''), _confirmadoAtipico: true,
          })),
          registroId: reg.id ?? null,
        }];
        this.planillaActivaIdx = 0;

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

  // Borrador local en localStorage
  private readonly DRAFT_KEY = 'borrador_pesos';

  private guardarBorrador(): void {
    const vacio = !this.fecha && !this.turno &&
      this.planillas.every(p => !p.maquina && !p.referencia);
    if (vacio) {
      localStorage.removeItem(this.DRAFT_KEY);
      return;
    }
    const snapshot = {
      fecha: this.fecha, turno: this.turno,
      nombre_operario: this.nombre_operario,
      planillas: this.planillas, planillaActivaIdx: this.planillaActivaIdx,
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
      this.planillas = (s.planillas && s.planillas.length) ? s.planillas : this.planillas;
      this.planillaActivaIdx = s.planillaActivaIdx ?? 0;
    } catch { /* borrador corrupto: se ignora */ }
  }

  private limpiarBorrador(): void {
    localStorage.removeItem(this.DRAFT_KEY);
  }

  // Contexto compartido desde Bobinas
  camposDesdeBobinas = false;

  cargarContextoCompartido(): void {
    const raw = localStorage.getItem('contexto_activo_turno');
    if (!raw) return;
    try {
      const ctx = JSON.parse(raw);
      const esReciente = ctx.actualizado_en && (Date.now() - ctx.actualizado_en) < 16 * 60 * 60 * 1000;
      if (!esReciente) return;

      // Los datos de Bobinas siempre ganan sobre un borrador viejo
      if (ctx.fecha) this.fecha = ctx.fecha;
      if (ctx.turno) this.turno = ctx.turno;
      this.regenerarHorasPlanilla(this.planillas[0]);

      if (ctx.maquina) {
        this.planillas[0].maquina = ctx.maquina;
        if (ctx.referencia_producto) this.planillas[0].referencia = ctx.referencia_producto;
        if (ctx.maquinaB) {
          if (this.planillas.length < 2) {
            const nueva = nuevaPlanilla(ctx.maquinaB, this.turno);
            if (ctx.referencia_producto) nueva.referencia = ctx.referencia_producto;
            this.planillas.push(nueva);
          } else {
            this.planillas[1].maquina = ctx.maquinaB;
            this.regenerarHorasPlanilla(this.planillas[1]);
            if (ctx.referencia_producto) this.planillas[1].referencia = ctx.referencia_producto;
          }
        } else if (this.planillas.length > 1) {
          this.planillas.length = 1;
          if (this.planillaActivaIdx > 0) this.planillaActivaIdx = 0;
        }
        this.camposDesdeBobinas = true;
      }
    } catch { /* contexto corrupto: se ignora */ }
  }

  desbloquearCampos(): void {
    if (!confirm('¿Seguro que quieres cambiar estos datos manualmente? Deben coincidir con la planilla de Bobinas.')) return;
    this.camposDesdeBobinas = false;
  }

  // Firma tomada automáticamente de la cuenta del operario
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

  /** Angular no permite indexar "Fila" con una clave dinámica directo en el template */
  getMuestra(f: Fila, idx: number): number | null {
    return (f as any)[MUESTRA_KEYS[idx]] ?? null;
  }

  onMuestraChange(f: Fila, idx: number, valor: number | null): void {
    (f as any)[MUESTRA_KEYS[idx]] = valor;
    this.colorPeso(f, idx);
  }

  colorPeso(f: Fila, idx: number): void {
    const v = +((f as any)[MUESTRA_KEYS[idx]]) || 0;
    f._confirmadoAtipico = false; // cambió un valor: hay que volver a confirmar si sigue atípico
    if (v === 0) { f._clases[idx] = ''; return; }
    const ok = v > 800 ? (v >= 1000 && v <= 1015) : (v >= 500 && v <= 508);
    f._clases[idx] = ok ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800';
  }

  /** true si alguna muestra de la fila está fuera del rango normal (500-508 o 1000-1015) */
  filaAtipica(f: Fila): boolean {
    return f._clases.some(c => c === 'bg-red-100 text-red-800');
  }

  confirmarAtipico(f: Fila): void {
    f._confirmadoAtipico = true;
  }

  /** Filas con valores atípicos sin confirmar, de TODAS las planillas — bloquean el guardado */
  private validarRangosPeso(): string[] {
    const problemas: string[] = [];
    const revisar = (filas: Fila[], etiqueta: string) => {
      filas.forEach(f => {
        if (this.filaAtipica(f) && !f._confirmadoAtipico) {
          problemas.push(
            `${etiqueta}, fila de las ${f.hora}: hay un peso fuera del rango normal (500-508 g o 1000-1015 g). ` +
            `Corrígelo o confirma con el botón "Es correcto"junto a la fila.`
          );
        }
      });
    };
    if (this.planillas.length === 1) {
      revisar(this.planillas[0].filas, 'Planilla');
    } else {
      this.planillas.forEach((p, i) => revisar(p.filas, `Planilla ${i + 1}`));
    }
    return problemas;
  }

  // Validación cruzada con Bobinas y Rotulado
  alertaConsistencia: string | null = null;
  conflictosConsistencia: { formato: string; maquina: string; operario: string; turno: string }[] = [];
  alertaEsError = true;

  private async validarConsistenciaTurnoParaMaquina(maquina: string, registroId: number | null): Promise<boolean> {
    if (!this.fecha || !this.turno || !maquina) return true;
    try {
      const params = new URLSearchParams({
        fecha: this.fecha, maquina, turno: this.turno,
        excluir_formato: 'Pesos',
      });
      if (registroId) params.set('excluir_id', String(registroId));
      const resp = await fetch(`${API_URL}/api/validacion/turno?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
      });
      if (!resp.ok) {
        this.alertaEsError = false;
        this.alertaConsistencia = 'No se pudo verificar la consistencia con Bobinas y Rotulado (error del servidor). Se guardará de todas formas — revisa manualmente que el turno coincida en los 3 formatos.';
        return true;
      }
      const data = await resp.json();
      if (!data.consistente) {
        this.alertaEsError = true;
        this.alertaConsistencia = data.mensaje;
        this.conflictosConsistencia = data.conflictos;
        return false;
      }
      return true;
    } catch {
      this.alertaEsError = false;
      this.alertaConsistencia = 'No se pudo verificar la consistencia con Bobinas y Rotulado (sin conexión). Se guardará de todas formas — revisa manualmente que el turno coincida en los 3 formatos.';
      return true;
    }
  }

  private async validarConsistenciaTurno(): Promise<boolean> {
    this.alertaConsistencia = null;
    this.conflictosConsistencia = [];
    for (const p of this.planillas) {
      const ok = await this.validarConsistenciaTurnoParaMaquina(p.maquina, p.registroId);
      if (!ok) return false;
    }
    return true;
  }

  camposFaltantes: string[] = [];

  private validarCamposObligatoriosPlanilla(p: Planilla, etiqueta: string): string[] {
    const faltan: string[] = [];
    if (!p.maquina) faltan.push(`${etiqueta}: Máquina`);
    if (!p.referencia || !p.referencia.trim()) faltan.push(`${etiqueta}: Referencia`);
    return faltan;
  }

  private validarCamposObligatorios(): string[] {
    const faltan: string[] = [];
    if (!this.fecha) faltan.push('Fecha');
    if (!this.turno) faltan.push('Turno');
    if (!this.firma_data) faltan.push('Firma del Operario (pide al administrador que registre tu firma)');

    if (this.planillas.length === 1) {
      faltan.push(...this.validarCamposObligatoriosPlanilla(this.planillas[0], 'Planilla'));
    } else {
      this.planillas.forEach((p, i) => faltan.push(...this.validarCamposObligatoriosPlanilla(p, `Planilla ${i + 1}`)));
    }
    return faltan;
  }

  async guardar(): Promise<void> {
    this.alertaConsistencia = null;
    this.camposFaltantes = [];
    this.conflictosConsistencia = [];

    const faltan = this.validarCamposObligatorios();
    if (faltan.length > 0) {
      this.alertaEsError = true;
      this.camposFaltantes = faltan;
      this.alertaConsistencia = 'Antes de guardar, completa estos campos obligatorios:';
      return;
    }

    const problemasPeso = this.validarRangosPeso();
    if (problemasPeso.length > 0) {
      this.alertaEsError = true;
      this.camposFaltantes = problemasPeso;
      this.alertaConsistencia = 'Hay pesos que parecen error de digitación — revisa antes de guardar:';
      return;
    }

    const ok = await this.validarConsistenciaTurno();
    if (!ok) return;

    for (const p of this.planillas) {
      const payload: RegistroPesos = {
        fecha: this.fecha, turno: this.turno, maquina: p.maquina, referencia: p.referencia,
        nombre_operario: this.nombre_operario, firma_data: this.firma_data,
        filas: p.filas.map(f => {
          const out: any = { numero_fila: f.numero_fila, hora: f.hora, observaciones: f.observaciones };
          MUESTRA_KEYS.forEach(k => out[k] = (f as any)[k]);
          return out;
        })
      };

      try {
        if (p.registroId) {
          await this.svc.updatePesos(p.registroId, payload).toPromise();
        } else {
          const res: any = await this.svc.createPesos(payload).toPromise();
          p.registroId = res.id!;
        }
      } catch {
        this.mostrarToast(`Error al guardar la planilla de ${p.maquina}`);
        return;
      }
    }

    this.limpiarBorrador();
    this.mostrarToast('Guardado');
  }

  limpiar(): void {
    if (!confirm('¿Limpiar todos los datos del turno?')) return;
    this.fecha=''; this.turno='';
    this.nombre_operario=this.auth.getNombre();
    this.planillas = [nuevaPlanilla()];
    this.planillaActivaIdx = 0;
    this.camposDesdeBobinas = false;
    this.cargarMiFirma();
    this.limpiarBorrador();
    this.cargarContextoCompartido();
    this.mostrarToast('Turno limpiado');
  }

  generarPDF(): void {
    const tituloOriginal = document.title;
    if (this.pro_numero || this.lote) {
      document.title = ['CONTROL DE PESO', this.pro_numero ? `PRO${this.pro_numero}` : '', this.lote ? `LOTE ${this.lote}` : '']
        .filter(Boolean).join(' - ');
      const restaurar = () => { document.title = tituloOriginal; window.removeEventListener('afterprint', restaurar); };
      window.addEventListener('afterprint', restaurar);
    }
    setTimeout(() => window.print(), 150);
  }

  mostrarToast(msg: string): void {
    this.toast=msg; clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => this.toast='', 2500);
  }
}