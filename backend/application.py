from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pony.orm import db_session, select
from models import db, Zivotinja, Udomitelj
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')


# PONY ORM KONFIGURACIJA 
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "database.sqlite")

db.bind(provider='sqlite', filename=db_path, create_db=True)
db.generate_mapping(create_tables=True)



@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "api": "PowTrack backend radi.",
        "koristi": [
            "/zivotinje (GET, POST, PUT, PATCH, DELETE)",
            "/udomitelji (GET, POST, PUT, PATCH, DELETE)",
            "/statistika"
        ],
        "status": "OK"
    })

# CRUD ŽIVOTINJA 

@app.route('/zivotinje', methods=['GET'])
@db_session
def get_zivotinje():
    zivotinje = list(Zivotinja.select())
    return jsonify([z.to_dict() for z in zivotinje])

@app.route('/zivotinje', methods=['POST'])
@db_session
def dodaj_zivotinju():
    """
    Dodaje jednu ili više novih životinja u bazu podataka.
    Očekuje JSON objekt za jednu životinju ili listu JSON objekata za više životinja.
    """
    input_data = request.get_json(force=True)
    
    # Provjerava je li ulaz lista ili pojedinačni objekt
    if isinstance(input_data, list):
        animals_to_add = input_data
    else:
        animals_to_add = [input_data] # Pretvara pojedinačni objekt u listu radi unificirane obrade

    added_animals = []
    errors = []
    
    fields = ('ime', 'vrsta', 'starost', 'spol', 'datum_prijema', 'status')

    for data in animals_to_add:
        try:
            # Provjeravamo jesu li svi obavezni podaci prisutni za svaku životinju
            if not all(field in data for field in fields):
                raise ValueError('Nedostaje neki obavezni podatak za životinju.')

            # Provjera i parsiranje datuma prijema
            datum_prijema = datetime.fromisoformat(data['datum_prijema'])

            # Parsiranje datuma udomljenja (ako postoji)
            datum_udomljenja = None
            if data.get('datum_udomljenja'):
                datum_udomljenja = datetime.fromisoformat(data['datum_udomljenja'])

            # Pronalaženje udomitelja ako je ID udomitelja poslan
            udomitelj = None
            if data.get('id_udomitelja'):
                udomitelj = Udomitelj.get(id_udomitelja=data['id_udomitelja'])
                if not udomitelj:
                    raise ValueError(f'Traženi udomitelj s ID {data["id_udomitelja"]} ne postoji!')

            # Kreiranje novog entiteta Zivotinja
            z = Zivotinja(
                ime = data['ime'],
                vrsta = data['vrsta'],
                starost = int(data['starost']), 
                spol = data['spol'],
                datum_prijema = datum_prijema,
                status = data['status'],
                datum_udomljenja = datum_udomljenja,
                udomitelj = udomitelj
            )
            added_animals.append(z.to_dict())
        except ValueError as e:
            errors.append({'data': data, 'error': str(e)})
        except Exception as e:
            errors.append({'data': data, 'error': f'Neočekivana greška: {str(e)}'})

    if errors:
        # Ako ima grešaka, vraćamo 400 i listu grešaka s podacima koji su ih uzrokovali
        db.rollback() # Vraćamo sve promjene u ovoj transakciji ako ima grešaka
        return jsonify({'message': 'Neke životinje nisu dodane zbog grešaka.', 'added_count': len(added_animals), 'errors': errors, 'added_animals': added_animals}), 400
    else:
        # Ako nema grešaka, sve je uspješno dodano
        return jsonify({'message': f'Uspješno dodano {len(added_animals)} životinja.', 'added_animals': added_animals}), 201


@app.route('/zivotinje/<int:id>', methods=['GET'])
@db_session
def get_zivotinja(id):
    z = Zivotinja.get(id_zivotinje=id)
    if z:
        return jsonify(z.to_dict())
    return jsonify({'error': 'Životinja ne postoji'}), 404

