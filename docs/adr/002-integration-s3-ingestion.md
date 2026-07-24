# 002 — Intégration de S3 dans le pipeline d'ingestion

## Contexte

Le pipeline sauvegardait uniquement le JSON brut en local (data/raw/).
La roadmap prévoyait l'introduction d'AWS dès la Phase 1, pas repoussée
à une phase ultérieure.

## Décision

Après la sauvegarde locale, le JSON brut est aussi uploadé sur S3 (préfixe
raw/ dans le bucket), via boto3. Un utilisateur IAM dédié, restreint aux
actions s3:PutObject et s3:GetObject sur ce bucket précis, est utilisé
plutôt que les identifiants root ou un accès plus large.

## Pourquoi

- Cohérence avec l'architecture cible définie dès le Project Brief
- Le principe du moindre privilège limite les dégâts en cas de fuite des
  identifiants : seul ce bucket est exposé, avec seulement lecture/écriture
- IAM Roles Anywhere (identifiants temporaires) a été considéré mais écarté
  pour l'instant : complexité de mise en place disproportionnée pour un
  MVP de portfolio

## Conséquences

Le JSON brut existe désormais en double (local + S3). Le stockage local
reste la référence pour l'instant ; S3 pourra devenir la source de vérité
si le projet évolue vers une vraie automatisation (Lambda, EventBridge).
Une rotation des clés d'accès ou une migration vers IAM Roles Anywhere
reste une amélioration future à envisager si le projet se rapproche d'un
contexte de production.
