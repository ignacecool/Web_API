from sys import *
import os
from bottle import route, run,abort,request
import html.parser
import requests
from xml.parsers import expat
import re
import json
import xml.sax
import operator


liste=[]
i=0
glob_path=''
glob_cost=0
arbre_auteurs={}

"""
    Classe permettant de parser le fichier xml afin de créer une structure,
    ici il s'agit d'une liste de dictionnaires
"""
class MyHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.author = False
        self.principal = True
        self.doc_entete=["article","inproceedings","proceedings","book","incollection","phdthesis","mastersthesis"]
        self.doc_element=["author","title","year","journal","booktitle"]
        self.element={}
        self.is_element=False
        self.current_name=''
        self.authorList=[]
    def startElement(self, name, attrs):
        self.current_name=name
        if name in self.doc_entete:
            self.is_element=False
            self.principal = True
        else:
            if name in self.doc_element :
                if name=="author":
                    self.author=True
                self.is_element=True



    def endElement(self, name):
        if name in self.doc_entete:
            self.principal = False
            self.element["author"]=self.authorList
            liste.append(self.element)
            #print(self.element)
            self.element={}
            self.authorList=[]
        else:
            if name in self.doc_element :
                if name=="author":
                    self.author=False
        self.is_element=False


    def characters(self, content):
        if self.principal and self.author and self.is_element:
            self.authorList.append(content)
        else:
            if self.principal and self.is_element:
                self.element[self.current_name]=content

"""
    Fonctionnalité:
            Fonction permettant de lister tous les co-autheurs d'un auteur donné,
            elle parcours la liste des publications dans lesquelles l'auteur est
            intervenue puis extrait tous les co-autheurs

    Paramètres:
            -nom: le nom de l'auteur dont on veut connaitre les co-autheurs

    Résultat:
            Retourne une liste contenat les co-auteurs
"""
def listeCoAutheur(nom):
    coAuthor=[]
    for element in liste:
        tab=element["author"]
        if nom in tab:
            for co in tab:
                if (co not in coAuthor) :
                    if not co == nom:
                        coAuthor.append(co)
    #print(json.dumps(coAuthor))
    return coAuthor

"""
    Fonctionnalité:
            Fonction permettant de lister toutes les publications dans lesquelles un auteur est intervenu

    Paramètres:
            -nom: le nom de l'auteur dont on veut connaitre les publications

    Résultat:
            Retourne une liste contenat les publications
"""
def listePublications(nom):
    LaList=[]
    for element in liste:
        print(element)
        tab=element["author"]
        if nom in tab:
            LaList.append(element)
    return LaList
    #return coAuthor


"""
    Fonctionnalité:
            Route permettant d'afficher les détails par rapport à une publication donnée

    Paramètres:
            -id: le numéro de la publication, ici considéré comme l'index de la ligne

    Résultat:
            Retourne un dictionnaire,au format json, contenant les informations sur la publication

    Erreurs:
            id superieur à la taille de la liste
"""
@route("/publications/<id:int>")
def publications(id):
    if id>=0 and id<len(liste):
        return json.dumps(liste[id])
    else:
        abort(404, "id out of lenght")


"""
    Fonctionnalité:
            Route permettant d'afficher les informations concernant un auteu: nbre de publication,nbre de co-autheur

    Paramètres:
            -nom: nom de l'auteur

    Résultat:
            Retourne une liste,au format json
"""
@route("/authors/<nom>")
def authors(nom):
    resp=[]
    resp.append({"Nombre de publications":len(listePublications(nom))})
    resp.append({"nombre de co-autheurs":len(listeCoAutheur(nom))})
    return (json.dumps(resp))



"""
    Fonctionnalité:
            Route permettant d'afficher les toutes les publications d'un auteur

    Paramètres:
            -nom: nom de l'auteur
            -start: index de début
            -count: nombre de lignes à afficher
            -fields: mes champs à afficher
            -ordre: champs selon lequel la liste des résultats sera trier

    Résultat:
            Retourne la liste des publications,au format json
"""
@route("/authors/<nom>/publications")
def AuthPublication(nom):
    t=listePublications(nom)
    field=''
    ordre=''
    debut=0
    nombre=100
    if 'fields' in request.query.keys():
        field=request.query['fields']

    if 'order' in request.query.keys():
        ordre=request.query['order']

    if 'start' in request.query.keys():
        debut=int(request.query['start'])

    if 'count' in request.query.keys():
        nombre=int(request.query['count'])

    yo=FonctDecoupe(debut,nombre,t,field,ordre)
    if yo:
        return (json.dumps(yo))
    else:
        abort(404, "Aucun résultat ne correspond à votre recherche")



