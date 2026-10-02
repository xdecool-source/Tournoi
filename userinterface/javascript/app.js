// Vérifie une licence, récupère les infos d’un joueur
// Affiche et gère son inscription à un tournoi (avec gestion admin, email, tableaux, etc.).

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
import { setIsAdmin } from "./state.js";
import { FROM_EMAIL, DATE_TOURNOI, DATE_TOURNOI_JOUR, NBRE_TABLEAU, NOM_TOURNOI, ORIGINE_EMAIL } from "./config.js";

window.loginAdmin = loginAdmin;
window.logoutAdmin = logoutAdmin;
window.sendInscription = sendInscription;
window.places = places;
window.closeModal = closeModal;
window.sendCode = sendCode;
window.verifyCode = verifyCode;
window.limitSelection = limitSelection;
window.showRecap = showRecap
window.renderTableaux = renderTableaux

window.openListeInscrits = function () {
    window.open("/export-inscrits", "fenetre_inscrits");
}

// reveil database 
document.addEventListener("DOMContentLoaded", () => {
    fetch("/wake-db").catch(() => {});
});

let tableauxGlobal = null;
window.updateAdminButtons = updateAdminButtons;

async function init(){

    // console.log("INIT RUN");
    updateAdminButtons();
    tableauxGlobal  = await loadTableaux()
    await loadPlaces()
    renderTableaux(tableauxGlobal, places, null, false, [], false)

     // focus automatique licence
    // déclenche check quand on appuie sur Entrée
    document.getElementById("licence").addEventListener("keydown", e=>{
        if(e.key === "Enter"){
            check();
        }
    });

    const licenceInput = document.getElementById("licence");
    if(licenceInput){
        licenceInput.addEventListener("click", () => {
            // console.log("CLICK OK"); // test

            resetInterface();
            licenceInput.select();
        });
        
    }
}

