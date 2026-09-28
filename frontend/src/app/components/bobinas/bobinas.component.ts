import { Component, OnInit, OnDestroy, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { FormatosService } from '../../services/formatos.service';
import { AuthService } from '../../services/auth.service';
import { RegistroBobinas, FilaBobina, ReferenciaCatalogo, RegistroRotulado, FilaRotulado, RegistroPesos, FilaPeso } from '../../models/formatos.model';
import { API_URL } from '../../config';

// Catálogo de referencias — solo empaque de trigo y maíz con conteo de pacas.
// Divisor (unidades por paca): trigo libra 25 / trigo kilo 10 / maíz libra 24 /
// maíz kilo 20 (excepto maíz blanco no rovema -> 10).
export const REFS: ReferenciaCatalogo[] = [
  // Trigo (código SIGO)
  { key: '10-20-5', label: 'EMP TRIGO TRADICIONAL 1000GR', div: 10, categoria: 'TRIGO' },         // kilo
  { key: '10-20-6', label: 'EMP TRIGO TRADICIONAL 500GR', div: 25, categoria: 'TRIGO' },          // libra
  { key: '10-20-64', label: 'EMP LAMINA HNA TRIGO QUICKSY 500GR', div: 25, categoria: 'TRIGO' },  // libra
  { key: '10-20-65', label: 'EMP LAMINADO TRIGO LEUDANTE QUICKSY 500GR', div: 25, categoria: 'TRIGO' }, // libra
  { key: '10-20-66', label: 'EMP LAMINA TRIGO DEL COSTAL 500 G CALOR CONST', div: 25, categoria: 'TRIGO' }, // libra
  { key: '10-20-7', label: 'EMP TRIGO LEUDANTE 1000GR', div: 10, categoria: 'TRIGO' },            // kilo
  { key: '10-20-8', label: 'EMP TRIGO LEUDANTE 500GR', div: 25, categoria: 'TRIGO' },             // libra

  // Maíz (código SIGO)
  { key: '11-20-5', label: 'EMP MAIZ BLANCO 1000GR', div: 20, categoria: 'MAIZ' },                 // kilo, rovema
  { key: '11-20-84', label: 'EMP MAIZ BLANCO 500GR', div: 24, categoria: 'MAIZ' },         // libra
  { key: '11-20-19', label: 'EMP MAIZ BCO 1000 NAL ROVEMA', div: 20, categoria: 'MAIZ' },          // kilo, rovema
  { key: '11-20-20', label: 'EMP MAIZ BLANCO MASAPAN NAL ROVEMA', div: 20, categoria: 'MAIZ' },    // kilo, rovema
  { key: '11-20-21', label: 'EMP MAIZ AMARILLO 1000G NAL ROVEMA', div: 20, categoria: 'MAIZ' },    // kilo, rovema
  { key: '11-20-25', label: 'EMP MAIZ BLANCO 250GR', div: 96, categoria: 'MAIZ' },                 // presentación 250gr
  { key: '11-20-3', label: 'EMP MAIZ AMARILLO 500GR', div: 24, categoria: 'MAIZ' },                // libra
  { key: '11-20-57', label: 'EMP MAIZ BLANCO 500GR MANTEQUILLA Y SAL', div: 24, categoria: 'MAIZ' }, // libra
  { key: '11-20-59', label: 'EMP LAM MANTEQUILLA SAL KL EXPORTACION PANAMA', div: 20, categoria: 'MAIZ' }, // kilo
  { key: '11-20-6', label: 'EMP MAIZ BL. LAM EXPO PANAMA 1000KG', div: 20, categoria: 'MAIZ' },    // kilo
  { key: '11-20-61', label: 'EMP MASAPAN LIBRA', div: 24, categoria: 'MAIZ' },                     // libra
  { key: '11-20-62', label: 'EMP MASAPAN 1000 GMS ALMOHADILLA', div: 20, categoria: 'MAIZ' },      // kilo
  { key: '11-20-65', label: 'EMP MAIZ AMARLLO 1000 GMS', div: 20, categoria: 'MAIZ' },             // kilo
  { key: '11-20-66', label: 'EMP MAIZ AMARILLO EXP 1000 CATEDRAL PANAMA', div: 20, categoria: 'MAIZ' }, // kilo
  { key: '11-20-72', label: 'EMP MAIZ BCO EXP 1000G DISTRISANDER CATEDRAL', div: 20, categoria: 'MAIZ' }, // kilo
  { key: '11-20-73', label: 'EMP MAIZ B ALMO DISTRISANDER 1000GRM', div: 20, categoria: 'MAIZ' },  // kilo
  { key: '11-20-76', label: 'EMP HNA MAIZ BLANCO QUICKSY 1000 GR NO ROVEMA', div: 10, categoria: 'MAIZ' }, // kilo, blanco NO ROVEMA -> excepción
  { key: '11-20-77', label: 'EMP MAIZ AMARILLO 1000 GR QUICKSY NO ROVEMA', div: 20, categoria: 'MAIZ' }, // kilo, amarillo -> excepción no aplica (confirmado)
  { key: '11-20-79', label: 'EMP HNA PREC MAIZ BCO DEL COSTAL 1000 GRARA', div: 20, categoria: 'MAIZ' }, // kilo
  { key: '11-20-83', label: 'EMP PREC BLANCA 1010G NEW BRAZ.', div: 20, categoria: 'MAIZ' },       // kilo
  { key: '11-20-85', label: 'EMP MAIZ BLANCO EXP 1000GR ROVEMA USA', div: 20, categoria: 'MAIZ' }, // kilo, rovema
  { key: '11-20-86', label: 'EMP PREC BLANCA LA COMADRE 1000G', div: 20, categoria: 'MAIZ' },      // kilo
  { key: '11-20-87', label: 'EMP PREC AMARILLA LA COMADRE 1000G', div: 20, categoria: 'MAIZ' },    // kilo
];

export const MAQUINAS = ['1P','2Q','4T','5U','6V','7W','8S','9X','10Y','11Z'];

// Máquinas de trigo — el resto se considera maíz
const MAQUINAS_TRIGO = new Set(['8S','9X','10Y','11Z']);

// La 7W es la máquina Rovema — dedicada exclusivamente a estas referencias de
// maíz (export/marca Rovema). El resto de máquinas de maíz nunca las usa.
const REFS_ROVEMA_7W = new Set([
  '11-20-19', '11-20-20', '11-20-21', '11-20-6', '11-20-66',
  '11-20-72', '11-20-83', '11-20-85', '11-20-86', '11-20-87',
]);

// Parejas: al elegir una, la otra se asigna automáticamente al grupo B
const PAREJAS: Record<string, string> = {
  '1P': '2Q', '2Q': '1P',
  '5U': '6V', '6V': '5U',
  '8S': '9X', '9X': '8S',
  '10Y': '11Z', '11Z': '10Y',
};

type Fila = FilaBobina & {
  _consumido: number;
  _atipico: boolean;          // true si peso_montar o peso_desmontar está fuera del rango normal
  _confirmadoAtipico: boolean; // el operario confirmó que el valor inusual sí es correcto
  _estimacionInconsistente?: boolean; // true si el cálculo automático dio negativo (algo no cuadra)
};

// Rango normal de peso al montar (kg) — fuera de esto se advierte posible error de digitación.
// El peso al desmontar no se valida contra un rango: a veces el rollo se baja antes de
// terminarse y pesa más de lo usual, así que un valor "alto" ahí no es un error.
// Aplica solo a Empacadora A/B — en Enfardadora peso_montar/peso_desmontar son kilos de
// fardo, una magnitud totalmente distinta a un rollo de empaque.
const RANGO_PESO_MONTAR = { min: 1, max: 25.80 };

@Component({
  selector: 'app-bobinas',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './bobinas.component.html'
})
export class BobinasComponent implements OnInit, OnDestroy {
  refs    = REFS;
  // Distinta de referencia_producto (la de cabecera). Empacadoras usan las 3 láminas; Enfardadora solo Tuboplast.
  referenciasEmpaqueFila = ['TUBOPLAST', 'PLASTILENE', 'DORFAN', 'FLEXOSPRING'];
  referenciasEmpaqueEnf = ['TUBOPLAST', 'FLEXOSPRING'];
  maquinas = MAQUINAS;
  turnos = [
    { key: 'T1', label: 'Turno 1 — 6:00 a.m. a 2:00 p.m.' },
    { key: 'T2', label: 'Turno 2 — 2:00 p.m. a 10:00 p.m.' },
    { key: 'T3', label: 'Turno 3 — 10:00 p.m. a 6:00 a.m.' },
  ];

  // Cabecera
  periodo = '';
  referencia_producto = this.refs[0].key;
  filtroReferencia = '';
  maquinaA = '';   // empacadora A (única selección)
  maquinaB = '';   // empacadora B (auto si hay pareja, vacío si es sola)
  esPar    = false;
  fecha = '';
  turno = '';

  // Ancho de fardo de Enfardadora, distinto de referencia_producto. Se carga
  // del catálogo de Bodega filtrando por "FARDO" en la descripción.
  referencia_enfardadora = '';
  referenciasFardo: { codigo: string; descripcion: string }[] = [];
  cargandoReferenciasFardo = false;
  peso_desperdicio: number | null = null;        // Desperdicio material empaque (bobinas)
  peso_desperdicio_fardo: number | null = null;   // Desperdicio fardo
  nombre_operario = '';
  firma_data = '';
  firmaAutomatica = false;   // true si la firma se cargó sola desde la cuenta del operario
  cargandoFirma = false;

  // Filas dinámicas por sección
  filasA: Fila[] = [];
  filasB: Fila[] = [];
  filasENF: Fila[] = [];

  // Totales
  totalKgA = 0; totalKgB = 0; totalKgENF = 0;
  totalConsumoAB = 0; totalCntA = 0; totalCntB = 0; totalCntENF = 0;
  totalPacas = 0; porcentajeDesperdicio = 0; porcentajeDesperdicioFardo = 0;

  // UI
  toast = ''; toastTimer: any;
  registroId: number | null = null;

  // Reportar Problema de Mantenimiento
  mostrandoModalReporte = false;
  enviandoReporte = false;
  formReporte = { maquina: '', descripcion_problema: '', prioridad: 'MEDIA' };

  abrirModalReporte(): void {
    this.formReporte = { maquina: this.maquinaA || '', descripcion_problema: '', prioridad: 'MEDIA' };
    this.mostrandoModalReporte = true;
  }

  cerrarModalReporte(): void {
    this.mostrandoModalReporte = false;
  }

  enviarReporte(): void {
    if (!this.formReporte.maquina || !this.formReporte.descripcion_problema.trim()) {
      alert('Completa la máquina y describe el problema.');
      return;
    }
    this.enviandoReporte = true;
    fetch(`${API_URL}/api/mantenimiento/solicitudes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${this.auth.getToken()}` },
      body: JSON.stringify(this.formReporte)
    })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(() => {
        this.enviandoReporte = false;
        this.mostrandoModalReporte = false;
        this.mostrarToast('Problema reportado — le llegará al ingeniero de mantenimiento');
      })
      .catch(() => { this.enviandoReporte = false; alert('Error al enviar el reporte'); });
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
      return; // no cargar borrador ni contexto compartido en modo solo lectura
    }
    this.calcular();
    this.cargarMiFirma();
    this.restaurarBorrador();
    this.nombre_operario = this.auth.getNombre();
    this.cargarReferenciasFardo();
  }

  /** Carga un registro guardado para verlo en modo solo lectura, desde el panel admin */
  private cargarRegistroGuardado(id: number): void {
    this.cargandoRegistroGuardado = true;
    fetch(`${API_URL}/api/bobinas/${id}`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then((reg: RegistroBobinas) => {
        this.registroId = reg.id ?? null;
        this.periodo = reg.periodo || '';
        this.referencia_producto = reg.referencia_producto || '';
        this.referencia_enfardadora = reg.referencia_enfardadora || '';
        this.fecha = reg.fecha || '';
        this.turno = reg.turno || '';
        this.peso_desperdicio = reg.peso_desperdicio ?? null;
        this.peso_desperdicio_fardo = reg.peso_desperdicio_fardo ?? null;
        this.nombre_operario = reg.nombre_operario || '';
        this.firma_data = reg.firma_data || '';
        this.firmaAutomatica = !!reg.firma_data;
        this.pro_numero = reg.pro_numero || '';
        this.lote = reg.lote || '';

        const maquinaTexto = reg.maquina || '';
        const partes = maquinaTexto.split('-');
        this.maquinaA = partes[0] || '';
        this.esPar = partes.length > 1;
        this.maquinaB = partes[1] || '';

        const filas = reg.filas || [];
        this.filasA = filas.filter(f => f.maquina_grupo === 'A').map(f => ({ ...f, _consumido: f.consumido || 0, _atipico: false, _confirmadoAtipico: true })) as any;
        this.filasB = filas.filter(f => f.maquina_grupo === 'B').map(f => ({ ...f, _consumido: f.consumido || 0, _atipico: false, _confirmadoAtipico: true })) as any;
        this.filasENF = filas.filter(f => f.maquina_grupo === 'ENF').map(f => ({ ...f, _consumido: f.consumido || 0, _atipico: false, _confirmadoAtipico: true })) as any;

        this.cargandoRegistroGuardado = false;
        this.calcular();
      })
      .catch(() => { this.cargandoRegistroGuardado = false; });
  }

  /** Referencias de bodega filtradas por "FARDO" en la descripción */
  cargarReferenciasFardo(): void {
    this.cargandoReferenciasFardo = true;
    fetch(`${API_URL}/api/bodega/referencias`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then((data: any[]) => {
        this.referenciasFardo = (Array.isArray(data) ? data : [])
          .filter(r => (r.descripcion || '').toUpperCase().includes('FARDO'))
          .map(r => ({ codigo: r.codigo, descripcion: r.descripcion }));
        this.cargandoReferenciasFardo = false;
      })
      .catch(() => { this.cargandoReferenciasFardo = false; });
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

  // Borrador local en localStorage, para no perder lo escrito al cambiar de pantalla
  private readonly DRAFT_KEY = 'borrador_bobinas';

  private guardarBorrador(): void {
    const snapshot = {
      periodo: this.periodo, referencia_producto: this.referencia_producto,
      referencia_enfardadora: this.referencia_enfardadora,
      maquinaA: this.maquinaA, maquinaB: this.maquinaB, esPar: this.esPar,
      fecha: this.fecha, turno: this.turno,
      peso_desperdicio: this.peso_desperdicio, peso_desperdicio_fardo: this.peso_desperdicio_fardo,
      nombre_operario: this.nombre_operario,
      filasA: this.filasA, filasB: this.filasB, filasENF: this.filasENF,
      registroId: this.registroId,
    };
    // Si el formulario está completamente vacío, no dejamos un borrador vacío
    const vacio = !this.fecha && !this.turno && !this.maquinaA && !this.periodo &&
      this.filasA.length === 0 && this.filasB.length === 0 && this.filasENF.length === 0;
    if (vacio) {
      localStorage.removeItem(this.DRAFT_KEY);
    } else {
      localStorage.setItem(this.DRAFT_KEY, JSON.stringify(snapshot));
    }
  }

  private restaurarBorrador(): void {
    const raw = localStorage.getItem(this.DRAFT_KEY);
    if (!raw) return;
    try {
      const s = JSON.parse(raw);
      this.periodo = s.periodo ?? '';
      this.referencia_producto = s.referencia_producto ?? this.refs[0].key;
      this.referencia_enfardadora = s.referencia_enfardadora ?? '';
      this.maquinaA = s.maquinaA ?? '';
      this.maquinaB = s.maquinaB ?? '';
      this.esPar = s.esPar ?? false;
      this.fecha = s.fecha ?? '';
      this.turno = s.turno ?? '';
      this.peso_desperdicio = s.peso_desperdicio ?? null;
      this.peso_desperdicio_fardo = s.peso_desperdicio_fardo ?? null;
      this.nombre_operario = s.nombre_operario ?? '';
      this.filasA = s.filasA ?? [];
      this.filasB = s.filasB ?? [];
      this.filasENF = s.filasENF ?? [];
      this.registroId = s.registroId ?? null;
      this.calcular();
    } catch { /* borrador corrupto: se ignora */ }
  }

  private limpiarBorrador(): void {
    localStorage.removeItem(this.DRAFT_KEY);
  }

  // Contexto compartido con Rotulado y Pesos: Bobinas es la planilla maestra,
  // sus valores de turno se propagan para evitar turnos distintos por error.
  private readonly CONTEXTO_KEY = 'contexto_activo_turno';

  private compartirContexto(): void {
    if (!this.fecha && !this.turno && !this.maquinaA) return; // nada que compartir todavía
    const refInfo = this.refs.find(r => r.key === this.referencia_producto);
    const contexto = {
      fecha: this.fecha, turno: this.turno, maquina: this.maquinaA,
      maquinaB: this.esPar ? this.maquinaB : null,
      referencia_producto: this.referencia_producto,
      referencia_label: refInfo?.label ?? '',
      referencia_enfardadora: this.referencia_enfardadora,
      actualizado_en: Date.now(),
    };
    localStorage.setItem(this.CONTEXTO_KEY, JSON.stringify(contexto));
  }

  private limpiarContexto(): void {
    localStorage.removeItem(this.CONTEXTO_KEY);
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

  onMaquinaAChange(): void {
    const par = PAREJAS[this.maquinaA];
    if (par) {
      this.maquinaB = par;
      this.esPar = true;
    } else {
      this.maquinaB = '';
      this.esPar = false;
    }
    // Resetear referencia si no es válida para el nuevo tipo de máquina
    const refsValidas = this.refsFiltradas;
    if (!refsValidas.find(r => r.key === this.referencia_producto)) {
      this.referencia_producto = refsValidas[0]?.key ?? '';
    }
    this.calcular();
  }

  get labA(): string { return this.maquinaA || 'Emp. A'; }
  get labB(): string { return this.maquinaB || 'Emp. B'; }

  /** Refs filtradas por categoría (trigo/maíz) y, en maíz, por si la máquina es la 7W (Rovema) */
  get refsFiltradas(): ReferenciaCatalogo[] {
    if (!this.maquinaA) return REFS;
    if (MAQUINAS_TRIGO.has(this.maquinaA)) return REFS.filter(r => r.categoria === 'TRIGO');
    const esRovema = this.maquinaA === '7W';
    return REFS.filter(r => r.categoria === 'MAIZ' && REFS_ROVEMA_7W.has(r.key) === esRovema);
  }

  /** Refs filtradas por máquina + texto de búsqueda (código o nombre) */
  get refsFiltradasBusqueda(): ReferenciaCatalogo[] {
    const base = this.refsFiltradas;
    if (!this.filtroReferencia || !this.filtroReferencia.trim()) return base;
    const t = this.filtroReferencia.trim().toLowerCase();
    return base.filter(r => r.key.toLowerCase().includes(t) || r.label.toLowerCase().includes(t));
  }

  private nuevaFila(grupo: string, idx: number): Fila {
    return {
      numero_fila: idx,
      maquina_grupo: grupo,
      referencia_empaque: '',
      peso_montar: undefined,
      peso_desmontar: undefined,
      peso_desmontar_estimado: false,
      consumido: 0,
      contador: undefined,
      observaciones: '',
      _consumido: 0,
      _atipico: false,
      _confirmadoAtipico: false,
    };
  }

  agregarFilaA(): void {
    this.filasA.push(this.nuevaFila('A', this.filasA.length + 1));
  }
  agregarFilaB(): void {
    this.filasB.push(this.nuevaFila('B', this.filasB.length + 1));
  }
  agregarFilaENF(): void {
    this.filasENF.push(this.nuevaFila('ENF', this.filasENF.length + 1));
  }

  eliminarFilaA(i: number): void { this.filasA.splice(i, 1); this.calcular(); }
  eliminarFilaB(i: number): void { this.filasB.splice(i, 1); this.calcular(); }
  eliminarFilaENF(i: number): void { this.filasENF.splice(i, 1); this.calcular(); }

  /** Marca la fila como "atípica" si el peso al montar está fuera del rango normal (posible error de digitación) */
  private evaluarAtipico(f: Fila): void {
    const montar = +f.peso_montar! || 0;
    f._atipico = montar > 0 && (montar < RANGO_PESO_MONTAR.min || montar >RANGO_PESO_MONTAR.max);
  }

  /** Al cambiar Peso al Montar: reinicia la confirmación de atípico y reintenta la estimación automática */
  onPesoMontarChange(f: Fila, filas: Fila[], idx: number): void {
    f._confirmadoAtipico = false;
    this.calcular();
    this.intentarEstimarRestante(filas, idx);
  }

  /** Peso al Desmontar ingresado a mano: ya no es una estimación */
  onPesoDesmontarChange(f: Fila): void {
    f.peso_desmontar_estimado = false;
    f._estimacionInconsistente = false;
    f._confirmadoAtipico = false;
    this.calcular();
  }

  /** Al escribir el Contador: intenta estimar el peso restante si es la última fila */
  onContadorChange(filas: Fila[], idx: number): void {
    this.calcular();
    this.intentarEstimarRestante(filas, idx);
  }

  /** Rendimiento (kg/unidad) del rollo completo y medido más reciente de este turno, sin contar estimaciones */
  private calcularPesoPorUnidadLocal(filas: Fila[], idx: number): number | null {
    for (let j = idx - 1; j >= 0; j--) {
      const fila = filas[j];
      const montar = +fila.peso_montar! || 0;
      const desmontar = +fila.peso_desmontar! || 0;
      if (montar <= 0 || desmontar <= 0 || fila.peso_desmontar_estimado) continue;

      const contadorAnteriorDeEsa = j > 0 ? (+filas[j - 1].contador! || 0) : 0;
      const unidadesDeEsa = (+fila.contador! || 0) - contadorAnteriorDeEsa;
      if (unidadesDeEsa <= 0) continue;

      const consumidoReal = montar - desmontar;
      if (consumidoReal <= 0) continue;

      return consumidoReal / unidadesDeEsa;
    }
    return null;
  }

  // Estima el peso restante del rollo a medias con el rendimiento real más
  // reciente; nunca aprende de otra estimación ni de un rollo ya pesado a mano.
  private async intentarEstimarRestante(filas: Fila[], idx: number): Promise<void> {
    if (idx !== filas.length - 1) return; // solo aplica a la última fila del grupo
    const f = filas[idx];
    if (!this.referencia_producto) return;
    if (!f.peso_montar || +f.peso_montar <= 0) return;
    if (!f.contador || +f.contador <= 0) return;
    if (f.peso_desmontar && !f.peso_desmontar_estimado) return; // ya lo pesaron de verdad, no tocar

    const contadorAnterior = idx > 0 ? (+filas[idx - 1].contador! || 0) : 0;
    const unidades = (+f.contador! || 0) - contadorAnterior;
    if (unidades <= 0) return;

    // 1) Rollo anterior de este mismo turno
    const pesoPorUnidadLocal = this.calcularPesoPorUnidadLocal(filas, idx);
    if (pesoPorUnidadLocal !== null) {
      const consumidoEstimado = unidades * pesoPorUnidadLocal;
      const restanteSinRedondear = f.peso_montar - consumidoEstimado;
      f.peso_desmontar = Math.max(0, +restanteSinRedondear.toFixed(2));
      f.peso_desmontar_estimado = true;
      f._estimacionInconsistente = restanteSinRedondear < 0;
      this.calcular();
      return;
    }

    // 2) Si no hay nada en este turno, busca en el histórico guardado
    try {
      const params = new URLSearchParams({
        referencia_producto: this.referencia_producto,
        unidades_rollo_actual: String(unidades),
        peso_montar_actual: String(f.peso_montar),
      });
      const resp = await fetch(`${API_URL}/api/bobinas/estimar-restante?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
      });
      if (!resp.ok) return;
      const data = await resp.json();
      if (data.disponible) {
        f.peso_desmontar = data.peso_restante_estimado;
        f.peso_desmontar_estimado = true;
        f._estimacionInconsistente = data.consumido_estimado > f.peso_montar!;
        this.calcular();
      }
    } catch {
      // Sin conexión: se pesa manual como siempre
    }
  }

  confirmarAtipico(f: Fila): void {
    f._confirmadoAtipico = true;
  }

  calcular(): void {
    this.compartirContexto();
    let kgA = 0, kgB = 0, kgENF = 0;
    this.filasA.forEach(f => { this.evaluarAtipico(f); f._consumido = Math.max(0, (+f.peso_montar!||0) - (+f.peso_desmontar!||0)); kgA += f._consumido; });
    this.filasB.forEach(f => { this.evaluarAtipico(f); f._consumido = Math.max(0, (+f.peso_montar!||0) - (+f.peso_desmontar!||0)); kgB += f._consumido; });
    this.filasENF.forEach(f => { f._consumido = Math.max(0, (+f.peso_montar!||0) - (+f.peso_desmontar!||0)); kgENF += f._consumido; });

    this.totalKgA = kgA; this.totalKgB = kgB; this.totalKgENF = kgENF;
    this.totalConsumoAB = kgA + kgB;

    this.totalCntA   = this.ultimoValido(this.filasA.map(f => +f.contador!||0));
    this.totalCntB   = this.ultimoValido(this.filasB.map(f => +f.contador!||0));
    this.totalCntENF = this.ultimoValido(this.filasENF.map(f => +f.contador!||0));

    const div = this.refs.find(r => r.key === this.referencia_producto)?.div ?? 24;
    this.totalPacas = (this.totalCntA + this.totalCntB) > 0 ? (this.totalCntA + this.totalCntB) / div : 0;

    const desp = +this.peso_desperdicio! || 0;
    const despFardo = +this.peso_desperdicio_fardo! || 0;
    this.porcentajeDesperdicio = this.totalConsumoAB > 0 && desp > 0
      ? (desp / this.totalConsumoAB) * 100 : 0;
    this.porcentajeDesperdicioFardo = this.totalKgENF > 0 && despFardo > 0
      ? (despFardo / this.totalKgENF) * 100 : 0;
  }

  private ultimoValido(arr: number[]): number {
    for (let i = arr.length - 1; i >= 0; i--) { if (arr[i] > 0) return arr[i]; }
    return 0;
  }

  // Validación cruzada con Rotulado y Pesos
  alertaConsistencia: string | null = null;
  conflictosConsistencia: { formato: string; maquina: string; operario: string; turno: string }[] = [];
  alertaEsError = true; // true = conflicto real (bloquea), false = no se pudo verificar (advierte)

  private async validarConsistenciaTurno(): Promise<boolean> {
    this.alertaConsistencia = null;
    this.conflictosConsistencia = [];
    if (!this.fecha || !this.turno || !this.maquinaA) return true; // falta info, no hay nada que comparar
    try {
      const params = new URLSearchParams({
        fecha: this.fecha, maquina: this.maquinaA, turno: this.turno,
        excluir_formato: 'Bobinas',
      });
      if (this.registroId) params.set('excluir_id', String(this.registroId));
      const resp = await fetch(`${API_URL}/api/validacion/turno?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
      });
      if (!resp.ok) {
        this.alertaEsError = false;
        this.alertaConsistencia = 'No se pudo verificar la consistencia con Rotulado y Pesos (error del servidor). Se guardará de todas formas — revisa manualmente que el turno coincida en los 3 formatos.';
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
      this.alertaConsistencia = 'No se pudo verificar la consistencia con Rotulado y Pesos (sin conexión). Se guardará de todas formas — revisa manualmente que el turno coincida en los 3 formatos.';
      return true;
    }
  }

  camposFaltantes: string[] = [];

  private validarCamposObligatorios(): string[] {
    const faltan: string[] = [];
    if (!this.fecha) faltan.push('Fecha');
    if (!this.turno) faltan.push('Turno');
    if (!this.maquinaA) faltan.push('Máquina');
    if (!this.referencia_producto) faltan.push('Referencia de Producto');
    if (!this.firma_data) faltan.push('Firma del Operario (pide al administrador que registre tu firma)');
    const hayFilas = this.filasA.length > 0 || this.filasB.length > 0 || this.filasENF.length > 0;
    if (!hayFilas) faltan.push('Al menos una fila de producción (Empacadora A, B o Enfardadora)');
    return faltan;
  }

  /** Valores de peso fuera de rango que el operario aún no confirmó — bloquean el guardado */
  private validarRangosPeso(): string[] {
    const problemas: string[] = [];
    const revisar = (filas: Fila[], grupo: string) => {
      filas.forEach((f, i) => {
        if (f._atipico && !f._confirmadoAtipico) {
          problemas.push(
            `Fila ${i + 1} de Empacadora ${grupo}: el peso al montar parece un error de digitación ` +
            `(normal: ${RANGO_PESO_MONTAR.min}-${RANGO_PESO_MONTAR.max} kg). ` +
            `Corrígelo o confirma con el botón "Es correcto"junto al campo.`
          );
        }
      });
    };
    revisar(this.filasA, 'A');
    revisar(this.filasB, 'B');
    return problemas;
  }

  // Guarda Bobinas + Rotulado + Pesos juntos, leyendo los borradores de
  // localStorage que Rotulado/Pesos van guardando solos. Si alguno está
  // incompleto, no guarda nada.

  private leerBorrador(key: string): any | null {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    try { return JSON.parse(raw); } catch { return null; }
  }

  private validarBorradorRotulado(b: any | null): string[] {
    const problemas: string[] = [];
    if (!b) {
      problemas.push('Rotulado: todavía no se ha llenado — ve a esa pestaña y complétala primero.');
      return problemas;
    }
    const planillas = b.planillas || [];
    if (planillas.length === 0) problemas.push('Rotulado: no tiene ninguna planilla.');
    planillas.forEach((p: any, i: number) => {
      const etiqueta = planillas.length > 1 ? `Rotulado — Planilla ${i + 1}` : 'Rotulado';
      if (!p.maquina) problemas.push(`${etiqueta}: falta la Máquina`);
      if (!p.referencia) problemas.push(`${etiqueta}: falta la Referencia`);
    });
    return problemas;
  }

  private validarBorradorPesos(b: any | null): string[] {
    const problemas: string[] = [];
    if (!b) {
      problemas.push('Pesos: todavía no se ha llenado — ve a esa pestaña y complétala primero.');
      return problemas;
    }
    const planillas = b.planillas || [];
    if (planillas.length === 0) problemas.push('Pesos: no tiene ninguna planilla.');
    planillas.forEach((p: any, i: number) => {
      const etiqueta = planillas.length > 1 ? `Pesos — Planilla ${i + 1}` : 'Pesos';
      if (!p.maquina) problemas.push(`${etiqueta}: falta la Máquina`);
      if (!p.referencia || !String(p.referencia).trim()) problemas.push(`${etiqueta}: falta la Referencia`);
    });
    return problemas;
  }

  private async guardarPlanillasRotulado(b: any): Promise<void> {
    for (const p of b.planillas) {
      const filas: FilaRotulado[] = (p.filas || []).map((f: any) => ({
        numero_fila: f.numero_fila, hora: f.hora,
        fechado: f.fechado, fechado_cumple: f.fechado_cumple,
        sellado_cumple: f.sellado_cumple, referencia: p.referencia
      }));
      const payload: RegistroRotulado = {
        fecha: this.fecha, turno: this.turno, maquina: p.maquina,
        nombre_operario: this.nombre_operario, firma_data: this.firma_data,
        filas
      };
      if (p.registroId) {
        await this.svc.updateRotulado(p.registroId, payload).toPromise();
      } else {
        await this.svc.createRotulado(payload).toPromise();
      }
    }
  }

  private async guardarPlanillasPesos(b: any): Promise<void> {
    for (const p of b.planillas) {
      const filas: FilaPeso[] = (p.filas || []).map((f: any) => ({
        numero_fila: f.numero_fila, hora: f.hora,
        muestra_1: f.muestra_1, muestra_2: f.muestra_2, muestra_3: f.muestra_3,
        muestra_4: f.muestra_4, muestra_5: f.muestra_5, observaciones: f.observaciones
      }));
      const payload: RegistroPesos = {
        fecha: this.fecha, turno: this.turno, maquina: p.maquina, referencia: p.referencia,
        nombre_operario: this.nombre_operario, firma_data: this.firma_data,
        filas
      };
      if (p.registroId) {
        await this.svc.updatePesos(p.registroId, payload).toPromise();
      } else {
        await this.svc.createPesos(payload).toPromise();
      }
    }
  }

  async guardar(): Promise<void> {
    this.alertaConsistencia = null;
    this.camposFaltantes = [];
    this.conflictosConsistencia = [];

    const faltan = this.validarCamposObligatorios();
    if (faltan.length > 0) {
      this.alertaEsError = true;
      this.camposFaltantes = faltan;
      this.alertaConsistencia = 'Antes de guardar, completa estos campos obligatorios de Bobinas:';
      return;
    }

    const problemasPeso = this.validarRangosPeso();
    if (problemasPeso.length > 0) {
      this.alertaEsError = true;
      this.camposFaltantes = problemasPeso;
      this.alertaConsistencia = 'Hay pesos que parecen error de digitación — revisa antes de guardar:';
      return;
    }

    // Deben estar completos antes de guardar, para no dejar Bobinas guardado solo
    const borradorRotulado = this.leerBorrador('borrador_rotulado');
    const borradorPesos = this.leerBorrador('borrador_pesos');
    const problemasOtros = [
      ...this.validarBorradorRotulado(borradorRotulado),
      ...this.validarBorradorPesos(borradorPesos),
    ];
    if (problemasOtros.length > 0) {
      this.alertaEsError = true;
      this.camposFaltantes = problemasOtros;
      this.alertaConsistencia = 'Antes de guardar, completa Rotulado y Pesos (no se guarda nada hasta que estén completos):';
      return;
    }

    const ok = await this.validarConsistenciaTurno();
    if (!ok) return;

    const todasFilas: FilaBobina[] = [
      ...this.filasA.map((f, i) => ({ ...f, numero_fila: i+1, maquina_grupo: 'A', consumido: f._consumido, peso_montar: +f.peso_montar!||0, peso_desmontar: +f.peso_desmontar!||0, contador: +f.contador!||0 })),
      ...this.filasB.map((f, i) => ({ ...f, numero_fila: i+1+100, maquina_grupo: 'B', consumido: f._consumido, peso_montar: +f.peso_montar!||0, peso_desmontar: +f.peso_desmontar!||0, contador: +f.contador!||0 })),
      ...this.filasENF.map((f, i) => ({ ...f, numero_fila: i+1+200, maquina_grupo: 'ENF', consumido: f._consumido, peso_montar: +f.peso_montar!||0, peso_desmontar: +f.peso_desmontar!||0, contador: +f.contador!||0 })),
    ];
    const payload: RegistroBobinas = {
      periodo: this.periodo,
      referencia_producto: this.referencia_producto,
      referencia_enfardadora: this.referencia_enfardadora,
      maquina: this.esPar ? `${this.maquinaA}-${this.maquinaB}` : this.maquinaA,
      fecha: this.fecha, turno: this.turno,
      peso_desperdicio: +this.peso_desperdicio!||0,
      peso_desperdicio_fardo: +this.peso_desperdicio_fardo!||0,
      nombre_operario: this.nombre_operario, firma_data: this.firma_data,
      filas: todasFilas
    };

    try {
      if (this.registroId) {
        await this.svc.updateBobinas(this.registroId, payload).toPromise();
      } else {
        const res: any = await this.svc.createBobinas(payload).toPromise();
        this.registroId = res.id!;
      }

      await this.guardarPlanillasRotulado(borradorRotulado);
      await this.guardarPlanillasPesos(borradorPesos);

      this.limpiarBorrador();
      localStorage.removeItem('borrador_rotulado');
      localStorage.removeItem('borrador_pesos');
      this.limpiarContexto();
      this.mostrarToast('Guardado — Bobinas, Rotulado y Pesos');
    } catch {
      this.mostrarToast('Error al guardar — revisa tu conexión e intenta de nuevo');
    }
  }

  limpiar(): void {
    if (!confirm('¿Limpiar todos los datos del turno?')) return;
    this.periodo=''; this.referencia_producto=this.refs[0].key;
    this.maquinaA=''; this.maquinaB=''; this.esPar=false;
    this.fecha=''; this.turno='';
    this.peso_desperdicio=null; this.peso_desperdicio_fardo=null; this.nombre_operario=this.auth.getNombre(); this.registroId=null;
    this.filasA=[]; this.filasB=[]; this.filasENF=[];
    this.calcular(); this.cargarMiFirma(); this.limpiarBorrador(); this.limpiarContexto(); this.mostrarToast('Turno limpiado');
  }

  generarPDF(): void {
    this.mostrarToast('Abriendo...');
    const tituloOriginal = document.title;
    if (this.pro_numero || this.lote) {
      document.title = ['CONTROL DE EMPAQUE', this.pro_numero ? `PRO${this.pro_numero}` : '', this.lote ? `LOTE ${this.lote}` : '']
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