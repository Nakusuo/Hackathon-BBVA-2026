"""Que columnas puede ver un modelo. Evita la fuga de la verdad oculta del generador."""

# Atributos que el cliente declararia o que el banco conoce (contrato de datos del plan, tabla seguro.clientes).
OBSERVABLES_CLIENTE = [
    "rango_edad", "region", "tipo_trabajo", "frecuencia_ingreso", "personas_a_cargo", "deuda_total", "n_creditos", "cuota_mensual",
    "tcea_promedio", "colchon_meses", "antiguedad_cliente_meses", "meta_ahorro", "paga_en_usd",
]
# Etiquetas de referencia: solo para evaluar, nunca como entrada de un modelo.
ETIQUETAS_CLIENTE = [
    "arquetipo", "segmento", "subtipo", "perfil_ahorro_real", "perfil_gasto_real", "necesidad_oculta", "prob_acepta_reco", "cambio_patron",
]
# Parametros internos del simulador: describen como se genero el dato, no algo que un cliente real exponga.
INTERNAS_GENERADOR = [
    "ingreso_base", "gasto_ratio", "ahorro_tasa", "fraccion_efectivo", "traspaso_inflacion", "planilla", "tiene_alquiler", "alquiler_share",
    "tiene_deuda", "cuota_share", "saldo_inicial", "ahorro_inicial", "acceso_credito_informal", "tasa_credito_informal", "pos_cambio_patron",
    "factor_cambio_ingreso", "heterogeneidad_consumo", "peso_muestral", "lote",
]
ETIQUETAS_TRANSACCION = ["es_recurrente", "es_atipico", "es_suscripcion_duplicada"]