"""
    Fonctionnalité:
            Route permettant d'afficher les co-auteurs d'un auteur

    Paramètres:
            -nom: nom de l'auteur
            -start: index de début
            -count: nombre de lignes à afficher

    Résultat:
            Retourne la liste des co-auteurs,au format json
"""
@route("/authors/<nom>/coauthors")
def AuthCo(nom):
    t=listeCoAutheur(nom)
    field=''
    ordre=''
    debut=0
    nombre=100
    if 'fields' in request.query.keys():
        field=request.query['fields']

    if 'order' in request.query.keys():
        ordre=request.query['order']

    if 'start' in request.query.keys():
        debut=int(request.query['start'])

    if 'count' in request.query.keys():
        nombre=int(request.query['count'])

    yo=FonctDecoupe(debut,nombre,t,field,ordre)
    if yo:
        return (json.dumps(yo))
    else:
        abort(404, "Aucun résultat ne correspond à votre recherche")


"""
    Fonctionnalité:
            Route permettant de rechercher tous les noms d'auteurs correspondant à un format bien précis

    Paramètres:
            -searchString: format de chaîne de caractères recherché
            -start: index de début
            -count: nombre de lignes à afficher

    Résultat:
            Retourne la liste des noms d'auteurs répondant aux paramètres,au format json
"""
@route("/search/authors/<searchString>")
def SearchAuthor(searchString):
    strs = searchString.replace('%', '.')
    strs = strs.replace('*', '.+')
    t=fonctionRecherhceAuteur(strs)
    field=''
    ordre=''
    debut=0
    nombre=100
    if 'fields' in request.query.keys():
        field=request.query['fields']

    if 'order' in request.query.keys():
        ordre=request.query['order']

    if 'start' in request.query.keys():
        debut=int(request.query['start'])

    if 'count' in request.query.keys():
        nombre=int(request.query['count'])

    yo=FonctDecoupe(debut,nombre,t,field,ordre)
    if yo:
        return (json.dumps(yo))
    else:
        abort(404, "Aucun résultat ne correspond à votre recherche")


"""
    Fonctionnalité:
            Route permettant de rechercher toutes les publications dont le titre correspondant à un format bien précis

    Paramètres:
            -searchString: format de chaîne de caractères recherché
            -start: index de début
            -count: nombre de lignes à afficher
            -fields: mes champs à afficher
            -ordre: champs selon lequel la liste des résultats sera trier
            -filter: paramètre permettant d'affiner la recherche,elle impose d'autres conditions aux résultats

    Résultat:
            Retourne la liste des publications répondant aux paramètres,au format json
"""
@route("/search/publications/<searchString>")
def SearchPublication(searchString):
    strs = searchString.replace('%', '.')
    strs = strs.replace('*', '.+')
    field=''
    ordre=''
    debut=0
    nombre=100
    if 'filter' in request.query.keys():
        t=fonctionRecherhcePublication(strs,request.query['filter'])
    else:
        t=fonctionRecherhcePublication(strs,"")

    if 'fields' in request.query.keys():
        field=request.query['fields']

    if 'order' in request.query.keys():
        ordre=request.query['order']

    if 'start' in request.query.keys():
        debut=int(request.query['start'])

    if 'count' in request.query.keys():
        nombre=int(request.query['count'])

    yo=FonctDecoupe(debut,nombre,t,field,ordre)
    if yo:
        return (json.dumps(yo))
    else:
        abort(404, "Aucun résultat ne correspond à votre recherche")


@route("/authors/<name_origine>/distance/<name_destination>")
def distance(name_origine,name_destination):
    if arbre_auteurs:
        dijkstra(arbre_auteurs,name_origine,name_destination)
    else:
        dijkstra(ListAuthorCoAuthor(),name_origine,name_destination)
    if glob_cost:
        t='chemin: '+ str(glob_path)+ '---  cout: '+ str(glob_cost)
        return json.dumps(t)
    else:
        abort(404, "Aucune distance trouvée")





"""
Fontionnalité:
    fonction permettant de rechercher une liste d'auteurs dont le nom reponds à un critère donné

Paramètres:
    -recherche: chaine de carractère à rechercher
"""
def fonctionRecherhceAuteur(recherche):
    LaList=[]
    for element in liste:
        for auth in element["author"]:
            if re.match(recherche,auth,re.IGNORECASE):
                if auth not in LaList:
                    LaList.append(auth)
    return LaList

"""
Fontionnalité:
    fonction pour rechercher des publications en fanction des parametres donnés par l'utilisateur

Paramètres:
    -recherche: chaine de carractère à rechercher dans les titres de publication. exemple:"%%%complete*"-----------
    -filtre: Autres spécifications de la recherche. exemple: Autheur=ignace
"""
def fonctionRecherhcePublication(recherche,filtre):
    LaList=[]
    ver=0
    yo=[]
    if filtre:
        yo=filtre.split(",")
    for element in liste:
        if 'title' in element.keys():
           if re.match(recherche,element["title"],re.IGNORECASE):
               ver=0
               for val in yo:
                   tab=[]
                   tab=val.split(":")
                   if tab[1] not in element[tab[0]]:
                       ver=1
                       break
               if ver==0:
                   LaList.append(element)
    return LaList

