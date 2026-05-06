import subprocess
import time
import csv
import os
import sys

# La Base URL de votre application sur Google Cloud doit être passée en environnement
BASE_URL = "https://tp1-cloud-494919.ue.r.appspot.com"


# Enlève l'éventuel slash à la fin
BASE_URL = BASE_URL.rstrip('/')

def get_active_instances():
    """
    Récupère le nombre d'instances actives sur Google App Engine via gcloud.
    Nécessite que gcloud soit installé et authentifié sur le poste.
    """
    try:
        import json
        result = subprocess.run(
            ["gcloud", "app", "instances", "list", "--format=json"],
            capture_output=True,
            text=True,
            check=True
        )
        instances = json.loads(result.stdout)
        return len(instances)
    except Exception as e:
        print(f"⚠️ Impossible de récupérer le nb d'instances avec gcloud (Assurez-vous d'être authentifié).")
        return "?"

def run_locust(concurrent_users, run_time="30s"):
    """
    Lance Locust en mode headless (sans interface) et parse les résultats générés dans le CSV
    """
    spawn_rate = max(1, concurrent_users // 5) 
    if spawn_rate > 100: spawn_rate = 100 
    
    print(f"🚀 Lancement de Locust: {concurrent_users} utilisateurs simultanés pendant {run_time}...")
    cmd = [
        "locust",
        "-f", "locustfile.py",
        "--headless",
        "-u", str(concurrent_users),
        "-r", str(spawn_rate),
        "--run-time", run_time,
        "--host", BASE_URL,
        "--csv", "tmp_results"
    ]
    
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    avg_time = 0
    failures = 0
    try:
        with open("tmp_results_stats.csv", "r", encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Name'] == 'Aggregated':
                    avg_time = float(row.get('Average Response Time', 0))
                    failures = int(row.get('Failure Count', 0))
                    break
    except Exception as e:
        print("⚠️ Erreur de lecture des résultats locust:", e)
        
    return avg_time, failures

def run_experiment_2(fanout_param):
    print("\n" + "="*60)
    print("EXPERIENCE 2: PASSAGE A L'ECHELLE SUR LA TAILLE DES DONNEES")
    print("="*60)
    
    results = []
    p = fanout_param
    os.environ['DATA_USERS'] = '1000'
    
    print(f"\n--- Configuration: Test avec {p} followers (paramètre stocké) ---")
    
    prefix = "user"
    os.environ['DATA_PREFIX'] = prefix
    
    instances = get_active_instances()
    
    for i in range(1, 4):
        print(f"\n--- Exécution {i}/3 ---")
        avg_time, failures = run_locust(50, run_time="30s") # Charge fixée à 50
        failed = 1 if failures > 0 else 0
        
        print(f"  > Résultat | Temps moy: {avg_time:.1f}ms | Échecs: {failures}")
        results.append([p, f"{int(avg_time)}ms", i, failed, instances])
            
    file_exists = os.path.isfile("out/fanout.csv")
    with open("out/fanout.csv", "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["PARAM", "AVG_TIME", "RUN", "FAILED", "NB instances"])
        writer.writerows(results)
    print("✅ Fichier out/fanout.csv mis à jour avec succès.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_benchmark_data.py <nombre_de_followers>")
        sys.exit(1)
        
    try:
        fanout_param = int(sys.argv[1])
    except ValueError:
        print("Erreur: L'argument doit être un nombre entier.")
        sys.exit(1)

    os.makedirs("out", exist_ok=True)
    
    temp_files = ["tmp_results_stats.csv", "tmp_results_stats_history.csv", "tmp_results_failures.csv", "tmp_results_exceptions.csv"]
    for f in temp_files:
        if os.path.exists(f):
            os.remove(f)

    print("🚀 Début du benchmark sur la taille des données...")
    run_experiment_2(fanout_param)
    
    for f in temp_files:
        if os.path.exists(f):
            os.remove(f)
            
    print("\n🎉 Expérience terminée. Retrouvez le résultat dans 'out/fanout.csv'.")
    print("N'oubliez pas de remplacer les '?' dans la colonne 'NB instances' si besoin.")