@app.route('/zivotinje/<int:id>', methods=['PUT'])
@db_session
def azuriraj_zivotinju(id):
    """
    Ažurira postojeću životinju po ID-u (PUT metoda - potpuna zamjena ili djelomično ažuriranje).
    """
    data = request.get_json(force=True)
    z = Zivotinja.get(id_zivotinje=id)
    if not z:
        return jsonify({'error': 'Životinja ne postoji'}), 404
    
    for key, value in data.items():
        if key in ("datum_prijema", "datum_udomljenja") and value:
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return jsonify({'error': f'Pogrešan format datuma za {key}! Očekuje se ISO format.'}), 400
        elif key == "udomitelj" and value is not None:
            # Rukovanje s objektom udomitelja ili samo s ID-em
            if isinstance(value, dict) and 'id_udomitelja' in value:
                udomitelj_id = value['id_udomitelja']
                u = Udomitelj.get(id_udomitelja=udomitelj_id)
                if not u:
                    return jsonify({'error': f'Udomitelj s ID-em {udomitelj_id} ne postoji!'}), 400
                value = u
            elif isinstance(value, int):
                u = Udomitelj.get(id_udomitelja=value)
                if not u:
                    return jsonify({'error': 'Udomitelj s tim ID-em ne postoji!'}), 400
                value = u
            elif value is None:
                value = None
            else:
                return jsonify({'error': 'Invalidan format za udomitelja. Očekuje se ID, null ili objekt udomitelja s ID-em.'}), 400
        
        if hasattr(z, key):
            setattr(z, key, value)
    return jsonify(z.to_dict())

@app.route('/zivotinje/<int:id>', methods=['PATCH'])
@db_session
def djelomicno_azuriraj_zivotinju(id):
    """
    Djelomično ažurira postojeću životinju po ID-u (PATCH metoda).
    """
    data = request.get_json(force=True)
    z = Zivotinja.get(id_zivotinje=id)
    if not z:
        return jsonify({'error': 'Životinja ne postoji'}), 404
    
    for key, value in data.items():
        if key in ("datum_prijema", "datum_udomljenja") and value:
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return jsonify({'error': f'Pogrešan format datuma za {key}! Očekuje se ISO format.'}), 400
        elif key == "udomitelj" and value is not None:
            # Rukovanje s objektom udomitelja ili samo s ID-em
            if isinstance(value, dict) and 'id_udomitelja' in value:
                udomitelj_id = value['id_udomitelja']
                u = Udomitelj.get(id_udomitelja=udomitelj_id)
                if not u:
                    return jsonify({'error': f'Udomitelj s ID-em {udomitelj_id} ne postoji!'}), 400
                value = u
            elif isinstance(value, int):
                u = Udomitelj.get(id_udomitelja=value)
                if not u:
                    return jsonify({'error': 'Udomitelj s tim ID-em ne postoji!'}), 400
                value = u
            elif value is None:
                value = None
            else:
                return jsonify({'error': 'Invalidan format za udomitelja. Očekuje se ID, null ili objekt udomitelja s ID-em.'}), 400
        
        if hasattr(z, key):
            setattr(z, key, value)
    return jsonify(z.to_dict())


@app.route('/zivotinje/<int:id>', methods=['DELETE'])
@db_session
def obrisi_zivotinju(id):
    z = Zivotinja.get(id_zivotinje=id)
    if not z:
        return jsonify({'error': 'Životinja ne postoji'}), 404
    z.delete()
    return jsonify({'message': 'Životinja obrisana.'}), 204

# CRUD UDOMITELJ

@app.route('/udomitelji', methods=['GET'])
@db_session
def get_udomitelji():
    udomitelji = list(Udomitelj.select())
    return jsonify([u.to_dict() for u in udomitelji])

