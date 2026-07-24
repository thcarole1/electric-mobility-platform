# 003 — Normalisation de la ville depuis le titre du POI

## Contexte

56% des POI (28/50) avaient un champ `AddressInfo.Town` vide, alors que
le nom de la ville était souvent présent dans `title`, sous la forme
"Ville | Adresse".

## Décision

Ajout d'une colonne `town_normalisee` : si `town` est vide et que `title`
contient le motif " | ", extraire la partie avant comme ville de secours.
Sinon, conserver `null`. La colonne `town` d'origine est conservée
intacte, `town_normalisee` s'ajoute en complément.

## Pourquoi

- Le motif " | " n'est pas garanti universel sur toute la donnée Open
  Charge Map — appliquer la règle uniquement quand elle est vérifiée
  évite d'inventer une ville sur les cas qui ne suivent pas ce format
  (ex : le POI "pompidou", resté à null volontairement)
- Garder les deux colonnes préserve la traçabilité entre donnée source
  et donnée déduite, plutôt que d'écraser l'information d'origine

## Conséquences

Toute future analyse par ville doit utiliser `town_normalisee`, pas
`town`. Si l'échantillon s'élargit à d'autres villes, la règle reste
valide sans modification (elle ne dépend pas du nom "Paris").
