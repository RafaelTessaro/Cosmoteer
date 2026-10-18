"""Extrai quadros de um GIF lado a lado num PNG (para revisar a animacao com uma imagem so).

    python3 tools/blender/gif_strip.py <arquivo.gif> <saida.png> [n_quadros=8]
"""
import sys

from PIL import Image


def main():
    src, dst = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    im = Image.open(src)
    total = im.n_frames
    # concentra os quadros no trecho do disparo (depois dos 10 quadros de mira)
    start = min(10, total - 1)
    idx = [min(total - 1, start + round(i * (total - start - 12) / max(1, n - 1))) for i in range(n)]
    frames = []
    for i in idx:
        im.seek(i)
        frames.append(im.convert("RGB"))
    w = sum(f.width for f in frames)
    h = max(f.height for f in frames)
    out = Image.new("RGB", (w, h), (7, 9, 14))
    x = 0
    for f in frames:
        out.paste(f, (x, 0))
        x += f.width
    scale = min(1.0, 2400 / w)
    if scale < 1:
        out = out.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    out.save(dst)
    print("OK", dst, out.size, "quadros", idx)


if __name__ == "__main__":
    main()
