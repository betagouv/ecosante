from ecosante.recommandations.models import Recommandation
from ecosante.inscription.models import Inscription

def help_activites(nom_activite):
    r = Recommandation(**{nom_activite: True})
    i = Inscription(activites=[nom_activite])
    assert r.is_relevant(i, None)

    r = Recommandation(**{nom_activite: True})
    i = Inscription(activites=[])
    assert not r.is_relevant(i, None)

def help_deplacement(nom_deplacement, nom_deplacement_inscription=None):
    r = Recommandation(**{nom_deplacement: True})
    i = Inscription(deplacement=[nom_deplacement_inscription or nom_deplacement])
    assert r.is_relevant(i, None)

    r = Recommandation(**{nom_deplacement: True})
    i = Inscription(deplacement=[])
    assert not r.is_relevant(i, None)

def test_is_relevant_menage(db_session):
    help_activites('menage')

def test_is_relevant_bricolage(db_session):
    help_activites('bricolage')

def test_is_relevant_jardinage(db_session):
    help_activites('jardinage')

def test_is_relevant_sport(db_session):
    help_activites('sport')

def test_is_relevant_velo(db_session):
    r = Recommandation(velo_trott_skate=True)
    i = Inscription(deplacement=["velo"])
    assert r.is_relevant(i, None)

    r = Recommandation(velo_trott_skate=True)
    i = Inscription(deplacement=[])
    assert not r.is_relevant(i, None)

def test_is_relevant_transport_en_commun(db_session):
    help_deplacement("transport_en_commun", "tec")

def test_is_relevant_voiture(db_session):
    help_deplacement("voiture")


def test_is_relevant_allergie(db_session):
   r = Recommandation(allergies=True)
   i = Inscription(allergie_pollen=True)
   assert r.is_relevant(i, None)

   r = Recommandation(allergies=True)
   i = Inscription(allergie_pollen=False)
   assert not r.is_relevant(i, None)

def test_is_relevant_enfants(db_session):
    r = Recommandation(enfants=True)
    i = Inscription(enfants=True)
    assert r.is_relevant(i, None)

    r = Recommandation(enfants=True)
    i = Inscription(enfants=False)
    assert not r.is_relevant(i, None)

def test_is_relevant_fumeurs(db_session):
    r = Recommandation(fumeur=True)
    i = Inscription(fumeur=True)
    assert r.is_relevant(i, None)

    r = Recommandation(fumeur=True)
    i = Inscription(fumeur=False)
    assert not r.is_relevant(i, None)

def test_is_qualite_mauvaise(db_session):
    r = Recommandation(qa_mauvaise=True)
    i = Inscription()
    assert r.is_relevant(i, "mauvais")
    assert not r.is_relevant(i, "bon")

def test_is_qualite_tres_mauvaise(db_session):
    r = Recommandation(qa_mauvaise=True)
    i = Inscription()
    assert r.is_relevant(i, "tres_mauvais")
    assert not r.is_relevant(i, "bon")

def test_is_qualite_extrement_mauvaise(db_session):
    r = Recommandation(qa_mauvaise=True)
    i = Inscription()
    assert r.is_relevant(i, "extrement_mauvais")
    assert not r.is_relevant(i, "bon")

def test_is_qualite_bonne(db_session):
    r = Recommandation(qa_bonne=True)
    i = Inscription()
    assert r.is_relevant(i, "bon")
    assert r.is_relevant(i, "moyen")
    assert not r.is_relevant(i, "extrement_mauvais")

def test_is_qualite_bonne_mauvaise(db_session):
    r = Recommandation(qa_bonne=True, qa_mauvaise=True)
    i = Inscription()
    assert r.is_relevant(i, "bon")
    assert r.is_relevant(i, "moyen")
    assert r.is_relevant(i, "degrade")
    assert r.is_relevant(i, "extrement_mauvais")