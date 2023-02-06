# NAS

## Scripts

1. *Optionnel* `initialconfig.py`: Crée une config initiale à partir d'une description de mapping physique json.

```sh
python initialconfig.py physical_mapping.json > myconfig.gviz
```

2. Editer `myconfig.gviz`, ex: rajouter des clients

3. `main.py`: Crée les configs routeurs à partir de la config.

```sh
python main.py myconfig.gviz --phy physical_mapping.json
```

Ou si pas de mapping physique :

```sh
python main.py myconfig.gviz 
```

4. `gns3topo.py`: Crée la topologie dans GNS3 à partir du mapping physique.

```sh
python gns3topo.py -h
```

## Notes

Le programme fonctionne en 2 étapes, la première consiste à déméler le graphe et à en déduire les informations importantes.
Il y a 2 tables créées à ce moment là : `interfaces` et `vpn`.
`interfaces` contient les adresses ip et les sous réseaux de chaque interface de chaque routeur.
`vpn` contient toutes les informations de liaison entre les clients pour les routeurs de bordure (ex: peer bgp, asn du client).

Avec toutes ces informations, la deuxième partie du programme (`config_generator.py`) construit les configurations des routeurs.
Il s'agit d'un simple templating où l'on ajoute les commandes nécessaires en lisant les tables.

## TODO

- Chargement automatique des configs (via copie de fichier)
- Mise à jour des configs (via telnet, diff)
- Placement des routeurs dans le projet GNS3 (parsing du svg)

## Exemples de rendu

![rendered topology (cluster)](rendered_cluster.svg)
![rendered topology (neato)](rendered_neato.svg)
