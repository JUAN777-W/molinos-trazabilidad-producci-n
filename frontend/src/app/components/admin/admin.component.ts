import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { AuthService, Usuario, UsuarioCreate } from '../../services/auth.service';
import { FormatosService } from '../../services/formatos.service';
import { RegistroBobinas, RegistroRotulado, RegistroPesos } from '../../models/formatos.model';
import { API_URL } from '../../config';

const MAQUINAS = ['1P','2Q','4T','5U','6V','7W','8S','9X','10Y','11Z'];
const AREAS_BODEGA = ['Trigo', 'Paquitas', 'Carrusel', 'Afrecho', 'Salvado'];

// ── Crear Salida (pide a Bodega) — card de planta (Kardex) + sugerencia histórica ──
interface ReferenciaEmpaqueOrden {
  codigo: string;
  descripcion: string;
  categoria?: string;
}

interface InventarioPlantaItem {
  codigo: string;
  descripcion: string;
  categoria?: string;
  saldo_planta_kg: number;
  saldo_planta_bobinas: number;
  consumo_promedio_diario_kg: number;
  cobertura_dias_planta?: number;
  estado_cobertura: string;   // SOBRA | OK | BAJO | SIN_DATO
  tiene_ajuste_manual: boolean;
}

interface SugerenciaOut {
  referencia_producto: string;
  kg_promedio_historico: number;
  kg_sugerido: number;
  bobinas_sugeridas: number;
  turnos_analizados: number;
  fuente_promedio_bobina: string;
  nota: string;
}

// ── Interfaces dashboard e informes ──────────────────────────────────────────
interface TarjetaResumen {
  total_turnos_hoy: number;
  total_turnos_mes: number;
  total_kg_consumidos_hoy: number;
  promedio_desperdicio_pct: number;
  fechados_no_cumplen_hoy: number;
  maquinas_activas_hoy: number;
}

interface ProduccionMaquina {
  maquina: string;
  total_kg: number;
  total_unidades: number;
  turnos: number;
}

interface UltimoRegistro {
  id: number;
  tipo: string;
  fecha: string;
  maquina: string;
  operario: string;
  turno: string;
}

interface MaquinaEstado {
  maquina: string;
  tipo: string;
  operario: string;
  activo: boolean;
  turno_actual: string;
  referencia: string;
  fecha_registro: string;
}

interface PuntoTendencia {
  fecha: string;
  kg_consumidos: number;
  turnos: number;
}

interface DashboardData {
  tarjetas: TarjetaResumen;
  produccion_por_maquina: ProduccionMaquina[];
  ultimos_registros: UltimoRegistro[];
  fechados_semana: Record<string, { cumplen: number; no_cumplen: number }>;
  tendencia_diaria: PuntoTendencia[];
  alertas: Alerta[];
  meta_desperdicio_pct: number;
}

interface Alerta {
  tipo: string;
  severidad: string;
  mensaje: string;
}

interface RankingOperario {
  operario: string;
  turnos: number;
  kg_totales: number;
  pct_desperdicio_promedio: number;
}

interface RankingOperariosOut {
  mejores_desperdicio: RankingOperario[];
  peores_desperdicio: RankingOperario[];
  mas_productivos: RankingOperario[];
}

interface DesperdicioPorReferencia {
  referencia: string;
  turnos: number;
  kg_consumidos: number;
  kg_desperdicio: number;
  pct_desperdicio: number;
}

interface MesHistorico {
  mes: string;
  kg_consumidos: number;
  pct_desperdicio: number;
  turnos: number;
  cumple_meta: boolean;
  variacion_kg_pct: number | null;
}

interface CeldaHeatmap {
  dia_semana: string;
  turno: string;
  pct_desperdicio_promedio: number;
  turnos: number;
}

interface CumplimientoPesos {
  total_muestras: number;
  dentro_rango: number;
  fuera_rango: number;
  pct_dentro_rango: number;
}

interface ProveedorReferenciaItem {
  referencia_producto: string;
  kg_consumidos: number;
  kg_desperdicio: number;
  pct_desperdicio: number;
  turnos: number;
}

interface ProveedorItem {
  proveedor: string;
  kg_consumidos: number;
  kg_desperdicio: number;
  pct_desperdicio: number;
  turnos: number;
  referencias: ProveedorReferenciaItem[];
}

interface ProveedoresResumen {
  proveedores: ProveedorItem[];
  mayor_consumo: string | null;
  menor_consumo: string | null;
  mejor_rendimiento: string | null;
  peor_rendimiento: string | null;
}

interface AnaliticaData {
  ranking_operarios: RankingOperariosOut;
  desperdicio_por_referencia: DesperdicioPorReferencia[];
  historico_mensual: MesHistorico[];
  heatmap_turno_dia: CeldaHeatmap[];
  cumplimiento_pesos: CumplimientoPesos;
  dias_analizados: number;
  meta_desperdicio_pct: number;
}

interface NotificacionItem {
  tipo: string;         // "PREVENTIVO" | "SOLICITUD"
  id_origen: number;
  maquina: string;
  descripcion: string;
  prioridad_o_estado: string;
  fecha: string;
}

interface PlanPreventivoItem {
  id: number;
  linea: string;
  seccion_componente: string;
  actividad: string;
  tipo?: string;
  frecuencia?: string;
  responsable?: string;
  tiempo_min?: number;
  repuesto_insumo?: string;
}

interface CronogramaItem {
  id: number;
  maquina: string;
  seccion_componente: string;
  frecuencia?: string;
  ultima_ejecucion?: string;
  proxima_fecha?: string;
  dias_para_vencer?: number;
  estado: string;
  observaciones?: string;
  turnos_produccion_recientes: number | null;
}

