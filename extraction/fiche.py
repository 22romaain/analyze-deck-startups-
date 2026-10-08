from enum import Enum

from pydantic import BaseModel, Field


def champ(description):
    return Field(None, description=description)


class TypeBusinessModel(str, Enum):
    SAAS = "SaaS"
    MARKETPLACE = "marketplace"
    APPLICATION_MOBILE = "application mobile"
    HARDWARE = "hardware"
    DEEPTECH = "deeptech"
    SERVICES = "services"
    AI_NATIVE_SERVICE = "AI-native service"


class Cible(str, Enum):
    B2B = "B2B"
    B2C = "B2C"
    B2B2C = "B2B2C"


class Stade(str, Enum):
    PRE_SEED = "pre-seed"
    SEED = "seed"
    SERIE_A = "série A"
    SERIE_B = "série B"
    GROWTH = "growth"


class EtatProduit(str, Enum):
    PROTOTYPE = "prototype"
    MVP = "MVP"
    EN_PRODUCTION = "en production"
    COMMERCIALISE = "commercialisé"


class Chiffre(BaseModel):
    valeur: float
    unite: str | None = champ("unité ou devise (ex : €, %, clients)")
    periode: str | None = champ("période ou date (ex : 2024, mars 2025, par mois)")
    slide: int | None = champ("numéro de la slide d'où vient le chiffre")


class Fondateur(BaseModel):
    nom: str | None = champ("nom")
    role: str | None = champ("rôle")
    parcours: str | None = champ("parcours")


class Tour(BaseModel):
    date: str | None = champ("date")
    montant: Chiffre | None = champ("montant")
    valorisation: Chiffre | None = champ("valorisation")
    investisseurs: list[str] | None = champ("investisseurs : fonds, business angels et leurs profils, industriels")


class Identite(BaseModel):
    nom: str | None = champ("nom de la société")
    date_creation: str | None = champ("date de création")
    origine: str | None = champ("origine (spin-out d'un laboratoire ou d'une école, projet interne d'un groupe)")
    siege: str | None = champ("siège (ville, pays)")
    autres_implantations: list[str] | None = champ("autres implantations (bureaux, pays)")
    effectif: int | None = champ("effectif total à date")
    secteur: str | None = champ("secteur et sous-secteur")
    types_business_model: list[TypeBusinessModel] | None = champ("type de business model annoncé (SaaS, marketplace, application mobile, hardware, deeptech, services, AI-native service)")
    cible: Cible | None = champ("cible B2B, B2C ou B2B2C")
    payeur_vs_utilisateur: str | None = champ("qui paie vs qui utilise")
    stade: Stade | None = champ("stade déclaré (pre-seed, seed, série A, série B, growth)")
    pitch: str | None = champ("pitch en une ou deux phrases tel que formulé par la société")
    date_deck: str | None = champ("date du deck")


class Besoin(BaseModel):
    probleme: str | None = champ("problème résolu décrit simplement")
    client_cible: str | None = champ("client cible précis (segment, taille en salariés ou en CA, fonction de l'acheteur)")
    pain_points: list[str] | None = champ("pain points listés par la société")
    must_have: str | None = champ("caractère must-have ou nice-to-have du besoin tel que présenté")
    urgence: str | None = champ("urgence du besoin")
    pourquoi_maintenant: str | None = champ("pourquoi maintenant (déclencheur d'achat, déclencheur temporel)")
    solution_actuelle: str | None = champ("solution actuelle du client (produit concurrent, outil interne, process manuel, statu quo)")
    cout_probleme: str | None = champ("coût actuel du problème pour le client (temps, argent, risque)")
    gain_client: Chiffre | None = champ("gain annoncé pour le client (€ par an)")
    cout_unitaire_vs_alternative: str | None = champ("coût unitaire de la solution vs alternative existante (ex : €/tonne)")
    capex_energie_vs_existant: str | None = champ("capex et consommation d'énergie vs existant")
    proposition_valeur: str | None = champ("tableau client / cas d'usage / proposition de valeur")
    interviews_clients: list[str] | None = champ("interviews clients citées")
    disposition_a_payer: str | None = champ("disposition à payer (prix premium accepté ou non)")


