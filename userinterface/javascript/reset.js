// réinitialisation interface.
// Il remet toute l’interface à zéro (données, champs, boutons, affichage).

import { setCurrentPlayer, setJoueurPoints, setEmailVerified } from "./state.js";

export function resetInterface(){

    setCurrentPlayer(null);
    setJoueurPoints(null);
    setEmailVerified(false);

    const btnValider = document.getElementById("btnValider");
    if(btnValider) btnValider.style.display = "none";

    // remettre affichage cartes

    document.getElementById("licenceCard")?.classList.remove("hidden");
    document.getElementById("inscriptionCard")?.classList.add("hidden");
    document.getElementById("recapCard")?.classList.add("hidden");

// vider recap

const recapContent = document.getElementById("recapContent");
if(recapContent) recapContent.textContent = "";

const res = document.getElementById("result");
if(res) res.textContent = "";
    
    // vider email

    const mail = document.getElementById("email");
    if(mail){
        mail.value = "";
        mail.disabled = false;   
        
        // réactive le champ email
    }

    // vider code

    const code = document.getElementById("verificationCode");
    if(code) code.value = "";

    // réafficher email + code

    const emailRow = document.querySelector(".email-row");
    const codeRow = document.querySelector(".code-row");
    if(emailRow) emailRow.style.display = "flex";
    if(codeRow) codeRow.style.display = "flex";

    // cacher tableaux

    const tableaux = document.getElementById("tableauxContainer");
    if(tableaux) tableaux.classList.add("hidden");

    // masquer message déjà inscrit

    const msg = document.getElementById("alreadyMsg");
    if(msg){
        msg.classList.add("hidden");
        msg.innerHTML = "";
    }
    // réactiver bouton inscription

    const btn = document.querySelector("button[onclick='sendInscription()']");
    if(btn){
        btn.disabled = false;
        btn.innerText = "Valider";
        btn.style.opacity = 1;
    }
    // réactiver bouton envoyer code

    const sendBtn = document.querySelector("button[onclick='sendCode()']");
    if(sendBtn) sendBtn.disabled = false;

    // décocher tableaux
    
    document.querySelectorAll("#tableauxContainer input").forEach(el=>{
        el.checked = false;
        el.disabled = false;
    });
}