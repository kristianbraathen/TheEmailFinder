<template>
    <div>
        <button @click="downloadExcel">Last ned Excel</button>
    </div>
</template>

<script>
export default {
  methods: {
        async downloadExcel() {
            try {
                const response = await fetch("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/DbToExcel/export_to_excel");

                if (!response.ok) {
                    throw new Error("Feil under nedlasting.");
                }

                // Hent filnavn fra Content-Disposition header
                const disposition = response.headers.get("Content-Disposition");
                let filename = "fil.xlsx"; // fallback
                if (disposition && disposition.includes("filename=")) {
                    const match = disposition.match(/filename="?([^"]+)"?/);
                    if (match && match[1]) {
                        filename = match[1];
                    }
                }

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);

                const a = document.createElement("a");
                a.href = url;
                a.download = filename;  // ✅ Bruker korrekt filnavn
                document.body.appendChild(a);
                a.click();
                a.remove();

                window.URL.revokeObjectURL(url);
            } catch (error) {
                console.error("Feil under nedlasting:", error);
            }
        }

  },
};
</script>