class Produit(BaseModel):
    description: str | None = champ("description du produit")
    fonctionnalites_coeur: list[str] | None = champ("fonctionnalités cœur")
    captures_ecran: bool | None = champ("captures d'écran")
    demo: bool | None = champ("démo")
    video: bool | None = champ("vidéo")
    etat: EtatProduit | None = champ("état du produit (prototype, MVP, en production, commercialisé)")
    date_lancement_commercial: str | None = champ("date de lancement commercial")
    modules_production_vs_prevus: str | None = champ("produits ou modules déjà en production vs prévus")
    roadmap: list[str] | None = champ("roadmap produit à 6-18 mois")
    pivot: str | None = champ("pivot ou produit ajouté à la demande des clients")
    nouveaux_segments: list[str] | None = champ("nouveaux verticaux ou segments visés")
    connecteurs: str | None = champ("nombre de connecteurs et intégrations (API, logiciels métier, systèmes du client)")
    dependance_api_tiers: str | None = champ("dépendance à l'API de fabricants ou d'éditeurs tiers")
    marques_compatibles: str | None = champ("nombre de marques compatibles et part du marché couverte")
    mode_deploiement: str | None = champ("mode de déploiement (self-serve, déploiement assisté avec ingénieurs forward-deployed, calibrage sur site)")
    duree_onboarding: str | None = champ("durée d'onboarding client")
    vitesse_deploiement: str | None = champ("vitesse de déploiement (pays ou sites ouverts en N mois)")
    metriques_usage: list[str] | None = champ("métriques d'usage et d'engagement du produit")
    nps: int | None = champ("NPS")
    preuves_pmf: list[str] | None = champ("preuves de product-market fit avancées par la société")


class Data(BaseModel):
    vertical_ou_horizontal: str | None = champ("vertical (un domaine métier) ou horizontal (couche d'orchestration)")
    architecture_modeles: str | None = champ("architecture des modèles (petits modèles spécialisés vs LLM généralistes)")
    modeles_maison: str | None = champ("modèles maison entraînés sur une donnée spécifique")
    fournisseur_modele: str | None = champ("model-agnostic ou dépendant d'un fournisseur de modèle")
    multi_cloud: bool | None = champ("multi-cloud")
    donnee_proprietaire: str | None = champ("donnée propriétaire générée par l'usage, achetée ou sous licence")
    historique_comportemental: str | None = champ("historique comportemental accumulé par utilisateur")
    workflows_encodes: str | None = champ("workflows encodés par client dans le produit")
    donnee_resultat: str | None = champ("donnée de résultat capturée à chaque livraison (ex : montant finalement obtenu)")
    besoins_compute_energie: str | None = champ("besoins en compute et en énergie")
    raccordement_reseau: str | None = champ("accès au raccordement réseau")


