# Référentiel d'analyse de pitch deck (VC early-stage)

Version 1.0, 8 octobre 2026. Destiné au Deck Analyzer et à son relecteur humain.

Ce document rassemble les frameworks, formules, seuils et benchmarks utilisés par les investisseurs pour lire un deck, du pre-seed à la série B. Chaque repère chiffré indique sa source, sa date et son périmètre. La liste complète des sources est en section 13.

---

## 0. Mode d'emploi

### 0.1 Principes de neutralité

1. Un benchmark situe une donnée. Il ne rend pas de verdict. L'outil écrit « au-dessus de la médiane Bessemer 2010-2021 pour la tranche 1-10 M$ d'ARR », jamais « bonne croissance ».
2. Toujours afficher la source, l'année et l'échantillon d'un benchmark. Un chiffre 2021 (marché haussier) et un chiffre 2026 ne se comparent pas sans le dire.
3. Toujours caler le repère sur le stade. Un burn multiple de 3 au seed et en série B ne racontent pas la même chose (section 5.3).
4. Distinguer trois statuts pour chaque donnée du deck : fournie et vérifiable, fournie mais non vérifiable, absente. Une donnée absente est une question à poser, pas un défaut.
5. Les frameworks se recoupent. Aucun ne fait autorité seul. La section 2.7 donne la correspondance entre eux.

### 0.2 Hiérarchie des sources

| Niveau | Définition | Usage |
|---|---|---|
| A | Source primaire : publication du fonds, de l'auteur ou de l'organisme qui produit la donnée | Utilisable tel quel, avec date |
| B | Source secondaire sérieuse qui cite une source primaire non consultée directement ici | Utilisable avec mention « via » |
| C | Notes du projet (calls, cours) non recoupées | À signaler comme non vérifié |

Chaque repère porte son niveau entre crochets, par exemple [A].

### 0.3 Abréviations

ARR : revenu récurrent annualisé. MRR : revenu récurrent mensuel. CARR : ARR contracté (signé, pas encore live). NRR / NDR : rétention nette en revenu. GRR : rétention brute en revenu. CAC : coût d'acquisition client. LTV / CLTV : valeur vie client. GM : marge brute. FCF : free cash flow. GMV : volume brut de transactions. ACV : valeur annuelle d'un contrat. DAU / MAU : utilisateurs actifs quotidiens / mensuels. ARPU / ARPPU : revenu par utilisateur / par utilisateur payant.

---

## 1. Lire le deck : structure attendue et comportement de lecture

### 1.1 Structure de référence (Sequoia, « Writing a Business Plan ») [A via reproduction]

Sequoia recommande 15 à 20 slides dans cet ordre :

| Slide | Contenu attendu |
|---|---|
| Company purpose | L'entreprise définie en une phrase déclarative |
| Problem | La douleur du client et la façon dont il la traite aujourd'hui |
| Solution | La proposition de valeur, où le produit s'insère, des cas d'usage |
| Why now | L'évolution historique de la catégorie et les tendances récentes qui rendent la solution possible |
| Market size | Le client cible, TAM (top-down), SAM (bottom-up), SOM |
| Competition | Concurrents et avantages compétitifs |
| Product | Gamme, fonctionnalités, architecture, propriété intellectuelle, roadmap |
| Business model | Modèle de revenus, pricing, taille moyenne de compte et/ou LTV, modèle de vente, pipeline |
| Team | Fondateurs, management, board et advisors |
| Financials | P&L, bilan, cash flow, cap table, le deal |

Usage pour l'outil : cartographier chaque slide du deck sur cette grille et lister les rubriques absentes.

### 1.2 Comment les investisseurs lisent un deck (DocSend) [A/B]

| Donnée | Valeur | Source, date |
|---|---|---|
| Temps moyen passé par un investisseur sur un deck | 2 min 24 s, plus bas historique | DocSend, T4 2023 |
| Idem | 2 min 36 s | DocSend, T3 2021 |
| Decks ayant levé vs decks n'ayant pas levé | plus de 4 min vs 1 min 30 | DocSend, données 2020 |
| Sections dont le temps de lecture a le plus augmenté entre 2019 et 2020 | concurrence, maturité produit, business model | DocSend, rapport 2020 |

Lecture neutre : ces chiffres décrivent un comportement moyen sur la plateforme DocSend. Ils justifient de vérifier que le message clé apparaît dès les premières slides, sans en faire un critère de qualité.

---

## 2. Frameworks d'analyse

### 2.1 Point Nine Capital : deal memo en 9 rubriques [A]

Source : Savina van der Straten, Point Nine, décembre 2016. Point Nine précise que l'ordre ne reflète pas l'importance : l'équipe, en position 7, compte parmi ses critères principaux.

