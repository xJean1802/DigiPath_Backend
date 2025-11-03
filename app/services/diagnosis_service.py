from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Any
import pandas as pd
import numpy as np

from app.models.diagnosis import Diagnostico, Respuesta, DiagnosticoSHAP
from app.schemas.diagnosis_schema import RespuestaCreate
from app.ml.loader import get_model_components

# --- Mapeo de Preguntas a Dominios ---
MAPA_DOMINIOS = {
    'Contacto con el Cliente': [f'Q{i}' for i in range(1, 5)],
    'Operaciones': [f'Q{i}' for i in range(5, 9)],
    'Modelos de Negocio': [f'Q{i}' for i in range(9, 11)],
    'Visión': [f'Q{i}' for i in range(11, 13)],
    'Compromiso (Engagement)': [f'Q{i}' for i in range(13, 16)],
    'Gobernanza (Gobierno Digital)': [f'Q{i}' for i in range(16, 19)],
    'Capacidades Tecnológicas (Liderazgo de TI)': [f'Q{i}' for i in range(19, 21)]
}


# --- Funciones Helper Privadas ---

def _normalize_row(respuestas_dict: Dict[str, Any]) -> pd.DataFrame:
    """Normaliza un diccionario de respuestas crudas a una escala numérica en un DataFrame."""
    map_si_no = {'No': 1, 'Si': 7}
    map_b2 = {1: 1, 2: 3, 3: 5, 4: 7}
    map_f3 = {1: 1, 2: 4, 3: 7}
    
    fila_normalizada = {}
    for pregunta_id in range(1, 21):
        pregunta_key = f'Q{pregunta_id}'
        respuesta = respuestas_dict.get(pregunta_key)
        valor_normalizado = np.nan
        
        try:
            respuesta_int = int(respuesta)
        except (ValueError, TypeError):
            respuesta_int = None

        try:
            if pregunta_id in [1, 3, 7, 10, 13, 15, 17]:
                valor_normalizado = map_si_no.get(str(respuesta).strip())
            elif pregunta_id == 6 and respuesta_int is not None:
                valor_normalizado = map_b2.get(respuesta_int)
            elif pregunta_id == 18 and respuesta_int is not None:
                valor_normalizado = map_f3.get(respuesta_int)
            elif respuesta_int is not None:
                valor_normalizado = respuesta_int
        except Exception:
            pass
            
        fila_normalizada[pregunta_key] = valor_normalizado
        
    return pd.DataFrame([fila_normalizada])

def _calculate_domain_scores(fila_normalizada_df: pd.DataFrame) -> Dict[str, float]:
    """Calcula el puntaje promedio para cada uno de los 7 dominios."""
    puntajes_dominios = {}
    for dominio, preguntas in MAPA_DOMINIOS.items():
        puntaje = fila_normalizada_df[preguntas].mean(axis=1).iloc[0]
        puntajes_dominios[dominio] = round(puntaje, 2)
    return puntajes_dominios


# --- Servicios Públicos ---

def process_diagnosis(respuestas_crudas_dict: Dict[str, Any]) -> Dict[str, Any]:
    
    model, label_encoder, explainer = get_model_components()
    if not all([model, label_encoder, explainer]):
        raise RuntimeError("Los componentes de ML no están disponibles.")

    fila_normalizada_df = _normalize_row(respuestas_crudas_dict)

    # --- Predicción y Potencial (sin cambios) ---
    prediccion_encoded = model.predict(fila_normalizada_df)[0]
    prediccion_probabilidades = model.predict_proba(fila_normalizada_df)[0]
    nivel_predicho = label_encoder.inverse_transform([prediccion_encoded])[0]

    orden_niveles = ['Principiante Digital', 'Conservador Digital', 'Fashionista', 'Maestro Digital']
    potencial_avance = 0.0
    try:
        idx_actual = orden_niveles.index(nivel_predicho)
        if idx_actual < len(orden_niveles) - 1:
            siguiente_nivel = orden_niveles[idx_actual + 1]
            idx_siguiente = np.where(label_encoder.classes_ == siguiente_nivel)[0][0]
            potencial_avance = prediccion_probabilidades[idx_siguiente]
    except (ValueError, IndexError):
        pass

    # =========================================================================
    # LÓGICA DE SHAP UNIFICADA Y CORREGIDA
    # =========================================================================
    
    shap_explanation_obj = explainer(fila_normalizada_df)

    try:
        # Usamos los SHAP de "Maestro Digital" como la ÚNICA fuente de verdad para el análisis
        clase_objetivo_idx = np.where(label_encoder.classes_ == 'Maestro Digital')[0][0]
    except IndexError:
        clase_objetivo_idx = -1

    shap_values_analisis = shap_explanation_obj.values[:, :, clase_objetivo_idx].flatten()

    # Este DataFrame ahora es nuestra única fuente para SHAP
    df_shap_analisis = pd.DataFrame({
        'pregunta_id': [f'Q{i}' for i in range(1, 21)],
        'shap_value': shap_values_analisis
    })
    
    # Identificamos las debilidades (drivers) desde esta única fuente
    debilidades = df_shap_analisis[df_shap_analisis['shap_value'] < 0].copy().sort_values('shap_value', ascending=True).head(3)
    
    if not debilidades.empty:
        total_impacto_negativo = abs(debilidades['shap_value']).sum()
        if total_impacto_negativo > 0:
            debilidades['peso_impacto'] = (abs(debilidades['shap_value']) / total_impacto_negativo) * 100
        else:
            debilidades['peso_impacto'] = 0
    else:
        debilidades['peso_impacto'] = 0

    # --- Resto de la función (sin cambios) ---
    desglose_dominios = _calculate_domain_scores(fila_normalizada_df)
    puntaje_cap_digital = fila_normalizada_df.loc[:, 'Q1':'Q10'].mean(axis=1).iloc[0]
    puntaje_cap_liderazgo = fila_normalizada_df.loc[:, 'Q11':'Q20'].mean(axis=1).iloc[0]

    return {
        "nivel_madurez_predicho": nivel_predicho,
        "potencial_avance": round(potencial_avance * 100, 2),
        "puntaje_cap_digital": round(puntaje_cap_digital, 2),
        "puntaje_cap_liderazgo": round(puntaje_cap_liderazgo, 2),
        "areas_mejora_prioritarias": debilidades.to_dict('records'),
        "desglose_dominios": desglose_dominios,
        # Devolvemos los mismos valores SHAP que usamos para el análisis
        "shap_values": df_shap_analisis.to_dict('records')
    }

