$(document).ready(function () {
    ucitajZivotinje();
    ucitajUdomitelje();
    ucitajStatistiku();

    // Dodavanje događaja
    $('#tablica-zivotinja').on('click', '.udomi-btn', function () {
        udomiZivotinju($(this).data('id'));
    });

    $('#tablica-zivotinja').on('click', '.obrisi-zivotinju-btn', function () {
        obrisiZivotinju($(this).data('id'));
    });

    $('#tablica-udomitelja').on('click', '.obrisi-udomitelja-btn', function () {
        obrisiUdomitelja($(this).data('id'));
    });

    $('#tablica-udomitelja').on('click', '.uredi-udomitelja-btn', function () {
        urediUdomitelja($(this).data('id'));
    });

    $('#forma-zivotinja').submit(dodajZivotinju);
    $('#forma-udomitelj').submit(dodajUdomitelja);
});

//ŽIVOTINJE 

function ucitajZivotinje() {
    $.get('http://localhost:8080/zivotinje', function (data) {
        let rows = data.filter(z => z.status === 'u azilu').map(z => {
            let slika = 'https://placehold.co/50x50/f0f0f0/000?text=?';
            if (z.vrsta?.toLowerCase() === 'pas') slika = '/static/img/pas.jpg';
            else if (['mačka', 'macka'].includes(z.vrsta?.toLowerCase())) slika = '/static/img/macka.jpg';

            return `
                <tr>
                    <td><img src="${slika}" alt="${z.vrsta}" style="width: 50px; height: 50px; border-radius: 5px;"></td>
                    <td>${z.ime}</td>
                    <td>${z.vrsta}</td>
                    <td>${z.starost}</td>
                    <td>${z.spol}</td>
                    <td>${z.datum_prijema?.split('T')[0] || ''}</td>
                    <td>${z.status}</td>
                    <td>
                        <button class="btn btn-sm btn-success udomi-btn" data-id="${z.id_zivotinje}">Udomi</button>
                        <button class="btn btn-sm btn-danger obrisi-zivotinju-btn" data-id="${z.id_zivotinje}">Obriši</button>
                    </td>
                </tr>`;
        }).join("");
        $('#tablica-zivotinja tbody').html(rows);
    }).fail(console.error);
}

function dodajZivotinju(e) {
    e.preventDefault();
    let formData = new FormData(this);
    let data = Object.fromEntries(formData);

    for (let key in data) {
        if (!data[key]) return alert('Sva obavezna polja moraju biti popunjena!');
    }

    $.ajax({
        url: 'http://localhost:8080/zivotinje',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function () {
            $('#forma-zivotinja')[0].reset();
            ucitajZivotinje();
            ucitajStatistiku();
        },
        error: function (jqXHR) {
            console.error("Greška prilikom dodavanja životinje:", jqXHR.responseJSON);
            alert('Greška prilikom dodavanja životinje.');
        }
    });
}

function obrisiZivotinju(id) {
    if (!confirm('Jesi li sigurna da želiš obrisati ovu životinju?')) return;
    $.ajax({
        url: `http://localhost:8080/zivotinje/${id}`,
        type: 'DELETE',
        success: function () {
            alert('Životinja obrisana.');
            ucitajZivotinje();
            ucitajStatistiku();
        },
        error: function () {
            alert('Greška pri brisanju životinje.');
        }
    });
}

function udomiZivotinju(id_zivotinje) {
    $.get('http://localhost:8080/udomitelji', function (udomitelji) {
        let popis = udomitelji.map(u => `ID: ${u.id_udomitelja} - ${u.ime} ${u.prezime}`).join('\n');
        const unos = prompt(`Unesite ID udomitelja:\n\n${popis}`);
        if (!unos) return;

        const id = parseInt(unos);
        if (isNaN(id)) return alert("ID mora biti broj.");

        if (!udomitelji.some(u => u.id_udomitelja === id)) {
            return alert("Udomitelj s tim ID-om ne postoji.");
        }

        const payload = {
            status: 'udomljena',
            udomitelj: { id_udomitelja: id },
            datum_udomljenja: new Date().toISOString().split('.')[0]  // ISO bez milisekundi
        };

        $.ajax({
            url: `http://localhost:8080/zivotinje/${id_zivotinje}`,
            type: 'PATCH',
            contentType: 'application/json',
            data: JSON.stringify(payload),
            success: function () {
                alert('Životinja je uspješno udomljena!');
                ucitajZivotinje();
                ucitajUdomitelje();
                ucitajStatistiku();
            },
            error: function (jqXHR) {
                console.error("Greška pri udomljavanju:", jqXHR.responseText || jqXHR.statusText);
                alert('Greška prilikom udomljavanja životinje:\n\n' + (jqXHR.responseText || 'Nepoznata greška'));
            }
        });
    });
}

