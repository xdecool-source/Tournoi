

import { loginAdmin, logoutAdmin } from "./admin.js"
import { sendInscription } from "./inscription.js"
import { loadPlaces } from "./places.js"
import { loadTableaux } from "./tables.js"
import { resetInterface } from "./reset.js"
import { openModal, closeModal } from "./modal.js"
import { places, setCurrentPlayer, setJoueurPoints, setEmailVerified  } from "./state.js"
import { sendCode, verifyCode } from "./mail.js"
import { showRecap } from "./recap.js"
import { renderTableaux, limitSelection } from "./renderTableaux.js"
console.log("JS START")

window.loginAdmin = loginAdmin;
window.logoutAdmin = logoutAdmin;
window.sendInscription = sendInscription;
window.places = places;
window.check = check;
window.closeModal = closeModal;
window.sendCode = sendCode;
window.verifyCode = verifyCode;
window.limitSelection = limitSelection;
window.showRecap = showRecap
window.renderTableaux = renderTableaux

console.log("APP JS LOADED");


async function init(){
    console.log("INIT RUN");
    updateAdminButtons();
    const tableaux = await loadTableaux()
    await loadPlaces()
    renderTableaux(tableaux, places)

     // focus automatique licence
    setTimeout(()=>{
        document.getElementById("licence")?.focus();
    },200);


    // déclenche check quand on appuie sur Entrée
    document.getElementById("licence").addEventListener("keydown", e=>{
        if(e.key === "Enter"){
            check();
        }
    });

    const licenceInput = document.getElementById("licence");
    
    licenceInput.addEventListener("click", () => {
        resetInterface();          // remet l'interface à zéro
        //licenceInput.value = "";   // vide la licence
        //licenceInput.focus();      // remet le curseur
        licenceInput.select();   // sélectionne tout le texte
    });

    

        

    



}

let checkTimer = null;
async function check(){
    console.log("CHECK START");
    resetInterface();   // ← remet toute l'interface à zéro
    const input = document.getElementById("licence");
    if(!input) return;
    const lic = input.value.trim();
    if(!lic) return;
    clearTimeout(checkTimer);
    checkTimer = setTimeout(async ()=>{
        const isAdmin = document.cookie.includes("admin=1");
        if(!/^\d+$/.test(lic)){
            openModal("Licence numérique obligatoire");
            return;
        }
        try{
            const r = await fetch("/licence/" + lic);
            if(!r.ok){
                const text = await r.text();
                try{
                    const err = JSON.parse(text);
                    openModal(err.detail || "Licence inexistante");
                }catch{
                    openModal("Licence inexistante");
                }
                return;
            }
            const data = await r.json();

            if(isAdmin){

                setEmailVerified(true);

                const emailRow = document.querySelector(".email-row");
                const codeRow = document.querySelector(".code-row");

                if(emailRow) emailRow.style.display = "none";
                if(codeRow) codeRow.style.display = "none";

                document
                .getElementById("tableauxContainer")
                .classList.remove("hidden");

                const btnValider = document.getElementById("btnValider");
                if(btnValider) btnValider.style.display = "block";

            }
            setCurrentPlayer(data);
            const errBox = document.getElementById("licenceError");
            // cacher message si licence valide
            if(errBox){
                errBox.classList.add("hidden");
            }
            if(!data.fftt){
                // message inline
                if(errBox){
                    errBox.innerText = "Licence inconnue FFTT";
                    errBox.classList.remove("hidden");
                }

                // masquer tableaux
                document.getElementById("tableauxContainer").innerHTML="";

                // masquer inscription
                const card = document.getElementById("inscriptionCard");
                if(card){
                    card.style.display="none";
                    card.classList.add("hidden");
                }

                return; // STOP ici
            }

            setJoueurPoints(data.points ? Number(data.points) : 9999);
            const res = document.getElementById("result");
            if(res){
                res.innerHTML = `
                    <b>${data.prenom||""} ${data.nom||""}</b><br>
                    Club: ${data.club||""}<br>
                    Points: ${data.points||""}`;
            }
            const card = document.getElementById("inscriptionCard");
            if(card){
                card.classList.remove("hidden");
                card.style.display="block";
            }
            const mailInput = document.getElementById("email");
            if(mailInput){
                mailInput.value = data.mail || "";

                // focus automatique email
                setTimeout(()=>{
                    mailInput.focus();
                },120);
            }
            await loadTableaux();
            await loadPlaces();
            renderTableaux();

            if(data.already_inscrit){
                // cacher verification email
                const emailRow = document.querySelector(".email-row");
                const codeRow = document.querySelector(".code-row");
                if(emailRow) emailRow.style.display = "none";
                if(codeRow) codeRow.style.display = "none";
                // afficher tableaux
                document
                .getElementById("tableauxContainer")
                .classList.remove("hidden");

                const msg = document.getElementById("alreadyMsg");

                if (msg) {
                    if (!isAdmin) {
                        msg.classList.remove("hidden");
                        msg.innerHTML = `
                            Vous êtes déjà inscrit.<br>
                            Pour modifier votre inscription<br>
                            merci d'envoyer un mail à <br>
                            <a href="mailto:thuirtt66@gmail.com"
                            style="color:red;text-decoration:underline;">
                            thuirtt66@gmail.com
                            </a>
                        `;
                    } else {
                        msg.classList.add("hidden");
                        msg.innerHTML = "";
                    }
                }
            data.tableaux_inscrits?.forEach(t=>{
                const el = document.querySelector(`input[value="${t}"]`);
                if(el){
                    el.checked = true;
                    el.disabled = !isAdmin; // admin peut modifier
                }
            });
                const btn = document.querySelector("button[onclick='sendInscription()']");
                if(btn){
                    if(!isAdmin){
                        btn.disabled = true;
                        btn.innerText = "Déjà inscrit";
                        btn.style.opacity = 0.5;
                    }else{
                        btn.disabled = false;
                        btn.innerText = "Modifier inscription";
                        btn.style.opacity = 1;
                    }
                }
            }
   
        }catch(e){
            console.error("check error", e);
            openModal("Erreur serveur licence");
        }
    }, 250);
}

function updateAdminButtons(){

    const isAdmin = document.cookie.includes("admin=1");

    const adminBtn  = document.querySelector("button[onclick='loginAdmin()']");
    const logoutBtn = document.getElementById("logoutBtn");
    if(isAdmin){
        if(adminBtn) adminBtn.style.display = "none";
        if(logoutBtn) logoutBtn.style.display = "block";
    }else{
        if(adminBtn) adminBtn.style.display = "block";
        if(logoutBtn) logoutBtn.style.display = "none";
    }
}

window.addEventListener("load", init)
