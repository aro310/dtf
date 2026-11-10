# Accordeur chromatique et detecteur de notes en temps reel

Systeme de detection de notes musicales et accordeur chromatique base sur la Transformee de Fourier Discrete (TFD).

## Installation

```
pip install -r requirements.txt
```

## Fichiers

| Fichier | Role |
|---|---|
| `accordeur.py` | Programme principal : TFD manuelle, detection de notes, modes `--test` et `--spectre` |
| `dft.py` | Accordeur simple base sur la TFD (scipy) |
| `HPS.py` | Accordeur avance par la methode HPS (Harmonic Product Spectrum) |
| `interface.py` | Interface graphique (tkinter) pour lancer les demonstrations |
| `generer_spectre.py` | Genere les images du spectre |
| `requirements.txt` | Dependances Python |

## Utilisation

```
# Interface graphique (recommande)
python interface.py

# Accordeur temps reel (microphone)
python accordeur.py

# Mode test sans microphone : sinus 440 Hz doit donner La4
python accordeur.py --test

# Mode test + sauvegarde du spectre dans spectre.png
python accordeur.py --test --spectre

# Generer toutes les images pour le rapport PDF
python generer_spectre.py
```

## Methode

1. **Capture** : le signal audio est decoupage en fenetres de 1 seconde (44 100 echantillons).
2. **Fenetrage** : une fenetre de Hann est appliquee pour reduire les fuites spectrales.
3. **TFD** : la Transformee de Fourier Discrete calcule le spectre : `X[k] = somme x[n] * exp(-2j*pi*k*n/N)`.
4. **Fondamentale** : le module `|X[k]|` est calcule sur la moitie utile (`k < N/2`) et le pic donne la frequence : `f = k * fe / N`.
5. **Note** : la frequence est convertie en note chromatique par `i = arrondi(log2(f/440) * 12)`, avec l'ecart en cents.

## Verification de la TFD

```
python accordeur.py --test
```

Resultat attendu :
- `tfd([1,6,8,-4,9])` : X[0] = 20, X[1] = 2.399 - 4.2j
- Sinus 440 Hz detecte comme **La4** avec ecart de 0.0 cents
