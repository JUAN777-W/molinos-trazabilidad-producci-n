import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';
import { API_URL } from '../../config';

// ── Interfaces ──────────────────────────────────────────────────────────────
interface ReferenciaEmpaque {
  codigo: string;
  descripcion: string;
  categoria?: string;
  promedio_bobina_kg?: number;
}

interface OrdenSalida {
  id: number;
  fecha: string;
  turno: string;
  area_solicitante: string;
  codigo_producto?: string;
  referencia_producto: string;
  cantidad_bobinas: number;
  cantidad_kg: number;
  observaciones?: string;
  nombre_operario: string;
  creado_en?: string;
}

interface ReconciliacionItem {
  orden_id: number;
  fecha: string;
  turno: string;
  referencia_producto: string;
  kg_pedido: number;
  bobinas_pedidas: number;
  kg_consumido_real: number;
  diferencia_kg: number;
  diferencia_pct: number;
  estado: string;
}

interface ReconciliacionResumen {
  fecha: string;
  total_ordenes: number;
  total_kg_pedido: number;
  total_kg_consumido: number;
  diferencia_total_kg: number;
  items: ReconciliacionItem[];
}

interface MovimientoInv {
  id: number;
  fecha: string;
  tipo_operacion: string;
  codigo_producto: string;
  referencia_producto: string;
  cantidad_kg: number;
  cantidad_bobinas: number;
  n_documento?: string;
  proveedor?: string;
  destino?: string;
  observaciones?: string;
  nombre_usuario: string;
  creado_en?: string;
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

interface PedidoCompra {
  id: number;
  numero_orden_compra?: string;
  fecha: string;
  proveedor: string;
  codigo_producto: string;
  referencia_producto: string;
  cantidad_pedida_kg: number;
  cantidad_recibida_kg: number;
  fecha_estimada?: string;
  precio_unitario?: number;
  estado: string;
  observaciones?: string;
  creado_en?: string;
}

interface RendimientoItem {
  referencia_producto: string;
  kg_consumido: number;
  unidades_producidas: number;
  rendimiento_unid_por_kg: number;
  desperdicio_kg: number;
  pct_desperdicio: number;
  turnos: number;
}

interface RendimientoResumen {
  mes: string;
  total_kg_consumido: number;
  total_unidades_producidas: number;
  total_desperdicio_kg: number;
  pct_desperdicio_promedio: number;
  variacion_kg_vs_mes_anterior_pct: number;
  items: RendimientoItem[];
}

@Component({
  selector: 'app-bodega',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './bodega.component.html'
})
export class BodegaComponent implements OnInit {
  subTab: 'ordenes' | 'movimientos' | 'inventario' | 'pedidos' | 'rendimientos' = 'inventario';

  toast = '';

  // Catálogo de referencias (para los formularios de movimientos y pedidos)
  referenciasEmpaque: ReferenciaEmpaque[] = [];
  cargandoReferencias = false;
  filtroRefMovimiento = '';
  filtroRefPedido = '';

  // Órdenes de salida recibidas (solo lectura, las llena producción) + reconciliación
  filtroOrdenesFecha = '';
  ordenesBodega: OrdenSalida[] = [];
  cargandoOrdenesBodega = false;
  filtroReconciliacionFecha = '';
  reconciliacion: ReconciliacionResumen | null = null;
  cargandoReconciliacion = false;
  ordenParaImprimir: OrdenSalida | null = null;
  mostrandoImprimirOrden = false;

  // Movimientos de inventario
  tiposMovimiento = [
    { value: 'COMPRA', label: 'Compra (entrada de proveedor)' },
    { value: 'DEVOLUCION', label: 'Devolución (vuelve a bodega)' },
    { value: 'MERCANCIA_NO_APTA', label: 'Mercancía No Apta (baja)' },
    { value: 'AJUSTE', label: 'Ajuste de inventario' },
    { value: 'INVENTARIO_INICIAL', label: 'Inventario Inicial' },
  ];
  formMovimiento = this.nuevoFormMovimiento();
  guardandoMovimiento = false;
  movimientos: MovimientoInv[] = [];
  cargandoMovimientos = false;
  filtroMovimientoFecha = '';

  // Control de Inventario
  inventario: InventarioItem[] = [];
  cargandoInventario = false;
  filtroInventarioCategoria = '';

  // Pedidos de Compra
  pedidos: PedidoCompra[] = [];
  cargandoPedidos = false;
  formPedido = this.nuevoFormPedido();
  guardandoPedido = false;
  pedidoRecepcion: PedidoCompra | null = null;
  formRecepcionKg = 0;
  guardandoRecepcion = false;

