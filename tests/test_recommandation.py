from ecosante.recommandations.models import Recommandation
from ecosante.inscription.models import Inscription
from datetime import date, timedelta

def help_activites(nom_activite):
    r = Recommandation(**{nom_activite: True})
    i = Inscription(activites=[nom_activite])
    assert r.is_relevant(i, None, [], 0, date.today())

    r = Recommandation(**{nom_activite: True})
    i = Inscription(activites=[])
    assert not r.is_relevant(i, None, [], 0, date.today())

def help_deplacement(nom_deplacement, nom_deplacement_inscription=None):
    r = Recommandation(**{nom_deplacement: True})
    i = Inscription(deplacement=[nom_deplacement_inscription or nom_deplacement])
    assert r.is_relevant(i, None, [], 0, date.today())

    r = Recommandation(**{nom_deplacement: True})
    i = Inscription(deplacement=[])
    assert not r.is_relevant(i, None, [], 0, date.today())

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
    assert r.is_relevant(i, None, [], 0, date.today())

    r = Recommandation(velo_trott_skate=True)
    i = Inscription(deplacement=[])
    assert not r.is_relevant(i, None, [], 0, date.today())

def test_is_relevant_transport_en_commun(db_session):
    help_deplacement("transport_en_commun", "tec")

def test_is_relevant_voiture(db_session):
    help_deplacement("voiture")

def test_is_relevant_enfants(db_session):
    r = Recommandation(enfants=True)
    i = Inscription(enfants='oui')
    assert r.is_relevant(i, None, [], 0, date.today())

    r = Recommandation(enfants=True)
    i = Inscription(enfants='non')
    assert not r.is_relevant(i, None, [], 0, date.today())

def test_is_qualite_mauvaise(db_session):
    r = Recommandation(qa_mauvaise=True)
    i = Inscription()
    assert r.is_relevant(i, "mauvais", [], 0, date.today())
    assert not r.is_relevant(i, "bon", [], 0, date.today())

def test_is_qualite_tres_mauvaise(db_session):
    r = Recommandation(qa_mauvaise=True)
    i = Inscription()
    assert r.is_relevant(i, "tres_mauvais", [], 0, date.today())
    assert not r.is_relevant(i, "bon", [], 0, date.today())

def test_is_qualite_extrement_mauvaise(db_session):
    r = Recommandation(qa_mauvaise=True)
    i = Inscription()
    assert r.is_relevant(i, "extrement_mauvais", [], 0, date.today())
    assert not r.is_relevant(i, "bon", [], 0, date.today())

def test_is_qualite_bonne(db_session):
    r = Recommandation(qa_bonne=True)
    i = Inscription()
    assert r.is_relevant(i, "bon", [], 0, date.today())
    assert r.is_relevant(i, "moyen", [], 0, date.today())
    assert not r.is_relevant(i, "extrement_mauvais", [], 0, date.today())

def test_is_qualite_bonne_mauvaise(db_session):
    r = Recommandation(qa_bonne=True, qa_mauvaise=True)
    i = Inscription()
    assert r.is_relevant(i, "bon", [], 0, date.today())
    assert r.is_relevant(i, "moyen", [], 0, date.today())
    assert r.is_relevant(i, "degrade", [], 0, date.today())
    assert r.is_relevant(i, "extrement_mauvais", [], 0, date.today())

def test_is_relevant_ozone(db_session):
    r = Recommandation(ozone=True)
    i = Inscription()
    assert r.is_relevant(i, "bon", ["ozone"], 0, date.today())
    assert r.is_relevant(i, "moyen", ["ozone", "particules_fines"], 0, date.today())
    assert not r.is_relevant(i, "degrade", [], 0, date.today())
    assert not r.is_relevant(i, "degrade", ["particules_fines"], 0, date.today())

def test_is_relevant_particules_fines(db_session):
    r = Recommandation(particules_fines=True)
    i = Inscription()
    assert r.is_relevant(i, "degrade", ["particules_fines"], 0, date.today())
    assert r.is_relevant(i, "moyen", ["ozone", "particules_fines"], 0, date.today())
    assert not r.is_relevant(i, "degrade", [], 0, date.today())
    assert not r.is_relevant(i, "bon", ["ozone"], 0, date.today())

def test_is_relevant_dioxyde_azote(db_session):
    r = Recommandation(dioxyde_azote=True)
    i = Inscription()
    assert r.is_relevant(i, "degrade", ["dioxyde_azote"], 0, date.today())
    assert r.is_relevant(i, "moyen", ["ozone", "dioxyde_azote"], 0, date.today())
    assert not r.is_relevant(i, "degrade", [], 0, date.today())
    assert not r.is_relevant(i, "bon", ["ozone"], 0, date.today())

