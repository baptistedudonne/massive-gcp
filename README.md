# Tiny Instagram (minimal) on Google App Engine

This repository contains a tiny Instagram-like demo implemented with Flask and Google Cloud Datastore (Firestore in Datastore mode). It is a small, educational project that demonstrates posting, following, and reading a simple timeline.

This README describes how to run, seed and test the app, plus notes about GQL queries and common deployment troubleshooting.

## Prerequisites
- Create a GCP Project:`https://console.cloud.google.com/`
  - See the prof.

- Open a cloud shell 
  - see the prof.

* Initialize or select your GCP project and create the App Engine application (if not already created):

```sh
gcloud init
gcloud app repair
```

- clone the prof github repository : 
```
git clone https://github.com/momo54/massive-gcp
cd massive-gcp
```

* Install dependencies
```sh
pip install -r requirements.txt
```

* Deploy the app:

```sh
gcloud app deploy
```

* [OPTIONAL] Index does not matter:

```sh
gcloud app deploy index.yaml
# or
gcloud datastore indexes create index.yaml
```

* open the URL address of the you application, create account, post, follow. Does it Works?? If something is wrong where to find the error ?? 
  * See the prof


* How many servers are working for this app?? How much are you paying for running this app ? What is the cloud model for this app (Iaas, Paas, Saas). What is the Platform in PaaS ??

* See the impact in the datastore: do you see your data ?
  * See the prof

* How much are you paying for hosting these data in this store ?? 
* What is the consistency of this store ?
* What is the sharding strategy of this store ? How to be sure of that ? 
* What queries can you write with store (expressivity)

## HTTP Endpoints

- `/` — HTML UI for simple interactions
- `POST /login` — login with a username (no password)
- `POST /post` — create a new post (form)
- `POST /follow` — follow another user (form)
- `GET /api/timeline?user=<username>&limit=<n>` — JSON timeline for a user (default limit 20)
- `POST /admin/seed` — server-side seed (requires `SEED_TOKEN` via header `X-Seed-Token` or `token` param)

Example server-side seed call:

```sh
curl -X POST \
  -H "X-Seed-Token: change-me-seed-token" \
  "https://<YOUR_APP>.appspot.com/admin/seed?users=8&posts=100&follows_min=1&follows_max=4&prefix=load"
```

## Access the backend from the CLI

The JSON endpoint `GET /api/timeline?user=<username>&limit=20` is suitable for basic load experiments.

- Run locally against the dev server:

```sh
ab -n 200 -c 20 "http://127.0.0.1:8080/api/timeline?user=demo1&limit=20"
```

- Run against the deployed app (no cookie):

```sh
ab -n 500 -c 50 "https://<YOUR_APP>.appspot.com/api/timeline?user=demo1&limit=20"
```

- Optional: include a session cookie if you want to test authenticated flows (get `session` cookie from your browser devtools):

```sh
AB_COOKIE="session=<VALUE>"
ab -n 500 -c 50 -H "Cookie: $AB_COOKIE" "https://<YOUR_APP>.appspot.com/api/timeline?limit=20"
```

Interpreting common metrics:
- `Requests per second` — throughput
- `Time per request` — latency
- `Failed requests` — should remain near 0 for a healthy run

## GQL & Datastore notes

The timeline query used by the app is roughly:

```sql
SELECT * FROM Post WHERE author IN @authors ORDER BY created DESC
```

Notes:
- `IN` queries are conceptually implemented as a union of per-author scans followed by a k-way merge ordered by `created DESC`.
- The repository includes `index.yaml` with a composite index (author + created desc), which is required for efficient execution of the timeline query.
- Writes use the Datastore entity API; GQL is used for convenient reads only.

Limitations and trade-offs:
- `IN` with many values increases work and latency because it becomes multiple queries merged server-side.
- Global queries are eventually consistent; only key lookups and ancestor queries are strongly consistent. See `NOTES.md` for more detail.

## Troubleshooting: Cloud Build / staging bucket error

If you encounter an error like:

```
Failed to create cloud build: ... invalid bucket "staging.<PROJECT>.appspot.com"; service account ... does not have access
```

Check the following:

1. Required services are enabled:

```sh
gcloud services enable appengine.googleapis.com cloudbuild.googleapis.com iam.googleapis.com storage.googleapis.com
```

2. Ensure the App Engine service account has sufficient permissions on the staging bucket. For example, grant storage admin at project level (adjust to least privilege required):

```sh
PROJECT_ID="<YOUR_PROJECT>"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
  --role="roles/storage.admin"
```