"""
Fonctionnalité:
    fonction pour formater les donnés selon les paramètres de l'utilisateur: nombre de lignes,colonnes,tri...

Paramètres:
    -début: indice de départ
    -fin: indice de fin
    -element: liste de résultats
    -champs: les colonnes à afficher
    -ordre: colonne à trier
"""
def FonctDecoupe(debut,fin,element,champs,ordre):
    listRetur=[]
    limit=0
    elementCpy=element[:]
    field=[]
    if champs:
        field=champs.split(",");
    if (len(elementCpy)>debut):
        if((len(elementCpy)-debut)>fin):
            limit=fin
        else:
            limit=len(elementCpy)-debut
        i=0

        while(i<limit) :
            listRetur.append(elementCpy[debut+i])
            i=i+1
    l=[]
    if(len(listRetur)>0) and len(field)>0:
        print("fieeld")
        k=[]
        k=list(listRetur[0].keys())
        for val in k:
            if val not in field:
                l.append(val)

        for il in listRetur:
            for f in l:
                del il[f]

    if ordre:
        listRetur = sorted(listRetur, key=lambda k: k[ordre])
    return listRetur

"""
Fonctionnalité:
    fonction permettant de créér une structure contenant l'enssemble des auteurs et co-auteurs.
    Cette structure nous sera ensuite utile pour faire la recherche de la distance entre 2 auteurs.
    Exemple:
    graph = {
         'Hans-Ulrich Simon': {'Oded Shmueli': 1},
         'Nathan Goodman': {'Oded Shmueli': 1},
         'Norbert Blum': {'Oded Shmueli': 1}
    }
"""
def ListAuthorCoAuthor():
    ListAuthor=[]
    VariablAuth=[]
    for element in liste:
        for auth in element['author']:
            if auth not in VariablAuth:
                print(auth)
                ya={}
                for ik in listeCoAutheur(auth):
                    ya[ik]=1
                arbre_auteurs[auth]=ya
                ListAuthor.append(arbre_auteurs)
                VariablAuth.append(auth)
    print(json.dumps(arbre_auteurs))
    return arbre_auteurs


"""
Fonctionnalité:
    fonction permettant de rechercher le chemin minimal entre 2 auteurs(origine et destination), cet algorithme est inspiré de l'algo de Dijkstra
    de recherche du plus court chemin.

Paramètres:
    -graphe: structure sur laquelle la recherche se fera, il s'agit ici d'un dictionnaire
    -origine: nom de l'auteur de départ
    -destination: nom de l'auteur final
"""
def dijkstra(graphe,source,destination,visites=[],distances={},predecesseurs={}):
    """ calcul le plus court chemin à partir de la source
    """
    # quelques vérifications
    if source not in graphe:
        return
    if destination not in graphe:
        return

    if source == destination:
        #construction du chemin entre la source et la destination
        path=[]
        pred=destination
        while pred != None:
            path.append(pred)
            pred=predecesseurs.get(pred,None)
        global glob_path
        global glob_cost
        glob_path=path
        glob_cost=distances[destination]
    else :
        # initialisation du cout
        if not visites:
            distances[source]=0
        # parcours des voisins
        for neighbor in graphe[source] :
            if neighbor not in visites:
                new_distance = distances[source] + graphe[source][neighbor]
                if new_distance < distances.get(neighbor,float('inf')):
                    distances[neighbor] = new_distance
                    predecesseurs[neighbor] = source
        # marquer comme visité
        visites.append(source)
        # tous les voisins ont été visité
        # choisir les non-visités ayant la distance minimale
        # appliquer le même algorithme
        unvisites={}
        for k in graphe:
            if k not in visites:
                unvisites[k] = distances.get(k,float('inf'))
        x=min(unvisites, key=unvisites.get)
        dijkstra(graphe,x,destination,visites,distances,predecesseurs)

"""
def read_in_chunks(file_object, chunk_size=1024):
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data


f = open("C:/Users/Ephraïm/Documents/Projet_upmc/PROGRES/PROJET1/data.xml")
for piece in read_in_chunks(f):
    parser.parse(piece)
"""
parser = xml.sax.make_parser()
handler = MyHandler()
parser.setContentHandler(handler)
#parser.parse("C:/Users/Ephraïm/Documents/Projet_upmc/PROGRES/PROJET1/data_2013_2014.xml",'',encoding='ISO-8859-1')
filename="C:/Users/Ephraïm/Documents/Projet_upmc/PROGRES/PROJET1/data.xml"
encoding="ISO-8859-1"
with open(filename, "rb") as f:
        input_source = xml.sax.xmlreader.InputSource()
        input_source.setByteStream(f)
        input_source.setEncoding(encoding)
        parser.parse(input_source)
#ListAuthorCoAuthor()
run(host='localhost', port=8083, debug=True)
