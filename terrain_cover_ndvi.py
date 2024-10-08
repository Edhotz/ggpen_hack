import os
import numpy as np
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import pandas as pd
import matplotlib.colors as mcolors


def load_ndvi_image(file_path):
    """Carrega uma imagem NDVI do arquivo."""
    with rasterio.open(file_path) as src:
        return src.read(1), src.meta


def classify_land_cover(ndvi_image):
    """Classifica a cobertura do solo com base nos valores de NDVI."""
    classification = np.select(
        [
            ndvi_image < 0,  # Água
            (ndvi_image >= 0) & (ndvi_image < 0.2),  # Solo nu
            (ndvi_image >= 0.2) & (ndvi_image < 0.5),  # Vegetação rala/pastagem
            ndvi_image >= 0.5,  # Vegetação densa/floresta
        ],
        [
            1,  # Água
            2,  # Solo nu
            3,  # Vegetação rala/pastagem
            4,  # Vegetação densa/floresta
        ],
        default=0,  # Sem dados
    )
    return classification


def visualize_land_cover(classification_image, meta, output_file):
    """Visualiza e salva o mapa de classificação da cobertura do solo."""
    plt.figure(figsize=(10, 10))

    # Definir colormap e legendas
    cmap = mcolors.ListedColormap(["blue", "yellow", "lightgreen", "darkgreen"])
    bounds = [0, 1, 2, 3, 4]
    norm = mcolors.BoundaryNorm(bounds, cmap.N)

    # Exibir o mapa classificado
    plt.imshow(classification_image, cmap=cmap, norm=norm, interpolation="nearest")
    plt.colorbar(
        label="Cobertura do Solo",
        ticks=[1, 2, 3, 4],
        format=plt.FuncFormatter(
            lambda x, _: {
                1: "Água",
                2: "Solo nu",
                3: "Vegetação rala/pastagem",
                4: "Vegetação densa/floresta",
            }.get(x, "")
        ),
    )

    plt.title("Classificação da Cobertura do Solo")
    plt.axis("off")

    # Salvar como PNG
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close()


def switch_visualization(ndvi_image, classification_image):
    """Alterna entre visualização de NDVI e classificação de cobertura do solo."""
    fig, ax = plt.subplots(figsize=(10, 10))

    def display_ndvi(event):
        ax.clear()
        ax.imshow(ndvi_image, cmap="RdYlGn", interpolation="nearest")
        ax.set_title("Visualização NDVI")
        ax.axis("off")
        plt.draw()

    def display_classification(event):
        ax.clear()
        cmap = mcolors.ListedColormap(["blue", "yellow", "lightgreen", "darkgreen"])
        bounds = [0, 1, 2, 3, 4]
        norm = mcolors.BoundaryNorm(bounds, cmap.N)

        ax.imshow(classification_image, cmap=cmap, norm=norm, interpolation="nearest")
        ax.set_title("Classificação de Cobertura do Solo")
        ax.axis("off")
        plt.draw()

    # Exibe o NDVI inicialmente
    display_ndvi(None)

    # Adicionar botões para alternar entre NDVI e classificação
    ax_button_ndvi = plt.axes([0.7, 0.05, 0.1, 0.075])
    btn_ndvi = Button(ax_button_ndvi, "NDVI")
    btn_ndvi.on_clicked(display_ndvi)

    ax_button_class = plt.axes([0.81, 0.05, 0.1, 0.075])
    btn_class = Button(ax_button_class, "Classificação")
    btn_class.on_clicked(display_classification)

    plt.show()


def process_image(file_path):
    """Processa uma imagem NDVI e aplica classificação de cobertura de solo."""
    ndvi_image, meta = load_ndvi_image(file_path)

    # Classificar cobertura de solo
    classification_image = classify_land_cover(ndvi_image)

    return ndvi_image, classification_image, meta


# Exemplo de uso
if __name__ == "__main__":
    image_folder = "./Angola_MODIS_Images"
    output_folder = "./Resultados_Classificacao"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Processar a primeira imagem como exemplo
    file_path = os.path.join(image_folder, "angola_modis_000.tif")
    ndvi_image, classification_image, meta = process_image(file_path)

    # Visualizar o mapa classificado
    output_file = os.path.join(output_folder, "classificacao_cobertura_solo.png")
    visualize_land_cover(classification_image, meta, output_file)

    # Alternar visualização entre NDVI e classificação
    switch_visualization(ndvi_image, classification_image)