@app.route('/udomitelji', methods=['POST'])
@db_session
def dodaj_udomitelja():
    """
    Dodaje jednog ili više novih udomitelja u bazu podataka.
    """
    input_data = request.get_json(force=True)
    
    # Provjerava je li ulaz lista ili pojedinačni objekt
    if isinstance(input_data, list):
        adopters_to_add = input_data
    else:
        adopters_to_add = [input_data] # Pretvara pojedinačni objekt u listu radi unificirane obrade

    added_adopters = []
    errors = []
    
    fields = ('ime', 'prezime', 'kontakt') # Obavezna polja za Udomitelja

    for data in adopters_to_add:
        try:
            # Stvaramo rječnik samo s poljima koja su potrebna za konstruktor Udomitelja.
            adopter_data = {field: data[field] for field in fields if field in data}

            # Provjeravamo jesu li svi obavezni podaci prisutni u filtriranim podacima
            if not all(field in adopter_data for field in fields):
                raise ValueError('Nedostaje neki obavezni podatak za udomitelja (ime, prezime, kontakt).')

            # Kreiranje novog entiteta Udomitelj
            u = Udomitelj(**adopter_data)
            added_adopters.append(u.to_dict())
        except ValueError as e:
            errors.append({'data': data, 'error': str(e)})
        except Exception as e:
            errors.append({'data': data, 'error': f'Neočekivana greška: {str(e)}'})

    if errors:
        # Ako ima grešaka, vraćamo 400 i listu grešaka s podacima koji su ih uzrokovali
        db.rollback() 
        return jsonify({'message': 'Neki udomitelji nisu dodani zbog grešaka.', 'added_count': len(added_adopters), 'errors': errors, 'added_adopters': added_adopters}), 400
    else:
        # Ako nema grešaka, sve je uspješno dodano
        return jsonify({'message': f'Uspješno dodano {len(added_adopters)} udomitelja.', 'added_adopters': added_adopters}), 201


@app.route('/udomitelji/<int:id>', methods=['GET'])
@db_session
def get_udomitelj(id):
    u = Udomitelj.get(id_udomitelja=id)
    if u:
        return jsonify(u.to_dict())
    return jsonify({'error': 'Udomitelj ne postoji'}), 404

@app.route('/udomitelji/<int:id>', methods=['PUT'])
@db_session
def azuriraj_udomitelja(id):
    """
    Ažurira postojećeg udomitelja po ID-u.
    """
    data = request.get_json(force=True)
    u = Udomitelj.get(id_udomitelja=id)
    if not u:
        return jsonify({'error': 'Udomitelj ne postoji'}), 404
    for key, value in data.items():
        if hasattr(u, key):
            setattr(u, key, value)
    return jsonify(u.to_dict())

@app.route('/udomitelji/<int:id>', methods=['PATCH'])
@db_session
def djelomicno_azuriraj_udomitelja(id):
    """
    Djelomično ažurira postojećeg udomitelja po ID-u (PATCH metoda).
    """
    data = request.get_json(force=True)
    u = Udomitelj.get(id_udomitelja=id)
    if not u:
        return jsonify({'error': 'Udomitelj ne postoji'}), 404
    for key, value in data.items():
        if hasattr(u, key):
            setattr(u, key, value)
    return jsonify(u.to_dict())


@app.route('/udomitelji/<int:id>', methods=['DELETE'])
@db_session
def obrisi_udomitelja(id):
    u = Udomitelj.get(id_udomitelja=id)
    if not u:
        return jsonify({'error': 'Udomitelj ne postoji'}), 404
    
    # Postavi udomitelj = None za sve povezane životinje
    for zivotinja in u.zivotinje:
        zivotinja.udomitelj = None

    u.delete()
    return jsonify({'message': 'Udomitelj obrisan.'}), 204

# STATISTIKA

@app.route('/statistika', methods=['GET'])
@db_session
def statistika():
    ukupno_zivotinja = Zivotinja.select().count()
    po_vrstama = {}
    for z in select(z for z in Zivotinja):
        po_vrstama[z.vrsta] = po_vrstama.get(z.vrsta, 0) + 1

    ukupno_udomljene = select(z for z in Zivotinja if z.status == 'udomljena').count()
    ukupno_azil = select(z for z in Zivotinja if z.status == 'u azilu').count()
    
    return jsonify({
        'ukupno_zivotinja': ukupno_zivotinja,
        'po_vrstama': po_vrstama,
        'ukupno_udomljene': ukupno_udomljene,
        'ukupno_azil': ukupno_azil
    })

if __name__ == '__main__':
    app.run(port=8080, debug=True)
