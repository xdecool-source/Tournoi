// Envoie un code par mail 
// puis vérifie ce code pour valider l’email avant l’inscription.

import { setEmailVerified } from "./state.js";

export async function sendCode(){
    console.log("SEND CODE CLICK");   // test
    const email = document.getElementById("email").value.trim();
    const res = await fetch("/send-code",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({email})
    });
    const data = await res.json();
    console.log(data);
    if(!data.success){
        alert(data.error);
        return;
    }
    // alert("Code envoyé");
}

export async function verifyCode(){

    console.log("VERIFY CLICK");
    const email = document.getElementById("email").value;
    const code = document.getElementById("verificationCode").value;
    const res = await fetch("/verify-code",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({email,code})
    });
    const data = await res.json();
    if(data.success){
        // alert("Email vérifié");
        console.log("VERIFY SUCCESS", data);
        setEmailVerified(true);
        // verrouiller email
        document.getElementById("email").disabled = true;
        // masquer champs email + code
        const emailRow = document.querySelector(".email-row");
        const codeRow = document.querySelector(".code-row");
        if(emailRow) emailRow.style.display="none";
        if(codeRow) codeRow.style.display="none";
            // afficher tableaux
        document
      .getElementById("tableauxContainer")
      .classList.remove("hidden");
        // afficher bouton valider
        const btnValider = document.getElementById("btnValider");
        if(btnValider) btnValider.style.display="block";

    }else{
        alert("Code incorrect");
    }
}
