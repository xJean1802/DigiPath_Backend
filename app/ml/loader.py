import joblib

MODEL_PATH = "app/ml/modelo_rf.joblib"
ENCODER_PATH = "app/ml/label_encoder.joblib"
# Es MUY recomendable cargar el explainer que creaste en Colab.
EXPLAINER_PATH = "app/ml/shap_explainer.joblib"

try:
    model = joblib.load(MODEL_PATH)
    label_encoder = joblib.load(ENCODER_PATH)
    # Cargas el explainer en lugar de crearlo de nuevo.
    explainer = joblib.load(EXPLAINER_PATH)
    print("Modelo de ML, Label Encoder y Explainer de SHAP cargados exitosamente.")
except Exception as e:
    print(f"Error crítico al cargar los artefactos de ML: {e}")
    model, label_encoder, explainer = None, None, None

# El resto del código no cambia
def get_model_components():
    return model, label_encoder, explainer