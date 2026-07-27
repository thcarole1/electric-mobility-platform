# 007 — Extraction d'un module commun pour les fonctions génériques d'E/S

## Contexte

En démarrant l'ingestion d'une deuxième source de données (météo, via
Open-Meteo), trois fonctions déjà écrites pour Open Charge Map se sont
révélées nécessaires à l'identique : generer_nom_fichier,
sauvegarder_local, uploader_s3. Elles ne contenaient aucune référence
spécifique à Open Charge Map — leur généricité était déjà prouvée par
leur propre code, pas une hypothèse.

## Décision

Extraction de ces trois fonctions vers src/common/io.py, importées
depuis ingestion/openchargemap.py plutôt que dupliquées. La fonction
generer_nom_fichier a été généralisée avec des paramètres suffixe et
extension à valeur par défaut, pour rester compatible avec les appels
existants tout en permettant un usage différent (ex : un suffixe
"meteo" plutôt que "extract").

## Pourquoi

La règle générale de ce projet est de ne pas factoriser avant un
troisième cas d'usage prouvé, pour éviter de deviner une abstraction
sur une hypothèse. Ici, la situation est différente : les fonctions
existaient déjà sous une forme déjà générique et déjà testée — le choix
n'était donc pas "deviner une abstraction", mais "arrêter de coupler
du code déjà générique à un module qui ne devrait pas le posséder".
Dupliquer ce code dans ingestion/meteo.py aurait été un coût sans
bénéfice, la duplication n'apportant ici aucune valeur contrairement à
une factorisation prématurée sur du code non éprouvé.

## Conséquences

Toute nouvelle source de données (météo, puis futures sources) importe
ses fonctions génériques d'E/S depuis src/common/io.py plutôt que de
les dupliquer ou de les importer depuis un autre module source. Les
tests associés vivent dans tests/test_common_io.py, distincts des tests
propres à chaque source.