let checkTimer = null;
async function check(){

    // console.log("CHECK START");
    // remet toute l'interface à zéro
    resetInterface();

    // const isAdmin = localStorage.getItem("isAdmin") === "1";
    const input = document.getElementById("licence");
    if(!input) return;
    const lic = input.value.trim();
    if(!lic) return;

    // cacher bouton liste inscrits et admin 
    // mode ADMIN : licence 000
    const btnListe = document.getElementById("btnListeInscrits");
    if(btnListe){
        btnListe.style.display = "block";
    }
    const adminBtn = document.getElementById("adminBtn");
    const emailRow = document.querySelector(".email-row");
    const codeRow = document.querySelector(".code-row");
    const inscriptionCard = document.getElementById("inscriptionCard");
    const selectionTitre = document.getElementById("selectionTitre");
    const tableauxContainer = document.getElementById("tableauxContainer");
    const totalPrix = document.getElementById("totalPrix");
    const licence = input.value.trim();

    // Licence spéciale ADMIN = 000

    if(licence === "000"){
        
        // Afficher Admin uniquement sur grand écran
        if(adminBtn){
            if(window.innerWidth > 600)
                {adminBtn.style.display = "block";}
            else{adminBtn.style.display = "none";}
        }

        // Masquer complètement la partie inscription
        if(inscriptionCard){
            inscriptionCard.classList.add("hidden");
            inscriptionCard.style.display = "none";
        }

        // Masquer email
        if(emailRow){emailRow.style.display = "none";}

        // Masquer code
        if(codeRow){codeRow.style.display = "none";}

        // Masquer les tableaux
        if(selectionTitre){
            selectionTitre.classList.add("hidden");
            selectionTitre.style.display = "none";
        }
        if(tableauxContainer){
            tableauxContainer.classList.add("hidden");
            tableauxContainer.style.display = "none";
        }
        if(totalPrix){
            totalPrix.classList.add("hidden");
            totalPrix.style.display = "none";
        }

        // Ne pas afficher la liste des inscrits ici
        // if(btnListe){btnListe.style.display = "none";}
        // Annuler un éventuel ancien timer
        clearTimeout(checkTimer);

        // IMPORTANT :
        // ne surtout pas continuer vers /licence/000
        return;
    }

    // Licence normale
    if(adminBtn){adminBtn.style.display = "none";}
    if(emailRow){emailRow.style.display = "";}
    if(codeRow){codeRow.style.display = "";}
    if(inscriptionCard){inscriptionCard.style.display = "";}
    if(selectionTitre){selectionTitre.style.display = "";}
    if(tableauxContainer){tableauxContainer.style.display = "";}
    if(totalPrix){totalPrix.style.display = "";}

    clearTimeout(checkTimer);
    checkTimer = setTimeout(async ()=>{
        const resAdmin = await fetch("/me", {
            credentials: "include"
        });

        const dataAdmin = await resAdmin.json();

        // console.log("ADMIN BACK:", dataAdmin);
        setIsAdmin(dataAdmin.admin);
        const isAdmin = dataAdmin.admin; 

        if (!/^\d+$/.test(lic)) {
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
            if (data.admin) {const adminBtn = document.getElementById("adminBtn");
                if (adminBtn) {adminBtn.style.display = "block";}
                // openModal("Mode administrateur détecté");
                return;
            }

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
            if(errBox){errBox.classList.add("hidden");}
            if(!data.fftt){
                // message inline

                if(errBox){
                    errBox.innerText = "Licence inconnue FFTT";
                    errBox.classList.remove("hidden");
                }

                // masquer tableaux
                // xx document.getElementById("tableauxContainer").innerHTML="";
                document.getElementById("selectionTitre").classList.remove("hidden");
                document.getElementById("tableauxContainer").classList.remove("hidden");

                // masquer inscription
                const card = document.getElementById("inscriptionCard");
                if(card){
                    card.style.display="none";
                    card.classList.add("hidden");
                }
                return; 
            }
            setJoueurPoints(data.points ? Number(data.points) : 9999);
            const res = document.getElementById("result");
            if(res){
                res.innerHTML = `<strong>${data.prenom || ""} ${data.nom || ""}</strong><br>
                Club: ${data.club || ""}<br>
                Points: ${data.points || ""}`;
            }
            const card = document.getElementById("inscriptionCard");
            if(card){
                card.classList.remove("hidden");
            }
            const mailInput = document.getElementById("email");
            if(mailInput){
                mailInput.value = data.mail || "";

                // focus automatique email
                requestAnimationFrame(() => {
                    try{
                        mailInput.focus({preventScroll:true});
                    }catch(e){
                        mailInput.focus();
                    }
                });
            }
    
            await loadPlaces();
            renderTableaux(
                tableauxGlobal,
                places,
                Number(data.points),
                data.already_inscrit,
                data.tableaux_inscrits || [],
                isAdmin   //  important 
            );
            if(isAdmin){
                document.querySelectorAll("#tableauxContainer input").forEach(cb => {
                    cb.disabled = false;
                });
            }
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
                    console.log("MSG =", document.getElementById("alreadyMsg"));
                    msg.className = "infoBox";

                    // variable FROM_EMAIL initiliser dans config.js
                    if (!isAdmin) {
                        msg.innerHTML = `
                            <h2 style="font-size: 0.9rem;">Vous êtes inscrit.</h2>
                            Vérifiez vos choix comme suit :  
                            <span style="color:#007bff;">☑️</span> 
                            <br>
                            Si vous souhaitez modifier votre inscription <br>
                            merci d'envoyer un e-mail avec : <br>
                            <h2 style="font-size: 0.8rem;" ><b>vos choix et votre numéro de licence</b> à <br></h2>
                            <a href="mailto:${ORIGINE_EMAIL}"
                            style="color:red;text-decoration:underline;">
                            ${ORIGINE_EMAIL}
                            </a>
                        `;
                    } else {
                        msg.classList.add("hidden");
                        msg.innerHTML = "";
                    }
                }
                const btn = document.querySelector("button[onclick='sendInscription()']");
                // const adminBtn = document.getElementById("adminBtn");
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
        }
        catch(e){

            console.error("CHECK ERROR =", e);
            openModal("Erreur serveur licence");
        }
    }, 250);
}

window.check = check;

async function updateAdminButtons(){

    const res = await fetch("/me", {
        credentials: "include"   
    });
    const data = await res.json();
    const isAdmin = data.admin;
    // const adminBtn  = document.querySelector("button[onclick='loginAdmin()']");
    const adminBtn = document.getElementById("adminBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    if(isAdmin){
        if(adminBtn) adminBtn.style.display = "none";
        if(logoutBtn) logoutBtn.style.display = "block";
    }else{
        if(adminBtn) adminBtn.style.display = "none";
        if(logoutBtn) logoutBtn.style.display = "none";
    }
}

window.addEventListener("load", init)

// positionne le cursur dans la zone de saisie du N° de licence 

window.addEventListener("load", () => {
    setTimeout(() => {
        const licence = document.getElementById("licence");
        if (licence) {
            licence.focus();
            licence.select();
        }
    }, 100);
});
