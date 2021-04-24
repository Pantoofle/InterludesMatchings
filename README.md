# InterludesMatchings

Un algo pour faire une répartition d'activité, en essayant de donner au moins une activité satisfaisante à chaque participant.es.\
Il utilise la libraire matching de python pour une grosse partie de la résolution. 

## Description de l'algo

L'algo se base sur le problème hôpital-résident, comme celui des années précédentes. Sont fonctionnement exact est un peu modifié : 
- 1. L'algo commence par essayer d'attribuer une activité à chaque participant.es au mieux possible. Les égalités sont départagées aléatoirement. Plus un choix est haut dans votre liste de souhait, plus vous avez de chance de vous le voir attribuer.
- 2. Puis, toutes les activités attribuées sont supprimées, les voeux résolu des joueurs aussi. 
- 3. Tant qu'il reste des place dans des activités et des participant.es qui veulent y participer, on recommence à l'étape 1. 
