import joblib
import os

# --- Definimos las rutas a los artefactos ---
# Usamos rutas absolutas para mayor robustez.
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(_BASE_DIR, "modelo_rf.joblib")
ENCODER_PATH = os.path.join(_BASE_DIR, "label_encoder.joblib")
EXPLAINER_PATH = os.path.join(_BASE_DIR, "shap_explainer.joblib")

# --- Variables globales para almacenar los modelos en caché ---
# Las inicializamos como None. Solo las cargaremos una vez.
_model = None
_label_encoder = None
_explainer = None

def get_model_components():
    """
    Función de carga perezosa (Lazy Loading).
    Carga los artefactos de ML desde el disco la primera vez que se llama
    y los almacena en caché en memoria para las llamadas posteriores.
    """
    global _model, _label_encoder, _explainer

    # Si los modelos no han sido cargados todavía...
    if _model is None or _label_encoder is None or _explainer is None:
        print("Cargando artefactos de Machine Learning por primera vez...")
        try:
            _model = joblib.load(MODEL_PATH)
            _label_encoder = joblib.load(ENCODER_PATH)
            _explainer = joblib.load(EXPLAINER_PATH)
            print("Artefactos cargados y cacheados exitosamente.")
        except Exception as e:
            print(f"Error crítico al cargar los artefactos de ML: {e}")
            # Si falla, nos aseguramos de que todo quede en None para evitar estados parciales
            _model, _label_encoder, _explainer = None, None, None
            raise RuntimeError(f"No se pudieron cargar los artefactos de ML: {e}")

    return _model, _label_encoder, _explainer