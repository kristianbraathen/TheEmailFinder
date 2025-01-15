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
                    <button @click="nextCompany">Neste Bedrift</button>
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
                    const response = await axios.get("http://localhost:5000/KseApi/search_emails");
                    this.companies = Array.isArray(response.data) ? response.data : [];
                    this.processRunning = true;

                } catch (error) {
                    console.error("Feil under henting av selskaper:", error);
                }
            },

            // Select an email and send it to the backend
            async selectEmail(orgNr, email) {
                try {
                    const response = await axios.post("http://localhost:5000/KseApi/update_email", {
                        org_nr: orgNr,
                        email: email,
                    });
                    alert(response.data.status || "E-post oppdatert!");
                } catch (error) {
                    console.error("Feil under oppdatering:", error);
                }
            },

            // Move to the next company
            nextCompany() {
                if (this.currentCompanyIndex < this.companies.length - 1) {
                    this.currentCompanyIndex++;
                }
            },

            async startProcess() {
                if (!this.processRunning) {
                    try {
                        const response = await axios.post("http://localhost:5000/KseApi/start_process");
                        alert(response.data.status);
                        this.processRunning = true;  // Sett prosessen til å være aktiv
                        this.currentSearchQuery = "Prossessen Kjører.." // Eksempelpå søkeprogresjon
                        // Start å hente selskaper og søke parallelt
                        await this.fetchCompanies(); // Hent selskaper
                        // Søke parallelt i fetchCompanies ved hjelp av Promise.all i fetchCompanies-metoden

                    } catch (error) {
                        console.error("Feil under start:", error);
                    }
                } else {
                    alert("Prosessen kjører allerede.");
                }
            },
            async stopProcess() {
                try {
                    const response = await axios.post("http://localhost:5000/KseApi/stop_process");
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
        position: fixed;
        top: 0;
        left: 25%;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    }

    .popup-content {
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
