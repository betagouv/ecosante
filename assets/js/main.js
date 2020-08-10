const OUI = `Oui`;
const NON = `Non`;

const INPUT_ALLERGIQUE_COLUMN_NAME = 'Êtes-vous allergique aux pollens (graminées, ambroisie, etc.) ?'
const OUTPUT_ALLERGIQUE_COLUMN_NAME = 'Allergies'

const INPUT_EMAIL_COLUMN_NAME = 'Adresse e-mail'
const OUTPUT_EMAIL_COLUMN_NAME = 'Mail'

const INPUT_REGION_COLUMN_NAME = 'Région'
const OUTPUT_REGION_COLUMN_NAME = INPUT_REGION_COLUMN_NAME

const INPUT_VILLE_COLUMN_NAME = 'Ville'
const OUTPUT_VILLE_COLUMN_NAME = INPUT_VILLE_COLUMN_NAME

const INPUT_PATHOLOGIE_RESPIRATOIRE_COLUMN_NAME = `Vivez-vous avec une pathologie respiratoire ?`
const OUTPUT_PATHOLOGIE_RESPIRATOIRE_COLUMN_NAME = `Pathologie_respiratoire`;

const INPUT_ACTIVITE_SPORTIVE_COLUMN_NAME = `Pratiquez-vous une activité sportive ? `
const OUTPUT_ACTIVITE_SPORTIVE_COLUMN_NAME = `Activité_sportive`

const INPUT_TRANSPORT_COLUMN_NAME = `Quel(s) moyen(s) de transport utilisez-vous pour vos déplacements ?`
const OUTPUT_CYCLISTE_COLUMN_NAME = `Cycliste`
const OUTPUT_AUTOMOBILISTE_COLUMN_NAME = `Automobiliste`

const INPUT_FUMEUR_COLUMN_NAME = `Êtes-vous fumeur.euse (cigarette, cigare, cigarette électronique) ?`
const OUTPUT_FUMEUR_COLUMN_NAME = `Fumeur`

const INPUT_CANAL_COLUMN_NAME = `Souhaitez-vous recevoir les recommandations Ecosanté par :`
const OUTPUT_CANAL_COLUMN_NAME = `Format`
const CANAL_EMAIL = 'Mail'
const CANAL_SMS = 'SMS'

const INPUT_PHONE_NUMBER_COLUMN_NAME = `Si vous avez choisi par SMS ou WhatsApp, veuillez renseigner votre numéro de téléphone`
const OUTPUT_PHONE_NUMBER_COLUMN_NAME = `Téléphone`

const INPUT_FREQUENCY_COLUMN_NAME = `A quelle fréquence souhaitez-vous recevoir les notifications ? `
const OUTPUT_FREQUENCY_COLUMN_NAME = `Fréquence`


const OUTPUT_QUALITE_AIR_COLUMN_NAME = `Qualité de l'air`

function makeSendingRow(row){
    const sendingRow = Object.create(null);
    const TODAY_DATE_STRING = (new Date()).toISOString().slice(0, 10)

    const ville = row[INPUT_VILLE_COLUMN_NAME].trim();
    return d3.json(`https://geo.api.gouv.fr/communes?nom=${ville}&boost=population&limit=1`)
    .then(geoResult => {
        const {code: codeINSEE} = geoResult[0];

        return d3.json(`http://app-6ccdcc10-da92-47b1-add6-59d8d3914d79.cleverapps.io/forecast?insee=${codeINSEE}`)
        .then(apiQAResult => {
            if(apiQAResult.length === 0)
                throw new Error('Pas trouvé !')

            return apiQAResult.find(res => res.date === TODAY_DATE_STRING)
        })
        .catch(err => {
            console.warn(`Pas d'information de qualité de l'air pour`, codeINSEE, ville, row, err)
        })
    })
    .catch(err => {
        console.warn('Code INSEE pour', ville, 'non trouvé', row, err)
    })
    .then(indiceATMODate => {
        //console.log('indiceATMODate', indiceATMODate, ville)
        const {qualif} = indiceATMODate || {}

        sendingRow[OUTPUT_EMAIL_COLUMN_NAME] = row[INPUT_EMAIL_COLUMN_NAME].trim()
        sendingRow[OUTPUT_REGION_COLUMN_NAME] = row[INPUT_REGION_COLUMN_NAME].trim()
        sendingRow[OUTPUT_VILLE_COLUMN_NAME] = ville
        if(qualif)
            sendingRow[OUTPUT_QUALITE_AIR_COLUMN_NAME] = qualif
        sendingRow[OUTPUT_PATHOLOGIE_RESPIRATOIRE_COLUMN_NAME] = row[INPUT_PATHOLOGIE_RESPIRATOIRE_COLUMN_NAME].trim()
        sendingRow[OUTPUT_ALLERGIQUE_COLUMN_NAME] = row[INPUT_ALLERGIQUE_COLUMN_NAME].trim().slice(0, 3)
        sendingRow[OUTPUT_ACTIVITE_SPORTIVE_COLUMN_NAME] = row[INPUT_ACTIVITE_SPORTIVE_COLUMN_NAME].trim() === NON ? NON : OUI;
        sendingRow[OUTPUT_CYCLISTE_COLUMN_NAME] = row[INPUT_TRANSPORT_COLUMN_NAME].includes('Vélo') ? OUI : NON;
        sendingRow[OUTPUT_AUTOMOBILISTE_COLUMN_NAME] = row[INPUT_TRANSPORT_COLUMN_NAME].includes('Voiture') ? OUI : NON;
        sendingRow[OUTPUT_FUMEUR_COLUMN_NAME] = row[INPUT_FUMEUR_COLUMN_NAME].trim()

        const canal = row[INPUT_CANAL_COLUMN_NAME].trim();
        sendingRow[OUTPUT_CANAL_COLUMN_NAME] = [CANAL_EMAIL, CANAL_SMS].includes(canal) ? canal : '?'

        sendingRow[OUTPUT_PHONE_NUMBER_COLUMN_NAME] = row[INPUT_PHONE_NUMBER_COLUMN_NAME].trim()
        sendingRow[OUTPUT_FREQUENCY_COLUMN_NAME] = row[INPUT_FREQUENCY_COLUMN_NAME].trim()
        
        return sendingRow;
    })
}


function makeSendingCSV(file){
    
    return (new Promise( (resolve, reject) => {
        const reader = new FileReader();  
        reader.addEventListener("loadend", e => {
            resolve(reader.result);
        });
        reader.readAsText(file);
    }))
    .then(textContent => {
        const content = d3.csvParse(textContent)//.slice(0, 10)

        //console.log('input file', file, content)

        return Promise.all(content.map(makeSendingRow))
        .then(sendingContent => d3.csvFormat(sendingContent))
    })
    
}

document.addEventListener('DOMContentLoaded', e => {
    const input = document.body.querySelector('.input input[type="file"]');
    const output = document.body.querySelector('.output');

    input.addEventListener('change', e => {
        // replace <input> with list of files
        const file = e.target.files[0];

        const sendingCSVTextP = makeSendingCSV(file)
        
        sendingCSVTextP.then(sendingCSVText => {
            //console.log('output', sendingCSVText)

            const name = "fichier de sortie écosanté.csv"

            const blob = new Blob([sendingCSVText], {type: 'text/csv'});
            const blobUrl = URL.createObjectURL(blob);
            const outputFileLink = document.createElement('a');
            
            outputFileLink.setAttribute('href', blobUrl);
            outputFileLink.setAttribute('download', name);
            outputFileLink.textContent = name;

            output.append(outputFileLink)
        })
    })


}, {once: true})