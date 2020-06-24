import numpy as np
import cairocffi as cairo
import json
import os
import argparse
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from config import connect_str

parser = argparse.ArgumentParser(
    description="convert .ndjson into .png and upload to azure blobstore"
)
parser.add_argument(
    "classNames",
    metavar="names",
    type=str,
    nargs="+",
    help="names of the classes that you want to convert",
)
parser.add_argument("-n", type=int, default=50, help="how many images of each class")
parser.add_argument("-u", type)


def vector_to_raster(
    vector_images,
    blob_service_client,
    side=28,
    line_diameter=16,
    padding=16,
    bg_color=(1, 1, 1),
    className="boat",
    fg_color=(0, 0, 0),
    dirp="",
    keys=[],
):
    """
    padding and line_diameter are relative to the original 256x256 image.
    """

    original_side = 256.0

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, side, side)
    ctx = cairo.Context(surface)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_width(line_diameter)

    # scale to match the new size
    # add padding at the edges for the line_diameter
    # and add additional padding to account for antialiasing
    total_padding = padding * 2.0 + line_diameter
    new_scale = float(side) / float(original_side + total_padding)
    ctx.scale(new_scale, new_scale)
    ctx.translate(total_padding / 2.0, total_padding / 2.0)

    raster_images = []
    for vector_image, key in zip(vector_images, keys):
        # clear background
        ctx.set_source_rgb(*bg_color)
        ctx.paint()

        intermediate = np.hstack(vector_image)
        bbox = intermediate.max(axis=1)
        offset = ((original_side, original_side) - bbox) / 2.0
        offset = offset.reshape(-1, 1)
        centered = [stroke + offset for stroke in vector_image]

        # draw strokes, this is the most cpu-intensive part
        ctx.set_source_rgb(*fg_color)
        for xv, yv in centered:
            ctx.move_to(xv[0], yv[0])
            for x, y in zip(xv, yv):
                ctx.line_to(x, y)
            ctx.stroke()

        filepath = f"{dirp}/{key}.png"
        surface.write_to_png(filepath)

        upload_to_blob(filepath, key, className, blob_service_client)
        data = surface.get_data()
        raster_image = np.copy(np.asarray(data)[::4])
        raster_images.append(raster_image)

    return raster_images


def upload_to_blob(path, key, className, blob_service_client):

    blob_client = blob_service_client.get_blob_client(className, blob=f"{key}.png")

    with open(path, "rb") as localFile:
        try:
            blob_client.upload_blob(localFile)
        except:
            print(f"the image {key} already exists")


def get_images_from_class(className, N=100):
    path = f"./data/{className}.ndjson"

    lines = []
    with open(path) as f:
        while len(lines) < N:
            try:
                line = json.loads(next(f))
            except StopIteration:
                break
            lines.append(line)
    return lines


if __name__ == "__main__":
    args = parser.parse_args()
    cnames = args.classNames

    # print(connect_str)
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    if not os.path.exists("./images"):
        os.makedirs("./images")

    for className in cnames:
        dirp = f"./images/{className}"

        container_name = className

        if container_name not in [
            c["name"] for c in blob_service_client.list_containers()
        ]:
            container_client = blob_service_client.create_container(container_name)

        if not os.path.exists(dirp):
            os.makedirs(dirp)
        vectors = get_images_from_class(className, N=args.n)
        paths = [v["drawing"] for v in vectors]
        keys = [v["key_id"] for v in vectors]

        raster = vector_to_raster(
            paths,
            blob_service_client,
            side=256,
            dirp=dirp,
            keys=keys,
            className=className,
        )
