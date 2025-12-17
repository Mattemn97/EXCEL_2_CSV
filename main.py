#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from PIL import Image, ImageFilter

# --------------------------
# FUNZIONI DI SIMULAZIONE
# --------------------------

def simulate_zoom(img, f_orig, f_new):
    """
    - f_new > f_orig → zoom (crop)
    - f_new < f_orig → grandangolo con bordi sfocati
    """

    w, h = img.size

    # -----------------------------
    # 1) ZOOM (crop)
    # -----------------------------
    if f_new > f_orig:
        zoom = f_new / f_orig
        new_w = int(w / zoom)
        new_h = int(h / zoom)

        left = (w - new_w) // 2
        top = (h - new_h) // 2
        right = left + new_w
        bottom = top + new_h

        return img.crop((left, top, right, bottom))

    # -----------------------------
    # 2) GRANDANGOLO (expand con blur)
    # -----------------------------
    elif f_new < f_orig:
        expand = f_orig / f_new

        new_w = int(w * expand)
        new_h = int(h * expand)

        # Crea sfondo sfocato: si parte dall'immagine ingrandita
        blurred_bg = img.resize((new_w, new_h), Image.LANCZOS)
        blurred_bg = blurred_bg.filter(ImageFilter.GaussianBlur(radius=50))

        # Incolla l'immagine originale al centro
        offset_x = (new_w - w) // 2
        offset_y = (new_h - h) // 2

        blurred_bg.paste(img, (offset_x, offset_y))
        return blurred_bg

    else:
        return img.copy()


# --------------------------
# MENÙ GUIDATO
# --------------------------

def guided_flow_zoom():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("— Generatore immagini a diverse lunghezze focali —\n")

    # 1) Input immagine
    while True:
        img_path = input("1) Inserisci il percorso dell'immagine sorgente: ").strip()
        if not os.path.isfile(img_path):
            print("❌ File non trovato. Riprova.")
            continue
        try:
            img = Image.open(img_path).convert("RGB")
        except Exception:
            print("❌ Formato immagine non valido.")
            continue
        break

    # 2) Focale originale
    while True:
        try:
            focale_orig = float(input("\n2) Inserisci la focale originale (mm): ").strip())
            break
        except ValueError:
            print("❌ Valore non valido, inserisci un numero.")

    # 3) Altre focali
    focali = []
    print("\n3) Inserisci le altre focali da simulare (mm)")
    print("   (separate da spazio, es: 12 18 35 70 200)")
    while True:
        try:
            raw = input("   → ").strip()
            focali = [float(x) for x in raw.split()]
            if len(focali) == 0:
                print("❌ Inserisci almeno una focale.")
                continue
            break
        except ValueError:
            print("❌ Formato non valido. Usa numeri separati da spazio.")

    # 4) Cartella output
    out_dir = input("\n4) Nome cartella output [default: output_zoom]: ").strip() or "output_zoom"
    os.makedirs(out_dir, exist_ok=True)

    # 5) Formato di output
    print("\n5) Formato output:")
    print("   jpg | png | webp | tiff")
    while True:
        fmt = input("   → [default: jpg]: ").strip().lower() or "jpg"
        if fmt in ("jpg", "jpeg", "png", "webp", "tiff"):
            break
        print("❌ Formato non valido.")

    # 6) Anteprima impostazioni
    print("\n📋 Anteprima impostazioni:")
    print(f" • Immagine sorgente: {img_path}")
    print(f" • Focale originale: {focale_orig} mm")
    print(f" • Focali da generare: {', '.join(str(int(f)) + 'mm' for f in focali)}")
    print(f" • Formato output: {fmt}")
    print(f" • Cartella output: {out_dir}\n")

    if input("Procedere con la generazione? [S/n]: ").strip().lower() in ("n", "no"):
        print("❌ Operazione annullata.")
        return

    # 7) Generazione immagini
    base_name = os.path.splitext(os.path.basename(img_path))[0]
    ext = f".{fmt}"

    print("\n⏳ Generazione in corso...\n")

    for f_new in focali:
        result = simulate_zoom(img, focale_orig, f_new)

        kind = "WIDE" if f_new < focale_orig else "ZOOM"
        out_name = f"{base_name}_{kind}_{int(f_new)}mm{ext}"
        out_path = os.path.join(out_dir, out_name)

        result.save(out_path)
        print(f"✔  Salvata {kind} {int(f_new)}mm → {out_path}")

    print("\n✅ Tutto fatto! Buona visione 🎉")


# --------------------------
# Entrypoint
# --------------------------

if __name__ == "__main__":
    guided_flow_zoom()