class Tech(BaseModel):
    technologie_proprietaire: bool | None = champ("technologie propriétaire ou non")
    briques_interne_vs_achetees: str | None = champ("brique technologique développée en interne vs achetée ou open source")
    stack: list[str] | None = champ("stack technique")
    brevets: str | None = champ("brevets (nombre, statut déposé ou accordé, type PCT, date de dépôt, fin de protection, absence de brevet)")
    brevets_publications_equipe: str | None = champ("nombre de brevets et de publications de l'équipe")
    difficulte_duplication: str | None = champ("difficulté de duplication revendiquée par la société")
    trl: int | None = champ("TRL (Technology Readiness Level)")
    jalons_techniques: list[str] | None = champ("jalons techniques atteints et à venir (prototype, démonstrateur, unité industrielle) avec capacité et date")
    donnees_pilote: str | None = champ("données brutes du pilote (rendement mesuré, performance dans la durée, heures de fonctionnement, consommation réelle)")
    resultats_demonstrateur: str | None = champ("résultat des tests ou vols de démonstrateur (succès total ou partiel)")
    performance_annoncee: str | None = champ("performance technique annoncée (pureté, rendement, précision)")
    comparatifs_performance: str | None = champ("comparatifs de performance produits par la société elle-même")
    operateurs_vs_classique: str | None = champ("nombre d'opérateurs nécessaires vs solution classique")
    conditions_fonctionnement: str | None = champ("conditions de fonctionnement du hardware (température, sensibilité aux vibrations, environnement)")
    chaine_de_valeur: str | None = champ("positionnement sur la chaîne de valeur (ex : capture seule vs transport et stockage)")
    fournisseurs_critiques: list[str] | None = champ("fournisseurs critiques (cryogénie, fonderie, composants)")
    production_continue: str | None = champ("production continue ou intermittente (énergie)")
    dependance_matieres_premieres: str | None = champ("dépendance géographique des matières premières (ex : raffinage en Chine)")
    quantique_segment: str | None = champ("quantique : segment (calcul, communication et cryptographie, capteurs)")
    quantique_modalite_qubit: str | None = champ("quantique : modalité de qubit (supraconducteurs, ions piégés, photonique, atomes neutres, spins de silicium, qubits de chat, nanotubes)")
    quantique_nombre_qubits: int | None = champ("quantique : nombre de qubits de la machine livrée")
    quantique_correction_erreur: str | None = champ("quantique : qubits physiques par qubit logique, taux d'erreur, mesures publiées vs feuille de route")
    quantique_performances: str | None = champ("quantique : vitesse des portes, fidélité, connectivité, température de fonctionnement, fabrication en série, rendement de fabrication")
    quantique_objectifs: list[str] | None = champ("quantique : objectifs datés (qubits logiques par année)")
    spatial: str | None = champ("spatial : position orbitale, spectre, infrastructure sol engagée par un partenaire, nombre de satellites cibles, calendrier démonstrateurs, déploiement, pleine capacité")


class Reglementation(BaseModel):
    textes_cites: list[str] | None = champ("texte réglementaire cité comme moteur ou frein (nom, date d'entrée en vigueur, seuils, pays concernés)")
    standards: list[str] | None = champ("standards publiés qui transforment le besoin en ligne budgétaire datée (ex : standards post-quantiques NIST 2024)")
    dependance_reglementaire: str | None = champ("dépendance du modèle à une réglementation (ex : biométhane, décret tertiaire, facture électronique)")
    hypothese_prix_externe: str | None = champ("hypothèse de prix d'un facteur externe utilisée dans le deck (ex : prix du carbone ETS projeté)")
    licences_detenues: list[str] | None = champ("licences et agréments détenus (ex : fournisseur d'information sur les comptes)")
    licences_visees: str | None = champ("licences et agréments visés (conseil, exécution) et calendrier")
    classement: str | None = champ("classement réglementaire (ex : Seveso)")
    autorisation_mise_sur_marche: str | None = champ("autorisation de mise sur le marché requise")
    souverainete: str | None = champ("argument réglementaire de souveraineté (RGPD, Cloud Act)")
    cadre_par_pays: str | None = champ("cadre réglementaire par pays de déploiement")


class Marche(BaseModel):
    definition: str | None = champ("définition du marché par la société")
    tam: Chiffre | None = champ("TAM annoncé")
    sam: Chiffre | None = champ("SAM annoncé")
    som: Chiffre | None = champ("SOM annoncé")
    methode_calcul: str | None = champ("méthode de calcul (top-down, bottom-up, les deux)")
    bottom_up: str | None = champ("bottom-up du deck (nombre de cibles × ACV)")
    sources: list[str] | None = champ("sources des chiffres de marché (rapports, registres officiels, fédérations)")
    tam_par_segment: list[str] | None = champ("TAM par segment d'application")
    part_adressee: str | None = champ("part du marché ou des émissions adressée selon la société")
    geographie: list[str] | None = champ("géographie du marché visé")
    croissance: Chiffre | None = champ("croissance annuelle du marché")
    tendances: list[str] | None = champ("tendances de marché citées")
    public_vs_prive: str | None = champ("clients secteur public vs privé (part du revenu)")
    contrats_cadres: list[str] | None = champ("acheteurs publics et contrats-cadres (plafond, date, programme, client final)")


