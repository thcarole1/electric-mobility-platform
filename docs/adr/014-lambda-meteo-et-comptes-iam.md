# 014 — Déploiement de l'ingestion météo sur Lambda et clarification des comptes IAM

## Contexte

Suite au déploiement réussi de l'ingestion Open Charge Map sur Lambda
(ADR-012) et à l'automatisation de son déclenchement (ADR-013), la
roadmap prévoyait de répliquer ce schéma pour la source météo. Au cours
de cette session, une confusion a également été identifiée entre
plusieurs identités AWS utilisées pour administrer le projet.

## Décision — déploiement Lambda météo

Réutilisation intégrale de l'infrastructure déjà en place pour Open
Charge Map : même Lambda Layer (`electric-mobility-ingestion-deps`,
requests uniquement — ingestion/meteo.py n'a besoin d'aucune dépendance
supplémentaire), même rôle IAM d'exécution
(`electric-mobility-lambda-role`), même bucket S3. Un nouveau handler
(`lambda_functions/meteo_handler.py`) invoque `ingerer_meteo` sur un
seul POI fixe (poi_id 7008, cohérent avec le principe de démarrer
simple avant d'élargir), avec la plage de dates calculée
dynamiquement (`date.today()`) plutôt que codée en dur, pour rester
pertinente à chaque exécution automatique future. Aucune variable
d'environnement n'est nécessaire, Open-Meteo ne demandant aucune clé
d'authentification.

## Décision — clarification des identités AWS

Trois identités distinctes sont désormais clairement établies pour ce
projet :
- **`electric-mobility-pipeline`** (utilisateur IAM, accès S3 minimal
  uniquement) : utilisé exclusivement par le code applicatif
  (boto3 local), jamais pour naviguer dans la console.
- **Le compte root** : réservé aux rares actions qui l'exigent
  strictement (facturation, fermeture de compte), jamais utilisé pour
  l'administration courante.
- **`emp-admin`** (nouvel utilisateur IAM, politique AdministratorAccess) :
  compte dédié à l'administration humaine courante du projet (création
  de ressources Lambda/IAM/EventBridge), remplaçant l'usage accidentel
  du compte root qui avait cours jusqu'ici sans que cela soit identifié.

## Pourquoi

Le déploiement Lambda météo a confirmé la valeur de la réutilisation
d'infrastructure déjà éprouvée (Layer, rôle) : contrairement au premier
déploiement (ADR-012), aucun bug n'a été rencontré, la fonction ayant
réussi dès le premier test. La distinction entre compte root et compte
administrateur dédié suit la recommandation standard d'AWS (ne pas
utiliser root pour les tâches quotidiennes) ; l'utilisation involontaire
du root jusqu'à cette session, bien que sans conséquence négative
concrète, constituait un écart non identifié à cette recommandation.
Un compte administrateur nommé explicitement pour le projet plutôt
qu'un root anonyme permet aussi une identification immédiate du
contexte de travail dans l'interface console.

## Conséquences

Deux fonctions Lambda tournent désormais en production sur ce projet,
partageant la même Layer et le même rôle d'exécution. Le réflexe de
vérifier systématiquement la région AWS et l'identité connectée avant
toute action en console est désormais explicite. L'automatisation du
déclenchement de la Lambda météo (EventBridge Scheduler, sur le même
modèle que ADR-013) reste à mettre en place, non traitée dans cette
session.
