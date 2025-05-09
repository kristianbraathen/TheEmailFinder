<template>
    <div v-if="isVisible" class="popup-overlay">
        <div class="popup-content">
            <h2>Finn e-poster fra Facebook</h2>
            <button @click="handleButtonClick">Start Prosessen</button>

            <!-- Check if there are companies -->
            <div class="emailresults" v-if="companies && companies.length">
                <div v-if="currentCompanyIndex < companies.length">
                    <h3>{{ companies[currentCompanyIndex].company_name }}</h3>
                    <p><strong>Org.nr:</strong> {{ companies[currentCompanyIndex].org_nr }}</p>
                    <p><strong>Søkestreng:</strong> {{ companies[currentCompanyIndex].query }}</p>

                    <ul>
                        <li v-for="email in companies[currentCompanyIndex].emails" :key="email">
                            {{ email }}
                            <button @click="selectEmail(companies[currentCompanyIndex].org_nr, email)">Velg</button>
                        </li>
                    </ul>

                    <!-- Navigation -->
                    <button @click="discardAndNextCompany">Forkast og gå til Neste Bedrift</button>
                </div>
                <p v-else>Alle selskaper er behandlet.</p>
            </div>

            <!-- Show currentSearchQuery when process is ongoing -->
            <div v-if="processRunning">
                <p>{{ currentSearchQuery }}</p>  <!-- Vise gjeldende søkestatus -->
            </div>
            <p v-else>
                
            </p>
            <!-- Control Buttons -->
            <div class="control-buttons">
                <button @click="stopProcess">Stopp Prosessen</button>
                <button @click="closePopup">Lukk</button>
            </div>
        </div>
    </div>
</template>


<script>
    import axios from "axios";

    export default {
        props: {
            isVisible: Boolean, // Controls visibility of popup
        },
        data() {
            return {
                companies: [], // Array to store companies
                currentCompanyIndex: 0, // Tracks the current company being displayed
                currentSearchQuery: 'Klikk "Start Prosessen" for å begynne.',
                processRunning: false,
                processMessage: '',
            };
        },
        methods: {
            async handleButtonClick() {
                try {
                    // Start prosessen
                    await this.startProcess(); // Starter prosessen
                    // Hent selskaper etter at prosessen er startet
                    await this.fetchCompanies();
                    
                } catch (error) {
                    console.error("Feil under knappetrykk:", error);
                }
            },
            async fetchCompanies() {
                try {

                    await axios.post("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/SearchResultHandler/initialize-email-results");

                    const response = await axios.get("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/KseApi/search_emails");
                    this.companies = Array.isArray(response.data) ? response.data : [];
                    this.processRunning = true;

                } catch (error) {
                    console.error("Feil under henting av selskaper:", error);
                }
            },
            async fetchStoredCompanies() {
                try {
                    const response = await axios.get("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/SearchResultHandler/get_email_results");
                    this.companies = Array.isArray(response.data) ? response.data : [];
                    this.processRunning = true;
                } catch (error) {
                    console.error("Feil under henting av lagrede selskaper:", error);
                }
            },
            // Select an email and send it to the backend
            async selectEmail(orgNr, email) {
                try {
                    const response = await axios.post("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/KseApi/update_email", {
                        org_nr: orgNr,
                        email: email,
                    });
                    alert(response.data.status || "E-post oppdatert!");
                } catch (error) {
                    console.error("Feil under oppdatering:", error);
                }
            },
            async discardCompany(orgNr) {
                try {
                    const response = await axios.post("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/KseApi/delete_stored_result", {
                        org_nr: orgNr
                    });
                    alert(response.data.status);
                    this.nextCompany();
                } catch (error) {
                    console.error("Feil ved forkasting:", error);
                }
            },
            // Move to the next company
            async discardAndNextCompany() {
                const orgNr = this.companies[this.currentCompanyIndex]?.org_nr;
                if (!orgNr) return;

                try {
                    await this.discardCompany(orgNr); // Forkast i backend
                    this.nextCompany();               // Gå videre i listen
                } catch (error) {
                    console.error("Feil under forkasting og henting av neste:", error);
                }
            },

            async startProcess() {
                if (!this.processRunning) {
                    try {
                        const response = await axios.post("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/KseApi/start_process_kse");
                        alert(response.data.status);
                        this.processRunning = true;  // Sett prosessen til å være aktiv
                        this.currentSearchQuery = "Prossessen Kjører.." // Eksempelpå søkeprogresjon
                    } catch (error) {
                        console.error("Feil under start:", error);
                    }
                } else {
                    alert("Prosessen kjører allerede.");
                }
            },
            async stopProcess() {
                try {
                    const response = await axios.post("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/KseApi/stop_process_kse");
                    alert(response.data.status);
                    this.processRunning = false;
                    this.currentSearchQuery = 'Prosessen er stoppet.';
                } catch (error) {
                    console.error("Feil under stopp:", error);
                }
            },
            // Close the popup and notify the parent component
            closePopup() {
                this.$emit("close");
            },
        },
    };
</script>


<style scoped>
    /* Popup styling */
    .popup-overlay {
        position: fixed; /* Fixed positioning to cover the entire viewport */
        top: 10%;
        left: 10%;
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



    .emailresults {
        font-family: Arial, sans-serif;
        background-color: #1e1e1e;
        color: #e0e0e0; /* Lys tekst for kontrast */
        padding: 20px;
        max-width: 600px;
        width: 100%;
        overflow-y: auto;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2)
    }
    button {
        display: block;
        width: 100%;
        max-width: 300px;
        margin: 10px auto;
        padding: 10px;
        font-size: 16px;
        background-color: #2c2c2c; /* Mørk bakgrunn for knapp */
        color: #e0e0e0; /* Lys tekst */
        border: 1px solid #444; /* Mørk kant */
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.3s ease, color 0.3s ease;
    }

        button:hover {
            background-color: #444; /* Lysere grå ved hover */
            color: #ffffff; /* Hvitere tekst ved hover */
        }

        button:disabled {
            background-color: #333; /* Gråaktig for deaktivert */
            color: #777; /* Dempet tekstfarge */
            cursor: not-allowed;
        }

    .control-buttons {
        margin-top: 20px;
        display: flex;
        justify-content: space-between;
    }
</style>
