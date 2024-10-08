import os
import numpy as np
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
from scipy import ndimage
from datetime import datetime
import pandas as pd
import matplotlib.colors as mcolors


def load_ndvi_image(file_path):
    """Carrega uma imagem NDVI do arquivo."""
    with rasterio.open(file_path) as src:
        return src.read(1), src.meta


def calculate_difference(image1, image2):
    """Calcula a diferença entre duas imagens NDVI."""
    return image2 - image1


def threshold_difference(diff_image, threshold):
    """Aplica um limiar à imagem de diferença para identificar mudanças significativas."""
    return np.where(
        diff_image > threshold,
        diff_image,
        np.where(diff_image < -threshold, diff_image, 0),
    )


def apply_spatial_filter(change_image, filter_size=3):
    """Aplica um filtro espacial para remover ruído."""
    return ndimage.median_filter(change_image, size=filter_size)


def classify_changes(filtered_image):
    """Classifica as mudanças em categorias (por exemplo, aumento, diminuição, sem mudança)."""
    return np.select(
        [filtered_image > 0, filtered_image < 0, filtered_image == 0], [1, -1, 0]
    )


def detect_changes(file_path1, file_path2, threshold=0.1):
    """Função principal para detectar mudanças entre duas imagens NDVI."""
    ndvi1, meta = load_ndvi_image(file_path1)
    ndvi2, _ = load_ndvi_image(file_path2)

    diff_image = calculate_difference(ndvi1, ndvi2)
    thresholded_diff = threshold_difference(diff_image, threshold)
    filtered_diff = apply_spatial_filter(thresholded_diff)
    change_map = classify_changes(filtered_diff)

    return change_map, meta


def visualize_heatmap(change_map, meta, output_file):
    """Visualiza e salva o mapa de calor das mudanças."""
    plt.figure(figsize=(10, 10))

    # Usar colormap ajustado para distinguir aumento (verde) e diminuição (vermelho)
    cmap = mcolors.ListedColormap(["red", "white", "green"])
    bounds = [-1, -0.5, 0.5, 1]
    norm = mcolors.BoundaryNorm(bounds, cmap.N)

    plt.imshow(change_map, cmap=cmap, norm=norm, interpolation="nearest")
    plt.colorbar(label="Intensidade da Mudança", ticks=[-1, 0, 1])
    plt.title("Mapa de Calor das Mudanças na Vegetação")
    plt.axis("off")

    # Salvar como PNG
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close()

    # Salvar também como GeoTIFF, se necessário
    with rasterio.open(output_file.replace(".png", ".tif"), "w", **meta) as dst:
        dst.write(change_map, 1)


def process_image_series(image_folder, output_folder):
    """Processa uma série de imagens NDVI e detecta mudanças ao longo do tempo."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    image_files = sorted([f for f in os.listdir(image_folder) if f.endswith(".tif")])
    change_stats = []

    for i in range(len(image_files) - 1):
        file1 = os.path.join(image_folder, image_files[i])
        file2 = os.path.join(image_folder, image_files[i + 1])

        output_file = os.path.join(output_folder, f"mudancas_{i}_to_{i+1}_heatmap.png")

        change_map, meta = detect_changes(file1, file2)
        visualize_heatmap(change_map, meta, output_file)  # Gera o mapa de calor

        # Calcular estatísticas de mudança
        total_pixels = change_map.size
        increased = np.sum(change_map == 1) / total_pixels * 100
        decreased = np.sum(change_map == -1) / total_pixels * 100
        unchanged = np.sum(change_map == 0) / total_pixels * 100

        change_stats.append(
            {
                "Período": f"{i} to {i+1}",
                "Aumento (%)": increased,
                "Diminuição (%)": decreased,
                "Sem Mudança (%)": unchanged,
            }
        )

        print(f"Processado: {file1} -> {file2}")

    # Criar um DataFrame com as estatísticas de mudança
    df_stats = pd.DataFrame(change_stats)
    df_stats.to_csv(
        os.path.join(output_folder, "estatisticas_mudancas.csv"), index=False
    )

    return df_stats


# Exemplo de uso
if __name__ == "__main__":
    image_folder = "./Angola_MODIS_Images"
    output_folder = "./Resultados_Mudancas"

    df_stats = process_image_series(image_folder, output_folder)
    print(df_stats)

    # Plotar gráfico de mudanças ao longo do tempo
    plt.figure(figsize=(12, 6))
    plt.plot(df_stats["Período"], df_stats["Aumento (%)"], label="Aumento", marker="o")
    plt.plot(
        df_stats["Período"], df_stats["Diminuição (%)"], label="Diminuição", marker="o"
    )
    plt.title("Mudanças na Vegetação ao Longo do Tempo")
    plt.xlabel("Período")
    plt.ylabel("Porcentagem de Área")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, "grafico_mudancas_temporais.png"))
    plt.close()

    print(f"Resultados salvos em {output_folder}")
