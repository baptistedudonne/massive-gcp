# Commandes pour le Benchmark TinyInsta sur GCP

Ce document détaille les commandes à exécuter séquentiellement pour réaliser les deux parties de votre projet, en utilisant vos scripts actuels.

## 1. Passage à l'échelle sur la charge

**Objectif :** 1000 utilisateurs, 50 posts par utilisateur, 20 followers par utilisateur.
Mesurer le temps avec : 1, 10, 20, 50, 100, 1000 utilisateurs simultanés.

**Étape 1.1 : Initialiser la base de données**
Vous partez d'une base de données vide (ou vous créez les nouveaux utilisateurs). Il faut 1000 utilisateurs, 50 posts en moyenne par utilisateur (donc 50 000 posts au total) et 20 followers.

```bash
python3 seed.py --users 1000 --posts 50000 --follows-min 20 --follows-max 20
```

**Étape 1.2 : Lancer le benchmark de charge**
Votre script `run_benchmark_charge.py` s'occupe de lancer les différents paliers de concurrence et d'écrire dans `out/conc.csv`.

```bash
python3 run_benchmark_charge.py
```

---

## 2. Passage à l'échelle sur la taille des données

**Objectif :** 1000 utilisateurs, 100 posts par utilisateur, 50 utilisateurs simultanés.
Faire varier les followers : 20, 40, 60.

Puisque nous avons déjà 1000 utilisateurs avec 50 posts et 20 followers grâce à la Phase 1, on "continue sur cette lancée" en ajoutant ce qui manque, au lieu de tout recréer. 

**Étape 2.1 : Atteindre 100 posts par utilisateur (Benchmark avec 20 followers)**
Il nous manque 50 posts par utilisateur pour atteindre les 100. On rajoute donc 50 000 posts. On ne modifie pas le nombre de followers puisqu'ils sont déjà à 20.

```bash
python3 seed.py --users 1000 --posts 50000 --follows-min 0 --follows-max 0
python3 run_benchmark_data.py 20
```

**Étape 2.2 : Passer à 40 followers (Benchmark avec 40 followers)**
On ne rajoute plus de posts (on est déjà à 100), mais on modifie les followers. Puisqu'ils en ont déjà 20 et que `seed.py` *fusionne* les nouveaux followers avec les anciens, on demande au script d'en rajouter **20 nouveaux**. (20 existants + 20 nouveaux = environ 40 abonnés).

```bash
python3 seed.py --users 1000 --posts 0 --follows-min 20 --follows-max 20
python3 run_benchmark_data.py 40
```
*(Note : La fusion n'est pas parfaite à 100% car il peut y avoir des doublons aléatoires, vous aurez donc environ 39-40 followers en base, ce qui est extrêmement précis).*

**Étape 2.3 : Passer à 60 followers (Benchmark avec 60 followers)**
De la même manière, pour passer de ~40 à 60 followers, on demande à `seed.py` d'en générer **20 nouveaux** qui vont s'additionner.

```bash
python3 seed.py --users 1000 --posts 0 --follows-min 20 --follows-max 20
python3 run_benchmark_data.py 60
```

---

## Résumé des commandes (à copier-coller)

```bash
# === PHASE 1 : Charge ===
python3 seed.py --users 1000 --posts 50000 --follows-min 20 --follows-max 20
python3 run_benchmark_charge.py

# === PHASE 2 : Taille des données ===
python3 seed.py --users 1000 --posts 50000 --follows-min 0 --follows-max 0
python3 run_benchmark_data.py 20

python3 seed.py --users 1000 --posts 0 --follows-min 20 --follows-max 20
python3 run_benchmark_data.py 40

python3 seed.py --users 1000 --posts 0 --follows-min 20 --follows-max 20
python3 run_benchmark_data.py 60
```

Une fois ces commandes terminées, vos fichiers `out/conc.csv` et `out/fanout.csv` contiendront l'intégralité des mesures nécessaires pour générer vos graphiques !
