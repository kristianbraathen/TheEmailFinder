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
        const response = await fetch("http://localhost:5000/DbToExcel/export_to_excel");
        if (!response.ok) {
          throw new Error("Feil under nedlasting.");
        }

        // Lag en blob fra responsen
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        // Lag en midlertidig nedlastingslenke
        const a = document.createElement("a");
        a.href = url;
        a.download = "exported_data.xlsx";
        document.body.appendChild(a);
        a.click();
        a.remove();

        // Frigjør URL
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error("Feil under nedlasting:", error);
      }
    },
  },
};
</script>