class Concurrence(BaseModel):
    directs: list[str] | None = champ("concurrents directs cités")
    indirects: list[str] | None = champ("concurrents indirects cités")
    forces_faiblesses: str | None = champ("forces et faiblesses comparées telles que présentées")
    tableau_concurrentiel: str | None = champ("tableau concurrentiel du deck (construit par la société, cases cochées)")
    positionnement: str | None = champ("positionnement revendiqué")
    avantage_defendable: str | None = champ("avantage compétitif défendable à long terme revendiqué")
    cibles_disruption: list[str] | None = champ("règles ou acteurs établis que la société prétend disrupter")


class Traction(BaseModel):
    kpi_mensuels: list[str] | None = champ("KPI mensuels depuis le lancement")
    ca_annuel: list[Chiffre] | None = champ("chiffre d'affaires par année depuis la création (années à 0 €)")
    ca_mensuel: list[Chiffre] | None = champ("chiffre d'affaires par mois (12 à 24 derniers mois)")
    croissance_mom: Chiffre | None = champ("croissance MoM")
    croissance_yoy: Chiffre | None = champ("croissance YoY")
    nombre_clients: list[Chiffre] | None = champ("nombre de clients à date et évolution mensuelle")
    logos: list[str] | None = champ("logos clients affichés")
    payants_vs_tests: str | None = champ("clients payants vs clients en test")
    pipeline: str | None = champ("pipeline commercial déclaré (prospects, prospects qualifiés)")
    pipeline_pondere: Chiffre | None = champ("pipeline pondéré par probabilité de closing")
    loi_vs_contrats: str | None = champ("LOI (signataires) vs contrats signés")
    bons_de_commande: str | None = champ("bons de commande")
    engagements_payants: str | None = champ("engagements payants")
    engagement_conditionnel: str | None = champ("engagement d'achat conditionnel")
    carnet_commandes: str | None = champ("carnet de commandes (montant, clients, part convertie en revenu facturé vs engagement non livré)")
    contrat_prime: str | None = champ("contrat prime (ESA, DGA)")
    jalons_commerciaux: list[str] | None = champ("jalons commerciaux déjà atteints")


class ARR(BaseModel):
    mrr: list[Chiffre] | None = champ("MRR et évolution mois par mois")
    arr: list[Chiffre] | None = champ("ARR à date, il y a 12 mois et fin des deux derniers exercices")
    mode_calcul: str | None = champ("mode de calcul de l'ARR déclaré (contractuel ou run-rate dernier mois × 12)")
    split_revenu: str | None = champ("split du revenu par nature (abonnement, usage, commission, one-shot, services)")
    arr_contractuel: Chiffre | None = champ("ARR contractuel seul")
    part_usage: Chiffre | None = champ("part d'usage incluse dans l'ARR")
    usage_engage: str | None = champ("usage engagé vs non engagé")
    usage_mensuel: list[Chiffre] | None = champ("série mensuelle d'usage sur 12 mois")
    poc_payants: str | None = champ("POC payants inclus dans l'ARR (nombre, montant, prix unitaire)")
    pilotes_non_signes: str | None = champ("pilotes non signés inclus dans l'ARR")
    frais_services: str | None = champ("frais d'implémentation, de setup, de paramétrage, professional services et formation (montant, % du CA)")
    bookings_vs_arr: str | None = champ("bookings vs ARR")
    contrats_pluriannuels: str | None = champ("contrats pluriannuels ramenés au montant annuel")
    arpa: Chiffre | None = champ("MRR ou ARR moyen par client (ARPA, ACV)")
    decomposition_mrr: str | None = champ("décomposition du MRR par segment (ex : résidentiel, entreprise, revendeur), par nature et par client")
    volumes_plateforme: Chiffre | None = champ("montants placés ou volumes transitant par la plateforme")
    ai_native_facturation: str | None = champ("AI-native service : facturation au dossier, au résultat ou à l'usage")
    ai_native_volume: Chiffre | None = champ("AI-native service : volume traité par semaine")


