<template>
    <div>
        <h1>Oppdater e-post for organisasjoner</h1>

        <!-- Knapp for å starte oppdatering -->
        <button @click="processAndCleanOrganizations" :disabled="isUpdating">
            {{ isUpdating ? 'Laster...' : 'Start oppdatering fra Brønnøysund' }}
            <span v-if="isUpdating" class="spinner"></span>
        </button>

        <button @click="openPopup3">Google Search</button>
        <button @click="openPopup1">Facebook Scrap</button>
        <button @click="openPopup2">1881 Scrap</button>
        <button @click="fetchSearchResults().then(openPopup4)"
                :disabled="!searchResults || searchResults.length === 0"
                :class="{'enabled-button': searchResults && searchResults.length > 0, 'disabled-button': !searchResults || searchResults.length === 0}">
            Vis resultater
        </button>
        <GoogleKsePopup :isVisible="showPopup3"
                        :companies="companies"
                        @close="closePopup3" />
        <!-- KSEPopUP popup -->
        <KSEPopUP :isVisible="showPopup1"
                  :companies="companies"
                  @close="closePopup1" />
        <!-- Kse1881PopUP popup -->
        <Kse1881PopUP :isVisible="showPopup2"
                      :companies="companies"
                      @close="closePopup2" />
        <!-- SearchResultPopup popup -->
        <SearchResultsPopup :results="searchResults"
                            :visible="showPopup4"
                            @close="closePopup4"
                            @updateResults="removeResult" />
        <!-- Manuelt søk -->
        <div>
            <input v-model="search_by_company_name" placeholder="Søk etter bedrifter" />
            <button @click="manualSearch">Søk</button>
        </div>
        <!-- Resultatvisning -->
        <div v-if="processingData">
            <h3>Status: {{ status }}</h3>
            <ul>
                <li>✅ Oppdatert (batch): {{ processingData.updated_count }}</li>
                <li>📭 Ingen e-post (batch): {{ processingData.no_email_count }}</li>
                <li>❌ Feil (batch): {{ processingData.error_count }}</li>
            </ul>
            <ul>
                <li>🔢 Totalt oppdatert: {{ processingData.total_updated }}</li>
                <li>🔢 Totalt ingen e-post: {{ processingData.total_no_email }}</li>
                <li>🔢 Totalt feil: {{ processingData.total_error }}</li>
            </ul>
            <p v-if="processingData.error">❗Feilmelding: {{ processingData.error }}</p>
        </div>



        <!-- Vis resultater hvis søket lykkes -->
        <div v-if="searchResults">
            <h2>Søkeresultater</h2>
            <pre>{{ searchResults }}</pre>
        </div>
        <!-- Drag-and-drop komponent -->
        <DragnDropComponent></DragnDropComponent>
        <ExcelOut></ExcelOut>

    </div>
</template>

<script>
    import axios from "axios";
    import DragnDropComponent from "./DragnDropComponent.vue";
    import KSEPopUP from "./KSEPopUP.vue";  // Importere KSEPopUP-komponenten
    import Kse1881PopUP from "./Kse1881PopUP.vue";  // Importere Kse1881PopUP-komponenten
    import ExcelOut from "./ExcelOut.vue";  // Importere ExcelOut-komponenten
    import GoogleKsePopup from "./GoogleKsePopup.vue";
    import SearchResultPopup from "./SearchResultPopup.vue";

    export default {
        data() {
            return {
                processingData: null, // Status for API-respons
                search_by_company_name: "", // For manuelt søk
                searchResults: null, // Resultater fra manuelt søk
                isUpdating: false, // For å deaktivere knappen under prosessering
                showPopup1: false,
                showPopup2: false,// Tilstand for å vise popup
                showPopup3: false,
                showPopup4: false,
                companies: [], // Selskapsdata for popup
                status: "", // Statusmelding
            };
        },
        components: {
            DragnDropComponent,
            KSEPopUP,
            Kse1881PopUP,
            ExcelOut,
            GoogleKsePopup,
            SearchResultPopup

        },
        methods: {
            async processAndCleanOrganizations() {
                this.isUpdating = true; // Disable the button
                this.status = "Processing..."; // Start status
                this.processingData = {
                    updated_count: 0,
                    no_email_count: 0,
                    error_count: 0,
                    total_updated: 0,
                    total_no_email: 0,
                    total_error: 0
                };
                     // Initialize counts

                try {
                    const response = await axios.post("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/BrregUpdate/process_and_clean_organizations");

                    // Process the response containing all batch results
                    if (response.data && response.data.batches) {
                        response.data.batches.forEach((batchResult) => {
                            if (batchResult.error) {
                                console.error("Error in batch:", batchResult.error);
                                this.processingData.error_count += 1;
                            } else {
                                this.processingData.updated_count += batchResult.updated_count;
                                this.processingData.no_email_count += batchResult.no_email_count;
                                this.processingData.error_count += batchResult.error_count;
                                // Update running totals
                                this.processingData.total_updated = batchResult.total_updated;
                                this.processingData.total_no_email = batchResult.total_no_email;
                                this.processingData.total_error = batchResult.total_error;
                            }
                        });
                        this.status = "Processing complete!";
                    } else {
                        this.status = "No data returned from the server.";
                    }
                } catch (error) {
                    console.error("Error during processing:", error);
                    this.processingData = {
                        status: "An error occurred during processing.",
                        error: error.message,
                    };
                } finally {
                    this.isUpdating = false; // Re-enable the button
                }
            },
            async manualSearch() {
                if (!this.search_by_company_name) {
                    this.status = "Vennligst skriv inn en bedrift.";
                    return;
                }

                try {
                    const response = await axios.get(
                        `https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/SeleniumScrap/search_by_company_name?company_name=${this.search_by_company_name}`
                    );
                    this.status = response.data.status;
                    this.searchResults = response.data;
                } catch (error) {
                    console.error("Feil ved manuell søk:", error);
                    this.status = "Feil ved manuell søk.";
                    this.searchResults = null;
                }
            },
            async fetchSearchResults() {
                 try {
                     // Fetch results from the backend
                     const response = await axios.get("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/SearchResultHandler/get_email_results");
         
                     // Update searchResults with the fetched data
                     this.searchResults = Array.isArray(response.data) ? response.data : [];
                 } catch (error) {
                     console.error("Error fetching search results:", error);
                     this.searchResults = []; // Set to an empty array on error
                 }
            },
            removeResult(orgNr) {
                this.searchResults = this.searchResults.filter(r => r.org_nr !== orgNr);
            },
            openPopup1() {
                this.showPopup1 = true;
            },
            openPopup2() {
                this.showPopup2 = true;
            },
            closePopup1() {
                this.showPopup1 = false; // Skjul popup når den lukkes
            },
            closePopup2() {
                this.showPopup2 = false; // Skjul popup når den lukkes
            },
            openPopup3() {
                this.showPopup3 = true;
            },
            closePopup3() {
                this.showPopup3 = false;
            },
            openPopup4() {
                this.showPopup4 = true;
            },
            closePopup4() {
                this.showPopup4 = false;
            },
        },
    };
