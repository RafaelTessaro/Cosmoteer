"""Extrai quadros de um GIF lado a lado num PNG (para revisar a animacao com uma imagem so).

    python3 tools/blender/gif_strip.py <arquivo.gif> <saida.png> [n_quadros=8] [primeiro_quadro]

GIF longo (> 30 quadros, ex.: disparo das armas): os quadros saem do trecho do disparo (depois dos 10 quadros de mira
e antes dos 12 finais). GIF curto (ex.: previas layered de 8 quadros do tranco, FX da Fita): espalhados do 1o ao
ultimo. primeiro_quadro forca o inicio.
"""
import sys

from PIL import Image


def main():
    src, dst = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    im = Image.open(src)
    total = im.n_frames
    if len(sys.argv) > 4:
        start = max(0, min(total - 1, int(sys.argv[4])))
        end = total - 1
    elif total > 30:
        # concentra os quadros no trecho do disparo (depois dos 10 quadros de mira)
        start, end = min(10, total - 1), total - 12
    else:
        start, end = 0, total - 1
    end = max(start, end)
    idx = [min(total - 1, start + round(i * (end - start) / max(1, n - 1))) for i in range(n)]
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