class Clients(BaseModel):
    par_categorie: str | None = champ("nombre de clients par catégorie (grands comptes, PME, secteur public)")
    concentration: str | None = champ("part du top 1, top 3, top 5 et top 10 clients dans le revenu")
    contrats_gros_clients: str | None = champ("nature des contrats des plus gros clients (pluriannuels fermes, renouvelables annuellement, spot)")
    renouvellements: str | None = champ("durée des contrats et dates de renouvellement des plus gros clients")
    minimums: str | None = champ("minimums contractuels")
    geographies: list[str] | None = champ("géographies des clients")
    partenaire_unique: str | None = champ("partenaire de distribution unique (intégrateur, revendeur, réseau) et part du revenu qu'il apporte")
    references_reglementees: list[str] | None = champ("références clients en secteur réglementé")


class Retention(BaseModel):
    courbes: str | None = champ("courbes de rétention")
    churn: str | None = champ("logo churn, revenue churn et downgrade séparés (%)")
    periode_churn: str | None = champ("période de mesure du churn")
    anciennete_cohortes: str | None = champ("ancienneté des cohortes utilisées")
    nrr: Chiffre | None = champ("Net Revenue Retention (NRR)")
    grr: Chiffre | None = champ("Gross Revenue Retention (GRR)")
    base_nrr: str | None = champ("base de calcul du NRR (nombre de clients de plus de 12 mois)")


class Marketplace(BaseModel):
    gmv: list[Chiffre] | None = champ("GMV et évolution mensuelle")
    take_rate: Chiffre | None = champ("take rate")
    revenu_net: Chiffre | None = champ("revenu net")
    marge_transactions: Chiffre | None = champ("marge sur transactions")
    frais: str | None = champ("frais sur la plateforme (logistique, assurance, frais bancaires)")
    moment_commission: str | None = champ("moment du prélèvement de la commission (paiement transitant par la plateforme ou non)")
    acheteurs_actifs: int | None = champ("nombre d'acheteurs actifs")
    vendeurs_actifs: int | None = champ("nombre de vendeurs ou offreurs actifs")
    panier_moyen: Chiffre | None = champ("panier moyen")
    frequence_achat: str | None = champ("fréquence d'achat par cohorte")
    taux_reachat: Chiffre | None = champ("taux de réachat")
    part_gmv_recurrents: Chiffre | None = champ("part du GMV venant d'acheteurs récurrents")
    retention_gmv: str | None = champ("rétention de cohorte de GMV côté offre et côté demande")
    concentration_offre: Chiffre | None = champ("concentration côté offre (part du GMV des top vendeurs)")
    liquidite: Chiffre | None = champ("liquidité de la marketplace (part de l'offre qui trouve preneur)")
    services: list[str] | None = champ("services au-delà de la mise en relation (paiement sécurisé, gestion des litiges, financement, assurance, flux de leads)")
    part_bouche_a_oreille: Chiffre | None = champ("part de la croissance venant du bouche-à-oreille et des effets de réseau")