</script>
<style scoped>
    .spinner {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        border-top-color: #fff;
        animation: spin 0.8s linear infinite;
        margin-left: 10px;
        vertical-align: middle;
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }
    /* Ensure white font for the processingData section */
    div[processingData] {
        color: #ffffff; /* White font */
    }
    div[processingData] h3,
    div[processingData] ul,
    div[processingData] p {
        color: #ffffff; /* Ensure all child elements have white font */
    }


    /* Generell styling */
    body {
        font-family: Arial, sans-serif;
        background-color: #121212; /* Mørk bakgrunn */
        color: #e0e0e0; /* Lys tekst for kontrast */
        margin: 0;
        padding: 0;
    }

    h1, h2 {
        text-align: center;
        color: #ffffff; /* Hvit tekst for overskrifter */
        margin-bottom: 20px;
    }

    h2 {
        margin-top: 20px;
    }

    p {
        color: #e0e0e0
    }
    /* Container for innhold */
    div {
        max-width: 800px;
        margin: 20px auto;
        padding: 20px;
        background: #1e1e1e; /* Mørk grå for kort/innhold */
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.5); /* Mørk skygge */
    }

    /* Input-felt */
    input[type="text"] {
        display: block;
        width: 100%;
        max-width: 300px;
        margin: 10px auto;
        padding: 10px;
        font-size: 16px;
        border: 1px solid #333; /* Mørk kant */
        background-color: #2c2c2c; /* Mørk bakgrunn for input */
        color: #ffffff; /* Hvit tekst */
        border-radius: 4px;
        outline: none;
        box-sizing: border-box;
    }

        input[type="text"]:focus {
            border-color: #555; /* Lysere kant ved fokus */
            box-shadow: 0 0 5px rgba(255, 255, 255, 0.2);
        }

    /* Knapp */
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

    .enabled-button {
        background-color: #2c2c2c; /* Dark background for enabled */
        color: #e0e0e0; /* Light text */
        border: 1px solid #444; /* Dark border */
        cursor: pointer;
        transition: background-color 0.3s ease, color 0.3s ease;
    }

        .enabled-button:hover {
            background-color: #444; /* Lighter gray on hover */
            color: #ffffff; /* Whiter text on hover */
        }

        .disabled-button {
            background-color: #333; /* Gray background for disabled */
            color: #777; /* Muted text color */
            border: 1px solid #444; /* Dark border */
            cursor: not-allowed; /* Show not-allowed cursor */
        }

    /* Statusvisning */
    pre {
        background-color: #1e1e1e; /* Mørk bakgrunn */
        color: #e0e0e0; /* Lys tekst */
        padding: 10px;
        border: 1px solid #333; /* Mørk kant */
        border-radius: 4px;
        overflow-x: auto;
    }

    /* Responsivt design */
    @media (max-width: 600px) {
        div {
            padding: 10px;
        }

        input[type="text"],
        button {
            max-width: 100%;
        }
    }
</style>


