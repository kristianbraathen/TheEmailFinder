(function(){"use strict";var e={382:function(e,t,n){var s=n(751),o=n(641);function a(e,t,n,s,a,r){const i=(0,o.g2)("FrontEnd");return(0,o.uX)(),(0,o.Wv)(i)}var r=n(33);const i={key:0},l={key:1};function c(e,t,n,a,c,p){const u=(0,o.g2)("GoogleKsePopup"),d=(0,o.g2)("KSEPopUP"),h=(0,o.g2)("Kse1881PopUP"),m=(0,o.g2)("DragnDropComponent"),y=(0,o.g2)("ExcelOut");return(0,o.uX)(),(0,o.CE)("div",null,[t[8]||(t[8]=(0,o.Lk)("h1",null,"Oppdater e-post for organisasjoner",-1)),(0,o.Lk)("button",{onClick:t[0]||(t[0]=(...e)=>p.processAndCleanOrganizations&&p.processAndCleanOrganizations(...e))},"Start oppdatering fra Brønnøysund"),(0,o.Lk)("button",{onClick:t[1]||(t[1]=(...e)=>p.openPopup3&&p.openPopup3(...e))},"Google Search"),(0,o.Lk)("button",{onClick:t[2]||(t[2]=(...e)=>p.openPopup1&&p.openPopup1(...e))},"Facebook Scrap"),(0,o.Lk)("button",{onClick:t[3]||(t[3]=(...e)=>p.openPopup2&&p.openPopup2(...e))},"1881 Scrap"),(0,o.bF)(u,{isVisible:c.showPopup3,companies:c.companies,onClose:p.closePopup3},null,8,["isVisible","companies","onClose"]),(0,o.bF)(d,{isVisible:c.showPopup1,companies:c.companies,onClose:p.closePopup1},null,8,["isVisible","companies","onClose"]),(0,o.bF)(h,{isVisible:c.showPopup2,companies:c.companies,onClose:p.closePopup2},null,8,["isVisible","companies","onClose"]),(0,o.Lk)("div",null,[(0,o.bo)((0,o.Lk)("input",{"onUpdate:modelValue":t[4]||(t[4]=e=>c.search_by_company_name=e),placeholder:"Søk etter bedrifter"},null,512),[[s.Jo,c.search_by_company_name]]),(0,o.Lk)("button",{onClick:t[5]||(t[5]=(...e)=>p.manualSearch&&p.manualSearch(...e))},"Søk")]),c.processingData?((0,o.uX)(),(0,o.CE)("div",i,[t[6]||(t[6]=(0,o.Lk)("h2",null,"Status",-1)),(0,o.Lk)("p",null,(0,r.v_)(c.processingData.status),1),(0,o.Lk)("p",null,"Updated: "+(0,r.v_)(c.processingData.details.updated_count),1),(0,o.Lk)("p",null,"No email: "+(0,r.v_)(c.processingData.details.no_email_count),1),(0,o.Lk)("p",null,"Errors: "+(0,r.v_)(c.processingData.details.error_count),1)])):(0,o.Q3)("",!0),c.searchResults?((0,o.uX)(),(0,o.CE)("div",l,[t[7]||(t[7]=(0,o.Lk)("h2",null,"Søkeresultater",-1)),(0,o.Lk)("pre",null,(0,r.v_)(c.searchResults),1)])):(0,o.Q3)("",!0),(0,o.bF)(m),(0,o.bF)(y)])}var p=n(605);const u={class:"drag-drop-container"},d={key:0},h={key:1};function m(e,t,n,s,a,i){return(0,o.uX)(),(0,o.CE)("div",u,[t[4]||(t[4]=(0,o.Lk)("h1",null,"Last opp Excel-fil",-1)),(0,o.Lk)("div",{class:(0,r.C4)(["drop-area",{dragging:a.isDragging}]),onDragover:t[0]||(t[0]=(...e)=>i.handleDragOver&&i.handleDragOver(...e)),onDragleave:t[1]||(t[1]=(...e)=>i.handleDragLeave&&i.handleDragLeave(...e)),onDrop:t[2]||(t[2]=(...e)=>i.handleDrop&&i.handleDrop(...e))},[a.file?((0,o.uX)(),(0,o.CE)("p",h,(0,r.v_)(a.file.name),1)):((0,o.uX)(),(0,o.CE)("p",d,"Dra og slipp Excel-filen her"))],34),a.file?((0,o.uX)(),(0,o.CE)("button",{key:0,onClick:t[3]||(t[3]=(...e)=>i.uploadFile&&i.uploadFile(...e))},"Last opp fil")):(0,o.Q3)("",!0)])}var y={data(){return{file:null,isDragging:!1}},methods:{handleDrop(e){e.preventDefault(),this.isDragging=!1;const t=e.dataTransfer.files[0];t&&"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"===t.type?this.file=t:alert("Vennligst last opp en Excel-fil")},handleDragOver(e){e.preventDefault(),this.isDragging=!0},handleDragLeave(){this.isDragging=!1},async uploadFile(){if(!this.file)return void alert("Vennligst velg en fil å laste opp.");const e=new FormData;e.append("file",this.file);try{const t=await p.A.post("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/ExcelHandler/upload-excel",e,{headers:{"Content-Type":"multipart/form-data"}});console.log("Fil lastet opp:",t.data),alert("Fil lastet opp vellykket!")}catch(t){console.error("Feil ved opplasting:",t),alert("Feil ved opplasting: "+t.response?.data?.error||0)}}}},k=n(262);const g=(0,k.A)(y,[["render",m],["__scopeId","data-v-b1f623d4"]]);var f=g;const C={key:0,class:"popup-overlay"},v={class:"popup-content"},b={key:0,class:"emailresults"},P={key:0},_=["onClick"],w={key:1},L={key:1},x={key:2},E={class:"control-buttons"};function F(e,t,n,s,a,i){return n.isVisible?((0,o.uX)(),(0,o.CE)("div",C,[(0,o.Lk)("div",v,[t[6]||(t[6]=(0,o.Lk)("h2",null,"Finn e-poster fra Facebook",-1)),(0,o.Lk)("button",{onClick:t[0]||(t[0]=(...e)=>i.handleButtonClick&&i.handleButtonClick(...e))},"Start Prosessen"),a.companies&&a.companies.length?((0,o.uX)(),(0,o.CE)("div",b,[a.currentCompanyIndex<a.companies.length?((0,o.uX)(),(0,o.CE)("div",P,[(0,o.Lk)("h3",null,(0,r.v_)(a.companies[a.currentCompanyIndex].company_name),1),(0,o.Lk)("p",null,[t[4]||(t[4]=(0,o.Lk)("strong",null,"Org.nr:",-1)),(0,o.eW)(" "+(0,r.v_)(a.companies[a.currentCompanyIndex].org_nr),1)]),(0,o.Lk)("p",null,[t[5]||(t[5]=(0,o.Lk)("strong",null,"Søkestreng:",-1)),(0,o.eW)(" "+(0,r.v_)(a.companies[a.currentCompanyIndex].query),1)]),(0,o.Lk)("ul",null,[((0,o.uX)(!0),(0,o.CE)(o.FK,null,(0,o.pI)(a.companies[a.currentCompanyIndex].emails,(e=>((0,o.uX)(),(0,o.CE)("li",{key:e},[(0,o.eW)((0,r.v_)(e)+" ",1),(0,o.Lk)("button",{onClick:t=>i.selectEmail(a.companies[a.currentCompanyIndex].org_nr,e)},"Velg",8,_)])))),128))]),(0,o.Lk)("button",{onClick:t[1]||(t[1]=(...e)=>i.nextCompany&&i.nextCompany(...e))},"Neste Bedrift")])):((0,o.uX)(),(0,o.CE)("p",w,"Alle selskaper er behandlet."))])):(0,o.Q3)("",!0),a.processRunning?((0,o.uX)(),(0,o.CE)("div",L,[(0,o.Lk)("p",null,(0,r.v_)(a.currentSearchQuery),1)])):((0,o.uX)(),(0,o.CE)("p",x)),(0,o.Lk)("div",E,[(0,o.Lk)("button",{onClick:t[2]||(t[2]=(...e)=>i.stopProcess&&i.stopProcess(...e))},"Stopp Prosessen"),(0,o.Lk)("button",{onClick:t[3]||(t[3]=(...e)=>i.closePopup&&i.closePopup(...e))},"Lukk")])])])):(0,o.Q3)("",!0)}var S={props:{isVisible:Boolean},data(){return{companies:[],currentCompanyIndex:0,currentSearchQuery:'Klikk "Start Prosessen" for å begynne.',processRunning:!1,processMessage:""}},methods:{async handleButtonClick(){try{await this.startProcess(),await this.fetchCompanies()}catch(e){console.error("Feil under knappetrykk:",e)}},async fetchCompanies(){try{const e=await p.A.get("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/KseApi/search_emails");this.companies=Array.isArray(e.data)?e.data:[],this.processRunning=!0}catch(e){console.error("Feil under henting av selskaper:",e)}},async selectEmail(e,t){try{const n=await p.A.post("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/KseApi/update_email",{org_nr:e,email:t});alert(n.data.status||"E-post oppdatert!")}catch(n){console.error("Feil under oppdatering:",n)}},nextCompany(){this.currentCompanyIndex<this.companies.length-1&&this.currentCompanyIndex++},async startProcess(){if(this.processRunning)alert("Prosessen kjører allerede.");else try{const e=await p.A.post("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/KseApi/start_process");alert(e.data.status),this.processRunning=!0,this.currentSearchQuery="Prossessen Kjører..",await this.fetchCompanies()}catch(e){console.error("Feil under start:",e)}},async stopProcess(){try{const e=await p.A.post("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/KseApi/stop_process");alert(e.data.status),this.processRunning=!1,this.currentSearchQuery="Prosessen er stoppet."}catch(e){console.error("Feil under stopp:",e)}},closePopup(){this.$emit("close")}}};const A=(0,k.A)(S,[["render",F],["__scopeId","data-v-fb11e28e"]]);var I=A;const D={key:0,class:"popup-overlay"},X={class:"popup-content"},O={key:0,class:"emailresults"},K={key:0},R=["onClick"],Q={key:1},V={class:"control-buttons"};function j(e,t,n,s,a,i){return n.isVisible?((0,o.uX)(),(0,o.CE)("div",D,[(0,o.Lk)("div",X,[t[6]||(t[6]=(0,o.Lk)("h2",null,"Finn e-poster fra 1881",-1)),(0,o.Lk)("button",{onClick:t[0]||(t[0]=(...e)=>i.handleButtonClick&&i.handleButtonClick(...e))},"Start Prosessen"),a.companies&&a.companies.length?((0,o.uX)(),(0,o.CE)("div",O,[a.currentCompanyIndex<a.companies.length?((0,o.uX)(),(0,o.CE)("div",K,[(0,o.Lk)("h3",null,(0,r.v_)(a.companies[a.currentCompanyIndex].company_name),1),(0,o.Lk)("p",null,[t[4]||(t[4]=(0,o.Lk)("strong",null,"Org.nr:",-1)),(0,o.eW)(" "+(0,r.v_)(a.companies[a.currentCompanyIndex].org_nr),1)]),(0,o.Lk)("p",null,[t[5]||(t[5]=(0,o.Lk)("strong",null,"Søkestreng:",-1)),(0,o.eW)(" "+(0,r.v_)(a.companies[a.currentCompanyIndex].query),1)]),(0,o.Lk)("ul",null,[((0,o.uX)(!0),(0,o.CE)(o.FK,null,(0,o.pI)(a.companies[a.currentCompanyIndex].emails,(e=>((0,o.uX)(),(0,o.CE)("li",{key:e},[(0,o.eW)((0,r.v_)(e)+" ",1),(0,o.Lk)("button",{onClick:t=>i.selectEmail(a.companies[a.currentCompanyIndex].org_nr,e)},"Velg",8,R)])))),128))]),(0,o.Lk)("button",{onClick:t[1]||(t[1]=(...e)=>i.nextCompany&&i.nextCompany(...e))},"Neste Bedrift")])):((0,o.uX)(),(0,o.CE)("p",Q,"Alle selskaper er behandlet."))])):(0,o.Q3)("",!0),(0,o.Lk)("p",null,(0,r.v_)(a.currentSearchQuery),1),(0,o.Lk)("div",V,[(0,o.Lk)("button",{onClick:t[2]||(t[2]=(...e)=>i.stopProcess&&i.stopProcess(...e))},"Stopp Prosessen"),(0,o.Lk)("button",{onClick:t[3]||(t[3]=(...e)=>i.closePopup&&i.closePopup(...e))},"Lukk")])])])):(0,o.Q3)("",!0)}var B={props:{isVisible:Boolean},data(){return{companies:[],currentCompanyIndex:0,currentSearchQuery:'Klikk "Start Prosessen" for å begynne.',processRunning:!1,processMessage:""}},methods:{async handleButtonClick(){try{await this.startProcess(),await this.fetchCompanies()}catch(e){console.error("Feil under knappetrykk:",e)}},async fetchCompanies(){try{const e=await p.A.get("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/Kseapi1881/search_emails");this.companies=Array.isArray(e.data)?e.data:[],this.processRunning=!0}catch(e){console.error("Feil under henting av selskaper:",e)}},async selectEmail(e,t){try{const n=await p.A.post("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/Kseapi1881/update_email",{org_nr:e,email:t});alert(n.data.status||"E-post oppdatert!")}catch(n){console.error("Feil under oppdatering:",n)}},nextCompany(){this.currentCompanyIndex<this.companies.length-1&&this.currentCompanyIndex++},async startProcess(){if(this.processRunning)alert("Prosessen kjører allerede.");else try{const e=await p.A.post("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/Kseapi1881/start_process");alert(e.data.status),this.processRunning=!0,this.currentSearchQuery="Prosessen kjører...",await this.fetchCompanies()}catch(e){console.error("Feil under start:",e)}},async stopProcess(){try{const e=await p.A.post("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/Kseapi1881/stop_process");alert(e.data.status),this.processRunning=!1,this.currentSearchQuery="Prosessen er stoppet."}catch(e){console.error("Feil under stopp:",e)}},closePopup(){this.$emit("close")}}};const z=(0,k.A)(B,[["render",j],["__scopeId","data-v-118842d8"]]);var U=z;function W(e,t,n,s,a,r){return(0,o.uX)(),(0,o.CE)("div",null,[(0,o.Lk)("button",{onClick:t[0]||(t[0]=(...e)=>r.downloadExcel&&r.downloadExcel(...e))},"Last ned Excel")])}var G={methods:{async downloadExcel(){try{const e=await fetch("https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net/DbToExcel/export_to_excel");if(!e.ok)throw new Error("Feil under nedlasting.");const t=await e.blob(),n=window.URL.createObjectURL(t),s=document.createElement("a");s.href=n,s.download="exported_data.xlsx",document.body.appendChild(s),s.click(),s.remove(),window.URL.revokeObjectURL(n)}catch(e){console.error("Feil under nedlasting:",e)}}}};const T=(0,k.A)(G,[["render",W]]);var M=T;const N={key:0,class:"popup-overlay"},$={class:"popup-content"},q={key:0,class:"emailresults"},H={key:0},J=["onClick"],Y={key:1},Z={class:"control-buttons"};function ee(e,t,n,s,a,i){return n.isVisible?((0,o.uX)(),(0,o.CE)("div",N,[(0,o.Lk)("div",$,[t[7]||(t[7]=(0,o.Lk)("h2",null,"Finn e-poster med Google søk",-1)),(0,o.Lk)("button",{onClick:t[0]||(t[0]=(...e)=>i.handleButtonClick&&i.handleButtonClick(...e))},"Start Prosessen"),a.companies&&a.companies.length?((0,o.uX)(),(0,o.CE)("div",q,[a.currentCompanyIndex<a.companies.length?((0,o.uX)(),(0,o.CE)("div",H,[(0,o.Lk)("h3",null,(0,r.v_)(a.companies[a.currentCompanyIndex].company_name),1),(0,o.Lk)("p",null,[t[5]||(t[5]=(0,o.Lk)("strong",null,"Org.nr:",-1)),(0,o.eW)(" "+(0,r.v_)(a.companies[a.currentCompanyIndex].org_nr),1)]),(0,o.Lk)("p",null,[t[6]||(t[6]=(0,o.Lk)("strong",null,"Søkestreng:",-1)),(0,o.eW)(" "+(0,r.v_)(a.companies[a.currentCompanyIndex].query),1)]),(0,o.Lk)("ul",null,[((0,o.uX)(!0),(0,o.CE)(o.FK,null,(0,o.pI)(a.companies[a.currentCompanyIndex].emails,(e=>((0,o.uX)(),(0,o.CE)("li",{key:e},[(0,o.eW)((0,r.v_)(e)+" ",1),(0,o.Lk)("button",{onClick:t=>i.selectEmail(a.companies[a.currentCompanyIndex].org_nr,e)},"Velg",8,J)])))),128))]),(0,o.Lk)("button",{onClick:t[1]||(t[1]=(...e)=>i.nextCompany&&i.nextCompany(...e))},"Neste Bedrift")])):((0,o.uX)(),(0,o.CE)("p",Y,"Alle selskaper er behandlet."))])):(0,o.Q3)("",!0),(0,o.Lk)("p",null,(0,r.v_)(a.currentSearchQuery),1),(0,o.Lk)("div",Z,[(0,o.Lk)("button",{onClick:t[2]||(t[2]=(...e)=>i.restartProcess&&i.restartProcess(...e))},"Omstart Prosessen"),(0,o.Lk)("button",{onClick:t[3]||(t[3]=(...e)=>i.stopProcess&&i.stopProcess(...e))},"Stopp Prosessen"),(0,o.Lk)("button",{onClick:t[4]||(t[4]=(...e)=>i.closePopup&&i.closePopup(...e))},"Lukk")])])])):(0,o.Q3)("",!0)}var te={props:{isVisible:Boolean},data(){return{companies:[],currentCompanyIndex:0,currentSearchQuery:'Klikk "Start Prosessen" for å begynne.',processRunning:!1,processMessage:""}},methods:{async handleButtonClick(){try{await this.startProcess(),await this.fetchCompanies()}catch(e){console.error("Feil under knappetrykk:",e)}},async fetchCompanies(){try{const e=await p.A.get("http://localhost:8080/GoogleKse/search_emails");this.companies=Array.isArray(e.data)?e.data:[],this.processRunning=!0}catch(e){console.error("Feil under henting av selskaper:",e)}},async selectEmail(e,t){try{const n=await p.A.post("http://localhost:8080/GoogleKse/update_email",{org_nr:e,email:t});alert(n.data.status||"E-post oppdatert!")}catch(n){console.error("Feil under oppdatering:",n)}},nextCompany(){this.currentCompanyIndex<this.companies.length-1&&this.currentCompanyIndex++},async startProcess(){if(this.processRunning)alert("Prosessen kjører allerede.");else try{const e=await p.A.post("http://localhost:8080/GoogleKse/start_process");alert(e.data.status),this.processRunning=!0,this.currentSearchQuery="Prosessen kjører...",await this.fetchCompanies()}catch(e){console.error("Feil under start:",e)}},async restartProcess(){try{const e=await p.A.post("http://localhost:8080/GoogleKse/restart_process");alert(e.data.status),this.processRunning=!0,this.currentSearchQuery="Prosessen er startet på nytt.",await this.fetchCompanies()}catch(e){console.error("Feil under omstart:",e)}},async stopProcess(){try{const e=await p.A.post("http://localhost:8080/GoogleKse/stop_process");alert(e.data.status),this.processRunning=!1,this.currentSearchQuery="Prosessen er stoppet."}catch(e){console.error("Feil under stopp:",e)}},closePopup(){this.$emit("close")}}};const ne=(0,k.A)(te,[["render",ee],["__scopeId","data-v-1523acfc"]]);var se=ne,oe={data(){return{processingData:null,search_by_company_name:"",searchResults:null,isUpdating:!1,showPopup1:!1,showPopup2:!1,showPopup3:!1,companies:[]}},components:{DragnDropComponent:f,KSEPopUP:I,Kse1881PopUP:U,ExcelOut:M,GoogleKsePopup:se},methods:{async processAndCleanOrganizations(){this.isUpdating=!0,this.status="Pending...";try{const e=await p.A.post("http://localhost:8080/BrregUpdate/process_and_clean_organizations");this.processingData={status:e.data.status,details:e.data.details}}catch(e){console.error("Feil under prosessering:",e),this.processingData={status:"En feil oppsto under prosesseringen.",details:null}}finally{this.isUpdating=!1}},async manualSearch(){if(this.search_by_company_name)try{const e=await p.A.get(`http://localhost:8080/SeleniumScrap/search_by_company_name?company_name=${this.search_by_company_name}`);this.status=e.data.status,this.searchResults=e.data}catch(e){console.error("Feil ved manuell søk:",e),this.status="Feil ved manuell søk.",this.searchResults=null}else this.status="Vennligst skriv inn en bedrift."},openPopup1(){this.showPopup1=!0},openPopup2(){this.showPopup2=!0},closePopup1(){this.showPopup1=!1},closePopup2(){this.showPopup2=!1},openPopup3(){this.showPopup3=!0},closePopup3(){this.showPopup3=!1}}};const ae=(0,k.A)(oe,[["render",c],["__scopeId","data-v-7ae60266"]]);var re=ae,ie={name:"App",components:{FrontEnd:re}};const le=(0,k.A)(ie,[["render",a]]);var ce=le;(0,s.Ef)(ce).mount("#app")}},t={};function n(s){var o=t[s];if(void 0!==o)return o.exports;var a=t[s]={exports:{}};return e[s](a,a.exports,n),a.exports}n.m=e,function(){var e=[];n.O=function(t,s,o,a){if(!s){var r=1/0;for(p=0;p<e.length;p++){s=e[p][0],o=e[p][1],a=e[p][2];for(var i=!0,l=0;l<s.length;l++)(!1&a||r>=a)&&Object.keys(n.O).every((function(e){return n.O[e](s[l])}))?s.splice(l--,1):(i=!1,a<r&&(r=a));if(i){e.splice(p--,1);var c=o();void 0!==c&&(t=c)}}return t}a=a||0;for(var p=e.length;p>0&&e[p-1][2]>a;p--)e[p]=e[p-1];e[p]=[s,o,a]}}(),function(){n.d=function(e,t){for(var s in t)n.o(t,s)&&!n.o(e,s)&&Object.defineProperty(e,s,{enumerable:!0,get:t[s]})}}(),function(){n.g=function(){if("object"===typeof globalThis)return globalThis;try{return this||new Function("return this")()}catch(e){if("object"===typeof window)return window}}()}(),function(){n.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)}}(),function(){n.r=function(e){"undefined"!==typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})}}(),function(){var e={524:0};n.O.j=function(t){return 0===e[t]};var t=function(t,s){var o,a,r=s[0],i=s[1],l=s[2],c=0;if(r.some((function(t){return 0!==e[t]}))){for(o in i)n.o(i,o)&&(n.m[o]=i[o]);if(l)var p=l(n)}for(t&&t(s);c<r.length;c++)a=r[c],n.o(e,a)&&e[a]&&e[a][0](),e[a]=0;return n.O(p)},s=self["webpackChunktheemailfinder"]=self["webpackChunktheemailfinder"]||[];s.forEach(t.bind(null,0)),s.push=t.bind(null,s.push.bind(s))}();var s=n.O(void 0,[504],(function(){return n(382)}));s=n.O(s)})();
//# sourceMappingURL=app.da4a1170.js.map