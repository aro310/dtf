import copy
import os
import numpy as np
import scipy.fftpack
import sounddevice as sd
import time

# Parametres globaux (modifiables par l'utilisateur)

taux_echantillonnage  = 48000   # frequence d'echantillonnage en Hz
taille_fenetre        = 48000   # nombre d'echantillons par fenetre d'analyse (1 seconde)
pas_fenetre           = 12000   # decalage entre deux fenetres successives
iterations_hps        = 5       # nombre d'iterations pour la methode HPS
seuil_puissance_min   = 1e-6    # seuil de puissance minimale sous lequel on ignore le signal
frequence_la_ref      = 440     # frequence de reference du La4 en Hz
seuil_bruit_blanc     = 0.2     # seuil de suppression du bruit blanc (fraction de l'energie moyenne)

duree_fenetre      = taille_fenetre / taux_echantillonnage  # duree de la fenetre en secondes
duree_echantillon  = 1 / taux_echantillonnage               # duree entre deux echantillons
resolution_freq    = taux_echantillonnage / taille_fenetre  # resolution frequentielle en Hz/bin
# Bandes d'octave utilisees pour le calcul de l'energie moyenne par bande
bandes_octave = [50, 100, 200, 400, 800, 1600, 3200, 6400, 12800, 25600]

# Noms des 12 notes chromatiques (gamme temperee, a partir du La)
noms_notes = ["La", "La#", "Si", "Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#"]


def note_la_plus_proche(frequence):
    """
    Trouve la note chromatique la plus proche d'une frequence donnee.

    Parametre :
        frequence (float) : frequence mesuree en Hz

    Retourne :
        nom_note       (str)   : nom de la note la plus proche (ex. La4, Sol3)
        frequence_note (float) : frequence theorique de cette note en Hz
    """
    # Nombre de demi-tons depuis La4 : i = arrondi( log2(f / 440) * 12 )
    i              = int(np.round(np.log2(frequence / frequence_la_ref) * 12))
    nom_note       = noms_notes[i % 12] + str(4 + (i + 9) // 12)
    frequence_note = frequence_la_ref * 2 ** (i / 12)
    return nom_note, frequence_note


# Fenetre de Hann precalculee pour reduire les fuites spectrales
fenetre_hann = np.hanning(taille_fenetre)


def callback(entree, frames, temps, statut):
    """
    Fonction de rappel sounddevice.
    Appelee automatiquement a chaque nouveau bloc d'echantillons audio.
    """
    # Initialisation du tampon circulaire (attribut statique de la fonction)
    if not hasattr(callback, "tampon"):
        callback.tampon = [0 for _ in range(taille_fenetre)]

    # Initialisation du tampon de lissage des notes (evite les affichages instables)
    if not hasattr(callback, "historique_notes"):
        callback.historique_notes = ["1", "2"]

    if statut:
        print(statut)
        return

    if any(entree):
        # Mise a jour du tampon circulaire par concatenation et decalage
        callback.tampon = np.concatenate(
            (callback.tampon, entree[:, 0])
        )
        callback.tampon = callback.tampon[len(entree[:, 0]):]

        # Ignorer les signaux trop faibles (silence ou bruit de fond negligeable)
        puissance_signal = (
            np.linalg.norm(callback.tampon, ord=2) ** 2
        ) / len(callback.tampon)
        if puissance_signal < seuil_puissance_min:
            os.system("cls" if os.name == "nt" else "clear")
            print("Note la plus proche : ....")
            return

        # Application de la fenetre de Hann pour reduire les fuites spectrales
        signal_fenetre  = callback.tampon * fenetre_hann
        # Calcul de la TFD et extraction du module sur la moitie utile (k < N/2)
        spectre_magnitude = abs(
            scipy.fftpack.fft(signal_fenetre)[: len(signal_fenetre) // 2]
        )

        # Suppression des frequences inferieures a 62 Hz (hum secteur + composante continue)
        for i in range(int(62 / resolution_freq)):
            spectre_magnitude[i] = 0

        # Calcul de l'energie moyenne par bande d'octave.
        # Les bins dont l'amplitude est inferieure au seuil sont mis a zero
        # pour reduire l'effet du bruit blanc (necessaire avant d'appliquer la methode HPS).
        for j in range(len(bandes_octave) - 1):
            debut = int(bandes_octave[j]     / resolution_freq)
            fin   = int(bandes_octave[j + 1] / resolution_freq)
            fin   = fin if len(spectre_magnitude) > fin else len(spectre_magnitude)
            energie_moyenne = (
                np.linalg.norm(spectre_magnitude[debut:fin], ord=2) ** 2
            ) / (fin - debut)
            energie_moyenne = energie_moyenne ** 0.5

            for i in range(debut, fin):
                spectre_magnitude[i] = (
                    spectre_magnitude[i]
                    if spectre_magnitude[i] > energie_moyenne * seuil_bruit_blanc
                    else 0
                )

        # Interpolation du spectre pour augmenter la resolution avant la methode HPS
        spectre_interpole = np.interp(
            np.arange(0, len(spectre_magnitude), 1 / iterations_hps),
            np.arange(0, len(spectre_magnitude)),
            spectre_magnitude,
        )
        # Normalisation du spectre interpole
        spectre_interpole = spectre_interpole / np.linalg.norm(spectre_interpole, ord=2)

        # Application de la methode HPS (Harmonic Product Spectrum)
        # Principe : multiplier le spectre par ses sous-echantillons successifs ;
        # le fondamental ressort car ses harmoniques se superposent.
        spectre_hps = copy.deepcopy(spectre_interpole)
        for i in range(iterations_hps):
            spectre_hps_temp = np.multiply(
                spectre_hps[: int(np.ceil(len(spectre_interpole) / (i + 1)))],
                spectre_interpole[:: (i + 1)],
            )
            if not any(spectre_hps_temp):
                break
            spectre_hps = spectre_hps_temp

        # Extraction de la frequence fondamentale depuis le spectre HPS
        indice_max    = np.argmax(spectre_hps)
        frequence_max = indice_max * (taux_echantillonnage / taille_fenetre) / iterations_hps

        nom_note, frequence_note = note_la_plus_proche(frequence_max)
        frequence_max  = round(frequence_max, 1)
        frequence_note = round(frequence_note, 1)

        # Lissage temporel : on affiche la note seulement si les deux derniers
        # resultats concordent (evite les affichages instables)
        callback.historique_notes.insert(0, nom_note)
        callback.historique_notes.pop()

        os.system("cls" if os.name == "nt" else "clear")
        if callback.historique_notes.count(callback.historique_notes[0]) == len(
            callback.historique_notes
        ):
            print(f"Note la plus proche : {nom_note}  {frequence_max} Hz / {frequence_note} Hz")
        else:
            print("Note la plus proche : ....")

    else:
        print("Aucune entree audio detectee.")


try:
    print("Demarrage de l'accordeur HPS (Harmonic Product Spectrum)...")
    with sd.InputStream(
        channels=1,
        callback=callback,
        blocksize=pas_fenetre,
        samplerate=taux_echantillonnage
    ):
        # Boucle principale : on attend les evenements audio dans le callback
        while True:
            time.sleep(0.5)

except Exception as erreur:
    print(str(erreur))
