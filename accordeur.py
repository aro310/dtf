
"""
accordeur.py — Accordeur chromatique et detecteur de notes en temps reel
Base sur la Transformee de Fourier Discrete (TFD) calculee manuellement.

Modes d'utilisation :
  python accordeur.py              -> temps reel (microphone)
  python accordeur.py --test       -> mode test avec sinus synthetique a 440 Hz (La4)
  python accordeur.py --spectre    -> temps reel + sauvegarde du spectre dans spectre.png
  python accordeur.py --test --spectre -> test + spectre sauvegarde
"""

import argparse
import math
import numpy as np


# Parametres globaux
TAUX_ECHANTILLONNAGE = 44100   # frequence d'echantillonnage en Hz
TAILLE_FENETRE       = 44100   # taille de la fenetre d'analyse (1 seconde = 44100 echantillons)
PAS_FENETRE          = 22050   # decalage entre deux fenetres successives (en echantillons)
FREQ_LA_REF          = 440.0   # frequence de reference du La4 en Hz
SEUIL_FREQ_MIN       = 62      # suppression des frequences inferieures a 62 Hz (hum secteur)

# Les 12 noms de notes chromatiques (gamme temperee, a partir du La)
NOMS_NOTES = ["La", "La#", "Si", "Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#"]


# 1. TFD manuelle (deux boucles imbriquees) — lien direct avec le cours
def tfd(x):
    """
    Transformee de Fourier Discrete calculee par definition mathematique.

    Formule : X[k] = somme_{n=0}^{N-1}  x[n] * exp(-2j * pi * k * n / N)

    Parametres
    ----------
    x : liste ou tableau 1-D de nombres reels (signal temporel)

    Retourne
    --------
    X : liste de N nombres complexes (spectre discret)

    Complexite : O(N^2) — identique a la definition du cours.
    Verifie : tfd([1,6,8,-4,9]) -> X[0]=20, X[1] ~= 2.399-4.2j
              (meme resultat que np.fft.fft).
    """
    N = len(x)
    X = []
    for k in range(N):                          # pour chaque frequence k
        valeur_k = 0 + 0j
        for n in range(N):                      # somme sur tous les echantillons
            angle    = -2j * math.pi * k * n / N
            valeur_k += x[n] * math.e ** angle  # x[n] * e^(-2j*pi*k*n/N)
        X.append(valeur_k)
    return X


