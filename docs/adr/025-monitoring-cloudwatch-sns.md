# 025 — Observabilité du pipeline : CloudWatch Alarms et notifications SNS

## Contexte

Jusqu'ici, aucun mécanisme ne permettait de savoir si l'ingestion
quotidienne (fonctions Lambda déclenchées par EventBridge) avait
échoué, en dehors d'une vérification manuelle des logs CloudWatch ou
du contenu du data lake. Cette absence de surveillance active
constituait une limite significative par rapport aux pratiques
attendues d'un pipeline en production.

## Décision

Mise en place d'un module Terraform dédié `monitoring`, distinct du
module `ingestion` qu'il surveille : deux alarmes CloudWatch (une par
fonction Lambda) déclenchées dès qu'une exécution échoue
(`metric_name = "Errors"`, seuil strictement supérieur à zéro, fenêtre
d'évaluation d'une heure), reliées à un topic SNS unique avec un
abonnement email. Les noms des fonctions Lambda à surveiller sont
transmis au module `monitoring` via le mécanisme output/variable déjà
utilisé entre les modules `iam` et `ingestion`, plutôt que redéclarés
en dur.

## Pourquoi

La séparation en module distinct répond au principe déjà appliqué sur
l'ensemble de l'infrastructure : un module regroupe des ressources qui
naissent et évoluent ensemble. Le monitoring n'a aucune dépendance
fonctionnelle vis-à-vis de l'ingestion — sa suppression n'affecterait
en rien l'exécution des Lambda elles-mêmes, seulement la visibilité
sur leur bon fonctionnement. Ce découpage garantit qu'une erreur dans
la configuration du monitoring ne peut jamais compromettre le
fonctionnement du pipeline qu'il surveille.

Le seuil de déclenchement (toute erreur, sans tolérance) a été choisi
en cohérence avec la fréquence d'exécution de ces fonctions (une fois
par jour) : contrairement à un service à haute fréquence où quelques
erreurs isolées seraient tolérables, chaque exécution quotidienne
manquée représente une perte de données non rattrapable
automatiquement, justifiant une alerte immédiate dès la première
occurrence.

## Conséquences

Le mécanisme complet a été validé de bout en bout par un déclenchement
manuel de l'alarme (`aws cloudwatch set-alarm-state`), confirmant la
réception effective de la notification par email avant remise en état
normal — une vérification jugée nécessaire plutôt que de supposer le
bon fonctionnement de la chaîne Alarm → SNS → email sans preuve
concrète.

Ce périmètre reste volontairement limité à la détection d'échecs
d'exécution (`Errors`) : les métriques de durée (`Duration`) et de
limitation de concurrence (`Throttles`), également disponibles
nativement pour Lambda, n'ont pas été instrumentées, ce type
d'anomalie étant jugé moins critique que l'échec complet d'une
exécution pour ce pipeline. Aucune surveillance n'a par ailleurs été
mise en place sur l'environnement MWAA ni sur le Glue Crawler, ces
composants n'étant pas exécutés en continu dans le cadre actuel du
projet.

## Incident : verrou de state orphelin lié à une variable sans valeur transmise en CI

L'intégration de ce module a révélé un incident lié au workflow
`terraform-plan.yml` existant (ADR-024) : la variable `alert_email`,
sans valeur par défaut et fournie uniquement via `terraform.tfvars`
(fichier local, jamais versionné), n'était pas transmise au workflow
CI. Terraform, ne recevant aucune valeur pour cette variable
obligatoire, a tenté une saisie interactive impossible dans un
environnement d'exécution automatisé, bloquant l'exécution sans
message d'erreur explicite pendant plus de dix minutes.

Ce blocage a eu une conséquence secondaire : le verrou natif S3 du
State (`terraform.tfstate.tflock`), acquis en début d'exécution, n'a
jamais été relâché par le processus resté bloqué, empêchant toute
nouvelle exécution — locale ou via CI — jusqu'à sa suppression
manuelle après vérification qu'aucune opération légitime n'était en
cours. Corrigé en transmettant la variable au workflow via un nouveau
secret GitHub (`ALERT_EMAIL`), suivant le même mécanisme déjà en place
pour `ocm_api_key`. Cet incident souligne la nécessité de vérifier
systématiquement, lors de l'ajout d'une nouvelle variable Terraform,
que sa valeur est bien accessible depuis chaque environnement
d'exécution (local et CI), pas uniquement celui utilisé au moment de
son introduction.
