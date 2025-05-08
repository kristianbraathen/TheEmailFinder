<template>
    <div v-if="visible" class="popup-overlay">
        <div class="popup-content">
            <h2>Søkeresultater</h2>
            <!-- Show message if no results -->
            <div v-if="results.length === 0">
                <p>Ingen resultater her ennå.</p>
            </div>

            <div v-for="result in results" :key="result.Org_nr" class="result-card">
                <h3>{{ result.company_name }} ({{ result.Org_nr }})</h3>

                <!-- Update email -->
                <input v-model="result.email"
                       :placeholder="'Email: ' + result.email"
                       @blur="updateEmail(result.Org_nr, result.email)"
                       type="email" />

                <ul>
                    <li v-for="email in result.email" :key="email">{{ email }}</li>
                </ul>

                <button @click="confirmDiscard(result.Org_nr)" :disabled="loadingOrgNr === result.Org_nr">
                    <span v-if="loadingOrgNr === result.Org_nr">⏳ Forkaster...</span>
                    <span v-else>🗑 Forkast</span>
                </button>
            </div>

            <div v-if="confirmingOrgNr" class="confirm-dialog">
                <p>Er du sikker på at du vil forkaste resultatet for org.nr {{ confirmingOrgNr }}?</p>
                <button @click="discardConfirmed">Ja</button>
                <button @click="cancelConfirmation">Nei</button>
            </div>

            <button @click="$emit('close')">Lukk</button>
        </div>
    </div>
</template>

<script>
    export default {
        name: 'SearchResultsPopup',
        props: {
            visible: {
                type: Boolean,
                required: true
            }
        },
        data() {
            return {
                results: [],
                confirmingOrgNr: null,
                loadingOrgNr: null
            };
        },
        watch: {
            visible(newVal) {
                if (newVal) {
                    this.fetchEmailResults();
                }
            }
        },
        methods: {
            async fetchEmailResults() {
                try {
                    const response = await fetch('/get-email-results');
                    if (!response.ok) {
                        throw new Error('Feil ved henting av e-postresultater');
                    }
                    const results = await response.json();
                    this.results = results;
                } catch (error) {
                    console.error(error);
                    alert('Kunne ikke hente e-postresultater.');
                }
            },
            async updateEmail(orgNr, email) {
                try {
                    const response = await fetch('/update_email', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            org_nr: orgNr,
                            email: email
                        })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        alert(data.status);
                    } else {
                        alert(data.error || 'Feil ved oppdatering av e-post.');
                    }
                } catch (error) {
                    console.error(error);
                    alert('Nettverksfeil ved oppdatering av e-post.');
                }
            },
            confirmDiscard(orgNr) {
                this.confirmingOrgNr = orgNr;
            },
            cancelConfirmation() {
                this.confirmingOrgNr = null;
            },
            async discardConfirmed() {
                const orgNr = this.confirmingOrgNr;
                this.loadingOrgNr = orgNr;

                try {
                    const response = await fetch('/delete_stored_result', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ org_nr: orgNr })
                    });

                    const data = await response.json();

                    if (!response.ok) {
                        alert(data.status || 'Sletting feilet.');
                        return;
                    }

                    this.$emit('updateResults', orgNr);
                } catch (error) {
                    alert('Nettverksfeil under sletting.');
                    console.error(error);
                } finally {
                    this.loadingOrgNr = null;
                    this.confirmingOrgNr = null;
                }
            }
        }
    };
</script>
 
<style scoped>
    .popup-overlay {
        position: absolute; /* Absolutt posisjonering i forhold til popupen */
        top: 0; /* Plasserer overlayen fra toppen */
        left: 0;
        width: 100%;
        height: 100%; /* Dekker hele bredden og høyden */
        background: rgba(0, 0, 0, 0.5); /* Halvgjennomsiktig bakgrunn */
        z-index: 999; /* Overlayen er under popupen */
        transition: opacity 0.3s ease; /* Smooth fade-in for bakgrunn */
    }

    .popup-content {
        position: absolute; /* Popupen plasseres over overlayen */
        top: 50%; /* Vertikal sentrering i forhold til overlayen */
        left: 50%; /* Horisontal sentrering i forhold til overlayen */
        transform: translate(-50%, -50%); /* Justering for popupens egen størrelse */
        z-index: 1000; /* Popupen er på toppen av overlayen */
        font-family: Arial, sans-serif;
        background-color: #121212; /* Mørk bakgrunn */
        color: #e0e0e0; /* Lys tekst for kontrast */
        padding: 20px;
        max-width: 600px;
        width: 90%; /* Gir litt luft på sidene */
        max-height: 80%; /* Begrens høyden */
        overflow-y: auto; /* Legg til rull hvis innholdet er for langt */
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }


    .result-card {
        background: #f2f2f2;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 10px;
    }

    .confirm-dialog {
        background: #ffe9e9;
        padding: 10px;
        border: 1px solid #cc0000;
        margin: 10px 0;
    }
</style>
