import csv
import matplotlib.pyplot as plt
import numpy as np
import os

# Chemin vers le fichier CSV
csv_file = "out/conc.csv"

if not os.path.exists(csv_file):
    print(f"Erreur: Le fichier {csv_file} est introuvable.")
    exit(1)

# Dictionnaire pour stocker les temps de réponse par configuration (PARAM)
data = {}

with open(csv_file, "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Extraire le nombre d'utilisateurs simultanés
        param = int(row["PARAM"])
        
        # Nettoyer et convertir le temps moyen (enlever "ms")
        time_str = row["AVG_TIME"].replace("ms", "")
        avg_time = float(time_str)
        
        if param not in data:
            data[param] = []
        data[param].append(avg_time)

# Calculer la moyenne pour chaque configuration
params = sorted(data.keys())
mean_times = [np.mean(data[p]) for p in params]
std_times = [np.std(data[p]) for p in params] # Pour ajouter une barre d'erreur si vous voulez

# Création du graphique (Barplot)
plt.figure(figsize=(10, 6))

# Les positions des barres
x_pos = np.arange(len(params))

# Créer les barres avec les moyennes
bars = plt.bar(x_pos, mean_times, color='skyblue', edgecolor='black', yerr=std_times, capsize=5)

# Ajouter les valeurs sur le haut de chaque barre
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + (max(mean_times)*0.01), 
             f'{int(yval)} ms', ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.xticks(x_pos, [str(p) for p in params])
plt.xlabel("Nombre d'utilisateurs simultanés", fontsize=12)
plt.ylabel("Temps de réponse moyen (ms)", fontsize=12)
plt.title("Performance de l'API selon la charge (Concurrency)", fontsize=14, fontweight='bold')
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Sauvegarder le graphique dans le dossier out/
output_image = "out/conc_plot.png"
plt.tight_layout()
plt.savefig(output_image, dpi=300)
print(f"✅ Graphique généré avec succès : {output_image}")

# Afficher la fenêtre du graphique
plt.show()