class AARRR(BaseModel):
    telechargements: int | None = champ("nombre de téléchargements")
    dau: int | None = champ("DAU")
    mau: int | None = champ("MAU")
    stickiness: Chiffre | None = champ("stickiness DAU/MAU")
    croissance_dau_mau: str | None = champ("croissance historique du DAU et du MAU")
    churn_onboarding: str | None = champ("churn à chaque étape de l'onboarding jusqu'à la fonctionnalité cœur (activation)")
    retention_d1_d7_d30: str | None = champ("rétention D1, D7 et D30")
    retention_long_terme: Chiffre | None = champ("part des utilisateurs actifs à 1 mois encore actifs à 3 mois (long terme)")
    sessions_par_dau: float | None = champ("sessions quotidiennes par DAU")
    k_factor: float | None = champ("K-factor (nombre moyen de nouveaux utilisateurs apportés par utilisateur)")
    arpu: Chiffre | None = champ("ARPU")
    arppu: Chiffre | None = champ("ARPPU")
    part_payants: Chiffre | None = champ("part des utilisateurs payants")
    gaming_ua: Chiffre | None = champ("gaming : dépenses d'UA (user acquisition)")
    gaming_iap: Chiffre | None = champ("gaming : revenus d'IAP (in-app purchases)")
    gaming_commissions: Chiffre | None = champ("gaming : commissions de plateformes (stores)")


class GTM(BaseModel):
    canaux: str | None = champ("canaux d'acquisition actuels et coût par canal")
    organique_vs_paye: str | None = champ("split croissance organique vs payée")
    mode_vente: str | None = champ("mode de vente (self-serve, sales-led, partenaires, revendeurs)")
    strategie: str | None = champ("go-to-market adopté et justification")
    land_and_expand: str | None = champ("modèle land and expand (périmètre d'entrée, sens de l'extension)")
    distribution_revenue_share: str | None = champ("distribution via fabricants, distributeurs ou installateurs en revenue share")
    partenariat_distribution: str | None = champ("accord de référencement ou partenariat de distribution (part du new business, exclusivité, durée, renouvellement)")
    defis_distribution: list[str] | None = champ("défis de distribution identifiés")
    avantage_distribution: str | None = champ("avantage de distribution revendiqué")
    cycle_vente: Chiffre | None = champ("cycle de vente moyen (mois)")
    buying_cycle: str | None = champ("étapes et décideurs du buying cycle")
    depenses_sales_marketing: str | None = champ("dépenses sales et marketing sur 12 mois et nombre de nouveaux logos obtenus")
    cac: Chiffre | None = champ("CAC")
    cac_blended_vs_paye: str | None = champ("CAC blended vs CAC payé")
    cac_fully_loaded: Chiffre | None = champ("CAC fully loaded (salaires sales et marketing inclus)")
    taille_equipe_commerciale: int | None = champ("taille de l'équipe commerciale")
    plan_sales_marketing: str | None = champ("plan sales et marketing futur")


class Monetisation(BaseModel):
    sources_revenus: list[str] | None = champ("sources de revenus (abonnement, usage, commission, fee revendeur, services réseau, revenue share, white label avec prix setup + annuel)")
    modele_hardware: str | None = champ("hardware : vente d'équipement, licence, location ou paiement à l'unité produite")
    pricing: str | None = champ("pricing (grille, prix par offre, prix par unité)")
    ltv: Chiffre | None = champ("LTV")
    ltv_cac: float | None = champ("LTV / CAC")
    payback: Chiffre | None = champ("CAC payback period")
    levier_operationnel: str | None = champ("levier opérationnel et scalabilité revendiqués")
    cycle_cash: str | None = champ("cycle de cash (facturation annuelle d'avance ou mensuelle, délais de paiement clients et fournisseurs)")
    bfr: str | None = champ("besoin en fonds de roulement (positif ou négatif)")