def create_and_process_diagnosis(db: Session, user_id: int, respuestas_schema: List[RespuestaCreate]) -> Diagnostico:
    """
    Servicio principal que guarda, procesa y limpia el historial de diagnósticos.
    """
    # Lógica de limpieza del historial (sin cambios)
    diagnosticos_existentes = db.query(Diagnostico.id_diagnostico).filter(
        Diagnostico.id_usuario == user_id
    ).order_by(
        Diagnostico.fecha_diagnostico.desc()
    ).offset(2).all()

    if diagnosticos_existentes:
        ids_a_eliminar = [d.id_diagnostico for d in diagnosticos_existentes]
        db.query(Diagnostico).filter(Diagnostico.id_diagnostico.in_(ids_a_eliminar)).delete(synchronize_session=False)
        db.commit()

    # 1. Preparar los datos y normalizarlos UNA SOLA VEZ
    respuestas_dict = {f"Q{i}": None for i in range(1, 21)}
    for r in respuestas_schema:
        respuestas_dict[f"Q{r.id_pregunta}"] = r.valor_respuesta_cruda

    # Se normalizan las respuestas para el modelo
    fila_normalizada_df = _normalize_row(respuestas_dict)
    # Creamos un diccionario para un acceso fácil a los valores normalizados
    valores_normalizados_dict = fila_normalizada_df.iloc[0].to_dict()

    # 2. Crear el registro principal del diagnóstico
    db_diagnostico = Diagnostico(id_usuario=user_id, nivel_madurez_predicho="EN PROCESO", puntaje_cap_digital=0.0, puntaje_cap_liderazgo=0.0)
    db.add(db_diagnostico)
    db.flush() 
    
    # 3. Guardar las respuestas crudas JUNTO con su valor normalizado
    for resp in respuestas_schema:
        # Buscamos el valor normalizado que ya calculamos
        valor_norm = valores_normalizados_dict.get(f'Q{resp.id_pregunta}')
        
        # SQLAlchemy maneja NaN como NULL, lo convertimos a un entero seguro (ej. 0) si falla.
        valor_norm_int = int(valor_norm) if pd.notna(valor_norm) else 0

        db_respuesta = Respuesta(
            id_diagnostico=db_diagnostico.id_diagnostico, 
            id_pregunta=resp.id_pregunta, 
            valor_respuesta_cruda=str(resp.valor_respuesta_cruda), 
            valor_normalizado=valor_norm_int # <-- Usamos el valor real
        )
        db.add(db_respuesta)

    # 4. Llamar a la lógica de ML (le pasamos el diccionario original, ya que internamente normaliza)
    analisis = process_diagnosis(respuestas_dict)

    # 5. Actualizar el diagnóstico con los resultados del análisis
    db_diagnostico.nivel_madurez_predicho = analisis["nivel_madurez_predicho"]
    db_diagnostico.puntaje_cap_digital = analisis["puntaje_cap_digital"]
    db_diagnostico.puntaje_cap_liderazgo = analisis["puntaje_cap_liderazgo"]

    # 6. Guardar los resultados de SHAP
    debilidades_ids = {d["pregunta_id"] for d in analisis["areas_mejora_prioritarias"]}
    for shap_data in analisis["shap_values"]:
        db_shap = DiagnosticoSHAP(
            id_diagnostico=db_diagnostico.id_diagnostico,
            id_pregunta=int(shap_data["pregunta_id"][1:]),
            valor_shap=shap_data["shap_value"],
            es_driver_clave=(shap_data["pregunta_id"] in debilidades_ids)
        )
        db.add(db_shap)

    db.commit()
    db.refresh(db_diagnostico)
    
    return db_diagnostico

def get_user_diagnoses(db: Session, user_id: int) -> List[Diagnostico]:
    """
    Devuelve hasta 3 de los últimos diagnósticos de un usuario.
    """
    # Limitar la consulta a los 3 más recientes para la vista.
    return db.query(Diagnostico).filter(
        Diagnostico.id_usuario == user_id
    ).order_by(
        desc(Diagnostico.fecha_diagnostico)
    ).limit(3).all()