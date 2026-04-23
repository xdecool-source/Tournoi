// loginAdmin
// demande un mot de passe
// active le mode admin
// affiche le bouton logout
// recharge le joueur (check())
// affiche une erreur
// logoutAdmin()
// désactive le mode admin

import { resetInterface } from "./reset.js";
import { openModal } from "./modal.js";
import { currentPlayer } from "./state.js";


export async function loginAdmin(){
    // console.log("LOGIN FRONT CALLED "); 

    const pwd = prompt("Mot de passe admin");
    
    if(!pwd) return;
    const res = await fetch("/login-admin",{
        method:"POST",
        credentials: "include",  
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({pwd})
    });

    const data = await res.json();
    if(data.success){
        const adminBtn = document.querySelector("button[onclick='loginAdmin()']");
        const logoutBtn = document.getElementById("logoutBtn");

        if(adminBtn) adminBtn.style.display="none";
        if(logoutBtn) logoutBtn.style.display="block";

            // await window.check(); 
            // juste rafraîchir l'affichage sans relancer tout

        if(currentPlayer){
            setTimeout(() => {
                window.check();   // RELOAD COMPLET AVEC isAdmin
            }, 200);
        }
    }else{
        openModal("Mot de passe incorrect");
    }
    setTimeout(()=>{
        document.getElementById("licence")?.focus();
    },100);
}

export async function logoutAdmin(){

    await fetch("/logout-admin",{
        method:"POST",
        credentials: "include" 
    });
    localStorage.removeItem("isAdmin");     
    const adminBtn = document.querySelector("button[onclick='loginAdmin()']");
    const logoutBtn = document.getElementById("logoutBtn");
    
    if(adminBtn) adminBtn.style.display="block";
    if(logoutBtn) logoutBtn.style.display="none";
    resetInterface();
    setTimeout(()=>{
        document.getElementById("licence")?.focus();
    },100);
}