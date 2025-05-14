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
            <p v-if="processingData.error">
                ❗Feilmelding: {{ processingData.error }}
                <span v-if="processingData.last_id"> (Siste behandlede ID: {{ processingData.last_id }})</span>
            </p>
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
    import KSEPopUP from "./KSEPopUP.vue";
    import Kse1881PopUP from "./Kse1881PopUP.vue";
    import ExcelOut from "./ExcelOut.vue";
    import GoogleKsePopup from "./GoogleKsePopup.vue";
    import SearchResultPopup from "./SearchResultPopup.vue";

    export default {
        data() {
            return {
                processingData: null,
                search_by_company_name: "",
                searchResults: null,
                isUpdating: false,
                showPopup1: false,
                showPopup2: false,
                showPopup3: false,
                showPopup4: false,
                companies: [],
                status: "",
                pollingInterval: null
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
                this.isUpdating = true;
                this.status = "Processing...";
                this.processingData = {
                    updated_count: 0,
                    no_email_count: 0,
                    error_count: 0,
                    total_updated: 0,
                    total_no_email: 0,
                    total_error: 0,
                    error: null,
                    last_id: null
                };

                try {
                    // Start the process in the backend
                    await axios.post("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/BrregUpdate/start_process_and_clean");
                    this.startPolling();
                } catch (error) {
                    this.isUpdating = false;
                    this.status = "Kunne ikke starte prosessen.";
                    this.processingData.error = error.message;
                }
            },
            startPolling() {
                if (this.pollingInterval) clearInterval(this.pollingInterval);
                this.pollingInterval = setInterval(this.fetchProcessStatus, 5000); // Poll every 5 seconds
            },
            async fetchProcessStatus() {
                try {
                    const response = await axios.get("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/BrregUpdate/process_status");
                    const data = response.data;

                    // Use the latest batch for batch stats
                    let latestBatch = (data.batches && data.batches.length > 0)
                        ? data.batches[data.batches.length - 1]
                        : {
                            updated_count: 0,
                            no_email_count: 0,
                            error_count: 0,
                            total_updated: 0,
                            total_no_email: 0,
                            total_error: 0
                        };

                    this.processingData = {
                        ...latestBatch,
                        error: data.error,
                        last_id: data.last_id
                    };

                    this.status = data.error
                        ? "Feil: " + data.error
                        : data.running
                            ? "Processing..."
                            : "Processing complete!";

                    // Stop polling if finished or error
                    if (!data.running || data.error) {
                        this.isUpdating = false;
                        clearInterval(this.pollingInterval);
                    }
                } catch (error) {
                    this.isUpdating = false;
                    this.status = "Feil under polling.";
                    this.processingData.error = error.message;
                    clearInterval(this.pollingInterval);
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
                    const response = await axios.get("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/SearchResultHandler/get_email_results");
                    this.searchResults = Array.isArray(response.data) ? response.data : [];
                } catch (error) {
                    console.error("Error fetching search results:", error);
                    this.searchResults = [];
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
                this.showPopup1 = false;
            },
            closePopup2() {
                this.showPopup2 = false;
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
        beforeDestroy() {
            if (this.pollingInterval) clearInterval(this.pollingInterval);
        }
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

    div[processingData] {
        color: #ffffff;
    }

        div[processingData] h3,
        div[processingData] ul,
        div[processingData] p {
            color: #ffffff;
        }

    body {
        font-family: Arial, sans-serif;
        background-color: #121212;
        color: #e0e0e0;
        margin: 0;
        padding: 0;
    }

    h1, h2 {
        text-align: center;
        color: #ffffff;
        margin-bottom: 20px;
    }

    h2 {
        margin-top: 20px;
    }

    p {
        color: #e0e0e0
    }

    div {
        max-width: 800px;
        margin: 20px auto;
        padding: 20px;
        background: #1e1e1e;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.5);
    }

    input[type="text"] {
        display: block;
        width: 100%;
        max-width: 300px;
        margin: 10px auto;
        padding: 10px;
        font-size: 16px;
        border: 1px solid #333;
        background-color: #2c2c2c;
        color: #ffffff;
        border-radius: 4px;
        outline: none;
        box-sizing: border-box;
    }

        input[type="text"]:focus {
            border-color: #555;
            box-shadow: 0 0 5px rgba(255, 255, 255, 0.2);
        }

    button {
        display: block;
        width: 100%;
        max-width: 300px;
        margin: 10px auto;
        padding: 10px;
        font-size: 16px;
        background-color: #2c2c2c;
        color: #e0e0e0;
        border: 1px solid #444;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.3s ease, color 0.3s ease;
    }

        button:hover {
            background-color: #444;
            color: #ffffff;
        }

        button:disabled {
            background-color: #333;
            color: #777;
            cursor: not-allowed;
        }

    .enabled-button {
        background-color: #2c2c2c;
        color: #e0e0e0;
        border: 1px solid #444;
        cursor: pointer;
        transition: background-color 0.3s ease, color 0.3s ease;
    }

        .enabled-button:hover {
            background-color: #444;
            color: #ffffff;
        }

    .disabled-button {
        background-color: #333;
        color: #777;
        border: 1px solid #444;
        cursor: not-allowed;
    }

    pre {
        background-color: #1e1e1e;
        color: #e0e0e0;
        padding: 10px;
        border: 1px solid #333;
        border-radius: 4px;
        overflow-x: auto;
    }

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
