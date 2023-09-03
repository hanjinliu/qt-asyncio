import numpy as np
import napari
from qt_asyncio import qasync, qcallback
from scipy.ndimage import gaussian_filter

@qcallback
def add_image(viewer: napari.Viewer, image) -> str:
    layer = viewer.add_image(image)
    return layer.name

@qcallback
def update_image(viewer: napari.Viewer, name: str, image):
    viewer.layers[name].data = image

@qasync
async def generate_images(viewer: napari.Viewer):
    name = await add_image(viewer, np.random.random((256, 256)))
    for i in range(10):
        new_image = gaussian_filter(viewer.layers[name].data, sigma=2.0)
        await update_image(viewer, name, new_image)

if __name__ == "__main__":
    viewer = napari.Viewer()

    @viewer.window.add_function_widget
    def start_task(viewer: napari.Viewer):
        generate_images(viewer).start()

    napari.run()