class Couts(BaseModel):
    marge_brute: list[Chiffre] | None = champ("marge brute actuelle et il y a 12 mois")
    marge_par_ligne: list[str] | None = champ("marge brute par ligne de revenu")
    marge_unitaire: str | None = champ("marge brute par unité, par tonne ou par contrat")
    cogs: str | None = champ("composantes du COGS (coûts d'inférence, validation humaine, équipe offshore)")
    part_intervention_humaine: str | None = champ("part des unités traitées avec intervention humaine et sa tendance")
    cout_traitement_unitaire: Chiffre | None = champ("coût de traitement par unité")
    experts_qualite: int | None = champ("nombre d'experts humains en contrôle qualité")
    opex_par_poste: list[str] | None = champ("charges opérationnelles par poste")
    opex_rd: str | None = champ("opex R&D (chercheurs, effort récurrent pour maintenir l'avance technologique)")


class Cash(BaseModel):
    pnl_historique: str | None = champ("P&L historique")
    ebitda: Chiffre | None = champ("EBITDA")
    marge_ebitda: Chiffre | None = champ("marge d'EBITDA (positive ou non)")
    cash_flows: str | None = champ("cash-flows")
    capex_production: Chiffre | None = champ("capex de production")
    capex_unitaire: Chiffre | None = champ("capex par unité")
    equipements: str | None = champ("équipements de pointe")
    capex_hors_ebitda: Chiffre | None = champ("capex hors EBITDA")
    tresorerie: Chiffre | None = champ("trésorerie à date")
    burn_mensuel: Chiffre | None = champ("burn mensuel actuel")
    net_burn: Chiffre | None = champ("net burn sur 12 mois glissants")
    net_new_arr: Chiffre | None = champ("net new ARR sur la même période que le net burn")
    gross_burn: Chiffre | None = champ("gross burn")
    encaissements: Chiffre | None = champ("encaissements clients")
    runway: Chiffre | None = champ("runway")
    emploi_fonds_precedent: str | None = champ("emploi des fonds du tour précédent")
    bootstrappee: bool | None = champ("société bootstrappée (autofinancée) ou non")
    dette: str | None = champ("dette existante")


class Previsionnel(BaseModel):
    business_plan: str | None = champ("P&L prévisionnel (business plan) et hypothèses")
    plan_croissance: str | None = champ("plan de croissance présenté")
    objectifs: list[str] | None = champ("objectifs chiffrés à 12, 18 et 24 mois")
    premier_revenu: Chiffre | None = champ("premier revenu (année et montant)")
    revenu_projete: list[Chiffre] | None = champ("revenu projeté à 7-10 ans")
    break_even: str | None = champ("date de break-even EBITDA")
    chemin_rentabilite: str | None = champ("chemin vers la rentabilité")
    besoin_capital: str | None = champ("besoin en capital total jusqu'au premier revenu et sur 5 ans")
    plan_financement: str | None = champ("plan de financement jusqu'à la première unité industrielle (part de subventions, part de dette, mois de runway achetés par le tour)")
    prochain_tour: str | None = champ("prochain tour annoncé (date)")


class Equipe(BaseModel):
    fondateurs: list[Fondateur] | None = champ("fondateurs (noms, rôles, parcours)")
    repartition_capital: str | None = champ("répartition du capital entre fondateurs")
    fondateur_praticien: str | None = champ("fondateur ayant vécu le problème en tant que praticien")
    parcours_secteur: str | None = champ("parcours chez des acteurs du secteur (grands groupes, concurrents, clients)")
    experience_gtm: str | None = champ("expérience des fondateurs en go-to-market")
    experience_entrepreneuriale: str | None = champ("expérience entrepreneuriale antérieure")
    exit_precedent: str | None = champ("exit précédent (montant, acquéreur, année)")
    historique_commun: str | None = champ("historique commun des fondateurs (équipe soudée)")
    effectif_par_fonction: str | None = champ("répartition de l'effectif par fonction (R&D, tech, sales, customer success, marketing, revenue ops)")
    profils: str | None = champ("profils de l'équipe (ingénieurs, docteurs) et entreprises d'origine")
    postes_cles: str | None = champ("postes clés pourvus et à pourvoir")
    organigramme: str | None = champ("organigramme")
    board_advisors: list[str] | None = champ("board et advisors")
    advisors_incumbents: list[str] | None = champ("advisors ou investisseurs issus d'incumbents")