| # | Rubrique | Ce que Point Nine cherche |
|---|---|---|
| 1 | Product | Description simple du problème et de la cible ; fonctionnalités cœur (pas exhaustives) ; roadmap à 6-18 mois ; démo, vidéo ou captures |
| 2 | Market | Cible précise (le fonds juge « toutes les PME d'Europe » trop vague) ; TAM bottom-up et top-down, que le fonds recalcule lui-même et dont il demande les sources ; tendances du marché |
| 3 | Competition | Liste des incumbents ; forces et faiblesses comparées (positioning chart, matrice) ; avantage défendable à long terme (tech complexe, effets de réseau). Le fonds lit « nous n'avons pas de concurrents » comme un mauvais signal |
| 4 | Traction | KPI mensuels depuis le lancement (marketplace : GMV, revenu net, panier moyen, marges ; SaaS : MRR, nombre de clients) ; analyse de cohortes ; pipeline par étape, pondéré par probabilité |
| 5 | Acquisition | Canaux actuels et leur coût ; plan sales et marketing. Le fonds note que la traction initiale (fruits faciles, bruit du lancement) ne prédit pas la traction à l'échelle |
| 6 | Business model | Pricing actuel comparé à des produits similaires |
| 7 | Team | Forces et faiblesses des fondateurs (interactions, parcours, références) ; qualité des premiers recrutements ; résultat de la DD tech |
| 8 | Funding / Deal | Taille et calendrier du tour ; runway ; jalons financés par le tour ; historique de financement |
| 9 | Reference calls | Appels courts avec des clients actuels ; avis d'experts du secteur |

### 2.2 Les 4M de Boris Golden (Partech) [B]

Source : notes de la conférence de Boris Golden au Lisbon Investment Summit, publiées par John Mathews ; présentations « Understanding VCs » et « What I look for in a startup pitch » sur le SlideShare de Boris Golden. Boris Golden est General Partner chez Partech et co-dirige le fonds seed.

| M | Critères |
|---|---|
| Market | Marché large et attractif ; besoin réel de personnes identifiées ; positionnement concurrentiel clair ; tendances favorables (why now) |
| Model | Produit différencié et à forte valeur ; go-to-market et canaux de croissance efficaces ; monétisation rentable ; scalabilité et défensibilité |
| Management | Équipe soudée, compétente ; capacité à exécuter et apprendre vite ; prête à viser grand ; vision unique et fit avec le projet |
| Momentum | Traction prouvant qu'un problème important est résolu ; plan de croissance ambitieux mais crédible ; modèle capital-efficient ; stratégie claire pour scaler et gagner |

Repères associés, même source : participation typique d'un VC autour de 20 % ; le VC a besoin d'une sortie d'au moins 100 M pour que son modèle fonctionne [B]. Frenchweb rapporte la même logique : sortie d'environ 100 M€ en moins de huit ans après le premier investissement [B].

Les 5 critères généraux de la même présentation (d'après les notes Eurazeo du projet, [C]) : grand marché, disruption des règles ou des incumbents, forces uniques crédibilisant la capacité à gagner, modèle capital-efficient, fort potentiel de sortie.

### 2.3 Sequoia [A via reproduction]

Voir 1.1. Le « why now » y est une rubrique à part entière : l'outil doit vérifier que le deck explique ce qui a changé (technologie, réglementation, comportement) et pourquoi la solution n'existait pas avant.

### 2.4 Edison Venture Template [C]

Source : notes Eurazeo du projet, non recoupées.

1. Business model solide : pricing récurrent, levier, scalabilité, marges brutes élevées.
2. Technologie propriétaire : difficulté de duplication, coût du maintien de l'avance.
3. Marché attractif : assez grand pour soutenir 40 % de croissance annuelle pendant 5 ans ; besoin urgent plutôt que « nice to have ».

### 2.5 Template Memohub (Clément Vouillon) [C]

Source : notes Eurazeo du projet, non recoupées.

Need (cible, pain points, proposition de valeur) ; Market sizing (top-down et bottom-up) ; Product (usage, rétention, NPS, preuves de PMF, interviews clients) ; Marketing, sales et distribution (go-to-market et pourquoi, avantage de distribution) ; Business model (type, unit economics) ; Compétition (directe, indirecte, densité) ; Team (founder-market fit : expérience du marché et du go-to-market) ; Moats (transversal à toutes les rubriques).

### 2.6 AARRR (Dave McClure) pour les produits grand public [C]

Source : notes Eurazeo du projet ; framework présenté par Dave McClure (« Startup Metrics for Pirates », 2007), non recoupé ici.

| Étape | Question | Métriques typiques |
|---|---|---|
| Acquisition | Comment le client trouve le produit | CAC par canal, volume par canal |
| Activation | Première expérience réussie | Taux de complétion de l'onboarding, temps jusqu'à la fonctionnalité cœur |
| Retention | Le client revient | D1/D7/D30, courbes de cohortes, DAU/MAU |
| Referral | Le client recommande | K-factor |
| Revenue | Le client paie | ARPU, ARPPU, conversion payante |

### 2.7 Table de correspondance entre frameworks

| Dimension | Point Nine | 4M | Sequoia | Memohub | Edison |
|---|---|---|---|---|---|
| Problème, besoin | 1 Product | Market | Problem | Need | 3 |
| Pourquoi maintenant | 2 Market (dynamiques) | Market (tendances) | Why now | Market sizing | 3 |
| Taille de marché | 2 Market | Market | Market size | Market sizing | 3 |
| Produit, différenciation | 1 Product | Model | Solution, Product | Product | 2 |
| Traction, PMF | 4 Traction | Momentum | Business model (pipeline) | Product | n.d. |
| Go-to-market | 5 Acquisition | Model | Business model | Marketing, sales | n.d. |
| Monétisation, unit economics | 6 Business model | Model | Business model | Business model | 1 |
| Concurrence, moat | 3 Competition | Market, Model | Competition | Compétition, Moats | 2 |
| Équipe | 7 Team | Management | Team | Team | n.d. |
| Deal, financement | 8 Funding | Momentum (capital efficiency) | Financials | n.d. | n.d. |
| Validation externe | 9 Reference calls | n.d. | n.d. | Product (interviews) | n.d. |

L'outil peut structurer son analyse sur ces 11 dimensions et indiquer pour chacune ce que chaque framework demande.

---

## 3. Calibration par stade

### 3.1 Ce que les investisseurs attendent à chaque stade (Christoph Janz, Point Nine)

Le « SaaS Funding Napkin » résume taille de tour, valorisation et traction attendues par stade. Les colonnes se décalent avec le marché ; toujours dater.

**Édition 2023** [B, via résumé Daphni et SaaStr de la présentation de Janz]

| Stade | Taille de tour | Valorisation | Traction typique |
|---|---|---|---|
| Pre-seed | environ 1,5 M$ | 5-10 M$ | Pas de revenu attendu |
| Seed | 4-5 M$ | 10-20 M$ pre-money | La moitié sans revenu récurrent ; les autres de quelques centaines de k$ à 1-1,5 M$ d'ARR |
| Série A | 5-15 M$ | 20-60 M$ | La plupart entre 1 et 5 M$ d'ARR |
| Série B | n.d. | n.d. | La plupart autour de 6-12 M$ d'ARR |

**Édition 2021, ARR par stade** [B, via SaaStr] : pre-seed 0-0,6 M$ ; seed 0-0,6 M$ ; série A 0,5-4 M$ ; série B 3,5-12 M$ ; série C 5-40 M$.

**Ce qui est jugé à chaque stade** [B] : au pre-seed, pourquoi cette équipe est particulièrement qualifiée pour ce problème ; au seed, des signes que le PMF se construit, souvent prouvés par des utilisateurs satisfaits joignables ; aux séries B et C, l'analyse devient de plus en plus quantitative.

### 3.2 Tailles de tour, valorisations, dilution (Carta)

**Logiciel, tours lancés sur les 6 derniers mois, publié le 10 juillet 2026** [A]. Hors bridges et extensions. Le post ne précise pas la géographie ; la base Carta est majoritairement américaine.

| Stade | Valorisation médiane | Montant levé médian | Dilution médiane |
|---|---|---|---|
| Seed | 24,3 M$ | 4,1 M$ | 18 % |
| Série A | 80 M$ | 14,4 M$ | 18 % |
| Série B | 191 M$ | 25 M$ | 12 % |
| Série C | 391 M$ post | environ 40 M$ | moins de 10 % |
| Série D | 789 M$ | 63 M$ | 8 % |

**Startups tech américaines, T4 2024, hors bridges** [A]

| Instrument, stade | Cap ou post-money médian | Montant médian | Dilution |
|---|---|---|---|
| SAFE pre-seed (0,5-1,9 M$ levés) | cap 10 M$ | 1 M$ | 10,1 % (à la conversion) |
| SAFE seed | cap 18 M$ | 2,8 M$ | 18,3 % implicite |
| Seed priced | 19,2 M$ post | n.d. | 20 % |
| Série A priced | 58,9 M$ post | n.d. | 20 % |
| Série B priced | 129,8 M$ post | n.d. | 15 % |

**Dispersion** [A] : la valorisation seed au 95e percentile est passée de 72,2 M$ (T2 2025) à 200,4 M$ (T2 2026) chez Carta, alors que le nombre de tours baisse. La médiane masque un marché très concentré sur quelques dossiers.

**Dilution, autres repères** [A] : en 2024, au seed et en série A primaires, la dilution médiane tourne autour de 20 %, le 75e percentile autour de 25 % ; les tours à 30 % ou plus sont rares. Les bridges diluent nettement plus.

### 3.3 Europe

| Repère | Valeur | Source, niveau |
|---|---|---|
| Délai médian seed → série A | environ 24 mois, probablement 6 mois de plus une fois le décalage de reporting corrigé | Dealroom [A] |
| Part des startups européennes atteignant la série A en 36 mois | environ 1 sur 4 | Dealroom [A] |
| Pre-money seed médian en Europe | 5,6 M€ au T1 2025 | PitchBook, via guide secondaire [B, à confirmer dans le rapport PitchBook] |

Conséquence pour l'outil : un benchmark américain (Carta) appliqué à un deck français surestime en général les valorisations attendues. Signaler l'origine géographique de chaque repère.

### 3.4 Valorisation early-stage : méthodes

| Repère | Contenu | Niveau |
|---|---|---|
| Méthode | Au stade early, valorisation par comparables et multiple d'ARR ; pas de DCF quand l'EBITDA est négatif. Plus le stade est précoce, plus la valorisation se négocie faute de métriques | Retour d'entretien praticien (notes du projet) [C] |
| Multiple SaaS cité par un praticien | 5 à 10x l'ARR, selon de nombreux facteurs | Notes du projet [C] |
| Multiples Bessemer, portefeuille 2010-2021 | Moyenne supérieure à 30x l'ARR entre 1 et 10 M$ d'ARR, environ 15x au-delà de 10 M$ ; 50 % central entre 10 et 20x | Bessemer 2021 [A] |
| Lien croissance / multiple | Sur les tours 2020-2021 du portefeuille, multiple ≈ 20 × taux de croissance (régression) | Bessemer 2021 [A] |
| Mécanique | Carta rappelle que la valorisation résulte souvent des deux autres paramètres : montant levé et dilution | Carta 2026 [A] |

Ces chiffres ne se contredisent pas : ils couvrent des périodes et des échantillons différents (praticien 2026, portefeuille Bessemer sur une décennie haussière). L'outil doit afficher la période.

---

## 4. Métriques de revenu et de croissance

### 4.1 Définitions de revenu

| Métrique | Définition | Piège fréquent | Source |
|---|---|---|---|
| ARR | Revenu récurrent annualisé, hors revenus non récurrents. Le revenu comptable reconnu tend à suivre l'ARR avec retard | Confondre ARR et run rate (revenu du dernier mois × 12, récurrent ou non) | Bessemer 2021 [A] ; a16z « 16 More Startup Metrics » [A] |
| CARR | ARR + contrats signés pas encore live, net du churn prévu | Écart CARR/ARR important si implémentations longues | Bessemer 2021 [A] |
| MRR | Revenu récurrent mensuel ; ARR = MRR × 12 | n.d. | Standard |
| Bookings vs revenue | Un booking est un engagement contractuel ; le revenu est reconnu au fil de la prestation | Présenter des bookings comme du revenu | a16z « 16 Startup Metrics » [A] |
| TCV vs ACV | Valeur totale du contrat vs valeur annuelle | Présenter le TCV pluriannuel comme un chiffre annuel | a16z [A] |
| GMV vs revenu | GMV : valeur totale des transactions ; revenu : la part captée (take rate) | Présenter le GMV comme du chiffre d'affaires | a16z [A] |
| Revenu récurrent vs total | Séparer abonnement et services, setup, one-shot | Mélanger les deux sous l'étiquette ARR | a16z [A] |

### 4.2 Taux de croissance : formules

- Croissance mensuelle : MoM = (MRR_m / MRR_m-1) - 1
- Croissance mensuelle composée sur n mois : CMGR = (MRR_fin / MRR_début)^(1/n) - 1
- Croissance annuelle : YoY = (ARR_t / ARR_t-12 mois) - 1
- Lien mensuel / annuel : (1 + MoM)^12 - 1. Exemple calculé : 10 % par mois ≈ 214 % par an ; 15 % par mois ≈ 435 % par an.
- Growth endurance : croissance de l'année n / croissance de l'année n-1. Bessemer observe environ 70 % dans le privé, environ 80 % pour les sociétés cotées de son indice [A, 2021].

Point d'attention [C, retour praticien] : un x18 sur une base de 100 k n'a pas la valeur d'un x18 sur une base de 10 M. Toujours lire la croissance avec la base absolue.

### 4.3 Benchmarks de croissance SaaS par taille (Bessemer, portefeuille cloud 2010 à mi-2021) [A]

| ARR | Croissance moyenne | Croissance médiane | 50 % central | Top performers |
|---|---|---|---|---|
| 1-10 M$ | environ 200 % | 165 % | 100-230 % | 230 %+ |
| 10-25 M$ | 115 % | 87 % | n.d. | 135 %+ |
| 25-50 M$ | 95 % | 77 % | n.d. | 110 %+ |
| 50-100 M$ | 60 % | 60 % | 35-80 % (50 M$+) | 80 %+ |
| 100 M$+ | 60 % | 57 % | 35-80 % | 80 %+ |

Biais signalé par Bessemer : échantillon = son propre portefeuille, avec un biais de sélection dans les tranches hautes.

### 4.4 Trajectoires de référence

| Trajectoire | Contenu | Source |
|---|---|---|
| T2D3 | Tripler, tripler, doubler, doubler, doubler l'ARR après environ 1-2 M$ d'ARR. Introduit par Neeraj Agrawal (Battery Ventures) en 2015 | Battery, via biographie CB Insights [B] |
| Délai moyen 1 → 100 M$ d'ARR | 5,3 ans (top quartile), 7,3 ans (médiane), 10,6 ans (bas quartile) | Bessemer State of the Cloud 2017, via notes de David Cummings [B] |

---

## 5. Rétention, unit economics, efficacité

### 5.1 Rétention et churn

**Formules (standard)**

- Churn logo mensuel = clients perdus sur le mois / clients en début de mois
- GRR (sur 12 mois, une cohorte) = (ARR début - churn - contraction) / ARR début. Plafonnée à 100 %.
- NRR (sur 12 mois, une cohorte) = (ARR début - churn - contraction + expansion) / ARR début. Les nouveaux clients sont exclus.
- Durée de vie moyenne ≈ 1 / churn (même période)

**Benchmarks SaaS (Bessemer 2021, portefeuille 2010 à mi-2021)** [A]

| Métrique | Repère |
|---|---|
| GRR | Stable autour de 85-90 % quel que soit l'ARR. Des SaaS SMB réussis tournent à 70-80 % (HubSpot avant IPO) |
| NRR moyenne | 140 % entre 1 et 10 M$ d'ARR ; 120 % de 10 à 100 M$+ |
| NRR médiane | 125 % (1-10 M$), 117 % (10-25 M$), 120 % (25-100 M$), 115 % (100 M$+) |
| NRR, dispersion | 105-145 % entre 1 et 10 M$ ; 105-125 % à 100 M$+ ; seul le quartile bas passe sous 100 % |
| Effet segment | NRR plus faible en SMB qu'en enterprise. Exemples : Mindbody 109 % sur ~2 k$ d'ACV ; Okta 123 % sur 50 k$+ d'ACV |
| Effet secteur | Outils développeurs et collaboration en tête ; sales/marketing, customer experience, finance/legal tech plus bas |

**Analyse de cohortes** [A, Point Nine] : Point Nine la juge essentielle pour comprendre usage et rétention. L'outil vérifie si le deck présente des cohortes, sur quelle période, en logos ou en revenu.

**Rétention mobile grand public (Andrew Chen et Quettra, 2015)** [A] : sur des données de plus de 125 M de téléphones Android, l'app moyenne perd 77 % de ses DAU dans les 3 jours suivant l'installation, 90 % en 30 jours, plus de 95 % en 90 jours. Les utilisateurs décident dans les 3 à 7 premiers jours. Ces chiffres datent de 2015 et portent sur Android.

**Stickiness DAU/MAU** [C] : les notes du projet indiquent qu'un ratio supérieur à 25 % placerait une app dans le top 10 %. Source originale non retrouvée ; ne pas utiliser sans vérification.

### 5.2 Unit economics

| Métrique | Formule | Repère | Source |
|---|---|---|---|
| CAC | Dépenses S&M de la période / nouveaux clients de la période | Distinguer CAC blended (tous canaux, organique compris) et CAC paid. Le blended flatte le chiffre | a16z [A] |
| LTV (CLTV) | ARPA × marge brute % / churn (même période). Bessemer la définit après marge brute | n.d. | Bessemer 2021 [A] ; formule standard |
| LTV / CAC | LTV / CAC | 3x ou plus avant d'accélérer l'acquisition ; sous 1x, chaque client détruit de la valeur | Bessemer 10 Laws 2019 et 2021 [A] |
| CAC payback (mois) | Dépenses S&M du trimestre précédent / (MRR net nouveau du trimestre × marge brute %) | Moyenne portefeuille : 15 mois entre 1 et 10 M$ d'ARR, en hausse avec la taille | Bessemer 2017 (formule) [B] ; Bessemer 2021 (moyennes) [A] |
| CAC payback, cibles par segment | idem | SMB < 12 mois ; mid-market < 18 ; enterprise < 24 | Bessemer 2021 [A] |
| CAC payback, version 2019 | idem | SMB environ 6-18 mois ; enterprise jusqu'à 24-36 mois ; au-delà de 36 mois, difficile à financer sauf LTV exceptionnelle | Bessemer 10 Laws 2019 [A] |
| SaaS Quick Ratio | (MRR nouveau + MRR expansion) / (MRR churné + MRR contraction) | 4 ou plus jugé sain par son créateur ; sous 2 problématique | Mamoon Hamid, SaaStr 2015 [A] |

Lecture du Quick Ratio [A, Tunguz avec Hamid] : on peut le réécrire (croissance mensuelle + churn) / churn. Avec 15 % de croissance mensuelle, un ratio de 4 tolère 5 % de churn mensuel. Le ratio ne s'interprète donc qu'avec le niveau de churn.

### 5.3 Efficacité du capital

| Métrique | Formule | Repères | Source |
|---|---|---|---|
| Burn multiple | Burn net / ARR net nouveau, sur la même période | Barème du post (publié sous forme d'image, valeurs telles que largement reprises) : < 1 excellent ; 1-1,5 très bon ; 1,5-2 bon ; 2-3 suspect ; > 3 mauvais. Le texte confirme les ancres : 2x raisonnable en early ; 3x ou plus suggère un PMF moins solide qu'il n'y paraît ; 5x jugé terrible | David Sacks, Craft, avril 2020 [A] |
| Burn multiple par stade | idem | Exemple de Sacks : 3 au seed, 2 après la série A, plus exigeant après la série B, tendant vers 0 ensuite. Non calculable avant revenu | Sacks 2020 [A] |
| Burn multiple, repère 2023 | idem | 1 à 1,5 jugé bon pour les sociétés jusqu'à 25 M$ d'ARR | Christoph Janz, Napkin 2023 [B] |
| Hype ratio | Capital levé (ou brûlé) / ARR | Pénalise durablement le capital gaspillé, à la différence du burn multiple | Kellblog, cité par Sacks [B] |
| Efficiency score (Bessemer) | Croissance ARR YoY + marge FCF | Pertinent seulement au-delà de 25 M$ d'ARR. Cibles : 70 % entre 25 et 50 M$ ; 50 % à 100 M$+ | Bessemer 2021 [A] |
| Cash Conversion Score | ARR / (capital total levé - trésorerie) | Moyenne ~0,5x entre 1 et 10 M$ d'ARR, ~1x à 100 M$+ ; 1x+ = best-in-class | Bessemer 2021 [A] |
| Rule of 40 | Croissance (%) + marge (EBITDA ou FCF, %) ≥ 40 % | Popularisée par Brad Feld en 2015 pour le SaaS late-stage. Peu pertinente en early | Standard Metrics, juillet 2026, retraçant l'historique [A] |
| Rule of X | Croissance × multiplicateur + marge FCF | Multiplicateur ~2 en privé, 2-3 en public (2,3 en décembre 2023). Bessemer montre une corrélation aux multiples de valorisation supérieure à celle de la Rule of 40 | Bessemer 2024, via SaaS Barometer et OnlyCFO [B] |
| Magic number | (Variation du revenu récurrent trimestriel × 4) / dépenses S&M du trimestre précédent | > 0,75 efficace, on peut accélérer ; 0,5-0,75 acceptable ; < 0,5 GTM à revoir. Inventé chez Scale Venture Partners | ChartMogul, CFI [B] |

Point de vigilance formule : le burn multiple utilise le burn **net** et l'ARR **net** nouveau (churn déduit). Des valeurs brutes faussent fortement le ratio [C, règle du projet, conforme à la définition de Sacks [A]].

### 5.4 Marges et structure de coûts (SaaS)

| Repère | Valeur | Source |
|---|---|---|
| Marge brute moyenne cloud | 65-70 % quel que soit le stade ; 50 % central entre ~60 et 80 % | Bessemer 2021 [A] |
| Contre-exemple | Twilio a longtemps tourné à ~50 % (coûts télécoms en COGS) | Bessemer 2021 [A] |
| Top performers 1-10 M$ d'ARR | Marge brute 85 %+, marge FCF -65 % ou mieux | Bessemer 2021 [A] |
| Médianes marge FCF | -167 % (1-10 M$), -75 % (10-25 M$), -62 % (25-50 M$) | Bessemer 2021 [A] |
| Structure à 100 M$ d'ARR | R&D ~35 %, S&M ~50 %, G&A ~20 % du revenu | Bessemer 2021 [A] |
| R&D en early | ~95 % du revenu au départ, tombant à 35 % | Bessemer 2021 [A] |
| G&A | ~70 % du revenu entre 1 et 10 M$, ~20 % à 50 M$+ | Bessemer 2021 [A] |
| Composition des COGS SaaS | Hébergement, implémentation, services, customer success | Bessemer 2021 [A] |

### 5.5 Cash et runway (formules standard)

- Burn brut = dépenses opérationnelles décaissées du mois
- Burn net = burn brut - encaissements du mois
- Runway (mois) = trésorerie disponible / burn net mensuel
- Jalons du tour : Point Nine demande les jalons que le tour doit financer [A]. L'outil vérifie la cohérence entre montant levé, burn prévu, runway et jalons annoncés. Exemple calculé : 4 M€ levés, burn net de 200 k€ par mois, runway ≈ 20 mois ; à rapprocher du délai médian seed → série A en Europe (~24 mois, Dealroom [A]).

---

## 6. Métriques par modèle d'affaires

### 6.1 SaaS B2B

Référence principale : sections 4 et 5. Liste minimale attendue d'après Point Nine [A] : MRR mensuel depuis le lancement, nombre de clients, cohortes, pipeline pondéré.

### 6.2 Marketplace (a16z, « 13 Metrics for Marketplace Companies », 2020) [A]

| Métrique | Définition, usage |
|---|---|
| GMV | Valeur totale des transactions ; mesure de taille, pas de revenu ; peut s'annualiser sur le dernier mois ou trimestre |
| Take rate | Part du GMV captée en revenu ; reflète la valeur apportée par la marketplace. Les marketplaces « managées » ont des take rates plus élevés car elles rendent plus de service |
| Liquidité | Probabilité qu'un vendeur trouve un acheteur et inversement ; a16z la juge l'aspect le plus critique, la plupart des échecs venant d'une liquidité jamais atteinte |
| Match rate (fill rate, utilization) | Part des recherches ou demandes qui aboutissent |
| Time to match | Délai entre demande et appariement (premier devis, première candidature, vente) |
| Concentration | Part de l'offre ou de la demande portée par quelques gros acteurs ; risque de départ |
| Multi-tenanting | Usage simultané de plusieurs plateformes concurrentes par l'offre ou la demande |

Unit economics marketplace (standard) : deux CAC (offre et demande) ; le revenu par transaction = panier moyen × take rate ; la contribution par transaction déduit paiement, support, incitations.

### 6.3 Consumer et mobile

| Métrique | Définition |
|---|---|
| DAU, MAU | Utilisateurs actifs quotidiens, mensuels ; définir « actif » |
| DAU/MAU | Stickiness (voir 5.1, repère non vérifié) |
| Rétention D1/D7/D30 | Part des installés actifs à J+1, J+7, J+30 (repères Chen 5.1) |
| ARPU | Revenu total / utilisateurs |
| ARPPU | Revenu / utilisateurs payants |
| K-factor | Nouveaux utilisateurs générés par utilisateur existant ; > 1 = croissance virale |
| UA, CPI | Acquisition payante ; coût par installation |
| IAP | Achats in-app |

Vanity metrics [A, a16z] : les téléchargements et les utilisateurs enregistrés figurent dans les listes a16z comme métriques à interpréter avec prudence ; les actifs et les cohortes priment.

---

## 7. Marché

### 7.1 TAM, SAM, SOM

| Notion | Définition | Méthode attendue |
|---|---|---|
| TAM | Marché total adressable | Top-down (rapports de marché) et bottom-up (nombre de clients cibles × prix annuel) |
| SAM | Part atteignable avec le produit et la géographie actuels | Bottom-up |
| SOM | Part capturable à horizon réaliste | Hypothèse de part de marché |

Sequoia demande TAM top-down, SAM bottom-up et SOM [A]. Point Nine demande les deux approches, recalcule lui-même et exige les sources [A].

Contrôle de cohérence (calcul) : TAM bottom-up = nombre de clients cibles × ACV. Si le deck annonce un TAM sans ce détail, l'outil le marque « non vérifiable ».

### 7.2 La taille de marché vue par le fonds (calcul)

Un VC raisonne en sortie potentielle par rapport à la taille de son fonds :

- Participation à la sortie = participation d'entrée × Π (1 - dilution de chaque tour suivant)
- Sortie nécessaire pour rembourser le fonds = taille du fonds / participation à la sortie

Exemple calculé avec les dilutions médianes Carta 2026 (série A 18 %, série B 12 %) : un fonds de 100 M€ entre au seed à 15 %, puis suit deux tours sans réinvestir. Participation à la sortie = 15 % × 0,82 × 0,88 = 10,8 %. Sortie nécessaire pour rembourser le fonds = 100 / 0,108 ≈ 924 M€.

Ce calcul explique pourquoi un marché trop petit pour une sortie de cette taille pose problème à un fonds, indépendamment de la qualité de l'entreprise. Golden fixe le plancher autour de 100 M de sortie [B] ; le seuil réel dépend de la taille du fonds et de la participation.

### 7.3 Distribution des rendements (power law) [A via Seth Levine]

Étude Correlation Ventures sur plus de 21 000 financements entre 2004 et 2013 : 65 % ne rendent pas le capital investi ; 10 % rendent 5x ou plus ; 4 % rendent 10x ou plus. Une mise à jour de 2019 aboutit à des proportions proches. Les données portent sur des financements, pas des sociétés.

---

## 8. Deal, cap table et term sheet

### 8.1 Formules

- Post-money = pre-money + montant investi
- Participation de l'investisseur = montant investi / post-money
- Prix par action = pre-money / nombre d'actions pre-money entièrement diluées
- Dilution d'un actionnaire existant = 1 - (actions avant / actions après)
- Option pool créé avant le tour (dans le pre-money) : il dilue uniquement les actionnaires existants, pas le nouvel investisseur (mécanique standard décrite dans Venture Deals de Feld et Mendelson)

Rappel du projet [C, règle interne] : dilution et distribution sont deux calculs séparés. La dilution concerne le pourcentage de détention ; la distribution concerne la répartition du cash à la sortie (waterfall).

### 8.2 SAFE post-money (Y Combinator) [A]

| Élément | Contenu |
|---|---|
| Versions US | Cap sans discount ; discount sans cap ; MFN sans cap ni discount ; pro rata dans une side letter séparée |
| Cap post-money | Calculé après tout l'argent levé en SAFE et après le pool d'options existant, avant le tour priced |
| Participation | Montant / cap post-money, figée à la signature. Exemple YC : 750 k$ sur un cap de 5 M$ = 15 % |
| Conversion | Au prix le plus favorable à l'investisseur entre prix au cap et prix décoté |
| Pro rata | Retiré du SAFE par défaut dans la version post-money, proposé en side letter |
| Historique | SAFE pre-money créé en 2013 ; version post-money en 2018 |

Conséquence de lecture : chaque SAFE post-money supplémentaire dilue entièrement les fondateurs. L'outil additionne les SAFE en circulation pour estimer la dilution cumulée avant le tour priced.

**Modèle du projet « Model 1_convertible debt and SAFEs_final.xlsx »** [C, relu le 8 octobre 2026]. Mécanique utilisée : prix de conversion = cap / actions pre-money (convention pre-money, différente du SAFE post-money YC) ; actions reçues = montant (+ intérêts pour une note) / prix de conversion. Exemple Great Oak : notes de 250 k$ à cap 1 M$ et 1,5 M$, série A de 500 k$ à 3 M$ pre-money sur 1 M d'actions, soit 3 $ par action ; les notes convertissent à 1 $ et 1,5 $ ; table post-A d'environ 1,58 M d'actions. Points à corriger dans le fichier :
- Il présente la convertible debt comme « aussi appelée venture debt ». Ce sont deux instruments distincts : la venture debt se rembourse en cash, la note convertible se convertit en actions.
- La « dilution de ~11 % » des fondateurs est un écart en points (30 % → environ 19 %). En relatif, chaque fondateur perd environ 37 % de sa détention (calcul : 300 000 / 1 583 333 = 18,9 %).
- L'exercice BusyHealth indique une décote de 50 % dans l'énoncé et de 30 % dans le corrigé.
- L'onglet « Further reading » situe les décotes usuelles entre 20 et 40 % (source non précisée).

### 8.3 Liquidation preference

| Repère | Valeur | Source |
|---|---|---|
| Standard | 1x non-participating | Carta [A] |
| Rareté du > 1x | 1,9 % des tours primaires seed et série A en 2024 | Carta 2024 [A] |
| Tous stades | 95 % des tours Carta de 2023 à 1x ou moins ; les > 1x surtout en late stage et en bridge | Carta 2023 [A] |
| Cooley | 98 % des tours à 1x, 95 % non participating, T2 2025 (238 financements) | Cooley via source secondaire [B] |

Formules (standard) :
- Non-participating : l'investisseur reçoit max(montant × multiple, participation × prix de sortie)
- Participating : l'investisseur reçoit montant × multiple, puis participation × (prix de sortie - préférences versées)
- Seuil de conversion (non-participating 1x) = montant investi / participation

Exemple calculé : 5 M€ investis pour 25 %. Sortie à 15 M€ : max(5 ; 3,75) = 5 M€, l'investisseur exerce sa préférence. Sortie à 50 M€ : max(5 ; 12,5) = 12,5 M€, il convertit. Seuil de conversion : 5 / 0,25 = 20 M€. En participating 1x sur la sortie à 50 M€ : 5 + 25 % × 45 = 16,25 M€.

### 8.4 Glossaire de term sheet (définitions standard, Venture Deals)

| Clause | Objet |
|---|---|
| Liquidation preference | Ordre et montant de remboursement à la sortie (8.3) |
| Anti-dilution (full ratchet, broad-based weighted average) | Ajustement du prix de conversion en cas de down round ; le weighted average est le plus courant et le moins punitif |
| Pro rata | Droit de suivre aux tours suivants pour maintenir sa participation |
| Board composition | Répartition des sièges fondateurs, investisseurs, indépendants |
| Protective provisions | Décisions soumises à l'accord des préférentiels |
| Drag-along / tag-along | Obligation de suivre une cession / droit de suivre une cession |
| Vesting et cliff | Acquisition progressive des actions des fondateurs (souvent 4 ans avec 1 an de cliff) |
| Option pool | Réserve d'actions pour les salariés (8.1) |
| Pay-to-play | Perte de droits pour l'investisseur qui ne suit pas un tour |

Niveau [C] pour les valeurs usuelles (4 ans, 1 an) : convention de marché, à confirmer dans le document de référence utilisé par le fonds.

---

## 9. Économie d'un fonds VC

Source : notes Eurazeo du projet [C], sauf mention contraire.

| Élément | Repère |
|---|---|
| Parties | Limited Partnership (véhicule) ; GP (équipe de gestion, 1-3 % du fonds) ; LP (investisseurs, 97-99 %) ; portefeuille |
| Durée de vie | Environ 10 ans ; période d'investissement souvent 5 ans |
| Management fees | Environ 2 % par an du capital engagé, souvent dégressifs après la période d'investissement |
| Carried interest | Environ 20 % de la plus-value. Exemple : 100 M levés, 200 M rendus, 100 M de profit, 20 M de carry |
| Hurdle rate | Souvent 7-8 % ; une clause de catch-up permet au GP de rattraper sa part une fois le hurdle franchi (dépend du LPA) |
| IRR | Rendement pondéré dans le temps |
| Multiple brut / net | Capital récupéré / capital investi, avant ou après frais et carry |
| DPI | Distributions / capital appelé |
| TVPI | (Valeur résiduelle + distributions) / capital appelé |
| Courbe en J | Rendements négatifs les premières années (frais), puis positifs à maturité |

Funnel de dealflow (exemple NYU cité dans les notes) [C] : environ 1 000 dossiers, 150 rencontres, 25 due diligences, 5 à 10 deals.

---

## 10. Points d'attention dans un deck (sourcés)

Chaque point est un signal à investiguer, pas une conclusion.

| # | Signal | Pourquoi | Source |
|---|---|---|---|
| 1 | « Pas de concurrents » | Suggère une connaissance insuffisante du marché | Point Nine [A] |
| 2 | Cible décrite en termes génériques | Suggère un marché mal étudié | Point Nine [A] |
| 3 | TAM sans source ni calcul bottom-up | Non vérifiable | Point Nine, Sequoia [A] |
| 4 | ARR calculé comme un run rate incluant du non récurrent | Surévalue le récurrent | a16z [A] |
| 5 | GMV ou bookings présentés comme revenu | Surévalue le revenu | a16z [A] |
| 6 | Graphiques cumulatifs | Un cumul monte toujours et masque un ralentissement | a16z [A] |
| 7 | Axe des ordonnées tronqué | Exagère visuellement la croissance | a16z [A] |
| 8 | Téléchargements ou inscrits comme métrique principale | Ne mesurent ni usage ni rétention | a16z [A] ; Chen [A] |
| 9 | CAC blended seul | Masque le coût réel des canaux payants | a16z [A] |
| 10 | Pas de cohortes | Rétention invérifiable | Point Nine [A] |
| 11 | Burn multiple > 3 avec revenu établi | Croissance très coûteuse, PMF possiblement fragile | Sacks [A] |
| 12 | Burn multiple qui se dégrade avec la maturité | Indique un problème même si la croissance nominale monte | Sacks [A] |
| 13 | LTV / CAC < 1 ou CAC payback au-delà de 36 mois | Acquisition difficile à financer | Bessemer [A] |
| 14 | Quick Ratio < 2 | Le churn absorbe la croissance | Hamid [A] |
| 15 | Concentration client ou fournisseur forte | Risque de départ d'un acteur majeur | a16z [A] |
| 16 | Forte croissance sur une base minuscule | Le pourcentage ne dit rien sans l'absolu | Retour praticien [C] |
| 17 | Liquidation preference > 1x ou participating au seed / série A | Hors standard de marché | Carta [A] |
| 18 | Bridges successifs | Dilution plus forte, préférences plus lourdes en moyenne | Carta [A] |
| 19 | Montant levé incohérent avec le burn et les jalons | Runway insuffisant pour atteindre le tour suivant | Point Nine (rubrique Funding) [A] ; Dealroom (délai seed → A) [A] |
| 20 | Pas de « why now » | Rubrique centrale chez Sequoia et dans les 4M | Sequoia [A] ; Golden [B] |

Axes de vigilance prioritaires cités par un praticien [C] : réglementaire, marché et surtout concurrence.

---

## 11. Grille de questions par dimension

Questions dérivées des rubriques Point Nine, Sequoia et 4M. L'outil les génère quand l'information manque dans le deck.

| Dimension | Questions |
|---|---|
| Problème | Qui a ce problème, précisément ? Comment le traite-t-il aujourd'hui ? Combien lui coûte-t-il ? |
| Why now | Qu'est-ce qui a changé récemment ? Pourquoi personne ne l'a fait avant ? |
| Marché | Quel est le calcul bottom-up ? D'où viennent les chiffres top-down ? Quelle sortie le marché permet-il ? |
| Produit | Quelles sont les fonctionnalités cœur ? Qu'est-ce qui est en production, en pilote, en roadmap ? |
| Traction | Quels sont les KPI mensuels depuis le lancement ? Que montrent les cohortes ? Quel est le pipeline pondéré ? |
| Acquisition | Quels canaux, à quel coût ? La traction actuelle vient-elle de fruits faciles ? Quel plan pour la suite ? |
| Business model | Quel pricing, comparé à quoi ? Quelle marge brute ? Quels unit economics ? |
| Concurrence | Qui sont les incumbents et les challengers ? Quel actif défendable à long terme ? |
| Équipe | Pourquoi cette équipe pour ce problème (founder-market fit) ? Qui manque ? Qualité des premières recrues ? |
| Deal | Combien, pour combien de runway, pour atteindre quels jalons ? Quels SAFE en circulation ? Quels termes ? |
| Références | Quels clients peut-on appeler ? Quels experts du secteur ? |

---

## 12. Vérification des notes du projet utilisées ici

| Note du projet | Constat | Source |
|---|---|---|
| « Stickiness DAU/MAU > 25 % = top 10 % des apps » | Source originale non retrouvée | Notes Eurazeo [C] |
| Chiffres de rétention Andrew Chen (77 %, 90 %, 95 %) | Confirmés. Données Android de 2015 | Chen [A] |
| Template Point Nine (9 rubriques) | Confirmé. Point Nine précise que l'ordre ne reflète pas l'importance | Point Nine [A] |
| 4M de Boris Golden | Confirmé via les notes de sa conférence | [B] |
| Multiple SaaS « 5 à 10x » (retour praticien) | Compatible avec un marché 2026 ; Bessemer donne 10-20x pour la décennie 2010-2021. Toujours dater le multiple | Bessemer 2021 [A] |

---

## 13. Sources

Classées par ordre d'apparition. Date de consultation : 8 octobre 2026.

**Frameworks**
1. Point Nine Capital, Savina van der Straten, « What do we base our investment decisions on? Open source deal memo template », décembre 2016. https://writing.pointnine.com/p/what-do-we-base-our-investment-decisions
2. John Mathews, notes de la conférence de Boris Golden « Understanding investment », Lisbon Investment Summit. https://johnmathews.eu/blog/investment
3. Boris Golden, présentations SlideShare (« Understanding VCs », « What I look for in a startup pitch »). https://www.slideshare.net/BorisGolden
4. Frenchweb, « Capital-risque : les règles du jeu que les entrepreneurs ignorent » (Boris Golden). https://www.frenchweb.fr/capital-risque-les-vraies-regles-du-jeu-que-les-entrepreneurs-ignorent/234585
5. Partech, « Partech promotes Boris Golden to Partner », 12 janvier 2021. https://partechpartners.com/news/partech-promotes-boris-golden-to-partner
6. Sequoia Capital, « Writing a Business Plan », reproduit par PitchDeckCoach. https://fenix.tecnico.ulisboa.pt/downloadFile/1126518382322406/Sequoia%20Capital_pitchdecktemplate.pdf

**Métriques et benchmarks SaaS**
7. David Sacks, « The Burn Multiple », 23 avril 2020. https://sacks.substack.com/p/the-burn-multiple-51a7e43cb200
8. Bessemer Venture Partners, « Scaling to $100 Million », 21 septembre 2021. https://www.bvp.com/atlas/scaling-to-100-million
9. Bessemer Venture Partners, « 10 Laws of Cloud », 19 juin 2019. https://www.bvp.com/atlas/10-laws-of-cloud
10. Bessemer, « The Rule of X » (2024), via The SaaS Barometer et OnlyCFO. https://www.bvp.com/atlas/the-rule-of-x ; https://thesaasbarometer.substack.com/p/saas-barometer-newsletter-saturday-77a ; https://www.onlycfo.io/p/crowdstrike-rule-of-x-winner
11. Bessemer State of the Cloud 2017, notes de David Cummings. https://davidcummings.org/2017/02/12/bessemers-2017-state-of-the-cloud-report/
12. Christoph Janz, « What does it take to raise capital in SaaS in 2023 ». https://medium.com/point-nine-news/what-does-it-take-to-raise-capital-in-saas-in-2023-56d8f617714 ; résumé Daphni : https://www.daphni.com/media-hub/what-does-it-take-to-raise-capital-in-saas-in-2023 ; SaaStr 2023 : https://cloud.substack.com/p/the-latest-2023-napkin-reveal-what
13. SaaStr, « What it takes to really raise capital in 2021 » (Janz). https://www.saastr.com/what-it-takes-to-really-raise-capital-in-2021
14. Antoine Buteau, « Lessons from Christoph Janz » (citation sur le burn multiple, Napkin 2023). https://www.antoinebuteau.com/lessons-from-christoph-janz/
15. Mamoon Hamid, SaaStr, transcription « Numbers that actually matter ». https://www.saastr.com/mamoon-hamid-social-capital-numbers-actually-matter-founders-video-transcript
16. Tomasz Tunguz, « What is the optimal quick ratio for your SaaS startup? ». https://tomtunguz.com/what-is-quick-ratio-hiding/
17. ChartMogul, « SaaS Magic Number ». https://chartmogul.com/saas-metrics/magic-number/ ; CFI : https://corporatefinanceinstitute.com/resources/valuation/saas-magic-number/
18. Standard Metrics, « Rule of 40, Revisited », juillet 2026. https://standardmetrics.io/wp-content/uploads/2026/07/Standard-Metrics-Private-Market-Report-Rule-of-40-Revisited.pdf
19. Battery Ventures (Neeraj Agrawal, T2D3, 2015), biographie CB Insights. https://www.cbinsights.com/company/stellaservice/people

**Métriques générales, marketplace, consumer**
20. a16z, « 16 Startup Metrics », août 2015. https://a16z.com/2015/08/21/16-metrics/
21. a16z, « 16 More Startup Metrics », 2015. https://a16z.com/our-top-listicles-of-2015/
22. a16z, « 13 Metrics for Marketplace Companies », février 2020. https://a16z.com/13-metrics-for-marketplace-companies/
23. Andrew Chen, « New data shows losing 80% of mobile users is normal », 2015. https://andrewchen.com/new-data-shows-why-losing-80-of-your-mobile-users-is-normal-and-that-the-best-apps-do-much-better/
24. Sean Ellis, test PMF à 40 % : https://learningloop.io/plays/product-market-fit-survey ; limites du seuil : https://leanb2bbook.com/blog/product-market-fit-survey

**Tours, valorisations, termes**
25. Carta, « VC Startup Fundraising Benchmarks From 1000 Rounds », 10 juillet 2026, et « Top Seed Valuations Hit Record Highs in Q2 2026 », 8 juillet 2026. https://carta.com/data/linkedin-archive/
26. Carta, « New Fundraising Cheatsheet for Founders in 2025 » (T4 2024). https://carta.com/data/linkedin-fundraising-cheatsheet-q4-2024/
27. Carta, « How Much Dilution Do Founders Sell in Each Round » (2024). https://carta.com/data/linkedin-dilution-by-round-primary-vs-bridge/
28. Carta, « Liquidation Preference Over 1x Is Not Market in 2024 ». https://carta.com/data/linkedin-liq-pref-over-1x-not-market-2024/
29. Carta, « High Liquidation Preferences Are Still Rare but Rising » (2023). https://carta.com/data/linkedin-high-liq-pref-rare-but-rising-2023/
30. Cooley, Venture Financing Report T2 2025, via Angel Investors Network. https://angelinvestorsnetwork.com/venture-capital/liquidation-preference-term-sheet-investors-explained
31. Y Combinator, Post-Money SAFE User Guide. https://www.ycombinator.com/documents
32. Brad Feld et Jason Mendelson, Venture Deals (ouvrage de référence pour les définitions de term sheet).

**Europe**
33. Dealroom, « The startup journey to Series A in Europe ». https://dealroom.co/journey-value-add/
34. PitchBook, pre-money seed européen T1 2025, via guide secondaire. https://hub.causo.ai/guides/european-startup-funding-this-quarter

**Rendements et lecture des decks**
35. Seth Levine, « Venture Outcomes are Even More Skewed Than You Think », août 2014 (données Correlation Ventures). https://sethlevine.com/archives/2014/08/venture-outcomes-are-even-more-skewed-than-you-think.html ; mise à jour 2019 : https://sethlevine.com/archives/2019/09/the-markets-are-great-but-venture-outcomes-havent-changed-much.html
36. DocSend, Pitch Deck Interest T3 2021. https://www.nasdaq.com/press-release/docsend-pitch-deck-interest-q3-2021-data-shows-consistent-highs-for-vc-interest ; T4 2023 : https://m.gurufocus.com/news/2154228/ ; rapport 2020 : https://www.dropbox.com/resources/docsend-pitch-deck-research

**Notes du projet (niveau C)**
37. Notion_Eurazeo_Breaking_into_VC.md (frameworks Edison et Memohub, AARRR, économie d'un fonds, funnel).
38. Retours d'entretien d'un praticien (septembre 2026), consignés dans les notes du projet.