3. If the staging bucket is missing, create it and grant the service account object admin on the bucket:

```sh
gsutil mb -p "$PROJECT_ID" -l europe-west1 "gs://staging.${PROJECT_ID}.appspot.com"
gsutil iam ch serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com:objectAdmin "gs://staging.${PROJECT_ID}.appspot.com"
```

Index deployment (if GCP prompts for missing indexes):

```sh
gcloud datastore indexes create index.yaml || gcloud app deploy index.yaml
```

## Notes on consistency, partitioning and CAP
See `NOTES.md` for a concise explanation of Datastore's partitioning (range partitioning with dynamic splits), replication, and its consistency model (generally AP for global queries; strong consistency for key lookups and ancestor queries).

## Expérimentations et Scalabilité

**Réalisé par :** Dudonné Baptiste
**URL de l'application :** [https://tp1-cloud2.ue.r.appspot.com](https://tp1-cloud2.ue.r.appspot.com)

### 1. Passage à l'échelle sur la charge (Concurrency)

![Concurrency Plot](out/conc_plot.png)

**Résultats bruts (extraits de `out/conc.csv`) :**
| Utilisateurs (PARAM) | Run 1 | Run 2 | Run 3 | Instances allouées |
|---|---|---|---|---|
| 1 | 426ms | 177ms | 187ms | 1 |
| 10 | 172ms | 172ms | 197ms | 1 à 2 |
| 20 | 184ms | 177ms | 175ms | 2 |
| 50 | 272ms | 251ms | 216ms | 4 |
| 100 | 217ms | 199ms | 191ms | 3 à 4 |
| 1000 | 2497ms | 892ms | 231ms | 10 -> 20 |

**Explication des résultats :**
L'application **scale de manière très efficace** face à une montée en charge. Jusqu'à 100 utilisateurs simultanés, le temps de réponse reste remarquablement stable aux alentours de 200ms (grâce à l'augmentation de 1 à 4 instances). 
Lorsqu'on passe brusquement à 1000 utilisateurs, le temps de réponse grimpe initialement (2497ms au run 1). Cela s'explique par les **"cold starts"** : App Engine doit instancier un grand nombre de nouveaux serveurs à la volée. Cependant, le système réagit très bien : dès les runs 2 et 3, le nombre d'instances passe de 10 à 20, permettant au temps de réponse de redescendre drastiquement (jusqu'à 231ms au run 3), retrouvant sa vitesse normale.

**Ce qu'il faudrait faire :** 
- Configurer un nombre d'instances minimum (warm instances) pour éviter le délai du premier pic de charge.
- Implémenter un cache en mémoire (ex: Redis ou Memcached) pour servir les requêtes de timeline les plus fréquentes et réduire la pression sur le Datastore.

### 2. Passage à l'échelle sur la taille des données (Fanout)

![Fanout Plot](out/fanout.png)

**Résultats bruts (extraits de `out/fanout.csv`) :**
| Followers (PARAM) | Run 1 | Run 2 | Run 3 | Instances allouées |
|---|---|---|---|---|
| 20 | 223ms | 212ms | 202ms | 11 |
| 40 | 6109ms | 2959ms | 1157ms | 11 |
| 60 | 8399ms | 4076ms | 1631ms | 12 |

**Explication des résultats :**
À l'inverse, **l'application ne scale pas du tout** sur la taille du réseau. Le chargement de la timeline s'appuie sur une requête `IN` sur Datastore. Avec 20 followers, on observe ~210ms. Dès 40 followers, le temps explose à plus de 6 secondes au premier lancement. À 60 followers, on dépasse les 8 secondes ! Le moteur Datastore peine à scanner les multiples index et à fusionner côté serveur une quantité de données aussi conséquente. (La baisse de temps observée sur les runs 2 et 3 est due aux mécanismes de cache internes de l'infrastructure GCP, mais l'architecture reste inadaptée pour la première lecture).

**Ce qu'il faudrait faire :** 
- Mettre en place une architecture de données en mode **"Push" (Fan-out on write)** au lieu de l'actuel "Pull". Lorsqu'un utilisateur publie un post, un processus en arrière-plan devrait l'insérer directement dans l'entité "Timeline" de chacun de ses abonnés.
- La lecture de la timeline redeviendrait ainsi une simple requête d'accès sur une seule entité (`SELECT * FROM Timeline WHERE owner = @me`), garantissant un temps de lecture constant en **O(1)**, qu'il y ait 10 ou 100 000 followers.