  // Rendimientos mensuales
  filtroRendimientoMes = '';
  rendimiento: RendimientoResumen | null = null;
  cargandoRendimiento = false;

  constructor(private auth: AuthService) {}

  ngOnInit(): void {
    this.filtroOrdenesFecha = this.hoyISO();
    this.filtroReconciliacionFecha = this.hoyISO();
    this.filtroRendimientoMes = this.hoyISO().slice(0, 7);
    this.cargarReferenciasEmpaque();
    this.cargarInventario();
  }

  get nombreUsuario(): string { return this.auth.getNombre(); }

  private hoyISO(): string {
    return new Date().toISOString().slice(0, 10);
  }

  private headers() {
    return { 'Authorization': `Bearer ${this.auth.getToken()}` };
  }

  logout(): void {
    this.auth.logout();
    window.location.href = '/login';
  }

  mostrarToast(msg: string): void {
    this.toast = msg;
    setTimeout(() => this.toast = '', 3000);
  }

  cambiarSubTab(tab: string): void {
    this.subTab = tab as 'inventario' | 'ordenes' | 'movimientos' | 'pedidos' | 'rendimientos';
    if (tab === 'ordenes') this.cargarOrdenesBodega();
    if (tab === 'movimientos') this.cargarMovimientos();
    if (tab === 'inventario') this.cargarInventario();
    if (tab === 'pedidos') this.cargarPedidos();
    if (tab === 'rendimientos') this.cargarRendimiento();
  }

  turnoColor(turno: string): string {
    return turno === 'T1' ? 'bg-blue-100 text-blue-800' :
           turno === 'T2' ? 'bg-amber-100 text-amber-800' :
                            'bg-purple-100 text-purple-800';
  }

  // ── Catálogo de referencias ─────────────────────────────────────────────────
  cargarReferenciasEmpaque(): void {
    this.cargandoReferencias = true;
    fetch(`${API_URL}/api/bodega/referencias`, { headers: this.headers() })
      .then(r => r.json())
      .then(d => { this.referenciasEmpaque = Array.isArray(d) ? d : []; this.cargandoReferencias = false; })
      .catch(() => { this.cargandoReferencias = false; });
  }

  filtrarReferencias(texto: string): ReferenciaEmpaque[] {
    if (!texto || !texto.trim()) return this.referenciasEmpaque;
    const t = texto.trim().toLowerCase();
    return this.referenciasEmpaque.filter(r =>
      r.codigo.toLowerCase().includes(t) || r.descripcion.toLowerCase().includes(t)
    );
  }

  // ── Órdenes de Salida recibidas + Reconciliación (solo lectura) ─────────────
  cargarOrdenesBodega(): void {
    this.cargandoOrdenesBodega = true;
    const fecha = this.filtroOrdenesFecha ? `?fecha=${this.filtroOrdenesFecha}` : '';
    fetch(`${API_URL}/api/bodega/ordenes${fecha}`, { headers: this.headers() })
      .then(r => r.json())
      .then(d => { this.ordenesBodega = Array.isArray(d) ? d : []; this.cargandoOrdenesBodega = false; })
      .catch(() => { this.cargandoOrdenesBodega = false; });
  }

  cargarReconciliacion(): void {
    if (!this.filtroReconciliacionFecha) { alert('Selecciona una fecha.'); return; }
    this.cargandoReconciliacion = true;
    fetch(`${API_URL}/api/bodega/reconciliacion?fecha=${this.filtroReconciliacionFecha}`, { headers: this.headers() })
      .then(r => r.json())
      .then(d => { this.reconciliacion = d; this.cargandoReconciliacion = false; })
      .catch(() => { this.cargandoReconciliacion = false; });
  }

  estadoReconciliacionColor(estado: string): string {
    switch (estado) {
      case 'AJUSTADO': return 'bg-emerald-100 text-emerald-700';
      case 'SOBRANTE': return 'bg-red-100 text-brand-red';
      case 'FALTANTE': return 'bg-amber-100 text-amber-700';
      case 'SIN_REGISTRO_PRODUCCION': return 'bg-gray-200 text-gray-600';
      default: return 'bg-gray-100 text-gray-600';
    }
  }

  estadoReconciliacionLabel(estado: string): string {
    switch (estado) {
      case 'AJUSTADO': return 'Ajustado';
      case 'SOBRANTE': return 'Sobrante';
      case 'FALTANTE': return 'Faltante';
      case 'SIN_REGISTRO_PRODUCCION': return 'Sin registro de producción';
      default: return estado;
    }
  }