interface HistorialCorrectivoItem {
  id: number;
  maquina: string;
  equipo_componente: string;
  fecha_mantenimiento: string;
  fecha_cambio?: string;
  mantenimiento_realizado: string;
  costo?: number;
  estado_resultante: string;
  hubo_cambio: string;
  prioridad?: string;
}

interface RepuestoCriticoItem {
  id: number;
  seccion?: string;
  componente?: string;
  referencia?: string;
  marca?: string;
  cantidad_instalada?: number;
  maquinas_aplica?: string;
  stock_minimo_sugerido?: number;
}

interface ResumenMantenimiento {
  total_puntos: number;
  vencidos: number;
  proximos: number;
  ok: number;
  sin_registrar: number;
  costo_total_historico: number;
  pct_historico_con_costo: number;
}

interface InformeResumen {
  id: number;
  fecha: string;
  turno: string;
  turno_label: string;
  maquina: string;
  operario: string;
  generado_en: string;
  pro_numero: string;
  lote: string;
}

interface ConsumoEmpaque {
  descripcion: string;
  consumo_produccion: number;
  desperdicio: number;
  consumo_total: number;
  porcentaje_desperdicio: number;
}

interface Productividad {
  tipo: string;
  meta_valor: number;
  meta_unidad: string;
  logrado: number;
  pct_meta: number;
  cumple_meta: boolean;
  total_pacas: number;
  divisor_usado: number;
}

interface InformeCompleto {
  id: number;
  fecha: string;
  turno: string;
  turno_label: string;
  maquina: string;
  operario: string;
  filas_maquinas: any[];
  total_produccion_maquinas: { empacadoras_AB: number; enfardadora: number; total_pacas: number; divisor: number };
  productividad: Productividad;
  total_fechados: number;
  fechados_cumplen: number;
  fechados_no_cumplen: number;
  consumo_empaque: ConsumoEmpaque[];
  total_consumido_kg: number;
  total_desperdicio_kg: number;
  porcentaje_desperdicio_global: number;
  total_muestras_pesos: number;
  generado_en: string;
}

interface InventarioItem {
  codigo: string;
  descripcion: string;
  categoria?: string;
  saldo_kg: number;
  saldo_bobinas: number;
  consumo_promedio_mensual_kg: number;
  cobertura_dias?: number;
  estado_cobertura: string;
  pedidos_pendientes_kg: number;
  proxima_entrega_fecha?: string;
}


@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './admin.component.html'
})
export class AdminComponent implements OnInit {
  tab = 'dashboard';

  // Usuarios
  usuarios: Usuario[] = [];
  maquinasDisponibles = MAQUINAS;
  mostrarFormUsuario = false;
  editandoId: number | null = null;
  formUsuario: UsuarioCreate & { activo?: string } = this.nuevoForm();
  errorUsuario = '';
  toastUsuario = '';

  // Filtros informes
  filtroOperario = '';
  filtroFecha = '';
  filtroMaquina = '';

  // Dashboard
  dashboard: DashboardData | null = null;
  cargandoDashboard = false;
  dashboardSubTab: string = 'resumen';

  // Panel Ejecutivo — Analítica Avanzada
  analitica: AnaliticaData | null = null;
  cargandoAnalitica = false;

  // Rendimiento por Proveedor de Empaque
  cargandoProveedores = false;
  resumenProveedores: ProveedoresResumen | null = null;
  proveedorExpandido: string | null = null;
  alertasInventario: InventarioItem[] = [];
  cargandoAlertasInventario = false;

  // ── Crear Salida (pide a Bodega) — card de planta + sugerencia histórica ─────
  areasBodega = AREAS_BODEGA;
  turnosOrden = [
    { key: 'T1', label: 'Turno 1 — 6:00 a.m. a 2:00 p.m.' },
    { key: 'T2', label: 'Turno 2 — 2:00 p.m. a 10:00 p.m.' },
    { key: 'T3', label: 'Turno 3 — 10:00 p.m. a 6:00 a.m.' },
  ];
  referenciasEmpaqueOrden: ReferenciaEmpaqueOrden[] = [];
  cargandoReferenciasOrden = false;
  formNuevaOrden = this.nuevoFormOrden();
  guardandoOrden = false;
  errorOrden = '';
  toastOrden = '';
  cardPlanta: InventarioPlantaItem | null = null;
  cargandoCardPlanta = false;
  sugerenciaPedido: SugerenciaOut | null = null;
  cargandoSugerencia = false;

  nuevoFormOrden() {
    return {
      fecha: new Date().toISOString().slice(0, 10),
      turno: '',
      area_solicitante: 'Producción',
      codigo_producto: '',
      referencia_producto: '',
      cantidad_bobinas: 0,
      cantidad_kg: 0,
      observaciones: '',
    };
  }

  cargarReferenciasOrden(): void {
    this.cargandoReferenciasOrden = true;
    fetch(`${API_URL}/api/bodega/referencias`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => { this.referenciasEmpaqueOrden = Array.isArray(d) ? d : []; this.cargandoReferenciasOrden = false; })
      .catch(() => { this.cargandoReferenciasOrden = false; });
  }

