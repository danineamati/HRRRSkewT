import glob

from PIL import Image

# 1. Settings
image_dir = "./skewt_point"
pattern = "*standard.png"
output_video_name = "standard_anim.gif"
fps = 5
duration_ms = int(1000 / fps)

# 2. Find and sort files chronologically
image_files = sorted(glob.glob(f"{image_dir}/{pattern}"))

if not image_files:
    print("No files found matching the pattern. Exiting.")
else:
    print(f"Compiling {len(image_files)} frames into {output_video_name}...")

    # 3. Load and prepare images
    images = []
    for file in image_files:
        img = Image.open(file).convert("RGB")
        img.load()
        images.append(img.copy())

    # Ensure all frames match the dimensions of the first frame (GIF requirement)
    target_size = images[0].size
    resample_filter = getattr(Image, "Resampling", Image).LANCZOS
    for i in range(len(images)):
        if images[i].size != target_size:
            images[i] = images[i].resize(target_size, resample_filter)

    # Quantize to Palette ('P') mode using an adaptive palette to prevent encoder failures
    images = [img.convert("P", palette=Image.ADAPTIVE) for img in images]

    # 4. Save animated GIF
    images[0].save(
        output_video_name,
        format="GIF",
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        optimize=False,
        loop=0,
        disposal=2,
    )
    print(f"Success! Video saved to {output_video_name}")
