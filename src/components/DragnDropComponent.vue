<template>
    <div class="drag-drop-container">
        <h1>Last opp Excel-fil</h1>
        <div class="drop-area"
             @dragover="handleDragOver"
             @dragleave="handleDragLeave"
             @drop="handleDrop"
             :class="{'dragging': isDragging}">
            <p v-if="!file">Dra og slipp Excel-filen her</p>
            <p v-else>{{ file.name }}</p>
        </div>
        <button v-if="file" @click="uploadFile" :disabled="loading">
            <span v-if="loading" class="spinner"></span>
            {{ loading ? 'Laster opp...' : 'Last opp fil' }}
        </button>
    </div>
</template>

<script>
    import axios from 'axios';

    export default {
        data() {
            return {
                file: null,
                isDragging: false,
                loading: false,

            };
        },
        methods: {
            handleDrop(event) {
                event.preventDefault(); // Prevent default behavior
                this.isDragging = false;
                const droppedFile = event.dataTransfer.files[0];
                if (
                    droppedFile &&
                    droppedFile.type ===
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ) {
                    this.file = droppedFile;
                } else {
                    alert("Vennligst last opp en Excel-fil");
                }
            },
            handleDragOver(event) {
                event.preventDefault(); // Prevent default behavior
                this.isDragging = true;
            },
            handleDragLeave() {
                this.isDragging = false;
            },
            async uploadFile() {
                if (!this.file) {
                    alert("Vennligst velg en fil å laste opp.");
                    return;
                }
                this.loading = true;
                const formData = new FormData();
                formData.append("file", this.file);

                try {
                    const response = await axios.post(
                        "https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/ExcelHandler/upload-excel",
                        formData,
                        {
                            headers: { "Content-Type": "multipart/form-data" },
                        }
                    );
                    console.log("Fil lastet opp:", response.data);
                    alert("Fil lastet opp vellykket!");
                } catch (error) {
                    console.error("Feil ved opplasting:", error);
                    alert("Feil ved opplasting: " + (error.response?.data?.error || error.message));
                } finally {
                    this.loading = false;
                }
            }
        },
    };
</script>

<style scoped>
    .drag-drop-container {
        text-align: center;
        padding: 20px;
    }

    .drop-area {
        border: 2px dashed #ccc;
        padding: 50px;
        cursor: pointer;
    }

        .drop-area.dragging {
            background-color: #f0f0f0;
        }
    .spinner {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        border-top-color: #fff;
        animation: spin 0.8s linear infinite;
        margin-right: 8px;
        vertical-align: middle;
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }
    button {
        margin-top: 10px;
        padding: 10px 20px;
        background-color: #4caf50;
        color: white;
        border: none;
        cursor: pointer;
    }

        button:hover {
            background-color: #45a049;
        }
</style>
