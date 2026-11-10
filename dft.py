import sounddevice as sd
import numpy as np
import scipy
import scipy.fftpack
import os


# Parametres globaux du programme

taux_echantillonnage = 44100  # frequence d'echantillonnage en Hz
taille_fenetre       = 44100  # taille de la fenetre d'analyse (1 seconde = 44100 echantillons)
pas_fenetre          = 21050  # decalage entre deux fenetres successives (en echantillons)
duree_fenetre        = taille_fenetre / taux_echantillonnage  # duree de la fenetre en secondes
duree_echantillon    = 1 / taux_echantillonnage               # duree entre deux echantillons
# Modification etudiant : double espace supprime avant le signe '=' ci-dessus (avertissement E221).
tampon_echantillons = [0 for _ in range(taille_fenetre)]  # tampon circulaire initialise a zero

# Frequence de reference et noms des 12 notes chromatiques (gamme temperee)
frequence_la_ref = 440
noms_notes = ["La", "La#", "Si", "Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#"]


def note_la_plus_proche(frequence):
    """
    Trouve la note chromatique la plus proche d'une frequence donnee.

    Parametre : frequence (float) — frequence mesuree en Hz
    Retourne  : (nom_note, frequence_note)
    """
    # Nombre de demi-tons depuis La4 : i = arrondi( log2(f / 440) * 12 )
    i = int(np.round(np.log2(frequence / frequence_la_ref) * 12))
    nom_note       = noms_notes[i % 12] + str(4 + (i + 9) // 12)
    frequence_note = frequence_la_ref * 2 ** (i / 12)
    return nom_note, frequence_note


# Fonction de rappel sounddevice
# Appelee automatiquement chaque fois que de nouveaux echantillons sont disponibles

def callback(entree, frames, temps, statut):
    # sounddevice transmet ici un objet CData (horodatage CFFI), pas le module time.
    # Le nom est conserve pour respecter la signature imposee par sounddevice ;
    # l'avertissement W0621 (redefined-outer-name) est donc normal ici.
    global tampon_echantillons
    if statut:
        print(statut)

    if any(entree):
        # Ajout des nouveaux echantillons a la fin du tampon
        tampon_echantillons = np.concatenate(
            (tampon_echantillons, entree[:, 0])
        )
        # Suppression des anciens echantillons en debut de tampon (fenetre glissante)
        tampon_echantillons = tampon_echantillons[len(entree[:, 0]):]

        # Calcul de la TFD et extraction du module sur la moitie utile (k < N/2)
        spectre_magnitude = abs(
            scipy.fftpack.fft(tampon_echantillons)[: len(tampon_echantillons) // 2]
        )

        # Suppression des frequences inferieures a 62 Hz (bruit secteur et composante continue)
        for i in range(int(62 / (taux_echantillonnage / taille_fenetre))):
            spectre_magnitude[i] = 0

        # Recherche de l'indice du pic dominant dans le spectre
        indice_max     = np.argmax(spectre_magnitude)
        # Conversion indice -> frequence : f = k * fe / N
        frequence_max  = indice_max * (taux_echantillonnage / taille_fenetre)
        note, freq_ref = note_la_plus_proche(frequence_max)

        # Effacement de la console (compatibilite Windows et Linux)
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")

        print(f"Note la plus proche : {note}  {frequence_max:.1f} Hz / {freq_ref:.1f} Hz")

    else:
        print("Aucune entree audio detectee.")


try:
    with sd.InputStream(
        channels=1,
        callback=callback,
        blocksize=pas_fenetre,
        samplerate=taux_echantillonnage
    ):
        # Modification etudiant : 'while True: pass' remplace par un sleep pour eviter
        # une boucle occupee (busy-wait) qui monopolise un coeur CPU a 100 %.
        # Avertissement corrige : W0107 "Unnecessary 'pass' in non-empty loop body".
        import time as module_temps
        while True:
            module_temps.sleep(0.1)

except Exception as erreur:
    print(str(erreur))
