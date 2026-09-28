// ─── BOBINAS ──────────────────────────────────────────────────
export interface FilaBobina {
  numero_fila: number;
  maquina_grupo?: string;
  referencia_empaque?: string;
  peso_montar?: number;
  peso_desmontar?: number;
  peso_desmontar_estimado?: boolean; // true = calculado automático (rollo a medias), no fue pesado de verdad
  consumido?: number;
  contador?: number;
  observaciones?: string;
}

export interface RegistroBobinas {
  id?: number;
  periodo?: string;
  referencia_producto?: string;
  referencia_enfardadora?: string;
  maquina?: string;
  proveedor?: string;
  fecha?: string;
  turno?: string;
  peso_desperdicio?: number;
  peso_desperdicio_fardo?: number;
  nombre_operario?: string;
  firma_data?: string;
  pro_numero?: string;
  lote?: string;
  filas: FilaBobina[];
}

export interface ReferenciaCatalogo {
  key: string;
  label: string;
  div: number;
  categoria?: string; // "TRIGO" | "MAIZ" — viene del catálogo de bodega
}

// ─── ROTULADO ──────────────────────────────────────────────────
export interface FilaRotulado {
  numero_fila: number;
  hora?: string;
  fechado?: string;
  fechado_cumple?: string;
  sellado_cumple?: string;
  referencia?: string;
}

export interface RegistroRotulado {
  id?: number;
  fecha?: string;
  turno?: string;
  maquina?: string;
  nombre_operario?: string;
  firma_data?: string;
  pro_numero?: string;
  lote?: string;
  filas: FilaRotulado[];
}

// ─── PESOS ─────────────────────────────────────────────────────
export interface FilaPeso {
  numero_fila: number;
  hora?: string;
  muestra_1?: number | null;
  muestra_2?: number | null;
  muestra_3?: number | null;
  muestra_4?: number | null;
  muestra_5?: number | null;
  muestra_6?: number | null;
  muestra_7?: number | null;
  muestra_8?: number | null;
  muestra_9?: number | null;
  muestra_10?: number | null;
  muestra_11?: number | null;
  muestra_12?: number | null;
  muestra_13?: number | null;
  muestra_14?: number | null;
  muestra_15?: number | null;
  muestra_16?: number | null;
  muestra_17?: number | null;
  muestra_18?: number | null;
  muestra_19?: number | null;
  muestra_20?: number | null;
  muestra_21?: number | null;
  muestra_22?: number | null;
  muestra_23?: number | null;
  muestra_24?: number | null;
  muestra_25?: number | null;
  observaciones?: string;
}

export interface RegistroPesos {
  id?: number;
  fecha?: string;
  turno?: string;
  maquina?: string;
  referencia?: string;
  nombre_operario?: string;
  firma_data?: string;
  pro_numero?: string;
  lote?: string;
  filas: FilaPeso[];
}

export interface FilaPesoEnfardadora {
  numero_fila: number;
  hora?: string;
  muestra_1?: number | null;
  muestra_2?: number | null;
  muestra_3?: number | null;
  muestra_4?: number | null;
  muestra_5?: number | null;
  muestra_6?: number | null;
  muestra_7?: number | null;
  muestra_8?: number | null;
  muestra_9?: number | null;
  muestra_10?: number | null;
  muestra_11?: number | null;
  muestra_12?: number | null;
  muestra_13?: number | null;
  muestra_14?: number | null;
  muestra_15?: number | null;
  observaciones?: string;
}

export interface RegistroPesoEnfardadora {
  id?: number;
  fecha?: string;
  turno?: string;
  enfardadora?: string;
  maquinas?: string;
  referencia?: string;
  nombre_operario?: string;
  firma_data?: string;
  pro_numero?: string;
  lote?: string;
  filas: FilaPesoEnfardadora[];
}