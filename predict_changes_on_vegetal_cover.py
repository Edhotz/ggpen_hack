import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import rasterio
from memory_profiler import profile
from sklearn.decomposition import PCA


# Carregar os dados (NDVI e cobertura do solo)
@profile
def load_data(image_folder):
    """Carrega e processa os dados de NDVI."""
    ndvi_files = sorted([f for f in os.listdir(image_folder) if f.endswith(".tif")])
    ndvi_data = []

    # Limitar a quantidade de arquivos processados
    sample_size = min(20, len(ndvi_files))  # Aumentado para 20
    for file in ndvi_files[:sample_size]:
        file_path = os.path.join(image_folder, file)
        with rasterio.open(file_path) as src:
            ndvi_image = src.read(1)  # Lê a primeira banda da imagem
            ndvi_data.append(
                ndvi_image.flatten()
            )  # Converter para vetor unidimensional

    ndvi_data = np.array(ndvi_data)

    # Verificação do conteúdo carregado
    print("Dados NDVI carregados:", ndvi_data)
    print("Shape de ndvi_data:", ndvi_data.shape)

    return ndvi_data


# Pré-processamento dos dados usando redução de dimensionalidade para aplicar PCA
def preprocess_data(ndvi_data):
    """Normaliza e estrutura os dados, aplicando PCA para redução de dimensionalidade."""
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(ndvi_data)

    print("Shape de scaled_data:", scaled_data.shape)  # Para depuração

    # Reduzir a dimensionalidade usando PCA
    n_components = min(
        9, scaled_data.shape[0]
    )  # O número de componentes deve ser menor ou igual ao número de amostras
    pca = PCA(n_components=n_components)
    reduced_data = pca.fit_transform(scaled_data)

    print("Shape de reduced_data:", reduced_data.shape)  # Para depuração

    # Prepare X e y para treinamento
    X, y = [], []
    sequence_length = 5  # Ajustado para 5 timesteps

    for i in range(len(reduced_data) - sequence_length):
        X.append(reduced_data[i : i + sequence_length])
        y.append(reduced_data[i + sequence_length])

    # Transformar para numpy arrays
    X = np.array(X)
    y = np.array(y)

    print("Shape de X antes do reshape:", X.shape)  # Para depuração

    # Verificações
    if len(X) == 0 or len(y) == 0:
        raise ValueError("X ou y estão vazios, verifique os dados de entrada.")

    if len(X) < 2:  # Garantir que haja pelo menos duas amostras para treino
        raise ValueError("Não há amostras suficientes após o pré-processamento.")

    # Transformar X para 2D (amostras, features) para o Random Forest
    X = X.reshape(X.shape[0], -1)  # (n_samples, n_features)

    return X, y, scaler


# Treinar modelo Random Forest
def train_with_random_forest(X_train, y_train):
    """Treina um modelo de Random Forest e avalia seu desempenho."""
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    return model


# Função principal para treinar e prever
def train_and_predict(image_folder, output_folder):
    # Carregar dados
    ndvi_data = load_data(image_folder)

    # Pré-processar os dados
    X, y, scaler = preprocess_data(ndvi_data)

    # Divisão em treino e teste
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Treinar o modelo
    model = train_with_random_forest(X_train, y_train)

    # Fazer previsões
    predictions = model.predict(X_test)

    # Desnormalizar previsões
    predictions_rescaled = scaler.inverse_transform(predictions.reshape(-1, 1))
    y_test_rescaled = scaler.inverse_transform(y_test.reshape(-1, 1))

    # Visualizar resultados
    plt.figure(figsize=(10, 6))
    plt.plot(y_test_rescaled, label="NDVI Real")
    plt.plot(predictions_rescaled, label="NDVI Previsto")
    plt.title("Previsão de NDVI")
    plt.xlabel("Amostras")
    plt.ylabel("NDVI")
    plt.legend()
    plt.show()

    # Salvar as previsões
    predictions_df = pd.DataFrame(
        {
            "NDVI_Real": y_test_rescaled.flatten(),
            "NDVI_Previsto": predictions_rescaled.flatten(),
        }
    )
    predictions_df.to_csv(
        os.path.join(output_folder, "predicoes_ndvi.csv"), index=False
    )


# Exemplo de uso
if __name__ == "__main__":
    image_folder = "./Angola_MODIS_Images"
    output_folder = "./Resultados_Predicoes"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    train_and_predict(image_folder, output_folder)