  seleccionarReferenciaOrden(codigo: string): void {
    const ref = this.referenciasEmpaqueOrden.find(r => r.codigo === codigo);
    this.cardPlanta = null;
    this.sugerenciaPedido = null;
    if (!ref) return;
    this.formNuevaOrden.codigo_producto = ref.codigo;
    this.formNuevaOrden.referencia_producto = ref.descripcion;

    this.cargandoCardPlanta = true;
    fetch(`${API_URL}/api/bodega/inventario-planta/${ref.codigo}`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.ok ? r.json() : null)
      .then(d => { this.cardPlanta = d; this.cargandoCardPlanta = false; })
      .catch(() => { this.cargandoCardPlanta = false; });

    this.cargandoSugerencia = true;
    fetch(`${API_URL}/api/bodega/sugerencia?referencia=${encodeURIComponent(ref.descripcion)}&codigo_producto=${ref.codigo}`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.ok ? r.json() : null)
      .then(d => { this.sugerenciaPedido = d; this.cargandoSugerencia = false; })
      .catch(() => { this.cargandoSugerencia = false; });
  }

  coberturaPlantaColor(estado: string): string {
    switch (estado) {
      case 'SOBRA': return 'bg-emerald-100 text-emerald-700';
      case 'OK': return 'bg-blue-100 text-brand-blue';
      case 'BAJO': return 'bg-red-100 text-brand-red';
      default: return 'bg-gray-200 text-gray-600';
    }
  }

  coberturaPlantaLabel(estado: string): string {
    switch (estado) {
      case 'SOBRA': return 'Sobra en planta';
      case 'OK': return 'Cobertura OK';
      case 'BAJO': return 'Cobertura baja — pide ya';
      default: return 'Sin dato de consumo';
    }
  }

