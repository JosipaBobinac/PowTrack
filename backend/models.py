from pony import orm
from datetime import datetime

db = orm.Database()

class Udomitelj(db.Entity):
    id_udomitelja = orm.PrimaryKey(int, auto=True)
    ime = orm.Required(str)
    prezime = orm.Required(str)
    kontakt = orm.Required(str)
    zivotinje = orm.Set("Zivotinja")

    def to_dict(self):
        return {
            'id_udomitelja': self.id_udomitelja,
            'ime': self.ime,
            'prezime': self.prezime,
            'kontakt': self.kontakt
        }

class Zivotinja(db.Entity):
    id_zivotinje = orm.PrimaryKey(int, auto=True)
    ime = orm.Required(str)
    vrsta = orm.Required(str)
    starost = orm.Required(int)
    spol = orm.Required(str)
    datum_prijema = orm.Required(datetime)
    status = orm.Required(str)
    datum_udomljenja = orm.Optional(datetime)
    udomitelj = orm.Optional(Udomitelj)


    def to_dict(self):
        return {
            'id_zivotinje': self.id_zivotinje,
            'ime': self.ime,
            'vrsta': self.vrsta,
            'starost': self.starost,
            'spol': self.spol,
            'datum_prijema': self.datum_prijema.isoformat(),
            'status': self.status,
            'datum_udomljenja': self.datum_udomljenja.isoformat() if self.datum_udomljenja else None,
            'udomitelj': self.udomitelj.to_dict() if self.udomitelj else None
        }