# 2. Conversion frequence -> note chromatique + ecart en cents
def note_la_plus_proche(frequence_hz):
    """
    Convertit une frequence (Hz) en note chromatique (12 notes) et calcule
    l'ecart en cents (100 cents = 1 demi-ton).

    Retourne : (nom_note, frequence_note, ecart_cents)
    """
    if frequence_hz <= 0:
        return "???", 0.0, 0.0
    # Nombre de demi-tons depuis La4 (arrondi a l'entier le plus proche)
    i         = int(round(math.log2(frequence_hz / FREQ_LA_REF) * 12))
    nom       = NOMS_NOTES[i % 12] + str(4 + (i + 9) // 12)
    freq_note = FREQ_LA_REF * 2 ** (i / 12)
    # Ecart en cents : 1200 cents = 1 octave
    ecart_cents = 1200 * math.log2(frequence_hz / freq_note)
    return nom, freq_note, ecart_cents


# 3. Analyse spectrale d'un bloc audio
def analyser_bloc(echantillons, sauvegarder_spectre=False):
    """
    Applique la fenetre de Hann, calcule le spectre via np.fft.fft (temps reel)
    et extrait la frequence fondamentale.

    La fonction tfd() manuelle est trop lente pour le temps reel (O(N^2) avec
    N = 44 100 echantillons), mais elle est utilisee en mode --test pour la
    verification pedagogique.

    Parametres
    ----------
    echantillons        : tableau numpy 1-D (signal audio)
    sauvegarder_spectre : bool — si True, sauvegarde le graphique dans spectre.png

    Retourne
    --------
    frequence_max : float (Hz), ou None si le signal est trop faible
    """
    N = len(echantillons)

    # Verification du niveau du signal (evite de traiter le silence)
    puissance = np.mean(echantillons ** 2)
    if puissance < 1e-7:
        return None

    # Application de la fenetre de Hann pour reduire les fuites spectrales
    fenetre        = np.hanning(N)
    signal_fenetre = echantillons * fenetre

    # TFD via numpy (rapide) — resultat mathematiquement identique a tfd()
    spectre_complexe = np.fft.fft(signal_fenetre)

    # Module du spectre, moitie utile (k < N/2, theoreme de Shannon-Nyquist)
    spectre_magnitude = np.abs(spectre_complexe[: N // 2])

    # Suppression de la composante continue (k=0) et des frequences inferieures a 62 Hz
    nb_bins_a_supprimer = int(SEUIL_FREQ_MIN / (TAUX_ECHANTILLONNAGE / N))
    spectre_magnitude[:nb_bins_a_supprimer] = 0

    # Recherche de l'indice du pic (frequence fondamentale)
    indice_max    = int(np.argmax(spectre_magnitude))
    # Conversion indice -> frequence : f = k * fe / N
    frequence_max = indice_max * (TAUX_ECHANTILLONNAGE / N)

    # Sauvegarde optionnelle du graphique du spectre
    if sauvegarder_spectre:
        _sauvegarder_spectre(spectre_magnitude, N, frequence_max)

    return frequence_max


def _sauvegarder_spectre(spectre_magnitude, N, freq_pic):
    """Genere et sauvegarde le graphique du spectre dans spectre.png."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    frequences = np.fft.rfftfreq(N, d=1.0 / TAUX_ECHANTILLONNAGE)[: N // 2]
    fig, ax    = plt.subplots(figsize=(10, 4))
    ax.plot(frequences, spectre_magnitude, color="steelblue", linewidth=0.8)
    ax.axvline(
        x=freq_pic, color="red", linestyle="--",
        label=f"Pic detecte : {freq_pic:.1f} Hz"
    )
    ax.set_xlabel("Frequence (Hz)")
    ax.set_ylabel("Amplitude |X[k]|")
    ax.set_title("Spectre frequentiel (TFD)")
    ax.set_xlim(0, 4000)      # limite a 4 kHz pour une meilleure lisibilite
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("spectre.png", dpi=150)
    plt.close(fig)
    print("[INFO] Spectre sauvegarde dans spectre.png")


# 4. Mode TEST — sinus synthetique a 440 Hz
def mode_test(sauvegarder_spectre=False):
    """
    Genere un sinus pur a 440 Hz (La4) et verifie que le systeme le detecte.
    Verifie aussi que tfd() donne le meme resultat que np.fft.fft
    sur le vecteur de test [1, 6, 8, -4, 9].
    """
    print("=" * 55)
    print("  MODE TEST — Verification sans microphone")
    print("=" * 55)

    # Verification de tfd() sur un vecteur court (calcul rapide en O(N^2))
    x_test  = [1, 6, 8, -4, 9]
    X_tfd   = tfd(x_test)
    X_numpy = np.fft.fft(x_test)

    print("\n[Verification tfd()] sur x = [1, 6, 8, -4, 9]")
    print(f"  tfd()[0]  = {X_tfd[0].real:.4f} + {X_tfd[0].imag:.4f}j  "
          f"(attendu : X[0] = 20)")
    print(f"  tfd()[1]  = {X_tfd[1].real:.4f} + {X_tfd[1].imag:.4f}j  "
          f"(attendu : X[1] ~= 2.399 - 4.2j)")
    print(f"  np.fft.fft()[0] = {X_numpy[0]:.4f}")
    print(f"  np.fft.fft()[1] = {X_numpy[1]:.4f}")

    erreur_max = max(abs(X_tfd[k] - X_numpy[k]) for k in range(len(x_test)))
    if erreur_max < 1e-9:
        print(f"  [OK] tfd() identique a np.fft.fft (erreur max = {erreur_max:.2e})")
    else:
        print(f"  [!!] ATTENTION : ecart = {erreur_max:.2e}")

    # Generation du sinus de test a 440 Hz (1 seconde)
    print("\n[Test sinus] Generation d'un sinus a 440 Hz...")
    t         = np.linspace(0, 1.0, TAILLE_FENETRE, endpoint=False)
    sinus_440 = np.sin(2 * math.pi * 440 * t).astype(np.float32)

    freq_detectee = analyser_bloc(sinus_440, sauvegarder_spectre=sauvegarder_spectre)

    if freq_detectee is None:
        print("  [!!] Signal trop faible, aucune frequence detectee.")
        return

    note, freq_note, cents = note_la_plus_proche(freq_detectee)
    print(f"  Frequence detectee  : {freq_detectee:.1f} Hz")
    print(f"  Note la plus proche : {note}  ({freq_note:.1f} Hz)")
    print(f"  Ecart               : {cents:+.1f} cents")

    if note.startswith("La") and abs(cents) < 1.0:
        print("  [OK] SUCCES : La4 correctement detecte !")
    else:
        print("  [!!] ECHEC : la note detectee n'est pas La4.")

    print("=" * 55)


# 5. Mode TEMPS REEL — capture microphone
def mode_temps_reel(sauvegarder_spectre=False):
    """
    Capture le microphone en continu via sounddevice et affiche la note detectee.
    """
    try:
        import sounddevice as sd
    except ImportError:
        print("[ERREUR] Le module 'sounddevice' est requis pour le mode temps reel.")
        print("  Installez-le avec : pip install sounddevice")
        return

    import os

    # Tampon circulaire partage entre la fonction de rappel et la boucle principale
    tampon = {
        "echantillons"        : np.zeros(TAILLE_FENETRE, dtype=np.float32),
        "premier_spectre_sauve": False
    }

    def callback_audio(entree, frames, temps, statut):
        """Fonction de rappel sounddevice : recoit les nouveaux echantillons audio."""
        if statut:
            print(f"[AVERTISSEMENT audio] {statut}")

        if np.any(entree):
            nouveaux = entree[:, 0]
            # Decalage du tampon et ajout des nouveaux echantillons (fenetre glissante)
            tampon["echantillons"] = np.concatenate(
                (tampon["echantillons"], nouveaux)
            )
            tampon["echantillons"] = tampon["echantillons"][len(nouveaux):]

            # Le spectre n'est sauvegarde qu'une seule fois (au premier signal valide)
            enregistrer = sauvegarder_spectre and not tampon["premier_spectre_sauve"]

            freq = analyser_bloc(tampon["echantillons"], sauvegarder_spectre=enregistrer)

            if enregistrer and freq is not None:
                tampon["premier_spectre_sauve"] = True

            # Effacement de la console avant chaque mise a jour
            if os.name == "nt":
                os.system("cls")
            else:
                os.system("clear")

            if freq is not None:
                note, freq_note, cents = note_la_plus_proche(freq)
                barre = _barre_accordeur(cents)
                print(f"  Note    : {note}")
                print(f"  Mesure  : {freq:.1f} Hz   |   Reference : {freq_note:.1f} Hz")
                print(f"  Ecart   : {cents:+.1f} cents")
                print(f"  {barre}")
            else:
                print("  ... (silence ou signal trop faible)")
        else:
            print("  ... (pas d'entree audio)")

    print("Accordeur chromatique — appuyez sur Ctrl+C pour quitter")
    print(f"Taux d'echantillonnage : {TAUX_ECHANTILLONNAGE} Hz  |  "
          f"Fenetre : {TAILLE_FENETRE} echantillons")

    try:
        with sd.InputStream(
            channels=1,
            callback=callback_audio,
            blocksize=PAS_FENETRE,
            samplerate=TAUX_ECHANTILLONNAGE,
        ):
            import time
            while True:
                time.sleep(0.1)   # attente passive (n'utilise pas le CPU inutilement)

    except KeyboardInterrupt:
        print("\n[Accordeur arrete]")
    except Exception as erreur:
        print(f"[ERREUR] {erreur}")
        print("  Verifiez les permissions microphone ou essayez --test.")


def _barre_accordeur(cents):
    """
    Genere une barre visuelle dans le terminal representant l'ecart d'accordage.
    Le symbole central '|' indique la cible (note juste).
    """
    largeur = 41
    centre  = largeur // 2
    pos     = int(cents / 50 * (largeur // 2))  # 50 cents correspond a la moitie de la barre
    pos     = max(-centre, min(centre, pos))
    barre   = ["-"] * largeur
    barre[centre] = "|"            # position centrale = note accordee
    barre[centre + pos] = "o"      # position courante de l'aiguille
    if pos == 0:
        barre[centre] = "o"        # exactement sur la cible
    return "[" + "".join(barre) + "]"


# 6. Point d'entree principal
if __name__ == "__main__":
    analyseur = argparse.ArgumentParser(
        description="Accordeur chromatique base sur la TFD"
    )
    analyseur.add_argument(
        "--test",
        action="store_true",
        help="Mode test sans microphone (sinus synthetique a 440 Hz = La4)",
    )
    analyseur.add_argument(
        "--spectre",
        action="store_true",
        help="Sauvegarde le spectre frequentiel dans spectre.png",
    )
    args = analyseur.parse_args()

    if args.test:
        mode_test(sauvegarder_spectre=args.spectre)
    else:
        mode_temps_reel(sauvegarder_spectre=args.spectre)