  imprimirOrdenSalida(orden: OrdenSalida): void {
    this.ordenParaImprimir = orden;
    this.mostrandoImprimirOrden = true;
  }

  cerrarImprimirOrden(): void {
    this.mostrandoImprimirOrden = false;
    this.ordenParaImprimir = null;
  }

  numeroOrdenFormateado(orden: OrdenSalida): string {
    return `BA-${orden.id.toString().padStart(5, '0')}`;
  }

  ejecutarImpresion(): void {
    window.print();
  }

  // ── Movimientos de Inventario ────────────────────────────────────────────────
  nuevoFormMovimiento() {
    return {
      fecha: new Date().toISOString().slice(0, 10),
      tipo_operacion: '',
      codigo_producto: '',
      referencia_producto: '',
      cantidad_kg: 0,
      cantidad_bobinas: 0,
      n_documento: '',
      proveedor: '',
      destino: '',
      observaciones: ''
    };
  }

  seleccionarReferenciaMovimiento(codigo: string): void {
    const ref = this.referenciasEmpaque.find(r => r.codigo === codigo);
    if (ref) {
      this.formMovimiento.codigo_producto = ref.codigo;
      this.formMovimiento.referencia_producto = ref.descripcion;
    }
  }

  guardarMovimiento(): void {
    if (!this.formMovimiento.fecha || !this.formMovimiento.tipo_operacion ||
        !this.formMovimiento.codigo_producto || !this.formMovimiento.cantidad_kg) {
      alert('Completa fecha, tipo de operación, referencia y cantidad de kilos.');
      return;
    }
    this.guardandoMovimiento = true;
    fetch(`${API_URL}/api/bodega/movimientos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...this.headers() },
      body: JSON.stringify(this.formMovimiento)
    })
      .then(r => { if (!r.ok) throw new Error('Error'); return r.json(); })
      .then(() => {
        this.guardandoMovimiento = false;
        this.mostrarToast('Movimiento registrado');
        this.formMovimiento = this.nuevoFormMovimiento();
        this.cargarMovimientos();
        this.cargarInventario();
      })
      .catch(() => { this.guardandoMovimiento = false; this.mostrarToast('Error al registrar el movimiento'); });
  }

  cargarMovimientos(): void {
    this.cargandoMovimientos = true;
    const fecha = this.filtroMovimientoFecha ? `?fecha=${this.filtroMovimientoFecha}` : '';
    fetch(`${API_URL}/api/bodega/movimientos${fecha}`, { headers: this.headers() })
      .then(r => r.json())
      .then(d => { this.movimientos = Array.isArray(d) ? d : []; this.cargandoMovimientos = false; })
      .catch(() => { this.cargandoMovimientos = false; });
  }

  tipoMovimientoLabel(tipo: string): string {
    const t = this.tiposMovimiento.find(x => x.value === tipo);
    return t ? t.label : tipo;
  }

  tipoMovimientoColor(tipo: string): string {
    switch (tipo) {
      case 'COMPRA': return 'bg-emerald-100 text-emerald-700';
      case 'DEVOLUCION': return 'bg-blue-100 text-blue-700';
      case 'ENTREGA': return 'bg-red-50 text-brand-red';
      case 'MERCANCIA_NO_APTA': return 'bg-red-100 text-brand-red';
      case 'AJUSTE': return 'bg-amber-100 text-amber-700';
      case 'INVENTARIO_INICIAL': return 'bg-gray-200 text-gray-700';
      default: return 'bg-gray-100 text-gray-600';
    }
  }

  // ── Control de Inventario ─────────────────────────────────────────────────────
  cargarInventario(): void {
    this.cargandoInventario = true;
    const cat = this.filtroInventarioCategoria ? `?categoria=${this.filtroInventarioCategoria}` : '';
    fetch(`${API_URL}/api/bodega/inventario${cat}`, { headers: this.headers() })
      .then(r => r.json())
      .then(d => { this.inventario = Array.isArray(d) ? d : []; this.cargandoInventario = false; })
      .catch(() => { this.cargandoInventario = false; });
  }

  coberturaColor(estado: string): string {
    switch (estado) {
      case 'CRITICO': return 'bg-red-100 text-brand-red';
      case 'BAJO': return 'bg-amber-100 text-amber-700';
      case 'OK': return 'bg-emerald-100 text-emerald-700';
      default: return 'bg-gray-100 text-gray-500';
    }
  }

  coberturaLabel(estado: string): string {
    switch (estado) {
      case 'CRITICO': return 'Crítico';
      case 'BAJO': return 'Bajo';
      case 'OK': return 'OK';
      default: return 'Sin consumo';
    }
  }

  get totalCriticos(): number {
    return this.inventario.filter(i => i.estado_cobertura === 'CRITICO').length;
  }

  get totalBajos(): number {
    return this.inventario.filter(i => i.estado_cobertura === 'BAJO').length;
  }

  // ── Pedidos de Compra ─────────────────────────────────────────────────────────
  nuevoFormPedido() {
    return {
      numero_orden_compra: '',
      fecha: new Date().toISOString().slice(0, 10),
      proveedor: '',
      codigo_producto: '',
      referencia_producto: '',
      cantidad_pedida_kg: 0,
      fecha_estimada: '',
      precio_unitario: 0,
      observaciones: ''
    };
  }

  seleccionarReferenciaPedido(codigo: string): void {
    const ref = this.referenciasEmpaque.find(r => r.codigo === codigo);
    if (ref) {
      this.formPedido.codigo_producto = ref.codigo;
      this.formPedido.referencia_producto = ref.descripcion;
    }
  }

  guardarPedido(): void {
    if (!this.formPedido.fecha || !this.formPedido.proveedor ||
        !this.formPedido.codigo_producto || !this.formPedido.cantidad_pedida_kg) {
      alert('Completa fecha, proveedor, referencia y cantidad pedida.');
      return;
    }
    this.guardandoPedido = true;
    fetch(`${API_URL}/api/bodega/pedidos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...this.headers() },
      body: JSON.stringify(this.formPedido)
    })
      .then(r => { if (!r.ok) throw new Error('Error'); return r.json(); })
      .then(() => {
        this.guardandoPedido = false;
        this.mostrarToast('Pedido de compra registrado');
        this.formPedido = this.nuevoFormPedido();
        this.cargarPedidos();
      })
      .catch(() => { this.guardandoPedido = false; this.mostrarToast('Error al registrar el pedido'); });
  }

  cargarPedidos(): void {
    this.cargandoPedidos = true;
    fetch(`${API_URL}/api/bodega/pedidos`, { headers: this.headers() })
      .then(r => r.json())
      .then(d => { this.pedidos = Array.isArray(d) ? d : []; this.cargandoPedidos = false; })
      .catch(() => { this.cargandoPedidos = false; });
  }

  abrirRecepcion(p: PedidoCompra): void {
    this.pedidoRecepcion = p;
    this.formRecepcionKg = Math.max((p.cantidad_pedida_kg || 0) - (p.cantidad_recibida_kg || 0), 0);
  }

  cerrarRecepcion(): void {
    this.pedidoRecepcion = null;
    this.formRecepcionKg = 0;
  }

  guardarRecepcion(): void {
    if (!this.pedidoRecepcion || !this.formRecepcionKg || this.formRecepcionKg <= 0) {
      alert('Ingresa una cantidad recibida válida.');
      return;
    }
    this.guardandoRecepcion = true;
    fetch(`${API_URL}/api/bodega/pedidos/${this.pedidoRecepcion.id}/recepcion`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...this.headers() },
      body: JSON.stringify({ cantidad_recibida_kg: this.formRecepcionKg })
    })
      .then(r => { if (!r.ok) throw new Error('Error'); return r.json(); })
      .then(() => {
        this.guardandoRecepcion = false;
        this.mostrarToast('Recepción registrada');
        this.cerrarRecepcion();
        this.cargarPedidos();
        this.cargarInventario();
      })
      .catch(() => { this.guardandoRecepcion = false; this.mostrarToast('Error al registrar la recepción'); });
  }

  estadoPedidoColor(estado: string): string {
    switch (estado) {
      case 'COMPLETO': return 'bg-emerald-100 text-emerald-700';
      case 'PARCIAL': return 'bg-amber-100 text-amber-700';
      default: return 'bg-gray-200 text-gray-700';
    }
  }

  // ── Rendimientos mensuales ────────────────────────────────────────────────────
  cargarRendimiento(): void {
    if (!this.filtroRendimientoMes) { alert('Selecciona un mes.'); return; }
    this.cargandoRendimiento = true;
    fetch(`${API_URL}/api/bodega/rendimientos?mes=${this.filtroRendimientoMes}`, { headers: this.headers() })
      .then(r => r.json())
      .then(d => { this.rendimiento = d; this.cargandoRendimiento = false; })
      .catch(() => { this.cargandoRendimiento = false; });
  }
}