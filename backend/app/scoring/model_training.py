import os
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_absolute_error, r2_score

from app.scoring.stmt_parser import parse_statement
from app.scoring.stmt_scoring import calculate_statement_features, calculate_score_from_features

'''
Генерация датасета
'''
def generate_synthetic_dataset(num_samples: int = 5000) -> pd.DataFrame:
    data = []
    for _ in range(num_samples):
        income = np.random.uniform(20000, 500000)
        expenses = np.random.uniform(20000, 500000)
        
        feats = {
            "income": income,
            "expenses": expenses,
            "cashflow_ratio": income / expenses,
            "essential_ratio": np.random.uniform(0.1, 0.95),
            "discretionary_ratio": np.random.uniform(0.0, 0.6),
            "num_incomes": np.random.randint(1, 15),
            "avg_income_interval": np.random.uniform(1.0, 45.0),
            "income_interval_std": np.random.uniform(1.0, 20.0),
            "cushion_ratio": np.random.uniform(0.0, 3.0),
        }

        # Вызываем боевую функцию скоринга из бэкенда
        result = calculate_score_from_features(feats)
        feats["target_score"] = result["score"]
        
        data.append(feats)
        
    return pd.DataFrame(data)


'''
Стандартизация признаков и разделение выборки на обучающую и тестовую
'''
def prepare_data(df: pd.DataFrame):
    # income и expenses не будем использовать в качестве обучающего признака из-за сильного отличия в масштабе
    feature_cols = [
        "cashflow_ratio", "essential_ratio", "discretionary_ratio", 
        "num_incomes", "avg_income_interval", "income_interval_std", "cushion_ratio"
    ]
    X = df[feature_cols]
    y = df["target_score"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, feature_cols


'''
Обучение модели
'''
def train_model(X_train_scaled, y_train, X_test_scaled, y_test, feature_cols):
    # Задаем модель и сетку гиперпараметров для подбора
    rf = RandomForestRegressor(random_state=42)
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [5, 10, None]
    }
    
    # Обучаем с кросс-валидацией (ищет лучшую комбинацию параметров)
    grid_search = GridSearchCV(rf, param_grid, cv=3, scoring='neg_mean_absolute_error', n_jobs=-1)
    grid_search.fit(X_train_scaled, y_train)
    best_model = grid_search.best_estimator_
    
    # Оценка точности на тестовой выборке
    y_pred = best_model.predict(X_test_scaled)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"\n[Оценка качества модели]")
    print(f"Лучшие параметры: {grid_search.best_params_}")
    print(f"Средняя ошибка предсказания (MAE): {mae:.2f} баллов")
    print(f"Точность модели (R2): {r2:.2f} (чем ближе к 1.0, тем лучше)")

    # У деревьев решений нет вектора (Coef), но есть "Важность признаков"
    print("\n[Влияние признаков на благонадёжность]")
    importances = pd.DataFrame({
        "Признак": feature_cols,
        "Важность (%)": best_model.feature_importances_ * 100
    }).sort_values(by="Важность (%)", ascending=False)
    
    for _, row in importances.iterrows():
        print(f"{row['Признак']:>20} | Вклад в итоговую оценку: {row['Важность (%)']:.1f}%")
        
    return best_model


'''
Сохранение и импорт модели
'''
def save_model_artifacts(model, scaler, feature_cols, base_dir="."):
    os.makedirs(base_dir, exist_ok=True)
    joblib.dump(model, os.path.join(base_dir, "reputa_lr_model.pkl"))
    joblib.dump(scaler, os.path.join(base_dir, "reputa_scaler.pkl"))
    joblib.dump(feature_cols, os.path.join(base_dir, "feature_cols.pkl"))

def load_model_artifacts(base_dir="."):
    model = joblib.load(os.path.join(base_dir, "reputa_lr_model.pkl"))
    scaler = joblib.load(os.path.join(base_dir, "reputa_scaler.pkl"))
    feature_cols = joblib.load(os.path.join(base_dir, "feature_cols.pkl"))
    return model, scaler, feature_cols


'''
Инференс (функция принимает обученную модель и сырой pdf-файл, возвращает оценку благонадёжности от 0 до 100)
'''
def predict_from_pdf(pdf_path: str, model, scaler, feature_cols) -> int:
    with open(pdf_path, "rb") as f:
        content = f.read()
        
    parsed_stmt = parse_statement(content)
    features_dict = calculate_statement_features(parsed_stmt)
    
    x_raw = pd.DataFrame([{col: features_dict[col] for col in feature_cols}])
    x_scaled = scaler.transform(x_raw)
    
    raw_prediction = model.predict(x_scaled)[0]
    return int(np.clip(round(raw_prediction), 0, 100))



if __name__ == "__main__":

    df = generate_synthetic_dataset(500000)
    X_train, X_test, y_train, y_test, scaler, cols = prepare_data(df)
    model = train_model(X_train, y_train, X_test, y_test, cols)
    save_model_artifacts(model, scaler, cols, base_dir="artifacts")
   

    files = ["AM_1788587469194pdf", "funds_movement", "Баглаева_А_А_о_движении_денежных_средств_ozonbank_document_35151989", "Выписка (1)", "Выписка (2)", "Выписка", "выписка по счету альфа", "Выписка по счёту дебетовой карты"]
    loaded_model, loaded_scaler, loaded_cols = load_model_artifacts("artifacts")
    for file in files:
        test_pdf = "C:/Users/maxto/Downloads/" + file + ".pdf"
        if os.path.exists(test_pdf):
            score = predict_from_pdf(test_pdf, loaded_model, loaded_scaler, loaded_cols)
            print(f"{file}: {score}/100")
        else:
            print(f"Файл {test_pdf} не найден.")