<template>
    <div v-if="isVisible" class="popup-overlay">
        <div class="popup-content">
            <h2>Finn e-poster fra KSE 1881</h2>
            <button @click="startProcess">Start Prosessen</button>
            <p v-if="processMessage">{{ processMessage }}</p>
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
            isVisible: Boolean,
        },
        data() {
            return {
                processMessage: "",
            };
        },
        methods: {
            async startProcess() {
                try {
                    // Steg 1: Klargjør databasen/tabellen for nye resultater
                    await axios.post(
                        "https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/SearchResultHandler/initialize-email-results"
                    );

                    // Steg 2: Start WebJob-en via webhook
                    const startResponse = await axios.post(
                        "https://theemailfinder-d8ctecfsaab2a7fh.scm.norwayeast-01.azurewebsites.net/api/triggeredwebjobs/webjobemailsearch-kse1881/run",
                        {},
                        {
                            auth: {
                                username: 'WEBJOBS_USER',
                                password: 'WEBJOBS_PASS'
                            }
                        }
                    );

                    this.processMessage = "WebJob startet - prosessen kjører i bakgrunnen";
                } catch (error) {
                    this.processMessage = "Feil under start av prosess/WebJob.";
                    console.error(error);
                }
            },
            async stopProcess() {
                try {
                    const response = await axios.post(
                        "https://theemailfinder-d8ctecfsaab2a7fh.scm.norwayeast-01.azurewebsites.net/api/triggeredwebjobs/webjobemailsearch-kse1881/stop",
                        {},
                        {
                            auth: {
                                username: 'WEBJOBS_USER',
                                password: 'WEBJOBS_PASS'
                            }
                        }
                    );
                    this.processMessage = response.data.status;
                } catch (error) {
                    this.processMessage = "Feil under stopp av prosess.";
                    console.error(error);
                }
            },
            closePopup() {
                this.$emit("close");
            },
        },
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
        background-color: #121212;
        color: #e0e0e0;
        padding: 20px;
        width: 90%;
        height: 90%;
        overflow-y: auto;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        font-family: Arial, sans-serif;
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

    .control-buttons {
        margin-top: 20px;
        display: flex;
        justify-content: space-between;
    }
</style>
