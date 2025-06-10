<template>
    <div v-if="visible" class="popup-overlay">
        <div class="popup-content">
            <h2>Søkeresultater</h2>

            <div v-if="results.length === 0">
                <p>Ingen resultater her ennå.</p>
            </div>

            <div v-for="group in paginatedResults" :key="group.Org_nr" class="result-card">
                <h3>{{ group.Firmanavn }} ({{ group.Org_nr }})</h3>

                <label :for="'emailSelect-' + group.Org_nr">Velg e-post:</label>
                <select :id="'emailSelect-' + group.Org_nr"
                        v-model="selectedEmails[group.Org_nr]">
                    <option v-for="email in group.emails" :key="email" :value="email">{{ email }}</option>
                </select>

                <button @click="updateEmail(group.Org_nr, selectedEmails[group.Org_nr])">
                    💾 Oppdater valgt e-post
                </button>
                <button @click="confirmDiscard(group.Org_nr)" :disabled="loadingOrgNr === group.Org_nr">
                    <span v-if="loadingOrgNr === group.Org_nr">⏳ Forkaster...</span>
                    <span v-else>🗑 Forkast</span>
                </button>
                <div v-if="confirmingOrgNr === group.Org_nr" class="confirm-dialog">
                    <p>Er du sikker på at du vil forkaste resultatet for org.nr {{ confirmingOrgNr }}?</p>
                    <button @click="discardConfirmed">Ja</button>
                    <button @click="cancelConfirmation">Nei</button>
                </div>
            </div>
            <!-- 🔽 PAGINERING -->
            <div class="pagination">
                <button @click="currentPage--" :disabled="currentPage === 1">Forrige</button>
                <span>Side {{ currentPage }} av {{ totalPages }}</span>
                <button @click="currentPage++" :disabled="currentPage === totalPages">Neste</button>
            </div>

            <button @click="$emit('close')">Lukk</button>
        </div>
    </div>
</template>

<script>
    import axios from 'axios';

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
                selectedEmails: {},
                confirmingOrgNr: null,
                loadingOrgNr: null,
                currentPage: 1,
                itemsPerPage: 10,
            };
        },
        watch: {
            visible(newVal) {
                if (newVal) {
                    this.fetchEmailResults();
                }
            }
        },
        computed: {
            groupedResults() {
                const map = {};
                this.results.forEach(result => {
                    const key = result.Org_nr;
                    if (!map[key]) {
                        map[key] = {
                            Firmanavn: result.Firmanavn,
                            Org_nr: key,
                            emails: []
                        };
                    }
                    // Only add .no emails
                    if (!map[key].emails.includes(result.email) && result.email.toLowerCase().endsWith('.no')) {
                        map[key].emails.push(result.email);
                    }
                });
                return Object.values(map);
            },
            paginatedResults() {
                const start = (this.currentPage - 1) * this.itemsPerPage;
                const end = start + this.itemsPerPage;
                return this.groupedResults.slice(start, end);
            },
            totalPages() {
                return Math.ceil(this.groupedResults.length / this.itemsPerPage);
            }
        },
        methods: {
            async fetchEmailResults() {
                try {
                    const response = await axios.get("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/SearchResultHandler/get_email_results");
                    console.log('Email results from API:', response.data);
                    this.results = response.data;

                    // Sett default valgt e-post for hver org.nr til første e-post i gruppen
                    this.selectedEmails = {};
                    this.groupedResults.forEach(group => {
                        if (group.emails.length > 0) {
                            this.selectedEmails[group.Org_nr] = group.emails[0];
                        }
                    });
                } catch (error) {
                    console.error('Error fetching email results:', error);
                    alert('Kunne ikke hente e-postresultater.');
                }
            },
            async updateEmail(orgNr, email) {
                try {
                    const response = await fetch('https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/SearchResultHandler/update_email', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            Org_nr: orgNr,
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
                    console.error('Error updating email:', error);
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
                    const response = await fetch('https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/SearchResultHandler/delete_stored_result', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ org_nr: orgNr })
                    });

                    const data = await response.json();

                    if (!response.ok) {
                        alert(data.status || 'Sletting feilet.');
                        return;
                    }

                    // Remove the item from the results array
                    this.results = this.results.filter(result => result.Org_nr !== orgNr);
                    
                    // Remove from selectedEmails if it exists
                    if (this.selectedEmails[orgNr]) {
                        delete this.selectedEmails[orgNr];
                    }

                    // Reset to first page if current page is empty
                    if (this.paginatedResults.length === 0 && this.currentPage > 1) {
                        this.currentPage = 1;
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
        position: fixed;
        top: 50%;
        left: 50%;
        width: 75vw;
        height: 75vh;
        transform: translate(-50%, -50%);
        background: rgba(0, 0, 0, 0.5);
        z-index: 999;
        display: flex;
        justify-content: center;
        align-items: center;
        border-radius: 12px;
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
        color: #000;
    }

    .confirm-dialog {
        background: #ffe9e9;
        padding: 10px;
        border: 1px solid #cc0000;
        margin: 10px 0;
        color: #000;
    }
    .pagination {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
        margin-top: 1rem;
    }
</style>
