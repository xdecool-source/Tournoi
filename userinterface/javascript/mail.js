// Envoie un code par mail 
// puis vérifie ce code pour valider l’email avant l’inscription.

import { setEmailVerified } from "./state.js";

document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("sendCodeBtn");

    if(btn){
        // reset état bouton
        btn.disabled = false;
        btn.innerText = "Valide ton mail";

        // ajout du click
        btn.addEventListener("click", sendCode);
    }
});


export async function sendCode(){

    const btn = document.getElementById("sendCodeBtn");
    if(!btn){
        console.error("Bouton introuvable");
        return;
    }
    const email = document.getElementById("email").value.trim();

    // état envoi

    btn.innerText = "Envoi...";
    btn.disabled = true;
    let res;
    try {
        res = await fetch("/send-code",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({email})
        });
    } catch(e){
        alert("Erreur réseau");
        btn.innerText = "Valide ton mail";
        btn.disabled = false;
        return;
    }

    let data = null;
    try{
        data = await res.json();
    }catch(e){
        console.error("Erreur parsing JSON");
    }

    if(!data){
        alert("Erreur serveur");
        btn.innerText = "Envoyer le code";
        btn.disabled = false;
        return;
    }

    if(!data.success){
        alert(data.error || "Code déjà envoyé");
        btn.innerText = "Valide ton mail";
        btn.disabled = false;
        return;
    }

    // succès

    btn.innerText = "Code envoyé ✅";

    //  reset automatique après 10s

    setTimeout(() => {
        btn.innerText = "Valide ton mail";
        btn.disabled = false;
    }, 10000);
}


export async function verifyCode(){

    // Bypass pour le dev
    if (window.ENVCODE === "dev") {

        setEmailVerified(true);

        document.getElementById("email").disabled = true;

        const emailRow = document.querySelector(".email-row");
        const codeRow = document.querySelector(".code-row");
        if(emailRow) emailRow.style.display="none";
        if(codeRow) codeRow.style.display="none";

        document.getElementById("tableauxContainer").classList.remove("hidden");

        const btnValider = document.getElementById("btnValider");
        if(btnValider) btnValider.style.display="block";

        return;
    }

    // mode normal
    const email = document.getElementById("email").value;
    const code = document.getElementById("verificationCode").value;

    const res = await fetch("/verify-code",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({email,code})
    });

    const data = await res.json();

    if(data.success){
        setEmailVerified(true);

        document.getElementById("email").disabled = true;

        const emailRow = document.querySelector(".email-row");
        const codeRow = document.querySelector(".code-row");
        if(emailRow) emailRow.style.display="none";
        if(codeRow) codeRow.style.display="none";

        document
          .getElementById("tableauxContainer")
          .classList.remove("hidden");

        const btnValider = document.getElementById("btnValider");
        if(btnValider) btnValider.style.display="block";

    }else{
        alert("Code incorrect");
    }
}
