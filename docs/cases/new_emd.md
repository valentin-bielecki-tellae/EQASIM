# Génération d'une population en utilsant une enquête ménages déplacements (EMD)

Sebastian HÖRL a ajouté les travaux de Valentin LE BESCOND à EQASIM (dernier commit le 01/06/2022) et a fait quelques changements depuis que j'ai fork le pipeline EQASIM pour l'utiliser sur Rennes. 
Il y a désormais un tutoriel dédié pour lancer EQASIM sur Nantes, mais aussi sur la Corse, Lyon etc.. Il y avait quelques changements à faire, notamment sur la base de données BD-TOPO et il y a de nouveaux scritps pour repondérer les données issues des enquêtes ménages déplacements.

Je me suis inspiré à la fois du code de Valentin LE BESCOND sur Nantes, générant une population synthétique sur le département de Loire-Atlantique avec l'enquête EDGT 44 2015, mais aussi de l'exemple avec l'EGT 2010 de Sebastian HÖRL sur l'Île-de-France. J'ai ajouté des scripts pour utiliser l'enquête EMC² 35 sur le département d'Ille-et-Vilaine.

Le dossier pour utiliser une EMD se décompose en 3 scripts principaux : 

- raw.py
- cleaned.py
- filtered.py

### raw.py

Ce script lit les données brutes. Il permet de créer plusieurs tables (3 ou 4 selon la source de données) avec les ménages, les personnes et les déplacements. Ces tables sont formatées, avec une liste de colonnes spécifiques, un encodage etc.. Par exemple pour utiliser l'EDGT de Nantes, il y a un script python format.py contenant les dictionnaires avec les colonnes (position, taille, nom) pour lire correctement les fichiers .txt de l'EMD. Ce script dépend donc des données, il fera appel à des fonctions spécifiques de la librairie pandas selon le format des fichiers d'entrée.

## cleaning.py

Ce script nettoie les données. Il récupère les différentes informations dans les tables, fait des jointures, ajoute des identifiants, catégorise certains attributs etc... Cette partie dépend aussi des données d'entrée, notamment des zonages propres à l'enquête, des libellés et des codes des réponses, des catégories pour désigner les motifs des déplacements... Il faut nécessairement utiliser la documentation de l'EMD pour faire le lien entre les différentes catégories de réponses et les catégories proposées par EQASIM. 

Exemple pour l'EGT : 

Il y a un dictionnaire PURPOSE_MAP dans hts/egt/cleaned.py qui fait le lien entre les réponses du motif de déplacement et les catégories d'EQASIM. Par exemple pour le motif *leisure*, les réponses suivantes sont comptabilisées avec un motif de loisir : la catégorie Loisirs (41 à 47) et la catégorie Restauration hors domicile (15 à 17). 

Même démarche pour catégoriser les modes et les CSP.

## filtered.py

EQASIM ne conserve que les déplacements des résidents et les déplacements à l'intérieur de la zone. Les ménages et les trajets sont ensuite filtrés. Les colonnes conservées sont les suivantes : 

HOUSEHOLD_COLUMNS = [
    "household_id", "household_weight", "household_size",
    "number_of_vehicles", "number_of_bikes", "departement_id",
    "income_class", "consumption_units"
]

PERSON_COLUMNS = [
    "person_id", "household_id", "person_weight",
    "age", "sex", "employed", "studies",
    "has_license", "has_pt_subscription",
    "number_of_trips", "departement_id", "trip_weight",
    "is_passenger", "socioprofessional_class"
]

TRIP_COLUMNS = [
    "person_id", "trip_id", "trip_weight",
    "departure_time", "arrival_time",
    "trip_duration", "activity_duration",
    "following_purpose", "preceding_purpose", "is_last_trip", "is_first_trip",
    "mode", "origin_departement_id", "destination_departement_id"
]

Je ne pense pas qu'il y ait besoin d'expliquer les attributs et les valeurs. Il faut se référer aux différents calculs dans la partie hts (household travel survey) d'EQASIM et les différents scripts utilisés dans le processus.


## Lancer EQASIM sur Nantes

Renommer le fichier config_nantes.yml en config.yml pour l'utiliser dans EQASIM.
Suivre les instructions dans docs/cases/nantes.md

## Lancer EQASIM sur Rennes

Renommer le fichier config_rennes.yml en config.yml pour l'utiliser dans EQASIM.
Suivre les instructions dans docs/cases/nantes.md pour ajouter les données BD-TOPO.
J'ai mis les données EMC² sur le [drive](https://drive.google.com/drive/folders/1enHgGUuNx29kQ1kyKVUf5ArqVd04aGcW?usp=sharing) avec la table ZONE_MAP.csv qui fait le lien entre les zones de l'enquête et les communes. Ces données doivent être ajoutées dans le répertoire data d'EQASIM.

Suite aux remarques de Rennes Métropole lors du projet sur les lignes de covoiturage, j'ai ajouté des données *Site & Organismes* en [Open Data](https://data.rennesmetropole.fr/explore/dataset/sites_organismes_sites/information/) à la base BPE. Pour utiliser ces données enrichies sur le département 35, il suffit de remplacer les appels à data.bpe.cleaned en data.bpe_enriched.cleaned (sauf dans le répertoire data/bpe). 

Le script formate les données *Site & Organismes* et conserve les activités liées à la culture et à l'éducation. Il va ensuite tout simplement remplacer les données BPE de ce type d'activité à l'intérieur de Rennes Métropole. Fort heureusement il y a plus de localisations avec la base de Rennes Métropole, car certains lieux ne sont pas pris en compte dans la BPE (ex: les petites associations). Ces localisations sont supposées plus complètes et plus précises. J'ai mis le fichier sur le [drive](https://drive.google.com/file/d/1OLXxop3YHHe23AnN3Uf3OwYIjCrUr7fC/view?usp=sharing).

Il faudra bien penser à ne pas utiliser bpe_enriched sur un autre département !

J'ai aussi ajouté un script reweighted.py pour ajouter plus de trajets. Il y avait ~3.5 millions de trajets à l'intérieur du département, j'ai donc arbitrairement augmenté le nombre de trajets de 20% pour atteindre les 4 millions de déplacements quotidiens.