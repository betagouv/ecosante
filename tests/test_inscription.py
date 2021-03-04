from ecosante.inscription.models import Inscription

def test_inscription(client):
    data = {
        'ville_entree': 'Marcillé-la-ville',
        'mail': 'lala@example.com',
        'diffusion': 'mail',
        'frequence': 'quotidien',
        'rgpd': 'true'
    }
    response = client.post('/inscription/', data=data)
    assert response.status_code == 302
    assert response.location == 'http://localhost:5000/inscription/personnalisation'

    data = {
        "deplacement": "velo",
        "activites": ["jardinage"],
        "enfants": "true",
        "pathologie_respiratoire": "true",
        "allergie_pollen": "true",
    }
    response = client.post('/inscription/personnalisation', data=data)
    assert response.status_code == 302
    assert response.location == 'http://localhost:5000/inscription/reussie'


def test_inscription_multi_etapes(client):
    data = {'mail': 'dodo@example.com'}
    response = client.post('/inscription/premiere-etape', data=data)
    assert response.status_code == 201
    uid = response.json['uid']

    data = {
        'ville_insee': '53130',
        'deplacement': ['velo', 'tec'],
        'activites': ['jardinage'],
        'pathologie_respiratoire': 'non',
        'allergie_pollen': 'oui'
    }
    response = client.put(f'/inscription/{uid}/', data=data)
    assert response.status_code == 200

    inscription = Inscription.query.filter_by(uid=uid).first()

    assert inscription
    assert inscription.mail == 'dodo@example.com'
    assert inscription.diffusion == 'mail'
    assert inscription.frequence == 'quotidien'
    assert inscription.ville_insee == '53130'
    assert inscription.deplacement == ['velo', 'tec']
    assert inscription.activites == ['jardinage']
    assert inscription.allergie_pollen == True
