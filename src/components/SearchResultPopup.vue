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
                    const response = await axios.get("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/SearchResultHandler/get_email_results");
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
                    const response = await fetch('https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/update_email', {
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
                    const response = await fetch('https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/delete_stored_result', {
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
        position: fixed; /* Fixed positioning to cover the entire viewport */
        top: 50%;
        left: 50%;
        width: 75%;
        height: 75%;
        background: rgba(0, 0, 0, 0.5); /* Semi-transparent background */
        z-index: 999;
        display: flex; /* Flexbox for centering */
        justify-content: center; /* Horizontal centering */
        align-items: center; /* Vertical centering */
    }

    .popup-content {
        position: relative; /* Relative to the flex container */
        background-color: #121212; /* Dark background */
        color: #e0e0e0; /* Light text for contrast */
        padding: 20px;
        max-width: 600px; /* Limit the width */
        width: 90%; /* Adjust width for smaller screens */
        max-height: 80%; /* Limit the height */
        overflow-y: auto; /* Add scroll if content overflows */
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        font-family: Arial, sans-serif;
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
