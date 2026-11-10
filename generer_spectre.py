import math
import cmath
import os
import sys


# TFD manuelle (deux boucles imbriquees)
# Formule : X[k] = somme_{n=0}^{N-1} x[n] * exp(-2j * pi * k * n / N)
def tfd(x):
    """Transformee de Fourier Discrete par definition — O(N^2), lien avec le cours."""
    N = len(x)
    return [
        sum(x[n] * cmath.exp(-2j * math.pi * k * n / N) for n in range(N))
        for k in range(N)
    ]


# Signal de test : sinus pur a 440 Hz, 1 seconde, fe = 44 100 Hz
fe      = 44100
N       = fe                             # nombre d'echantillons (1 seconde)
t       = [n / fe for n in range(N)]     # axe temporel
signal  = [math.sin(2 * math.pi * 440 * ti) for ti in t]  # sinus 440 Hz


# Importation de numpy et matplotlib
try:
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")          # moteur sans affichage (sauvegarde fichier uniquement)
    import matplotlib.pyplot as plt
except ImportError:
    print("ERREUR : numpy et matplotlib sont requis.")
    print("Installez-les avec : pip install numpy matplotlib")
    sys.exit(1)


# Figure 1 : spectre frequentiel du sinus 440 Hz (0 a 2000 Hz)
sig_np  = np.array(signal, dtype=np.float64)
fenetre = np.hanning(N)                       # fenetre de Hann pour reduire les fuites spectrales
spectre = np.abs(np.fft.fft(sig_np * fenetre)[: N // 2])  # module, moitie utile
freqs   = np.fft.rfftfreq(N, 1 / fe)[: N // 2]            # axe des frequences
idx_max = int(np.argmax(spectre))             # indice du pic dominant
f_pic   = freqs[idx_max]                      # frequence du pic en Hz

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(freqs, spectre, color="steelblue", linewidth=0.9, label="Spectre |X[k]|")
ax.axvline(
    f_pic, color="red", linestyle="--", linewidth=1.5,
    label=f"Pic detecte : {f_pic:.1f} Hz (La4 = 440 Hz)"
)
ax.set_xlim(0, 2000)
ax.set_xlabel("Frequence  f = k * fe / N   (Hz)", fontsize=12)
ax.set_ylabel("|X[k]|  (amplitude)", fontsize=12)
ax.set_title(
    "Spectre frequentiel TFD — Sinus synthetique 440 Hz (La4)\n"
    "Signal : 1 s, fe = 44 100 Hz, fenetre de Hann",
    fontsize=12
)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
sortie_1 = os.path.join(os.path.dirname(__file__), "spectre.png")
plt.savefig(sortie_1, dpi=150)
plt.close()
print(f"[OK] {sortie_1}")


# Figure 2 : verification tfd() manuelle vs numpy sur x = [1, 6, 8, -4, 9]
x_court  = [1, 6, 8, -4, 9]
X_tfd    = tfd(x_court)                    # TFD manuelle
X_numpy  = np.fft.fft(x_court)            # TFD numpy (reference)
indices  = list(range(len(x_court)))
amp_tfd  = [abs(v) for v in X_tfd]        # module de chaque coefficient (tfd manuelle)
amp_np   = [abs(v) for v in X_numpy]      # module de chaque coefficient (numpy)

fig2, (ax0, ax1) = plt.subplots(1, 2, figsize=(11, 4))
largeur_barre = 0.35

# Sous-figure gauche : comparaison des amplitudes |X[k]|
ax0.bar(
    [i - largeur_barre / 2 for i in indices], amp_tfd,
    width=largeur_barre, label="tfd() manuelle", color="steelblue"
)
ax0.bar(
    [i + largeur_barre / 2 for i in indices], amp_np,
    width=largeur_barre, label="np.fft.fft()", color="tomato", alpha=0.75
)
ax0.set_xticks(indices)
ax0.set_xticklabels([f"k={k}" for k in indices])
ax0.set_ylabel("|X[k]|")
ax0.set_title("Verification tfd([1,6,8,-4,9])\ntfd() manuelle vs np.fft.fft()")
ax0.legend()
ax0.grid(axis="y", alpha=0.3)

# Sous-figure droite : parties reelle et imaginaire de tfd()
re_tfd = [v.real for v in X_tfd]          # partie reelle
im_tfd = [v.imag for v in X_tfd]          # partie imaginaire
ax1.bar(
    [i - largeur_barre / 2 for i in indices], re_tfd,
    width=largeur_barre, label="Partie reelle", color="steelblue"
)
ax1.bar(
    [i + largeur_barre / 2 for i in indices], im_tfd,
    width=largeur_barre, label="Partie imaginaire", color="darkorange"
)
ax1.axhline(0, color="black", linewidth=0.8)
ax1.set_xticks(indices)
ax1.set_xticklabels([f"k={k}" for k in indices])
ax1.set_ylabel("Valeur")
ax1.set_title(
    f"X[0] = {X_tfd[0].real:.2f}  (attendu 20)\n"
    f"X[1] = {X_tfd[1].real:.3f}{X_tfd[1].imag:+.3f}j  (attendu 2.399-4.2j)"
)
ax1.legend()
ax1.grid(axis="y", alpha=0.3)

plt.suptitle("TFD manuelle — Verification sur x = [1, 6, 8, -4, 9]", fontsize=13, y=1.01)
plt.tight_layout()
sortie_2 = os.path.join(os.path.dirname(__file__), "spectre_tfd.png")
plt.savefig(sortie_2, dpi=150, bbox_inches="tight")
plt.close()
print(f"[OK] {sortie_2}")


# Figure 3 : schema du pipeline de traitement du signal
from matplotlib.patches import FancyBboxPatch  # formes rectangulaires arrondies

fig3, ax = plt.subplots(figsize=(11, 2.5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 2)
ax.axis("off")   # masquer les axes (schema uniquement)

# Definition des etapes du pipeline avec leur position, label et couleur
etapes = [
    (0.5, "Signal audio\nx[n]",          "lightblue"),
    (2.5, "Fenetre de Hann\nx[n]*w[n]",  "lightyellow"),
    (4.5, "TFD\nX[k]",                   "lightgreen"),
    (6.5, "Module |X[k]|\nk < N/2",      "lightyellow"),
    (8.5, "Note + Cents\nlog2(f/440)*12","lightcoral"),
]

for (x_pos, libelle, couleur) in etapes:
    # Dessin du bloc de l'etape
    ax.add_patch(
        FancyBboxPatch(
            (x_pos - 0.9, 0.4), 1.8, 1.2,
            boxstyle="round,pad=0.1", fc=couleur, ec="gray", lw=1.2
        )
    )
    ax.text(
        x_pos, 1.0, libelle,
        ha="center", va="center", fontsize=9.5,
        fontweight="bold" if libelle.startswith("TFD") else "normal"
    )

# Fleches de liaison entre les blocs
for i in range(len(etapes) - 1):
    x_debut = etapes[i][0] + 0.9
    x_fin   = etapes[i + 1][0] - 0.9
    ax.annotate(
        "", xy=(x_fin, 1.0), xytext=(x_debut, 1.0),
        arrowprops=dict(arrowstyle="->", color="gray", lw=1.5)
    )

# Formule de conversion frequence affichee sous le bloc TFD
ax.text(
    4.5, 0.15, "f = k * fe / N   Hz",
    ha="center", fontsize=9, color="darkgreen", style="italic"
)

ax.set_title(
    "Pipeline de traitement du signal — Accordeur chromatique TFD",
    fontsize=12, pad=10
)
plt.tight_layout()
sortie_3 = os.path.join(os.path.dirname(__file__), "schema_pipeline.png")
plt.savefig(sortie_3, dpi=150, bbox_inches="tight")
plt.close()
print(f"[OK] {sortie_3}")

# Resume des fichiers generes
print("\nImages generees :")
print(f"  spectre.png         -> spectre frequentiel du sinus 440 Hz")
print(f"  spectre_tfd.png     -> verification tfd() manuelle vs numpy")
print(f"  schema_pipeline.png -> schema du pipeline de traitement")