// UDOMITELJI 

function ucitajUdomitelje() {
    $.get('http://localhost:8080/udomitelji', function (udomitelji) {
        $.get('http://localhost:8080/zivotinje', function (zivotinje) {
            let udomljene = zivotinje.filter(z => z.status === 'udomljena');
            let rows = udomitelji.map(u => {
                let zivotinjeU = udomljene
                    .filter(z => z.udomitelj?.id_udomitelja === u.id_udomitelja)
                    .map(z => `${z.ime} (${z.vrsta}), udomljena: ${z.datum_udomljenja?.split('T')[0] || 'N/A'}`)
                    .join(", ");
                return `
                <tr>
                    <td>${u.id_udomitelja}</td>
                    <td>${u.ime}</td>
                    <td>${u.prezime}</td>
                    <td>${u.kontakt}</td>
                    <td>${zivotinjeU || 'Nema udomljenih životinja'}</td>
                    <td>
                        <button class="btn btn-sm btn-primary uredi-udomitelja-btn" data-id="${u.id_udomitelja}">Uredi</button>
                        <button class="btn btn-sm btn-danger obrisi-udomitelja-btn" data-id="${u.id_udomitelja}">Izbriši</button>
                    </td>
                </tr>`;
            }).join("");
            $('#tablica-udomitelja tbody').html(rows);
        });
    });
}

function dodajUdomitelja(e) {
    e.preventDefault();
    let formData = new FormData(this);
    let data = Object.fromEntries(formData);

    for (let key in data) {
        if (!data[key]) return alert('Sva obavezna polja moraju biti popunjena!');
    }

    $.ajax({
        url: 'http://localhost:8080/udomitelji',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function () {
            $('#forma-udomitelj')[0].reset();
            ucitajUdomitelje();
        },
        error: function (jqXHR) {
            console.error("Greška prilikom dodavanja udomitelja:", jqXHR.responseJSON);
            alert('Greška prilikom dodavanja udomitelja.');
        }
    });
}

function obrisiUdomitelja(id) {
    if (!confirm('Jesi li sigurna da želiš obrisati ovog udomitelja?')) return;
    $.ajax({
        url: `http://localhost:8080/udomitelji/${id}`,
        type: 'DELETE',
        success: function () {
            alert('Udomitelj obrisan.');
            ucitajUdomitelje();
            ucitajZivotinje();
            ucitajStatistiku();
        },
        error: function () {
            alert('Greška pri brisanju udomitelja.');
        }
    });
}

function urediUdomitelja(id) {
    $.get(`http://localhost:8080/udomitelji/${id}`, function (udomitelj) {
        const novoIme = prompt("Novo ime:", udomitelj.ime);
        if (novoIme === null) return;

        const novoPrezime = prompt("Novo prezime:", udomitelj.prezime);
        if (novoPrezime === null) return;

        const noviKontakt = prompt("Novi kontakt:", udomitelj.kontakt);
        if (noviKontakt === null) return;

        $.ajax({
            url: `http://localhost:8080/udomitelji/${id}`,
            type: 'PATCH',
            contentType: 'application/json',
            data: JSON.stringify({
                ime: novoIme,
                prezime: novoPrezime,
                kontakt: noviKontakt
            }),
            success: function () {
                alert('Udomitelj ažuriran.');
                ucitajUdomitelje();
            },
            error: function () {
                alert('Greška pri ažuriranju.');
            }
        });
    });
}

//  STATISTIKA 

function ucitajStatistiku() {
    $.get('http://localhost:8080/zivotinje', function (zivotinje) {
        const udomljene = zivotinje.filter(z => z.status === 'udomljena').length;
        const azil = zivotinje.filter(z => z.status === 'u azilu').length;

        const ctx = document.getElementById('statChart');
        if (!ctx) return;

        const chartData = [udomljene, azil];
        if (window.myChart instanceof Chart) window.myChart.destroy();

        window.myChart = new Chart(ctx.getContext('2d'), {
            type: 'pie',
            data: {
                labels: ['Udomljene', 'U azilu'],
                datasets: [{
                    data: chartData,
                    backgroundColor: ['#36a2eb', '#ffce56']
                }]
            },
            options: {
                plugins: {
                    legend: { position: 'top' },
                    title: { display: true, text: 'Distribucija životinja' },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const perc = ((context.parsed / total) * 100).toFixed(2);
                                return `${context.label}: ${context.parsed} (${perc}%)`;
                            }
                        }
                    }
                }
            }
        });
    });
}