def test_is_relevant_dioxyde_soufre(db_session):
    r = Recommandation(dioxyde_soufre=True)
    i = Inscription()
    assert r.is_relevant(i, "degrade", ["dioxyde_soufre"], 0, date.today())
    assert r.is_relevant(i, "moyen", ["ozone", "dioxyde_soufre"], 0, date.today())
    assert not r.is_relevant(i, "degrade", [], 0, date.today())
    assert not r.is_relevant(i, "bon", ["ozone"], 0, date.today())

def test_qualite_air_bonne_menage_bricolage(db_session):
    r = Recommandation(menage=True, bricolage=True, qa_bonne=True)

    i = Inscription(activites=["menage"])
    assert r.is_relevant(i, "bon", [], 0, date.today())

    i = Inscription(activites=["bricolage"])
    assert r.is_relevant(i, "bon", [], 0, date.today())

    i = Inscription(activites=["bricolage", "menage"])
    assert r.is_relevant(i, "bon", [], 0, date.today())


def test_reco_pollen_pollution(db_session):
    r = Recommandation(personne_allergique=True)

    i = Inscription(allergie_pollens=False)
    assert not r.is_relevant(i, "bon", ["ozone"], 0, date.today())

    i = Inscription(allergie_pollens=True)
    assert not r.is_relevant(i, "bon", ["ozone"], 0, date.today())

    r = Recommandation(personne_allergique=False)

    i = Inscription(allergie_pollens=False)
    assert not r.is_relevant(i, "bon", ["ozone"], 0, date.today())

    i = Inscription(allergie_pollens=True)
    assert not r.is_relevant(i, "bon", ["ozone"], 0, date.today())

def test_reco_pollen_pas_pollution_raep_nul(db_session):
    r = Recommandation(personne_allergique=True)

    i = Inscription(allergie_pollens=False)
    assert not r.is_relevant(i, "bon", [], 0, date.today())

    i = Inscription(allergie_pollens=True)
    assert not r.is_relevant(i, "bon", [], 0, date.today())

    r = Recommandation(personne_allergique=False)

    i = Inscription(allergie_pollens=False)
    assert r.is_relevant(i, "bon", [], 0, date.today())

    i = Inscription(allergie_pollens=True)
    assert r.is_relevant(i, "bon", [], 0, date.today())

def test_reco_pollen_pas_pollution_raep_faible_atmo_bon(db_session):
    r = Recommandation(personne_allergique=True)

    for delta in range(0, 7):
        date_ = date.today() + timedelta(days=delta)
        i = Inscription(allergie_pollens=False)
        assert not r.is_relevant(i, "bon", [], 1, date_)

        #On veut envoyer le mercredi et le samedi
        i = Inscription(allergie_pollens=True)
        assert r.is_relevant(i, "bon", [], 1, date_) == (date_.weekday() in [2, 5])

def test_reco_pollen_pas_pollution_raep_faible_atmo_mauvais(db_session):
    r = Recommandation(personne_allergique=True)

    for delta in range(0, 7):
        date_ = date.today() + timedelta(days=delta)
        i = Inscription(allergie_pollens=False)
        assert not r.is_relevant(i, "bon", [], 1, date_)

        #On veut envoyer le mercredi et le samedi
        i = Inscription(allergie_pollens=True)
        assert r.is_relevant(i, "bon", [], 1, date_) == (date_.weekday() in [2, 5])

def test_reco_pollen_pas_pollution_raep_eleve_atmo_bon(db_session):
    r = Recommandation(personne_allergique=True)

    for delta in range(0, 7):
        date_ = date.today() + timedelta(days=delta)
        i = Inscription(allergie_pollens=False)
        assert not r.is_relevant(i, "bon", [], 6, date_)

        #On veut envoyer le mercredi et le samedi
        i = Inscription(allergie_pollens=True)
        assert r.is_relevant(i, "bon", [], 6, date_) == (date_.weekday() in [2, 5])

def test_reco_pollen_pas_pollution_raep_eleve_atmo_mauvais(db_session):
    r = Recommandation(personne_allergique=True)

    for delta in range(0, 7):
        date_ = date.today() + timedelta(days=delta)
        i = Inscription(allergie_pollens=False)
        assert not r.is_relevant(i, "bon", [], 6, date_)

        #On veut envoyer le mercredi et le samedi
        i = Inscription(allergie_pollens=True)
        assert r.is_relevant(i, "bon", [], 6, date_) == (date_.weekday() in [2, 5])

def test_chauffage(db_session):
    r = Recommandation(chauffage=[])
    i = Inscription(chauffage=[])
    assert r.is_relevant(i, "bon", [], 0, date.today())

    r = Recommandation(chauffage=[])
    i = Inscription(chauffage=["bois"])
    assert r.is_relevant(i, "bon", [], 0, date.today())

    r = Recommandation(chauffage=["bois"])
    i = Inscription(chauffage=[""])
    assert not r.is_relevant(i, "bon", [], 0, date.today())

    r = Recommandation(chauffage=["bois"])
    i = Inscription(chauffage=["bois"])
    assert r.is_relevant(i, "bon", [], 0, date.today())