class Deal(BaseModel):
    montant: Chiffre | None = champ("montant levé")
    instrument: str | None = champ("instrument (equity, SAFE, BSA AIR, obligation convertible, dette)")
    pre_money: Chiffre | None = champ("valorisation pre-money")
    post_money: Chiffre | None = champ("valorisation post-money")
    closing: str | None = champ("timing du tour (closing visé)")
    lead: str | None = champ("lead du tour (confirmé ou recherché)")
    part_lead: Chiffre | None = champ("pourcentage de la table demandé au lead")
    ticket_demande: Chiffre | None = champ("ticket demandé au fonds")
    investisseurs_existants: str | None = champ("participation et soft-circle des investisseurs existants")
    montant_restant: Chiffre | None = champ("montant restant à trouver")
    tranches: str | None = champ("tour en tranches (même prix ou step-up, tranches conditionnées à l'ARR)")
    use_of_funds: str | None = champ("emploi des fonds (use of funds par fonction et par pays)")
    milestones: list[str] | None = champ("milestones visés avec l'investissement")
    preuve_prochaine_levee: str | None = champ("ce qui sera prouvé à la prochaine levée")
    runway_apres_tour: Chiffre | None = champ("runway après le tour")
    historique: list[Tour] | None = champ("historique de financement (tours, montants, dates, valorisations, investisseurs)")
    total_leve: Chiffre | None = champ("total levé à date")
    accord_test: str | None = champ("accord de test")
    consortium: str | None = champ("consortium signé")
    partenaires_pilotes: list[str] | None = champ("partenaires industriels donnant accès à des sites pilotes")
    non_dilutif: list[str] | None = champ("subventions et financements non dilutifs obtenus (France 2030, EIC, régions, concours)")


class CapTable(BaseModel):
    actuelle: str | None = champ("cap table actuelle par catégorie (fondateurs, seed, pool, SAFE et BSA AIR non convertis)")
    post_tour: str | None = champ("cap table post-tour")
    option_pool: str | None = champ("option pool (taille, refresh demandé, % cible, inclus dans le pre-money ou le post-money)")
    bspce_bsa: str | None = champ("BSPCE, BSA et BSA AIR émis")
    safe: str | None = champ("SAFE (montant, valuation cap, discount, pre-money ou post-money, MFN)")


class Moat(BaseModel):
    effets_reseau: str | None = champ("effets de réseau revendiqués")


class Exit(BaseModel):
    potentiel: str | None = champ("potentiel de sortie évoqué (acquéreurs possibles, IPO)")
    voie_cotation: str | None = champ("voie de cotation envisagée (IPO, SPAC)")
    horizon: str | None = champ("horizon de sortie")


class ESG(BaseModel):
    thematique: str | None = champ("thématique ESG ou impact (mobilité, décarbonation, etc.)")
    indicateurs: list[str] | None = champ("indicateurs d'impact suivis")


class References(BaseModel):
    programmes: list[str] | None = champ("programmes d'accélération ou d'incubation suivis")
    presse_prix: list[str] | None = champ("presse et prix")


class Fiche(BaseModel):
    identite: Identite
    besoin: Besoin
    produit: Produit
    data: Data | None = None
    tech: Tech | None = None
    reglementation: Reglementation
    marche: Marche
    concurrence: Concurrence
    traction: Traction
    arr: ARR | None = None
    clients: Clients
    retention: Retention | None = None
    marketplace: Marketplace | None = None
    aarrr: AARRR | None = None
    gtm: GTM
    monetisation: Monetisation
    couts: Couts
    cash: Cash
    previsionnel: Previsionnel
    equipe: Equipe
    deal: Deal
    cap_table: CapTable
    moat: Moat
    exit: Exit
    esg: ESG
    references: References
    contradictions: list[str]