  crearOrdenSalida(): void {
    this.errorOrden = '';
    this.toastOrden = '';
    if (!this.formNuevaOrden.turno || !this.formNuevaOrden.referencia_producto || this.formNuevaOrden.cantidad_kg <= 0) {
      this.errorOrden = 'Completa turno, referencia y una cantidad en Kg mayor a cero.';
      return;
    }
    this.guardandoOrden = true;
    fetch(`${API_URL}/api/bodega/ordenes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${this.auth.getToken()}` },
      body: JSON.stringify(this.formNuevaOrden),
    })
      .then(async r => {
        if (!r.ok) {
          const err = await r.json().catch(() => null);
          throw new Error(err?.detail || 'Error al crear la orden de salida');
        }
        return r.json();
      })
      .then(() => {
        this.guardandoOrden = false;
        this.formNuevaOrden = this.nuevoFormOrden();
        this.cardPlanta = null;
        this.sugerenciaPedido = null;
        this.toastOrden = 'Orden de salida registrada correctamente.';
      })
      .catch((e: Error) => {
        this.guardandoOrden = false;
        this.errorOrden = e.message || 'Error al crear la orden de salida';
      });
  }

  toggleProveedor(nombre: string): void {
    this.proveedorExpandido = this.proveedorExpandido === nombre ? null : nombre;
  }

  // Monitor máquinas
  monitor: MaquinaEstado[] = [];
  cargandoMonitor = false;

  // Informes
  informes: InformeResumen[] = [];
  informeSeleccionado: InformeCompleto | null = null;
  informeGeneral: any = null;
  cargandoInforme = false;
  cargandoGeneral = false;
  mostrandoInforme = false;
  mostrandoGeneral = false;
  filtroInformeFecha = '';
  filtroInformeTurno = '';

  // ── Notificaciones (campanita) ───────────────────────────────────────────────
  notificaciones: NotificacionItem[] = [];
  cargandoNotificaciones = false;
  mostrandoNotificaciones = false;
  mostrandoModalResolverSolicitud = false;
  solicitudAResolver: NotificacionItem | null = null;
  formResolverSolicitud = { resolucion_descripcion: '', costo: null as number | null, estado_resultante: 'BUENO', hubo_cambio: 'NO' };

  // ── Mantenimiento ─────────────────────────────────────────────────────────
  mttoSubTab: 'cronograma' | 'plan' | 'historial' | 'repuestos' = 'cronograma';
  resumenMtto: ResumenMantenimiento | null = null;

  cronograma: CronogramaItem[] = [];
  cargandoCronograma = false;
  filtroMttoEstado = '';

  planPreventivo: PlanPreventivoItem[] = [];
  cargandoPlan = false;
  filtroMttoLinea = '';

  historialCorrectivo: HistorialCorrectivoItem[] = [];
  cargandoHistorial = false;
  formHistorial: any = this.formHistorialVacio();

  repuestosCriticos: RepuestoCriticoItem[] = [];
  cargandoRepuestos = false;
  filtroMttoRepuesto = '';

  mostrandoModalEjecucion = false;
  itemEjecucion: CronogramaItem | null = null;
  fechaEjecucion = '';
  observacionesEjecucion = '';
  resolviendoSolicitud = false;

  Math = Math; // expuesto para usar Math.max en la plantilla del histórico mensual

  constructor(private auth: AuthService, private svc: FormatosService, private route: ActivatedRoute) {}

  ngOnInit(): void {
    const tabPedida = this.route.snapshot.queryParamMap.get('tab');
    if (tabPedida) this.tab = tabPedida;
    this.cargarUsuarios();
    this.cargarDashboard();
    this.cargarAnalitica();
    this.cargarResumenProveedores();
    this.cargarInformes();
    this.cargarMonitor();
    this.cargarAlertasInventario();
    this.cargarResumenMtto();
    this.cargarCronograma();
    this.cargarNotificaciones();
    this.cargarReferenciasOrden();
  }

  get nombreAdmin(): string { return this.auth.getNombre(); }

  private hoyISO(): string {
    return new Date().toISOString().slice(0, 10);
  }

  // ── Dashboard ─────────────────────────────────────────────────────────────
  cargarDashboard(): void {
    this.cargandoDashboard = true;
    fetch(`${API_URL}/api/dashboard/`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => { this.dashboard = d; this.cargandoDashboard = false; })
      .catch(() => { this.cargandoDashboard = false; });
  }

  cargarResumenProveedores(): void {
    this.cargandoProveedores = true;
    fetch(`${API_URL}/api/dashboard/proveedores`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => { this.resumenProveedores = d; this.cargandoProveedores = false; })
      .catch(() => { this.cargandoProveedores = false; });
  }

  get maxKgProductivo(): number {
    if (!this.analitica?.ranking_operarios?.mas_productivos?.length) return 1;
    return Math.max(...this.analitica.ranking_operarios.mas_productivos.map(r => r.kg_totales), 1);
  }

  get maxKgProveedor(): number {
    if (!this.resumenProveedores?.proveedores?.length) return 1;
    return Math.max(...this.resumenProveedores.proveedores.map(p => p.kg_consumidos), 1);
  }

  cargarAnalitica(): void {
    this.cargandoAnalitica = true;
    fetch(`${API_URL}/api/dashboard/analitica`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => { this.analitica = d; this.cargandoAnalitica = false; })
      .catch(() => { this.cargandoAnalitica = false; });
  }

  /** Color de fondo para una celda del mapa de calor según % de desperdicio */
  colorHeatmap(pct: number, turnos: number): string {
    if (turnos === 0) return 'bg-gray-50 text-gray-300';
    if (pct <= 0) return 'bg-gray-50 text-gray-400';
    if (pct <= 2) return 'bg-emerald-100 text-emerald-800';
    if (pct <= 3) return 'bg-emerald-50 text-emerald-700';
    if (pct <= 4) return 'bg-amber-100 text-amber-800';
    if (pct <= 5.5) return 'bg-orange-100 text-orange-800';
    return 'bg-red-100 text-red-800';
  }

  /** Celda del heatmap para un turno+día específico, o null si no hay datos */
  celdaHeatmap(dia: string, turno: string): CeldaHeatmap | undefined {
    return this.analitica?.heatmap_turno_dia.find(c => c.dia_semana === dia && c.turno === turno);
  }

  get diasSemanaHeatmap(): string[] {
    return ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
  }

  get maxKgReferencia(): number {
    if (!this.analitica?.desperdicio_por_referencia?.length) return 1;
    return Math.max(...this.analitica.desperdicio_por_referencia.map(r => r.kg_consumidos), 1);
  }

  get maxKgHistorico(): number {
    if (!this.analitica?.historico_mensual?.length) return 1;
    return Math.max(...this.analitica.historico_mensual.map(m => m.kg_consumidos), 1);
  }

  /** % de desperdicio promedio y turnos registrados por T1/T2/T3, derivado del heatmap */
  get resumenPorTurno(): { turno: string; pct: number; turnos: number }[] {
    return ['T1', 'T2', 'T3'].map(turno => {
      const celdas = (this.analitica?.heatmap_turno_dia ?? []).filter(c => c.turno === turno && c.turnos > 0);
      const totalTurnos = celdas.reduce((s, c) => s + c.turnos, 0);
      const pct = totalTurnos > 0
        ? celdas.reduce((s, c) => s + c.pct_desperdicio_promedio * c.turnos, 0) / totalTurnos
        : 0;
      return { turno, pct: Math.round(pct * 10) / 10, turnos: totalTurnos };
    });
  }

  get maxTurnos(): number {
    return Math.max(...this.resumenPorTurno.map(t => t.turnos), 1);
  }

  /** Titular en lenguaje simple con lo más importante del día, para leer de un vistazo */
  get insightPrincipal(): { tipo: 'good' | 'warning' | 'critical'; titulo: string; detalle: string } | null {
    const t = this.dashboard?.tarjetas;
    if (!t) return null;
    const meta = this.dashboard!.meta_desperdicio_pct;
    const sobreMeta = t.promedio_desperdicio_pct > meta;
    if (t.total_turnos_hoy === 0) {
      return {
        tipo: 'warning',
        titulo: 'Todavía no hay turnos registrados hoy',
        detalle: `${t.total_turnos_mes} turno(s) acumulados este mes.`,
      };
    }
    if (sobreMeta || t.fechados_no_cumplen_hoy > 0) {
      const partes: string[] = [];
      if (sobreMeta) partes.push(`el desperdicio de hoy (${t.promedio_desperdicio_pct}%) está por encima de la meta (${meta}%)`);
      if (t.fechados_no_cumplen_hoy > 0) partes.push(`${t.fechados_no_cumplen_hoy} fechado(s) no cumplen hoy`);
      return {
        tipo: sobreMeta ? 'critical' : 'warning',
        titulo: 'Hay puntos que revisar hoy',
        detalle: partes.join(' · ') + '.',
      };
    }
    return {
      tipo: 'good',
      titulo: 'La producción de hoy va bien',
      detalle: `Desperdicio ${t.promedio_desperdicio_pct}% (meta ${meta}%) · ${t.total_turnos_hoy} turno(s) registrados hoy en ${t.maquinas_activas_hoy} máquina(s).`,
    };
  }

  // ══════════════════════════════════════════════════════════════════════════
  // MANTENIMIENTO
  // ══════════════════════════════════════════════════════════════════════════
  private formHistorialVacio() {
    return {
      maquina: '', equipo_componente: '', fecha_mantenimiento: '',
      mantenimiento_realizado: '', costo: null, prioridad: '',
      estado_resultante: 'BUENO', hubo_cambio: 'SI',
    };
  }

  cambiarMttoSubTab(tab: string): void {
    this.mttoSubTab = tab as 'cronograma' | 'plan' | 'historial' | 'repuestos';
    if (tab === 'cronograma' && this.cronograma.length === 0) this.cargarCronograma();
    if (tab === 'plan' && this.planPreventivo.length === 0) this.cargarPlanPreventivo();
    if (tab === 'historial' && this.historialCorrectivo.length === 0) this.cargarHistorial();
    if (tab === 'repuestos' && this.repuestosCriticos.length === 0) this.cargarRepuestos();
  }

  cargarResumenMtto(): void {
    fetch(`${API_URL}/api/mantenimiento/resumen`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => this.resumenMtto = d)
      .catch(() => {});
  }

  cargarCronograma(): void {
    this.cargandoCronograma = true;
    const params = new URLSearchParams();
    if (this.filtroMttoEstado) params.set('estado', this.filtroMttoEstado);
    fetch(`${API_URL}/api/mantenimiento/cronograma?${params.toString()}`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => { this.cronograma = Array.isArray(d) ? d : []; this.cargandoCronograma = false; })
      .catch(() => { this.cargandoCronograma = false; });
  }

  cargarPlanPreventivo(): void {
    this.cargandoPlan = true;
    const params = new URLSearchParams();
    if (this.filtroMttoLinea) params.set('linea', this.filtroMttoLinea);
    fetch(`${API_URL}/api/mantenimiento/plan-preventivo?${params.toString()}`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => { this.planPreventivo = Array.isArray(d) ? d : []; this.cargandoPlan = false; })
      .catch(() => { this.cargandoPlan = false; });
  }

  cargarHistorial(): void {
    this.cargandoHistorial = true;
    fetch(`${API_URL}/api/mantenimiento/historial`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => { this.historialCorrectivo = Array.isArray(d) ? d : []; this.cargandoHistorial = false; })
      .catch(() => { this.cargandoHistorial = false; });
  }

  guardarHistorial(): void {
    if (!this.formHistorial.maquina || !this.formHistorial.equipo_componente ||
        !this.formHistorial.fecha_mantenimiento || !this.formHistorial.mantenimiento_realizado) {
      alert('Completa al menos: máquina, componente, fecha y descripción del mantenimiento.');
      return;
    }
    fetch(`${API_URL}/api/mantenimiento/historial`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${this.auth.getToken()}` },
      body: JSON.stringify(this.formHistorial)
    })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(() => {
        this.formHistorial = this.formHistorialVacio();
        this.cargarHistorial();
        this.cargarResumenMtto();
      })
      .catch(() => alert('Error al guardar el registro'));
  }

  cargarRepuestos(): void {
    this.cargandoRepuestos = true;
    const params = new URLSearchParams();
    if (this.filtroMttoRepuesto) params.set('maquina', this.filtroMttoRepuesto);
    fetch(`${API_URL}/api/mantenimiento/repuestos?${params.toString()}`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => { this.repuestosCriticos = Array.isArray(d) ? d : []; this.cargandoRepuestos = false; })
      .catch(() => { this.cargandoRepuestos = false; });
  }

  abrirModalEjecucion(item: CronogramaItem): void {
    this.itemEjecucion = item;
    this.fechaEjecucion = this.hoyISO();
    this.observacionesEjecucion = '';
    this.mostrandoModalEjecucion = true;
  }

  confirmarEjecucion(): void {
    if (!this.itemEjecucion) return;
    fetch(`${API_URL}/api/mantenimiento/cronograma/${this.itemEjecucion.id}/ejecutar`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${this.auth.getToken()}` },
      body: JSON.stringify({ ultima_ejecucion: this.fechaEjecucion, observaciones: this.observacionesEjecucion || null })
    })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(() => {
        this.mostrandoModalEjecucion = false;
        this.cargarCronograma();
        this.cargarResumenMtto();
      })
      .catch(() => alert('Error al registrar la ejecución'));
  }

  estadoMttoColor(estado: string): string {
    switch (estado) {
      case 'VENCIDO': return 'text-brand-red bg-red-50';
      case 'PROXIMO': return 'text-brand-gold-dark bg-brand-gold-50';
      case 'OK': return 'text-emerald-700 bg-emerald-50';
      default: return 'text-gray-500 bg-gray-100';
    }
  }

  estadoMttoLabel(estado: string): string {
    switch (estado) {
      case 'VENCIDO': return 'Vencido';
      case 'PROXIMO': return 'Próximo';
      case 'OK': return 'Al día';
      default: return 'Sin registrar';
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // NOTIFICACIONES (campanita)
  // ══════════════════════════════════════════════════════════════════════════
  toggleNotificaciones(): void {
    this.mostrandoNotificaciones = !this.mostrandoNotificaciones;
    if (this.mostrandoNotificaciones) this.cargarNotificaciones();
  }

  irAMantenimiento(): void {
    this.mostrandoNotificaciones = false;
    this.tab = 'mantenimiento';
    this.mttoSubTab = 'cronograma';
  }

  cargarNotificaciones(): void {
    this.cargandoNotificaciones = true;
    fetch(`${API_URL}/api/mantenimiento/notificaciones`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => { this.notificaciones = Array.isArray(d) ? d : []; this.cargandoNotificaciones = false; })
      .catch(() => { this.cargandoNotificaciones = false; });
  }

  abrirModalResolverSolicitud(n: NotificacionItem): void {
    this.solicitudAResolver = n;
    this.formResolverSolicitud = { resolucion_descripcion: '', costo: null, estado_resultante: 'BUENO', hubo_cambio: 'NO' };
    this.mostrandoModalResolverSolicitud = true;
  }

  cerrarModalResolverSolicitud(): void {
    this.mostrandoModalResolverSolicitud = false;
    this.solicitudAResolver = null;
  }

  resolverSolicitud(): void {
    if (!this.solicitudAResolver) return;
    if (!this.formResolverSolicitud.resolucion_descripcion.trim()) {
      alert('Describe qué se hizo para resolverlo.');
      return;
    }
    this.resolviendoSolicitud = true;
    fetch(`${API_URL}/api/mantenimiento/solicitudes/${this.solicitudAResolver.id_origen}/resolver`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${this.auth.getToken()}` },
      body: JSON.stringify(this.formResolverSolicitud)
    })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(() => {
        this.resolviendoSolicitud = false;
        this.cerrarModalResolverSolicitud();
        this.cargarNotificaciones();
        this.cargarHistorial(); // el Historial Correctivo también se actualiza, ya que queda registrado ahí
      })
      .catch(() => { this.resolviendoSolicitud = false; alert('Error al resolver la solicitud'); });
  }

  cargarMonitor(): void {
    this.cargandoMonitor = true;
    fetch(`${API_URL}/api/dashboard/monitor`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => { this.monitor = Array.isArray(d) ? d : []; this.cargandoMonitor = false; })
      .catch(() => { this.cargandoMonitor = false; });
  }

  cargarAlertasInventario(): void {
    this.cargandoAlertasInventario = true;
    fetch(`${API_URL}/api/bodega/alertas-inventario`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => { this.alertasInventario = Array.isArray(d) ? d : []; this.cargandoAlertasInventario = false; })
      .catch(() => { this.cargandoAlertasInventario = false; });
  }

  get diasSemana(): string[] {
    return this.dashboard ? Object.keys(this.dashboard.fechados_semana) : [];
  }

  maxBarraMaquina(): number {
    if (!this.dashboard?.produccion_por_maquina?.length) return 1;
    return Math.max(...this.dashboard.produccion_por_maquina.map(m => m.total_kg));
  }

  anchoBarra(kg: number): number {
    const max = this.maxBarraMaquina();
    return max > 0 ? Math.round((kg / max) * 100) : 0;
  }

  // ── Tendencia diaria (mini gráfico de barras, se mantiene por compatibilidad) ──
  maxTendencia(): number {
    if (!this.dashboard?.tendencia_diaria?.length) return 1;
    return Math.max(...this.dashboard.tendencia_diaria.map(t => t.kg_consumidos), 1);
  }

  altoBarraTendencia(kg: number): number {
    const max = this.maxTendencia();
    return max > 0 ? Math.round((kg / max) * 100) : 0;
  }

  fechaCorta(fecha: string): string {
    // "2026-07-10" -> "10/07"
    const partes = fecha.split('-');
    return partes.length === 3 ? `${partes[2]}/${partes[1]}` : fecha;
  }

  severidadColor(sev: string): string {
    return sev === 'alta' ? 'bg-red-50 border-red-300 text-red-700' : 'bg-amber-50 border-amber-300 text-amber-700';
  }

  // ── Fecha actual formateada para el header del dashboard ───────────────────
  get fechaHoyFormateada(): string {
    const f = new Date().toLocaleDateString('es-CO', {
      weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
    });
    return f.charAt(0).toUpperCase() + f.slice(1);
  }

  // ── Gráfico SVG de tendencia diaria (área + línea) ──────────────────────────
  private readonly chartW = 700;
  private readonly chartH = 200;
  private readonly padTop = 15;
  private readonly padBottom = 25;

  private tendenciaCoords(): { x: number; y: number; fecha: string; kg: number }[] {
    const data = this.dashboard?.tendencia_diaria ?? [];
    if (!data.length) return [];
    const max = Math.max(...data.map(d => d.kg_consumidos), 1);
    const usableH = this.chartH - this.padTop - this.padBottom;
    const stepX = data.length > 1 ? this.chartW / (data.length - 1) : 0;
    return data.map((d, i) => ({
      x: Math.round(i * stepX),
      y: Math.round(this.padTop + usableH - (d.kg_consumidos / max) * usableH),
      fecha: this.fechaCorta(d.fecha),
      kg: d.kg_consumidos
    }));
  }

  puntosTendenciaCoords() { return this.tendenciaCoords(); }

  lineaTendenciaPath(): string {
    const pts = this.tendenciaCoords();
    if (!pts.length) return '';
    return pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ');
  }

  areaTendenciaPath(): string {
    const pts = this.tendenciaCoords();
    if (!pts.length) return '';
    const base = this.chartH - this.padBottom;
    let d = `M${pts[0].x},${base} L${pts[0].x},${pts[0].y} `;
    for (let i = 1; i < pts.length; i++) d += `L${pts[i].x},${pts[i].y} `;
    d += `L${pts[pts.length - 1].x},${base} Z`;
    return d;
  }

  // ── Gauge circular (dona) para % de desperdicio vs. meta ────────────────────
  donutBackground(): string {
    const pct = this.dashboard?.tarjetas?.promedio_desperdicio_pct ?? 0;
    const meta = this.dashboard?.meta_desperdicio_pct ?? 3;
    const maxScale = Math.max(meta * 2.5, pct * 1.1, 5);
    const fraction = Math.min((pct / maxScale) * 100, 100);
    const color = pct > meta ? '#D62828' : '#0B8457';
    return `conic-gradient(${color} 0% ${fraction}%, #E5E7EB ${fraction}% 100%)`;
  }

  donutColorClass(): string {
    const pct = this.dashboard?.tarjetas?.promedio_desperdicio_pct ?? 0;
    const meta = this.dashboard?.meta_desperdicio_pct ?? 3;
    return pct > meta ? 'text-brand-red' : 'text-emerald-600';
  }

  // ── Barras comparadas (mes actual vs. mes anterior) ─────────────────────────
  pctBarWidth(valorA: number, valorB: number): number {
    const max = Math.max(Math.abs(valorA), Math.abs(valorB), 1);
    return Math.round((Math.abs(valorA) / max) * 100);
  }

  // ── Informes ──────────────────────────────────────────────────────────────
  cargarInformes(): void {
    fetch(`${API_URL}/api/informes/`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => { this.informes = Array.isArray(d) ? d : []; })
      .catch(() => {});
  }

  cargandoEnlacesPlanilla: number | null = null;

  /** Abre en pestañas nuevas la planilla exacta de Bobinas, Rotulado y Pesos
   *  de un turno guardado — en modo solo lectura, listas para imprimir/PDF. */
  mostrandoPanelPlanillas = false;
  planillasEncontradas: { tipo: string; id: number; label: string }[] = [];

  /** Busca las planillas exactas de un turno (Bobinas + Rotulado + Pesos) y
   *  las muestra como botones para abrir una por una — NO se abren solas,
   *  porque los navegadores bloquean varias ventanas abiertas automáticamente
   *  después de una consulta al servidor (solo la primera pasa el bloqueo). */
  verPlanillas(informe: InformeResumen): void {
    this.cargandoEnlacesPlanilla = informe.id;
    this.planillasEncontradas = [{ tipo: 'bobinas', id: informe.id, label: `Bobinas — Máq. ${informe.maquina}` }];

    fetch(`${API_URL}/api/informes/${informe.id}/enlaces`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then((enlaces: { bobinas_id: number; rotulado_ids: number[]; pesos_ids: number[]; pesos_enfardadora_ids: number[] }) => {
        enlaces.rotulado_ids.forEach((id, i) =>
          this.planillasEncontradas.push({ tipo: 'rotulado', id, label: `Rotulado${enlaces.rotulado_ids.length > 1 ? ' — Planilla ' + (i + 1) : ''}` })
        );
        enlaces.pesos_ids.forEach((id, i) =>
          this.planillasEncontradas.push({ tipo: 'pesos', id, label: `Pesos${enlaces.pesos_ids.length > 1 ? ' — Planilla ' + (i + 1) : ''}` })
        );
        (enlaces.pesos_enfardadora_ids || []).forEach((id, i) =>
          this.planillasEncontradas.push({ tipo: 'pesos-enfardadora', id, label: `Pesos Enfardadora${enlaces.pesos_enfardadora_ids.length > 1 ? ' — Planilla ' + (i + 1) : ''}` })
        );
        this.cargandoEnlacesPlanilla = null;
        this.mostrandoPanelPlanillas = true;
      })
      .catch(() => {
        this.cargandoEnlacesPlanilla = null;
        this.mostrandoPanelPlanillas = true; // igual muestra el panel — al menos Bobinas sí se puede abrir
      });
  }

  abrirPlanilla(p: { tipo: string; id: number }): void {
    window.open(`/${p.tipo}?verId=${p.id}`, '_blank');
  }

  // ── Asignar PRO / Lote de exportación (aplica a las 4 planillas del turno/máquina) ──
  mostrandoAsignarExportacion = false;
  informeParaAsignar: InformeResumen | null = null;
  proNumeroInput = '';
  loteInput = '';
  guardandoExportacion = false;
  toastInformes = '';

  abrirAsignarExportacion(informe: InformeResumen): void {
    this.informeParaAsignar = informe;
    this.proNumeroInput = informe.pro_numero || '';
    this.loteInput = informe.lote || '';
    this.mostrandoAsignarExportacion = true;
  }

  cerrarAsignarExportacion(): void {
    this.mostrandoAsignarExportacion = false;
    this.informeParaAsignar = null;
  }

  guardarAsignacionExportacion(): void {
    if (!this.informeParaAsignar) return;
    this.guardandoExportacion = true;
    fetch(`${API_URL}/api/informes/${this.informeParaAsignar.id}/asignar-exportacion`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${this.auth.getToken()}` },
      body: JSON.stringify({ pro_numero: this.proNumeroInput.trim(), lote: this.loteInput.trim() })
    })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then((res: { correo_enviado: boolean; correo_error: string }) => {
        this.guardandoExportacion = false;
        this.mostrarToastInformes(
          res.correo_enviado
            ? 'PRO y lote asignados, y las 4 planillas ya se enviaron por correo'
            : `PRO y lote asignados a las 4 planillas. No se enviaron por correo: ${res.correo_error || 'motivo desconocido'}`
        );
        this.cerrarAsignarExportacion();
        this.cargarInformes();
      })
      .catch(() => {
        this.guardandoExportacion = false;
        this.mostrarToastInformes('No se pudo guardar el PRO/lote — intenta de nuevo');
      });
  }

  reenviandoExportacion: number | null = null;

  reenviarExportacion(informe: InformeResumen): void {
    this.reenviandoExportacion = informe.id;
    fetch(`${API_URL}/api/informes/${informe.id}/reenviar-exportacion`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then((res: { correo_enviado: boolean; correo_error: string }) => {
        this.reenviandoExportacion = null;
        this.mostrarToastInformes(
          res.correo_enviado ? 'Planillas reenviadas por correo' : `No se pudo reenviar: ${res.correo_error || 'motivo desconocido'}`
        );
      })
      .catch(() => {
        this.reenviandoExportacion = null;
        this.mostrarToastInformes('No se pudo reenviar — intenta de nuevo');
      });
  }

  mostrarToastInformes(msg: string): void {
    this.toastInformes = msg; setTimeout(() => this.toastInformes = '', 4000);
  }

  cerrarPanelPlanillas(): void {
    this.mostrandoPanelPlanillas = false;
    this.planillasEncontradas = [];
  }

  verInformeGeneral(): void {
    if (!this.filtroInformeFecha || !this.filtroInformeTurno) {
      alert('Selecciona fecha y turno para generar el informe general.');
      return;
    }
    this.cargandoGeneral = true;
    this.mostrandoGeneral = true;
    fetch(`${API_URL}/api/informes/general?fecha=${this.filtroInformeFecha}&turno=${this.filtroInformeTurno}`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => { this.informeGeneral = d; this.cargandoGeneral = false; })
      .catch(() => { this.cargandoGeneral = false; this.mostrandoGeneral = false; alert('No hay registros para esa fecha y turno.'); });
  }

  cerrarGeneral(): void { this.mostrandoGeneral = false; this.informeGeneral = null; }

  verInforme(id: number): void {
    this.cargandoInforme = true;
    this.mostrandoInforme = true;
    fetch(`${API_URL}/api/informes/${id}`, {
      headers: { 'Authorization': `Bearer ${this.auth.getToken()}` }
    })
      .then(r => r.json())
      .then(d => { this.informeSeleccionado = d; this.cargandoInforme = false; })
      .catch(() => { this.cargandoInforme = false; });
  }

  cerrarInforme(): void {
    this.mostrandoInforme = false;
    this.informeSeleccionado = null;
  }

  imprimirInforme(): void { window.print(); }

  turnoColor(turno: string): string {
    return turno === 'T1' ? 'bg-blue-100 text-blue-800' :
           turno === 'T2' ? 'bg-amber-100 text-amber-800' :
                            'bg-purple-100 text-purple-800';
  }

  coberturaColor(estado: string): string {
    switch (estado) {
      case 'CRITICO': return 'bg-red-100 text-brand-red';
      case 'BAJO': return 'bg-amber-100 text-amber-700';
      case 'OK': return 'bg-emerald-100 text-emerald-700';
      default: return 'bg-gray-100 text-gray-500';
    }
  }

  // ── Usuarios ──────────────────────────────────────────────────────────────
  cargarUsuarios(): void {
    this.auth.getUsuarios().subscribe({ next: u => this.usuarios = u });
  }

  nuevoForm(): UsuarioCreate & { activo?: string } {
    return { nombre:'', cedula:'', username:'', password:'', rol:'operario', maquinas_asignadas:'', activo:'SI' };
  }

  abrirCrear(): void {
    this.formUsuario = this.nuevoForm(); this.editandoId = null;
    this.errorUsuario = ''; this.mostrarFormUsuario = true;
  }

  abrirEditar(u: Usuario): void {
    this.formUsuario = { nombre:u.nombre, cedula:u.cedula, username:u.username, password:'', rol:u.rol, maquinas_asignadas:u.maquinas_asignadas, activo:u.activo };
    this.editandoId = u.id; this.errorUsuario = ''; this.mostrarFormUsuario = true;
  }

  guardarUsuario(): void {
    this.errorUsuario = '';
    if (!this.formUsuario.nombre || !this.formUsuario.cedula || !this.formUsuario.username) {
      this.errorUsuario = 'Nombre, cédula y username son obligatorios.'; return;
    }
    if (!this.editandoId && !this.formUsuario.password) {
      this.errorUsuario = 'La contraseña es obligatoria al crear.'; return;
    }
    if (this.editandoId) {
      const data: any = { nombre: this.formUsuario.nombre, cedula: this.formUsuario.cedula, maquinas_asignadas: this.formUsuario.maquinas_asignadas, activo: this.formUsuario.activo };
      if (this.formUsuario.password) data.password = this.formUsuario.password;
      this.auth.actualizarUsuario(this.editandoId, data).subscribe({
        next: () => { this.cargarUsuarios(); this.mostrarFormUsuario=false; this.mostrarToastU('Usuario actualizado'); },
        error: e => this.errorUsuario = e.error?.detail ?? 'Error al actualizar.'
      });
    } else {
      this.auth.crearUsuario(this.formUsuario).subscribe({
        next: () => { this.cargarUsuarios(); this.mostrarFormUsuario=false; this.mostrarToastU('Usuario creado'); },
        error: e => this.errorUsuario = e.error?.detail ?? 'Error al crear.'
      });
    }
  }

  toggleActivo(u: Usuario): void {
    const nuevo = u.activo === 'SI' ? 'NO' : 'SI';
    this.auth.actualizarUsuario(u.id, { activo: nuevo }).subscribe({ next: () => this.cargarUsuarios() });
  }

  subirFirma(u: Usuario, event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      const base64 = reader.result as string;
      this.auth.subirFirma(u.id, base64).subscribe({
        next: () => this.mostrarToastU(`Firma de ${u.nombre} guardada`),
        error: () => this.mostrarToastU(`Error al subir la firma de ${u.nombre}`)
      });
    };
    reader.readAsDataURL(file);
    input.value = ''; // permite volver a subir el mismo archivo si hace falta reemplazarla
  }

  mostrarToastU(msg: string): void {
    this.toastUsuario = msg; setTimeout(() => this.toastUsuario = '', 2500);
  }

  limpiarFiltros(): void { this.filtroOperario=''; this.filtroFecha=''; this.filtroMaquina=''; }

  logout(): void { this.auth.logout(); window.location.href = '/login'; }
}